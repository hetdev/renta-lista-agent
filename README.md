# RentaLista Agent

**RentaLista: an evidence-first Colombian income tax agent**  
Built for the [Agents for Humans](https://agentsforhumans.devpost.com) hackathon.

Helps a Colombian tax-resident natural person reconcile third-party exogenous information and prepare a **traceable draft** of Formulario 210 (año gravable 2025) with a deterministic engine. It does **not** log in to DIAN, sign, file, or pay.

> Borrador para revisión. No ha sido presentado ante la DIAN.

## Status (11 Sep 2026 code review)

Honest snapshot. Full findings and priorities in [DOC.md](DOC.md).

| Piece | State |
|---|---|
| Deterministic Form 210 engine (`src/rentalista/tax/`) | Working, 50 tests green. Art. 241 bracket table verified against the statute and the rule-pack YAML by unit tests (fixed 11 Sep 2026; the deployed UI still shows the pre-fix snapshot until redeployed). |
| Ingestion: DIAN-layout exogenous XLSX + Nequi PDF | Working, as a local script (`scripts/run_demo_docs.py`) |
| Public API | Creates cases, saves the profile, accepts jobs. `PREPARE_DRAFT` currently runs with empty amounts and does not return a draft |
| Web UI (Next.js, es/en) | Profile page talks to the API. Documents, coverage and draft pages are local mocks; the draft page shows a static engine snapshot. The Live View page is inert in the deployed build |
| Strands agent, Bedrock Nova Micro, Gateway Web Search | Resources deployed and READY, **not invoked by any code path yet** |
| Synthetic demo portal (OTP `123456`) | Implemented in FastAPI; reachable only when running the API locally |

## What it does today

1. Parses a DIAN-layout exogenous workbook and a Nequi certificate PDF (synthetic fixtures under `demo/fixtures/`)
2. Evaluates the obligation to file (UVT 49.799, five thresholds with the DIAN operators)
3. Calculates a Form 210 draft with a **deterministic engine** (no LLM arithmetic): per-cell formula, rule version, saldo invariants
4. Serves a bilingual static UI and a small case/profile API

## Planned, not wired yet

Coverage matrix per reported row, missing-certificate recovery via portal search + AgentCore Browser with OTP handoff, human conflict resolution with a ledger, export packet. Domain models and policies exist under `src/rentalista/document_recovery/`; the API and UI wiring do not.

## Architecture

See [docs/architecture.md](docs/architecture.md). Solid arrows are implemented; dashed ones are planned.

- Deterministic tax engine in `src/rentalista/tax/`
- FastAPI on Lambda behind CloudFront `/api/v1/*` (in-memory store)
- **Amazon Bedrock AgentCore** Runtime `rentalista_agent` (READY) running the deterministic entrypoint
- **Gateway** `rentalista-websearch2` with **Web Search Tool** target (READY, unused by code so far)
- **Browser** `aws.browser.v1` Live View endpoint (signed URL ≤300 s; UI not wired in the deployed build)
- **Amazon Bedrock** model `amazon.nova-micro-v1:0` (us-east-1, unused by code so far)
- Public API: `https://deuhmh4dvlr6i.cloudfront.net/api/v1/`

### Deployed resources (us-east-1)

| Resource | Id / URL |
|---|---|
| **Live demo** | **https://deuhmh4dvlr6i.cloudfront.net/** |
| ES / EN | `/es/` · `/en/` |
| Web bucket (public website, synthetic only) | `rentalista-web-697020387519` |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` |
| AgentCore Gateway | `rentalista-websearch2-f29eutucy6` |
| Web Search target | `DP0IKFORKR` (connector `web-search` 1.2.0) |
| Bedrock model | `amazon.nova-micro-v1:0` |

Live View URL is generated per session (`max 300s`). Browser session timeout: 1800s.  
Demo uses **synthetic data only**; no real taxpayer PII.

## Quick start

```bash
# Python
make install
make test        # 50 tests
make verify      # lint + typecheck + test (currently red: ruff format, mypy)

# API locally (also serves the synthetic portal at /demo-portal/*)
uv run uvicorn rentalista.api.main:app --reload

# Frontend
cd frontend && npm install && npm run build
```

## Demo (synthetic data only)

End-to-end pipeline on the repo fixtures (local):

```bash
uv run python scripts/run_demo_docs.py \
  --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
  --pdf  demo/fixtures/nequi_retencion_demo.pdf
```

Current output: `must_file=True`, impuesto neto 3.878.107 COP, retenciones 4.635.000 COP, **saldo a favor 756.893 COP**. Until 11 Sep 2026 a wrong bracket table produced "saldo a pagar 189.288"; the public UI keeps showing that snapshot until the frontend is rebuilt and redeployed (`make demo-draft` regenerates `frontend/src/lib/demo-draft.json`).

Public UI: https://deuhmh4dvlr6i.cloudfront.net/es/ · *Probar caso sintético* · profile (API) · draft (static engine snapshot).

Synthetic portal, local API only: `POST /demo-portal/login`, `POST /demo-portal/otp` with `123456`, `GET /demo-portal/certificate`.

## Judge notes

- No login required for the public demo
- All taxpayer data is synthetic
- Entity names of banks may be real; the missing-reporter entity is fictional (`Banco Sintético Andino`)
- Seeded portal directory includes deliberate decoys (lookalike domain, shortener, paid third-party)

## License

MIT — see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
