# Aegis — "Multi-Agent AI Incident Response Platform"
## Vector Database

## Purpose

Document vector database integration, supported backends, configuration, and search strategies.

## Source Traceability

| Component | File |
|---|---|
| Vector DB abstract client | `src/core/vector_db.py:15-65` |
| ChromaDB client | `src/core/vector_db.py:68-184` |
| pgvector client | `src/core/vector_db.py:186-335` |
| Vector DB factory | `src/core/vector_db.py:338-345` |
| Embedding service | `src/core/embeddings.py` |
| Knowledge base search | `src/core/knowledge_base.py` |
| Similar incident search | `src/core/similar_incidents.py` |
| Vector DB settings | `src/core/config.py:65-83` |

## Supported Backends

### ChromaDB

Class: `ChromaVectorDB` (`src/core/vector_db.py:68-184`)

- **Connection:** Async HTTP client via `chromadb.AsyncHttpClient`
- **Default host:** `localhost:8000` (chroma default port in Docker: `8100`)
- **Collection management:** Client-side cache of collections
- **Search:** Cosine distance via `hnsw:space` metadata
- **Auth:** Configurable auth token via `VECTOR_DB_CHROMA_AUTH_TOKEN`
- **SSL:** Configurable via `VECTOR_DB_CHROMA_SSL`

### pgvector

Class: `PgVectorDB` (`src/core/vector_db.py:186-335`)

- **Connection:** Via existing asyncpg connection from `get_db_context()`
- **Table creation:** Auto-creates tables with IVFFlat index on first use
- **Index type:** `vector_cosine_ops` with 100 lists
- **Search:** Cosine distance (`<=>` operator)
- **Filtering:** JSONB metadata `->>` queries

## Embeddings

The `EmbeddingService` (`src/core/embeddings.py`) produces vectors used by both backends:

1. **API mode** — Uses `AsyncOpenAI` client configured via `LLM` settings
2. **Local fallback** — BLAKE2b hash-based deterministic embeddings for offline development

The local embedding algorithm:
- Tokenize text on word boundaries
- Hash each token with BLAKE2b
- Map hash to vector index with sign from hash byte
- L2-normalize the final vector

## Search Strategies

### Knowledge Base Search (`src/core/knowledge_base.py`)

```
search_knowledge_entries(query, category, top_k)
  ├─ Embed query text
  ├─ Try vector DB search (with category filter)
  │   ├─ Success → return formatted results
  │   └─ Failure → fall through
  └─ Search seed corpus
      ├─ Embed all matching seed entries
      ├─ Hybrid scoring: 70% semantic + 30% lexical
      └─ Return top_k sorted by score
```

### Similar Incident Search (`src/core/similar_incidents.py`)

```
find_similar(incident, limit)
  ├─ Build searchable text from incident
  ├─ Embed searchable text
  ├─ Try vector DB search (exclude self)
  │   ├─ Success → return formatted results
  │   └─ Failure → fall through
  └─ Brute force: compare against all in-memory incidents
      ├─ Embed each incident (local fallback)
      ├─ Cosine similarity
      └─ Return top limit sorted by score
```

## Seed Knowledge Corpus

The `SEED_KNOWLEDGE` list (`src/core/knowledge_base.py:16-80`) contains 5 bundled runbooks:

| ID | Topic |
|---|---|
| runbook-api-latency | API latency remediation |
| runbook-database-connections | Database connection exhaustion |
| runbook-kubernetes-crashloop | Kubernetes CrashLoopBackOff |
| runbook-cache-pressure | Cache pressure remediation |
| runbook-network-errors | Network error spike |

These are used when no vector DB is available.

## Collection Naming

- **Knowledge base:** Configured via `VECTOR_DB_COLLECTION_NAME` (default: `knowledge_base`)
- **Incidents:** Hard-coded as `"incidents"` in `similar_incidents.py:19`
- **pgvector tables:** Prefix configurable via `VECTOR_DB_PGVECTOR_TABLE_PREFIX` (default: `vec_`)

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `VECTOR_DB_PROVIDER` | pgvector | Backend selection |
| `VECTOR_DB_EMBEDDING_DIMENSION` | 4096 | Vector dimension |
| `VECTOR_DB_EMBEDDING_MODEL` | text-embedding-3-small | Embedding model |
| `VECTOR_DB_COLLECTION_NAME` | knowledge_base | Default collection |
| `VECTOR_DB_CHROMA_HOST` | localhost | ChromaDB host |
| `VECTOR_DB_CHROMA_PORT` | 8000 | ChromaDB port |
| `VECTOR_DB_PGVECTOR_TABLE_PREFIX` | vec_ | pgvector prefix |

## Limitations

- **pgvector SQL injection:** Table names are composed via f-strings. Functionally safe if confirmed to PostgreSQL's identifier quoting but flagged by static analysis.
- **No connection pooling for ChromaDB:** The async ChromaDB client is created fresh on initialize.
- **No vector DB health checks:** The system does not verify vector DB connectivity at startup.
- **pgvector requires shared session:** The `PgVectorDB` uses `get_db_context()` which shares the application's database pool.
