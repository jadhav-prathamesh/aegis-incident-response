# Documentation Index

## Overview

This is the complete documentation suite for **Aegis — "Multi-Agent AI Incident Response Platform"**. All documents are generated from the source code, with clear labelling for implemented vs. planned features.

## Document Structure

```
docs/                          # GitHub open-source documentation (20 files)
contest/                       # TCS RiO contest submission
├── source/                    # Contest source documents (15 files)
├── prompts/                   # Regeneration prompts (7 files)
├── review/                    # Review checklists
├── diagrams/                  # Diagram specifications (5 files)
├── presentation/              # Slide content (12 files)
├── generated/                 # Generated output
└── MASTER_DOCUMENTATION_PROMPT.md  # Single source of truth
```

## GitHub Documentation (docs/)

| # | File | Description |
|---|---|---|
| 01 | `docs/01_Project_Overview.md` | Project overview, purpose, key features |
| 02 | `docs/02_System_Architecture.md` | High-level system architecture |
| 03 | `docs/03_Agent_Architecture.md` | Multi-agent architecture details |
| 04 | `docs/04_Agent_Interaction.md` | Agent interaction patterns and flow |
| 05 | `docs/05_AI_Decision_Engine.md` | LLM integration and decision-making |
| 06 | `docs/06_Workflow.md` | 7-stage agentic workflow |
| 07 | `docs/07_API_Documentation.md` | Complete API reference (23 endpoints) |
| 08 | `docs/08_Configuration.md` | Configuration reference |
| 09 | `docs/09_Deployment_Guide.md` | Deployment instructions |
| 10 | `docs/10_Testing.md` | Testing strategy and test reference |
| 11 | `docs/11_Project_Structure.md` | Repository structure and file map |
| 12 | `docs/12_Component_Reference.md` | Component reference for all modules |
| 13 | `docs/13_Vector_Database.md` | Vector database architecture |
| 14 | `docs/14_Monitoring.md` | Monitoring and observability |
| 15 | `docs/15_Validation.md` | Validation framework |
| 16 | `docs/16_Security.md` | Security model and settings |
| 17 | `docs/17_Business_Value.md` | Business value and cost analysis |
| 18 | `docs/18_Future_Roadmap.md` | Future development roadmap |
| 19 | `docs/19_FAQ.md` | Frequently asked questions |
| 20 | `docs/20_Glossary.md` | Terminology reference |

## Contest Source Documents (contest/source/)

| # | File | Description |
|---|---|---|
| 01 | `Contest_Project_Summary.md` | Project overview for contest |
| 02 | `Contest_Problem_Statement.md` | Problem definition and context |
| 03 | `Contest_Customer_Challenges.md` | Customer/market challenges |
| 04 | `Contest_AI_Solution.md` | AI/ML solution details |
| 05 | `Contest_Solution_Architecture.md` | Solution architecture |
| 06 | `Contest_Agentic_Workflow.md` | Agent pipeline details |
| 07 | `Contest_Business_Value.md` | Business value analysis |
| 08 | `Contest_Implementation_Timeline.md` | Development phases |
| 09 | `Contest_Deployment.md` | Deployment documentation |
| 10 | `Contest_Future_Roadmap.md` | Planned enhancements |
| 11 | `Contest_Assumptions.md` | Assumptions register |
| 12 | `Contest_Evidence.md` | Source evidence traceability |
| 13 | `Contest_Risk_Register.md` | Risk documentation |
| 14 | `Contest_Demo_Script.md` | Live demo walkthrough |
| 15 | `Contest_QA.md` | Quality assurance report |

## Contest Prompts (contest/prompts/)

| # | File | Purpose |
|---|---|---|
| 01 | `01_Regenerate_Project_Summary.md` | Regeneration prompt for summary |
| 02 | `02_Regenerate_Problem_Statement.md` | Regeneration prompt for problem statement |
| 03 | `03_Regenerate_Customer_Challenges.md` | Regeneration prompt for challenges |
| 04 | `04_Regenerate_AI_Solution.md` | Regeneration prompt for AI solution |
| 05 | `05_Regenerate_Solution_Architecture.md` | Regeneration prompt for architecture |
| 06 | `06_Regenerate_Agentic_Workflow.md` | Regeneration prompt for workflow |
| 07 | `07_Regenerate_All_Source.md` | Batch regeneration prompt |

## Contest Review (contest/review/)

| File | Purpose |
|---|---|
| `Contest_Review_Checklist.md` | Comprehensive review checklist with 7 categories |

## Diagram Specifications (contest/diagrams/)

| File | Diagram Type | Description |
|---|---|---|
| `High_Level_Architecture.md` | Architecture diagram (Mermaid) | Enterprise system architecture |
| `Agent_Architecture.md` | Class + communication diagram (Mermaid) | Multi-agent hierarchy and paths |
| `Agent_Interaction_Diagram.md` | Sequence + flow diagram (Mermaid) | Runtime agent communication |
| `Workflow_Diagram.md` | State diagram (Mermaid) | 7-stage incident workflow |
| `Deployment_Diagram.md` | Deployment topology (Mermaid) | Docker Compose deployment |

## Presentation Slides (contest/presentation/)

| # | File | Title |
|---|---|---|
| 01 | `Slide_01_Title.md` | Title Slide |
| 02 | `Slide_02_Problem.md` | The Problem |
| 03 | `Slide_03_Solution_Overview.md` | Solution Overview |
| 04 | `Slide_04_Architecture.md` | System Architecture |
| 05 | `Slide_05_Agentic_Workflow.md` | Agentic Workflow |
| 06 | `Slide_06_Live_Demo.md` | Live Demo |
| 07 | `Slide_07_Business_Value.md` | Business Value |
| 08 | `Slide_08_Technical_Deep_Dive.md` | Technical Deep Dive |
| 09 | `Slide_09_Implementation_Status.md` | Implementation Status |
| 10 | `Slide_10_Future_Roadmap.md` | Future Roadmap |
| 11 | `Slide_11_Differentiation.md` | Differentiation |
| 12 | `Slide_12_Thank_You.md` | Thank You |

## Quick Reference

| Use Case | Key Documents |
|---|---|
| Understanding the platform | `docs/01_Project_Overview.md`, `contest/source/Contest_Project_Summary.md` |
| Architecture | `docs/02_System_Architecture.md`, `docs/03_Agent_Architecture.md` |
| API usage | `docs/07_API_Documentation.md` |
| Deployment | `docs/09_Deployment_Guide.md`, `contest/source/Contest_Deployment.md` |
| Contribution | `docs/10_Testing.md`, `docs/11_Project_Structure.md` |
| Business value | `docs/17_Business_Value.md`, `contest/source/Contest_Business_Value.md` |
| Contest submission | All files under `contest/` |
| Presentation | All files under `contest/presentation/` |
