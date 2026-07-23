"""Dashboard — operational overview for incident management.

Run with: streamlit run src/dashboard/app.py
"""

from __future__ import annotations

from collections import Counter

import streamlit as st

st.set_page_config(
    page_title="Incident Intelligence Dashboard",
    page_icon=":shield:",
    layout="wide",
)

from src.core.approval import list_pending_approvals  # noqa: E402
from src.core.incident_store import list_incidents  # noqa: E402
from src.core.models import (  # noqa: E402
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)
from src.core.utils import enum_val  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _severity_color(sev: str) -> str:
    """Map incident severity to a Streamlit colour for the dashboard."""
    return {
        "SEV1": "red",
        "SEV2": "orange",
        "SEV3": "gold",
        "SEV4": "blue",
        "SEV5": "gray",
    }.get(sev, "gray")


def _status_color(sts: str) -> str:
    """Map incident status to a Streamlit colour for the dashboard."""
    return {
        "OPEN": "red",
        "ACKNOWLEDGED": "orange",
        "INVESTIGATING": "orange",
        "IDENTIFIED": "gold",
        "RESOLVING": "blue",
        "RESOLVED": "green",
        "CLOSED": "gray",
    }.get(sts, "gray")


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("Aegis")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Incidents", "Approvals", "Create Incident"],
    index=0,
)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

if page == "Overview":
    st.title("Operational Overview")

    incidents = list_incidents()
    total = len(incidents)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Incidents", total)

    open_count = sum(
        1
        for i in incidents
        if enum_val(i.status) in ("OPEN", "ACKNOWLEDGED", "INVESTIGATING")
    )
    col2.metric("Active", open_count)

    resolved_count = sum(
        1 for i in incidents if enum_val(i.status) in ("RESOLVED", "CLOSED")
    )
    col3.metric("Resolved", resolved_count)

    pending_approvals = list_pending_approvals()
    col4.metric("Pending Approvals", len(pending_approvals))

    st.divider()

    if incidents:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Severity Distribution")
            sev_counts = Counter(enum_val(i.severity) for i in incidents)
            for sev in ["SEV1", "SEV2", "SEV3", "SEV4", "SEV5"]:
                cnt = sev_counts.get(sev, 0)
                if cnt:
                    st.markdown(
                        f":{_severity_color(sev)}[**{sev}**] — {cnt} "
                        f"incident{'s' if cnt != 1 else ''}"
                    )

        with c2:
            st.subheader("Status Distribution")
            status_counts = Counter(enum_val(i.status) for i in incidents)
            for status, cnt in status_counts.most_common():
                st.markdown(
                    f":{_status_color(status)}[**{status}**] — {cnt}"
                )

        st.divider()
        st.subheader("Recent Incidents")
        sorted_incidents = sorted(
            incidents,
            key=lambda i: i.created_at,
            reverse=True,
        )[:10]
        for inc in sorted_incidents:
            sev = enum_val(inc.severity)
            sts = enum_val(inc.status)
            st.markdown(
                f":{_severity_color(sev)}[**{sev}**] "
                f"**{inc.title}** — :{_status_color(sts)}[{sts}] "
                f"— _{inc.created_at.strftime('%Y-%m-%d %H:%M')}_"
            )
    else:
        st.info("No incidents recorded yet. Create one from the sidebar.")

# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

