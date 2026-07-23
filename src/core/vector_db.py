"""Vector database configuration and operations."""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import text

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VectorDBClient(ABC):
    """Abstract base class for vector database clients."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector database."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the vector database connection."""
        pass

    @abstractmethod
    async def add_documents(
        self,
        collection: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add documents to collection."""
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def get_collection(self, name: str) -> Any:
        """Get or create collection."""
        pass

    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """Delete collection."""
        pass

    @abstractmethod
    async def list_collections(self) -> list[str]:
        """List all collections."""
        pass


class ChromaVectorDB(VectorDBClient):
    """ChromaDB vector database client."""

    def __init__(self):
        self.client: Any | None = None
        self._collections: dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize ChromaDB client."""
        import chromadb

        self.client = await chromadb.AsyncHttpClient(
            host=settings.vector_db.chroma_host,
            port=settings.vector_db.chroma_port,
            ssl=settings.vector_db.chroma_ssl,
        )
        logger.info("ChromaDB client initialized", host=settings.vector_db.chroma_host)

    async def close(self) -> None:
        """Close ChromaDB client."""
        if self.client:
            # Chroma async client doesn't have explicit close
            self.client = None
            logger.info("ChromaDB client closed")

    async def get_collection(self, name: str) -> Any:
        """Get or create collection."""
        if name in self._collections:
            return self._collections[name]

        if not self.client:
            await self.initialize()

        collection = await self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
        self._collections[name] = collection
        return collection

    async def add_documents(
        self,
        collection: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add documents to ChromaDB collection."""
        coll = await self.get_collection(collection)

        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{} for _ in documents]

        await coll.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.debug("Added documents to ChromaDB", collection=collection, count=len(documents))
        return ids

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar documents."""
        coll = await self.get_collection(collection)

        results = await coll.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances", "embeddings"],
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
            "embeddings": results["embeddings"][0] if results["embeddings"] else [],
        }

    async def delete_collection(self, name: str) -> bool:
        """Delete collection."""
        if not self.client:
            return False

        try:
            await self.client.delete_collection(name)
            self._collections.pop(name, None)
            logger.info("Deleted ChromaDB collection", name=name)
            return True
        except Exception as e:
            logger.error("Failed to delete ChromaDB collection", name=name, error=str(e))
            return False

    async def list_collections(self) -> list[str]:
        """List all collections."""
        if not self.client:
            await self.initialize()

        collections = await self.client.list_collections()
        return [c.name for c in collections]


class PgVectorDB(VectorDBClient):
    """PostgreSQL with pgvector extension client."""

    def __init__(self):
        self._pool: Any = None

    async def initialize(self) -> None:
        """Initialize pgvector - register vector type."""
        from pgvector.asyncpg import register_vector

        from src.core.database import get_db_context

        async with get_db_context() as session:
            connection = await session.connection()
            await register_vector(connection.sync_connection.connection.driver_connection)
        logger.info("pgvector initialized")

    async def close(self) -> None:
        """Close pgvector - nothing special needed."""
        pass

    async def get_collection(self, name: str) -> str:
        """Get collection name (table name in pgvector)."""
        # In pgvector, collections are tables
        # Ensure table exists
        from src.core.database import get_db_context

        async with get_db_context() as session:
            await session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {name} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    embedding VECTOR({settings.vector_db.embedding_dimension}),
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS {name}_embedding_idx
                ON {name} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """))
        return name

    async def add_documents(
        self,
        collection: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Add documents to pgvector table."""
        import uuid

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{} for _ in documents]

        from src.core.database import get_db_context

        async with get_db_context() as session:
            for doc_id, doc, emb, meta in zip(ids, documents, embeddings, metadatas, strict=False):
                await session.execute(
                    text(f"""
                        INSERT INTO {collection} (id, content, embedding, metadata)
                        VALUES (:id, :content, :embedding, :metadata)
                    """),
                    {
                        "id": doc_id,
                        "content": doc,
                        "embedding": emb,
                        "metadata": meta,
                    },
                )

        logger.debug("Added documents to pgvector", collection=collection, count=len(documents))
        return ids

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar documents in pgvector."""
        where_clause = ""
        params = {
            "embedding": query_embedding,
            "limit": n_results,
        }

        if where:
            conditions = []
            for key, value in where.items():
                param_name = f"where_{key}"
                conditions.append(f"metadata->>'{key}' = :{param_name}")
                params[param_name] = value
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT id, content, metadata, embedding,
                   1 - (embedding <=> :embedding) as similarity
            FROM {collection}
            {where_clause}
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """

        from src.core.database import get_db_context

        async with get_db_context() as session:
            result = await session.execute(text(query), params)
            rows = result.fetchall()

        return {
            "ids": [row.id for row in rows],
            "documents": [row.content for row in rows],
            "metadatas": [row.metadata for row in rows],
            "distances": [1 - row.similarity for row in rows],
            "embeddings": [row.embedding for row in rows],
        }

    async def delete_collection(self, name: str) -> bool:
        """Delete pgvector table."""
        try:
            from src.core.database import get_db_context

            async with get_db_context() as session:
                await session.execute(text(f"DROP TABLE IF EXISTS {name}"))
            logger.info("Deleted pgvector table", name=name)
            return True
        except Exception as e:
            logger.error("Failed to delete pgvector table", name=name, error=str(e))
            return False

    async def list_collections(self) -> list[str]:
        """List all pgvector tables."""
        from src.core.database import get_db_context

        async with get_db_context() as session:
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE '%_vec'
            """))
            return [row[0] for row in result.fetchall()]


# Factory function
def get_vector_db() -> VectorDBClient:
    """Get vector database client based on configuration."""
    if settings.vector_db.provider == "chroma":
        return ChromaVectorDB()
    elif settings.vector_db.provider == "pgvector":
        return PgVectorDB()
    else:
        raise ValueError(f"Unknown vector DB provider: {settings.vector_db.provider}")


# Global instance
_vector_db: VectorDBClient | None = None


async def init_vector_db() -> VectorDBClient:
    """Initialize and return vector database client."""
    global _vector_db
    _vector_db = get_vector_db()
    await _vector_db.initialize()
    return _vector_db


async def close_vector_db() -> None:
    """Close vector database client."""
    global _vector_db
    if _vector_db:
        await _vector_db.close()
        _vector_db = None


def get_vector_db_instance() -> VectorDBClient | None:
    """Get current vector DB instance."""
    return _vector_db
