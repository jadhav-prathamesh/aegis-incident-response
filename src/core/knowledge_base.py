"""Knowledge-base search backed by vector DB with local fallback corpus."""

from __future__ import annotations

from typing import Any

from src.core.config import get_settings
from src.core.embeddings import cosine_similarity, get_embedding_service
from src.core.logging import get_logger
from src.core.vector_db import get_vector_db_instance

logger = get_logger(__name__)
settings = get_settings()


SEED_KNOWLEDGE: list[dict[str, Any]] = [
    {
        "id": "runbook-api-latency",
        "title": "API latency remediation runbook",
        "category": "runbooks",
        "content": (
            "For application performance incidents, inspect recent deployments, "
            "check CPU, memory, database latency, downstream dependency errors, "
            "and scale service replicas when saturation is confirmed. "
            "Roll back only when latency correlates with a deployment."
        ),
        "tags": ["application", "performance", "latency", "api", "scale"],
        "source": "seed",
    },
    {
        "id": "runbook-database-connections",
        "title": "Database connection exhaustion runbook",
        "category": "runbooks",
        "content": (
            "For database incidents with connection pool exhaustion, identify "
            "noisy services, review pool limits, terminate idle sessions "
            "cautiously, and scale read replicas or application workers "
            "only after confirming database health."
        ),
        "tags": ["database", "connections", "pool", "capacity"],
        "source": "seed",
    },
    {
        "id": "runbook-kubernetes-crashloop",
        "title": "Kubernetes CrashLoopBackOff runbook",
        "category": "runbooks",
        "content": (
            "For Kubernetes pod crash loops, inspect pod events, container "
            "logs, config map changes, secret mounts, image pull status, "
            "and restart the workload after configuration or image "
            "issues are corrected."
        ),
        "tags": ["kubernetes", "pod", "crashloop", "container"],
        "source": "seed",
    },
    {
        "id": "runbook-cache-pressure",
        "title": "Cache pressure remediation runbook",
        "category": "runbooks",
        "content": (
            "For cache pressure or high miss rate incidents, inspect memory "
            "utilization, eviction rate, hot keys, connection count, "
            "and restart or scale cache nodes only after preserving data "
            "safety requirements."
        ),
        "tags": ["cache", "memory", "eviction", "redis"],
        "source": "seed",
    },
    {
        "id": "runbook-network-errors",
        "title": "Network error spike runbook",
        "category": "runbooks",
        "content": (
            "For network incidents, check DNS resolution, load balancer health, firewall changes, "
            "packet loss, TLS certificate validity, and recent route or security group changes."
        ),
        "tags": ["network", "dns", "load-balancer", "firewall"],
        "source": "seed",
    },
]


async def search_knowledge_entries(
    query: str,
    category: str = "runbooks",
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Search configured vector DB and fall back to a deterministic local corpus."""
    embedding_service = get_embedding_service()
    query_embedding = await embedding_service.embed_text(query)

    vector_db = get_vector_db_instance()
    if vector_db is not None:
        try:
            results = await vector_db.search(
                collection=settings.vector_db.collection_name,
                query_embedding=query_embedding,
                n_results=top_k,
                where={"category": category} if category else None,
            )
            entries = _format_vector_results(results, top_k)
            if entries:
                return entries
        except Exception as exc:
            logger.warning("Vector knowledge search failed; using local fallback", error=str(exc))

    return await _search_seed_corpus(query, category, top_k, query_embedding)


def _format_vector_results(results: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
    """Normalize vector DB result payloads for planner consumption."""
    entries = []
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    distances = results.get("distances", [])

    for index, doc_id in enumerate(ids[:top_k]):
        metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
        distance = distances[index] if index < len(distances) else None
        score = 1.0 - float(distance) if distance is not None else None
        entries.append(
            {
                "id": str(doc_id),
                "title": metadata.get("title", str(doc_id)),
                "content": documents[index] if index < len(documents) else "",
                "category": metadata.get("category"),
                "tags": metadata.get("tags", []),
                "source": metadata.get("source", "vector_db"),
                "score": score,
            }
        )
    return entries


async def _search_seed_corpus(
    query: str,
    category: str,
    top_k: int,
    query_embedding: list[float],
) -> list[dict[str, Any]]:
    """Search bundled runbooks with the same embedding path used for vector search."""
    embedding_service = get_embedding_service()
    candidates = [
        entry for entry in SEED_KNOWLEDGE if not category or entry.get("category") == category
    ]
    candidate_embeddings = await embedding_service.embed_texts(
        [f"{entry['title']} {entry['content']} {' '.join(entry['tags'])}" for entry in candidates]
    )

    scored = []
    query_terms = set(query.lower().split())
    for entry, embedding in zip(candidates, candidate_embeddings, strict=False):
        semantic_score = cosine_similarity(query_embedding, embedding)
        searchable = f"{entry['title']} {entry['content']} {' '.join(entry['tags'])}".lower()
        matches = sum(1 for term in query_terms if term in searchable)
        lexical_score = matches / max(len(query_terms), 1)
        score = (semantic_score * 0.7) + (lexical_score * 0.3)
        scored.append({**entry, "score": round(score, 4)})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
