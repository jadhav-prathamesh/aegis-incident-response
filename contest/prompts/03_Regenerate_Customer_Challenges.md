# Regeneration Prompt: Contest Customer Challenges

## Objective

Regenerate the Customer Challenges document (`contest/source/Contest_Customer_Challenges.md`) from the codebase capabilities.

## Inputs

- `docs/01_Project_Overview.md` — Key features
- `docs/17_Business_Value.md` — Value proposition
- `src/core/incident_store.py` — Incident management
- `src/core/approval.py` — Approval workflow
- `src/core/monitoring.py` — Monitoring capabilities
- `docs/14_Monitoring.md` — Monitoring details

## Generation Instructions

1. Identify the top challenges the platform addresses:
   - Manual incident triage overhead
   - Inconsistent remediation procedures
   - Knowledge silos and runbook loss
   - Slow MTTR for common incidents
   - On-call burnout from repetitive alerts
2. Map each challenge to specific codebase features
3. Rate challenge severity as: Critical / High / Medium / Low
4. Rate solution coverage as: Full / Partial / Planned / None
5. Output structured document with challenge × solution mapping

## Verification

- [ ] Each challenge maps to at least one codebase feature
- [ ] Coverage ratings are honest (no "Full" for stub functions)
- [ ] No fabricated customer references or testimonials