elif page == "Incidents":
    st.title("Incidents")

    incidents = list_incidents()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severity_filter = st.multiselect(
            "Severity",
            [s.value for s in IncidentSeverity],
            default=[],
        )
    with col2:
        status_filter = st.multiselect(
            "Status",
            [s.value for s in IncidentStatus],
            default=[],
        )
    with col3:
        category_filter = st.multiselect(
            "Category",
            [c.value for c in IncidentCategory],
            default=[],
        )

    filtered = incidents
    if severity_filter:
        filtered = [i for i in filtered if enum_val(i.severity) in severity_filter]
    if status_filter:
        filtered = [i for i in filtered if enum_val(i.status) in status_filter]
    if category_filter:
        filtered = [i for i in filtered if enum_val(i.category) in category_filter]

    st.caption(f"Showing {len(filtered)} of {len(incidents)} incidents")

    if not filtered:
        st.info("No incidents match the current filters.")

    for inc in filtered:
        sev = enum_val(inc.severity)
        sts = enum_val(inc.status)
        cat = enum_val(inc.category)

        with st.expander(
            f":{_severity_color(sev)}[{sev}] **{inc.title}** — {sts} — {cat}",
            expanded=False,
        ):
            st.markdown(f"**Description:** {inc.description}")
            st.markdown(f"**Source:** {inc.source}")
            st.markdown(f"**Created:** {inc.created_at.isoformat()}")

            if inc.affected_services:
                st.markdown(f"**Affected Services:** {', '.join(inc.affected_services)}")
            if inc.affected_resources:
                st.markdown(f"**Affected Resources:** {', '.join(inc.affected_resources)}")
            if inc.root_cause:
                st.markdown(f"**Root Cause:** {inc.root_cause}")
            if inc.resolution:
                st.markdown(f"**Resolution:** {inc.resolution}")
            if inc.tags:
                st.markdown(f"**Tags:** {', '.join(inc.tags)}")

# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

elif page == "Approvals":
    st.title("Approval Workflow")

    pending = list_pending_approvals()

    if not pending:
        st.info("No pending approval requests.")
    else:
        st.metric("Pending Approvals", len(pending))
        for req in pending:
            with st.expander(
                f"**{req.action_type}** on _{req.target_resource}_ — {req.status.value}",
                expanded=True,
            ):
                st.markdown(f"**Requested by:** {req.requested_by}")
                st.markdown(f"**Created:** {req.created_at.isoformat()}")
                st.markdown(f"**Parameters:** `{req.parameters}`")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Approve", key=f"approve_{req.id}"):
                        from src.core.approval import approve_request

                        approve_request(
                            req.id,
                            approver="dashboard-user",
                            notes="Approved via dashboard",
                        )
                        st.success("Approved!")
                        st.rerun()
                with c2:
                    if st.button("Reject", key=f"reject_{req.id}"):
                        from src.core.approval import reject_request

                        reject_request(
                            req.id,
                            reason="Rejected via dashboard",
                            rejector="dashboard-user",
                        )
                        st.warning("Rejected!")
                        st.rerun()

# ---------------------------------------------------------------------------
# Create Incident
# ---------------------------------------------------------------------------

elif page == "Create Incident":
    st.title("Create Incident")

    with st.form("create_incident_form"):
        title = st.text_input("Title", placeholder="Brief incident title")
        description = st.text_area(
            "Description",
            placeholder="Detailed description of the incident",
        )

        col1, col2 = st.columns(2)
        with col1:
            severity = st.selectbox(
                "Severity",
                [s.value for s in IncidentSeverity],
                index=2,
            )
            category = st.selectbox(
                "Category",
                [c.value for c in IncidentCategory],
                index=10,  # UNKNOWN
            )
        with col2:
            source = st.text_input("Source", value="dashboard")
            affected_services = st.text_input(
                "Affected Services",
                placeholder="comma-separated, e.g. api-gateway, postgres-primary",
            )

        submitted = st.form_submit_button("Create Incident")

        if submitted:
            if not title or not description:
                st.error("Title and description are required.")
            else:
                from src.core.incident_store import save_incident
                from src.core.similar_incidents import index_incident

                inc = Incident(
                    title=title,
                    description=description,
                    severity=IncidentSeverity(severity),
                    status=IncidentStatus.OPEN,
                    category=IncidentCategory(category),
                    source=source,
                    affected_services=[
                        s.strip() for s in affected_services.split(",") if s.strip()
                    ],
                )
                saved = save_incident(inc)
                import asyncio

                try:
                    asyncio.run(index_incident(saved))
                except Exception:
                    st.warning(
                        "Incident saved but indexing for similarity search "
                        "failed. It may not appear in similar-incident results."
                    )

                st.success(f"Incident created: **{saved.title}** (ID: `{saved.id}`)")
                st.rerun()
