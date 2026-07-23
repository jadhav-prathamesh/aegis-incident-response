import unittest
from typing import Any

from src.agents.planner import search_knowledge_base
from src.core import knowledge_base
from src.core.vector_db import VectorDBClient


class FakeVectorDB(VectorDBClient):
    async def initialize(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def add_documents(
        self,
        collection: str,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        return ids or []

    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "ids": ["kb-1"],
            "documents": ["Restart overloaded API pods after checking dependency latency."],
            "metadatas": [
                {
                    "title": "API pod remediation",
                    "category": "runbooks",
                    "tags": ["api", "latency"],
                    "source": "test",
                }
            ],
            "distances": [0.12],
        }

    async def get_collection(self, name: str) -> Any:
        return name

    async def delete_collection(self, name: str) -> bool:
        return True

    async def list_collections(self) -> list[str]:
        return []


class PlannerSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_knowledge_base_uses_vector_db_when_available(self) -> None:
        original_getter = knowledge_base.get_vector_db_instance
        knowledge_base.get_vector_db_instance = FakeVectorDB
        try:
            results = await search_knowledge_base.ainvoke(
                {"query": "api latency remediation", "category": "runbooks", "top_k": 3}
            )
        finally:
            knowledge_base.get_vector_db_instance = original_getter

        self.assertEqual(results[0]["id"], "kb-1")
        self.assertEqual(results[0]["title"], "API pod remediation")
        self.assertAlmostEqual(results[0]["score"], 0.88)

    async def test_search_knowledge_base_falls_back_to_seed_corpus(self) -> None:
        original_getter = knowledge_base.get_vector_db_instance
        knowledge_base.get_vector_db_instance = lambda: None
        try:
            results = await search_knowledge_base.ainvoke(
                {
                    "query": "database connection pool exhaustion",
                    "category": "runbooks",
                    "top_k": 2,
                }
            )
        finally:
            knowledge_base.get_vector_db_instance = original_getter

        self.assertTrue(results)
        self.assertLessEqual(len(results), 2)
        self.assertEqual(results[0]["category"], "runbooks")
        self.assertIn("database", results[0]["title"].lower())



class MonitoringQueryTests(unittest.IsolatedAsyncioTestCase):
    """PromQL query correctness."""

    async def test_cpu_query_has_mode_idle_filter(self) -> None:
        from src.core.monitoring import query_metrics_for_resource, query_prometheus

        captured: list[str] = []

        async def fake_query_prometheus(query: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
            captured.append(query)
            return {"status": "healthy", "value": None}

        original = query_prometheus

        import src.core.monitoring as mon
        mon.query_prometheus = fake_query_prometheus  # type: ignore[assignment]
        try:
            await query_metrics_for_resource("test-instance")
        finally:
            mon.query_prometheus = original

        self.assertTrue(
            any("mode=\"idle\"" in q for q in captured),
            f"No CPU query contained mode=\"idle\". Queries: {captured}",
        )


if __name__ == "__main__":
    unittest.main()
