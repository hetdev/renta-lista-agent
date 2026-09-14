# RentaLista Agent

**RentaLista: an evidence-first Colombian income tax agent**  
Built for the [Agents for Humans](https://agentsforhumans.devpost.com) hackathon.

Helps a Colombian tax-resident natural person reconcile third-party exogenous information and prepare a **traceable draft** of Formulario 210 (año gravable 2025) with a deterministic engine. It does **not** log in to DIAN, sign, file, or pay.

> Borrador para revisión. No ha sido presentado ante la DIAN.

## Status (14 Sep 2026)

Honest snapshot. Full findings and priorities in [DOC.md](DOC.md).

| Piece | State |
|---|---|
| Deterministic Form 210 engine | **Working.** Art. 241 table (tested against the statute and the rule-pack YAML), art. 577 rounding, bilingual **es/en** cell labels. 25% labor rule and 72 UVT/dependent are present but **provisional**: the statute treats the 25% as exempt income capped at 790 UVT inside the 40% limit, and dependents are currently deducted twice (DOC.md H1–H2). 52 tests green. |
| Ingestion (DIAN XLSX + Nequi PDF) | **Working** on repo fixtures (`demo/fixtures/`) |
| Public API | **Working** on CloudFront: create case → profile → `PREPARE_DRAFT` (**SUCCEEDED**, case **DRAFT_READY**) → `GET /draft` (engine cells, credit balance 3,709,000), `GET /coverage` (5 exogenous rows), `POST/GET /documents` |
| Web UI (Next.js, es/en) | Landing, demo, profile, draft (engine snapshot + bilingual cell ledger + DIAN disclaimer). Coverage shows the API's exogenous rows next to a local inventory; documents are registered through the API. Live View page present but inert in the deployed build |
| Strands Agents / Bedrock / Gateway | **Strands Agents orchestrates the engine**: the agent (Amazon Bedrock `amazon.nova-micro-v1:0`) calls the `prepare_draft` tool and the deterministic engine returns every cell; the model only summarises. Reproduce with `AWS_PROFILE=<profile> uv run python scripts/run_strands_agent.py` (transcript: `demo/expected/strands_run.json`). The AgentCore Runtime entrypoint uses the same agent when `RENTALISTA_STRANDS=1`, with a direct-engine fallback. Gateway Web Search and Browser Live View are provisioned, not on the public path yet |
| Synthetic portal (OTP `123456`) | In FastAPI (`/demo-portal`); reachable only with the API running locally |

## Demo numbers (engine, rounded to thousands)

`must_file=True` · impuesto **926.000** · retenciones 4.635.000 · **saldo a favor 3.709.000**  
Provisional until the 25% rule and the dependent deduction are aligned with the statute (DOC.md H1–H2); the conclusion (credit balance) does not change, the amount does.

## What it does today

1. Parses DIAN-layout exogenous workbook + Nequi PDF (synthetic fixtures)
2. Evaluates obligation to file (UVT 49.799, five thresholds)
3. Calculates Form 210 draft with a deterministic engine (no LLM math)
4. Serves bilingual UI + case/profile/draft API behind CloudFront

## Planned / not fully wired

Coverage matrix per exogenous row, missing-certificate recovery (portal search + Browser OTP handoff), human conflict ledger, export packet. Domain policies exist under `src/rentalista/document_recovery/`; API/UI wiring is partial.

## Architecture

See [docs/architecture.md](docs/architecture.md). Solid arrows are implemented; dashed ones are planned.

- Deterministic tax engine in `src/rentalista/tax/`
- FastAPI on Lambda behind CloudFront `/api/v1/*` (in-memory store)
- **Strands Agents** + **Amazon Bedrock** `amazon.nova-micro-v1:0` (us-east-1): orchestration through the `prepare_draft` tool, never arithmetic
- **Amazon Bedrock AgentCore** Runtime `rentalista_agent` (READY) running the agent entrypoint (Strands orchestration behind `RENTALISTA_STRANDS=1`, engine fallback)
- **Gateway** `rentalista-websearch2` with **Web Search Tool** target (READY, unused by code so far)
- **Browser** `aws.browser.v1` Live View endpoint (signed URL ≤300 s; UI not wired in the deployed build)
- Public API: `https://deuhmh4dvlr6i.cloudfront.net/api/v1/`

### Deployed resources (us-east-1)

| Resource | Id / URL |
|---|---|
| **Live demo (EN default / ES)** | **https://deuhmh4dvlr6i.cloudfront.net/** · `/en/` · `/es/` |
| **Public API** | `https://deuhmh4dvlr6i.cloudfront.net/api/v1/` |
| Web bucket (public website, synthetic only) | `rentalista-web-697020387519` |
| Lambda API, master account | API Gateway `pi4y909mlf` (current code) |
| Lambda API, member account | `rentalista-api` · API Gateway `lnfsntpv6j` (CloudFront origin; same package as master since 14 Sep) |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` READY |
| AgentCore Gateway | `rentalista-websearch2-f29eutucy6` READY |
| Web Search target | `DP0IKFORKR` (connector `web-search` 1.2.0) |
| Bedrock model | `amazon.nova-micro-v1:0` |

Live View URL is generated per session (`max 300s`). Browser session timeout: 1800s.  
Demo uses **synthetic data only**; no real taxpayer PII.

## Quick start

```bash
# Python
make install
make test        # 58 tests
make verify      # lint + typecheck + test (currently red: ruff format 3 files, mypy 12 errors)

# Strands agent on Amazon Bedrock Nova Micro calling the engine tool (needs bedrock:InvokeModel)
AWS_PROFILE=<profile> uv run python scripts/run_strands_agent.py

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

Current output (rounded to thousands): `must_file=True`, impuesto neto 926.000 COP, retenciones 4.635.000 COP, **saldo a favor 3.709.000 COP**. `make demo-draft` regenerates `frontend/src/lib/demo-draft.json` and `demo/expected/real_demo_run.json` from the same engine run; the deployed draft page shows this snapshot.

Public UI: https://deuhmh4dvlr6i.cloudfront.net/en/ · start the synthetic case · profile (API) · draft (engine snapshot with cell ledger).

Synthetic portal, local API only: `POST /demo-portal/login`, `POST /demo-portal/otp` with `123456`, `GET /demo-portal/certificate`.

## Judge notes

- No login required for the public demo
- All taxpayer data is synthetic
- Entity names of banks may be real; the missing-reporter entity is fictional (`Banco Sintético Andino`)
- Seeded portal directory includes deliberate decoys (lookalike domain, shortener, paid third-party)

## License

MIT — see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
