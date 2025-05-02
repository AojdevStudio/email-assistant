# Dental Analytics Email Assistant – Proof-of-Concept

## 1 · Purpose
Build a lightweight, Python-based CLI tool that converts a Google-Sheets CSV export of dental KPIs into an executive-ready email draft, following the rules in `system-prompt.md`.  
This proof of concept validates the data-analysis workflow and OpenAI Assistants v2 integration before investing in full automation.

---

## 2 · Problem Statement
Leadership needs a consistent, data-driven weekly summary across multiple dental locations. Creating these emails manually is time-consuming and error-prone. An AI assistant can analyze uploaded metrics, overlay benchmarks, and output an action-oriented email within seconds.

---

## 3 · Goals & Success Metrics
| Goal | Success Metric |
|------|----------------|
| Accurate analysis | ≥ 95 % of benchmark bands and variance flags match manual review |
| Email quality | Leadership survey ≥ 4 / 5 for clarity & actionability |
| Ease of use | Run time ≤ 2 min on typical CSV (≤ 5 k rows) |
| Reproducibility | Deterministic outputs when fed identical CSV + seed |

---

## 4 · Target Users
* Ops leader who owns weekly reporting  
* Regional managers reviewing multiple locations  
* Data analyst validating the output

---

## 5 · User Journey
1. **Start CLI** → `python dental_report.py --file weekly_metrics.csv`  
2. CLI previews first rows, prompts "Proceed?"  
3. User confirms ➞ analysis runs (status spinner)  
4. CLI displays Markdown email + flags/KPI table  
5. User copies email into Gmail or saves JSON/MD via `--save` flag  
6. Optional iterative commands: `r` (regenerate), `f` (filter site), `q` (quit)

---

## 6 · Functional Requirements
| ID | Requirement |
|----|-------------|
| F-1 | Accept CSV via `--file` or URL via `--sheet` (public CSV link) |
| F-2 | Validate schema (columns A–V, correct types) & report issues |
| F-3 | Query OpenAI Assistant v2 using `system-prompt.md` + code-interpreter tool |
| F-4 | Upload sanitized DataFrame to assistant; poll until complete |
| F-5 | Parse returned JSON; print email in Markdown + flags + KPI table |
| F-6 | Color-code CLI output (green/on-track, red/behind, blue/ahead) |
| F-7 | `--save` flag writes `{timestamp}_report.json` & `{timestamp}_email.md` to `/output` |
| F-8 | Support interactive loop: `r`, `f <location>`, `q` without new CSV upload |

---

## 7 · Non-Functional Requirements
| N-1 | Python ≥ 3.9, packages pinned in `requirements.txt` |
| N-2 | Strict typing with `mypy`; no `any` |
| N-3 | Unit tests ≥ 80 % coverage (`pytest`, `hypothesis`) |
| N-4 | Runtime memory ≤ 1 GB; completes in < 2 min for 5 k-row CSV |
| N-5 | Handles network/API failures with graceful messages & retry prompt |

---

## 8 · Out of Scope (for PoC)
* Direct Google Sheets API integration  
* Gmail Draft creation  
* Automated triggers (Make.com, webhooks)  
* Full Supabase/pgvector backend

---

## 9 · Acceptance Criteria
1. Running CLI with sample `dental_kpi_metrics.csv` produces a JSON envelope conforming to § 8 of system prompt.  
2. Email draft ≤ 350 words, uses executive tone, bullet lists, **bold** key figures, SMART recommendations.  
3. Low-band KPIs are prepended with "⚠️".  
4. CLI exits 0 on success; non-zero on validation or API failure.  
5. All unit tests pass via `pytest`.  

---

## 10 · Future Enhancements
* Add `--gmail-draft` flag to push email directly to Gmail via API  
* Replace CLI prompts with Streamlit UI  
* Store historical snapshots in local SQLite for trend accuracy  
* Integrate Google Sheets watch → webhook → auto-run pipeline  
* Move benchmarks/research chunks into pgvector for semantic search

---

## 11 · Timeline & Milestones
| Week | Milestone |
|------|-----------|
| 1 | Project scaffolding, CSV validator, unit tests |
| 2 | OpenAI Assistant wrapper & prompt tuning |
| 3 | CLI workflow, colorized output, save option |
| 4 | QA against sample data, polish, documentation |

---

## 12 · Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| API cost variances | Cache assistant ID & reuse; small test dataset |
| Prompt drift | Version control `system-prompt.md`; add regression tests |
| Data privacy | Ensure local processing; strip PHI before upload |

---

*Version 1.0 · 2024-06-02* 