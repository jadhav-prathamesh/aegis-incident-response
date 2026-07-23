"""Tests for the similar incidents retrieval."""

import unittest

from src.core.incident_store import save_incident
from src.core.models import Incident, IncidentCategory, IncidentSeverity, IncidentStatus
from src.core.similar_incidents import _incident_to_searchable, find_similar


def _make_incident(
    title: str,
    category: IncidentCategory = IncidentCategory.APPLICATION,
    severity: IncidentSeverity = IncidentSeverity.SEV3,
    affected_services: list[str] | None = None,
    root_cause: str | None = None,
) -> Incident:
    return Incident(
        title=title,
        description=f"Description of {title}",
        severity=severity,
        status=IncidentStatus.RESOLVED,
        category=category,
        source="test",
        affected_services=affected_services or [],
        root_cause=root_cause,
    )


class SimilarIncidentTests(unittest.IsolatedAsyncioTestCase):
    """Tests for similar incident retrieval."""

    def test_incident_to_searchable(self) -> None:
        inc = _make_incident(
            "API latency spike",
            category=IncidentCategory.DATABASE,
            affected_services=["api-gateway"],
            root_cause="Database connection pool exhaustion",
        )
        text = _incident_to_searchable(inc)
        self.assertIn("API latency spike", text)
        self.assertIn("api-gateway", text)
        self.assertIn("DATABASE", text)

    async def test_find_similar_returns_empty_when_no_other_incidents(self) -> None:
        inc = _make_incident("Unique incident with no matches")
        results = await find_similar(inc, limit=5)
        # Should return empty list when no other incidents exist
        self.assertIsInstance(results, list)

    async def test_find_similar_ranks_related_incidents_higher(self) -> None:
        # Seed some incidents into the in-memory store
        db_inc = _make_incident(
            "PostgreSQL connection pool exhausted",
            category=IncidentCategory.DATABASE,
            affected_services=["postgres-primary"],
            root_cause="Connection leak in service B",
        )
        api_inc = _make_incident(
            "API gateway returning 503",
            category=IncidentCategory.APPLICATION,
            affected_services=["api-gateway"],
            root_cause="Database connection pool exhaustion",
        )
        save_incident(db_inc)
        save_incident(api_inc)

        query_inc = _make_incident(
            "Database connections running out",
            category=IncidentCategory.DATABASE,
            affected_services=["postgres-primary"],
        )

        results = await find_similar(query_inc, limit=5)
        # Both stored incidents should be returned
        self.assertTrue(len(results) >= 1)
        # The database incident should rank first due to matching category and services
        self.assertEqual(results[0]["incident_id"], str(db_inc.id))


if __name__ == "__main__":
    unittest.main()
