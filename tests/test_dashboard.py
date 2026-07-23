"""Tests for the Streamlit dashboard helpers."""

import unittest

from src.core.utils import enum_val
from src.dashboard.app import _severity_color, _status_color


class DashboardHelperTests(unittest.TestCase):
    """Unit tests for dashboard utility functions."""

    def test_enum_val_with_enum(self) -> None:
        from src.core.models import IncidentSeverity

        self.assertEqual(enum_val(IncidentSeverity.SEV1), "SEV1")

    def test_enum_val_with_string(self) -> None:
        self.assertEqual(enum_val("SEV3"), "SEV3")

    def test_severity_color_returns_string(self) -> None:
        result = _severity_color("SEV1")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "red")

    def test_severity_color_unknown(self) -> None:
        self.assertEqual(_severity_color("UNKNOWN"), "gray")

    def test_status_color_returns_string(self) -> None:
        result = _status_color("OPEN")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "red")

    def test_status_color_unknown(self) -> None:
        self.assertEqual(_status_color("UNKNOWN"), "gray")


class IncidentIndexingTests(unittest.IsolatedAsyncioTestCase):
    """Dashboard incident indexing — must not silently fail."""

    async def test_index_incident_does_not_raise(self) -> None:
        from src.core.models import Incident, IncidentCategory, IncidentSeverity, IncidentStatus
        from src.core.similar_incidents import index_incident

        inc = Incident(
            title="Dashboard index test",
            description="Verify indexing after creation",
            severity=IncidentSeverity.SEV4,
            category=IncidentCategory.APPLICATION,
            status=IncidentStatus.OPEN,
            source="dashboard-test",
        )
        try:
            await index_incident(inc)
        except Exception as exc:
            self.fail(f"index_incident raised unexpectedly: {exc}")


if __name__ == "__main__":
    unittest.main()
