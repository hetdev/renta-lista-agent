# RentaLista Agent

**RentaLista: an evidence-first Colombian income tax agent**  
Built for the [Agents for Humans](https://agentsforhumans.devpost.com) hackathon.

Helps a Colombian tax-resident natural person reconcile third-party exogenous information and prepare a **traceable draft** of Formulario 210 (año gravable 2025) with a deterministic engine. It does **not** log in to DIAN, sign, file, or pay.

> Borrador para revisión. No ha sido presentado ante la DIAN.

## Status (14 Sep 2026)

Honest snapshot. Full findings and priorities in [DOC.md](DOC.md).

| Piece | State |
|---|---|
| Deterministic Form 210 engine | **Working.** 25% labor (max 240 UVT), 72 UVT/dependent, art. 241 table, art. 577 rounding, art. 807 advance, bilingual **es/en** cell labels. 52 tests green. |
| Ingestion (DIAN XLSX + Nequi PDF) | **Working** on repo fixtures (`demo/fixtures/`) |
| Public API | **Working** on CloudFront: create case → profile → `PREPARE_DRAFT` returns **SUCCEEDED** with demo amounts and case locale |
| Web UI (Next.js, es/en) | Landing, demo, profile, draft (engine snapshot + bilingual cell ledger + DIAN disclaimer). Documents/coverage still mock. Live View page present |
| Strands / Bedrock / Gateway | Resources **READY**; Strands smoke-tested locally; not on the public demo path |
| Synthetic portal (OTP `123456`) | In FastAPI (`/demo-portal`) |

## Demo numbers (engine, rounded to thousands)

`must_file=True` · impuesto **926.000** · retenciones 4.635.000 · **saldo a favor 3.709.000**

## What it does today

1. Parses DIAN-layout exogenous workbook + Nequi PDF (synthetic fixtures)
2. Evaluates obligation to file (UVT 49.799, five thresholds)
3. Calculates Form 210 draft with a deterministic engine (no LLM math)
4. Serves bilingual UI + case/profile API behind CloudFront

## Planned / not fully wired

Coverage matrix per exogenous row, missing-certificate recovery (portal search + Browser OTP handoff), human conflict ledger, export packet. Domain policies exist under `src/rentalista/document_recovery/`; API/UI wiring is partial.

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
| **Live demo (ES/EN)** | **https://deuhmh4dvlr6i.cloudfront.net/** |
| **Public API** | `https://deuhmh4dvlr6i.cloudfront.net/api/v1/` |
| Web bucket (public, synthetic only) | `rentalista-web-697020387519` |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` READY |
| AgentCore Gateway + Web Search | `rentalista-websearch2-f29eutucy6` READY |
| Bedrock model | `amazon.nova-micro-v1:0` |
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
