"""Similar incident retrieval using embedding-based vector search."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from src.core.config import get_settings
from src.core.embeddings import cosine_similarity, get_embedding_service
from src.core.incident_store import list_incidents
from src.core.logging import get_logger
from src.core.models import Incident
from src.core.utils import enum_val
from src.core.vector_db import get_vector_db_instance

logger = get_logger(__name__)
settings = get_settings()

COLLECTION = "incidents"


def _incident_to_searchable(incident: Incident) -> str:
    """Build a textual representation of an incident for embedding."""
    parts = [
        incident.title,
        incident.description,
        enum_val(incident.severity),
        enum_val(incident.category),
        incident.root_cause or "",
    ]
    parts.extend(incident.affected_services)
    parts.extend(incident.affected_resources)
    parts.extend(incident.tags)
    return " ".join(p for p in parts if p)


async def index_incident(incident: Incident) -> None:
    """Index an incident into the vector DB for future similarity search."""
    embedding_service = get_embedding_service()
    text = _incident_to_searchable(incident)
    embedding = await embedding_service.embed_text(text)

    vector_db = get_vector_db_instance()
    if vector_db is None:
        logger.debug(
            "No vector DB available; skipping incident indexing",
            incident_id=str(incident.id),
        )
        return

    try:
        await vector_db.add_documents(
            collection=COLLECTION,
            documents=[text],
            embeddings=[embedding],
            metadatas=[
                {
                    "incident_id": str(incident.id),
                    "title": incident.title,
                    "severity": enum_val(incident.severity),
                    "category": enum_val(incident.category),
                    "status": enum_val(incident.status),
                    "affected_services": incident.affected_services,
                    "root_cause": incident.root_cause or "",
                    "resolution": incident.resolution or "",
                }
            ],
            ids=[str(incident.id)],
        )
        logger.info("Indexed incident", incident_id=str(incident.id))
    except Exception as exc:
        logger.warning("Failed to index incident", incident_id=str(incident.id), error=str(exc))


async def find_similar(
    incident: Incident,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Find incidents similar to the given one.

    Tries vector DB first, then falls back to brute-force comparison against
    the in-memory incident store.
    """
    embedding_service = get_embedding_service()
    text = _incident_to_searchable(incident)
    query_embedding = await embedding_service.embed_text(text)

    # --- vector DB path ---
    vector_db = get_vector_db_instance()
    if vector_db is not None:
        try:
            results = await vector_db.search(
                collection=COLLECTION,
                query_embedding=query_embedding,
                n_results=limit + 1,  # +1 to exclude self
            )
            entries = _format_vector_results(results, incident.id, limit)
            if entries:
                return entries
        except Exception as exc:
            logger.warning("Vector similarity search failed; using local fallback", error=str(exc))

    # --- local fallback: brute-force against in-memory incidents ---
    return _brute_force_search(query_embedding, incident.id, limit)


def _format_vector_results(
    results: dict[str, Any],
    exclude_id: UUID,
    limit: int,
) -> list[dict[str, Any]]:
    """Normalise vector DB results, excluding the query incident itself.

    Args:
        results: Raw response from the vector DB search.
        exclude_id: Incident ID to exclude from results.
        limit: Maximum number of entries to return.

    Returns:
        List of incident-like dicts with score, title, severity, etc.
    """
    entries: list[dict[str, Any]] = []
    ids = results.get("ids", [])
    metadatas = results.get("metadatas", [])
    distances = results.get("distances", [])

    for idx, doc_id in enumerate(ids):
        if str(doc_id) == str(exclude_id):
            continue
        meta = metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {}
        distance = distances[idx] if idx < len(distances) else None
        score = 1.0 - float(distance) if distance is not None else None
        entries.append(
            {
                "incident_id": doc_id,
                "title": meta.get("title", ""),
                "severity": meta.get("severity", ""),
                "category": meta.get("category", ""),
                "status": meta.get("status", ""),
                "root_cause": meta.get("root_cause", ""),
                "resolution": meta.get("resolution", ""),
                "affected_services": meta.get("affected_services", []),
                "score": score,
            }
        )
        if len(entries) >= limit:
            break
    return entries


def _brute_force_search(
    query_embedding: list[float],
    exclude_id: UUID,
    limit: int,
) -> list[dict[str, Any]]:
    """Fallback: compare query embedding against all in-memory incidents using cosine similarity."""
    embedding_service = get_embedding_service()
    all_incidents = list_incidents()
    candidates = [inc for inc in all_incidents if inc.id != exclude_id]
    if not candidates:
        return []

    texts = [_incident_to_searchable(inc) for inc in candidates]
    # Use the local embedding (no async needed since _local_embedding is sync)
    candidate_embeddings = [embedding_service._local_embedding(t) for t in texts]

    scored: list[tuple[float, Incident]] = []
    for inc, emb in zip(candidates, candidate_embeddings, strict=False):
        sim = cosine_similarity(query_embedding, emb)
        scored.append((sim, inc))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    results: list[dict[str, Any]] = []
    for score, inc in scored[:limit]:
        results.append(
            {
                "incident_id": str(inc.id),
                "title": inc.title,
                "severity": enum_val(inc.severity),
                "category": enum_val(inc.category),
                "status": enum_val(inc.status),
                "root_cause": inc.root_cause or "",
                "resolution": inc.resolution or "",
                "affected_services": inc.affected_services,
                "score": round(score, 4),
            }
        )
    return results
