# Devpost submission (English)

## Title
RentaLista: an evidence-first Colombian income tax agent

## Elevator pitch
RentaLista helps a Colombian tax-resident person reconcile third-party exogenous tax data and prepare a **traceable Form 210 draft**. The Form 210 math is a deterministic engine, never an LLM; the agent entrypoint runs on Amazon Bedrock AgentCore Runtime. **It never files with DIAN.**

> Draft for review only. Not filed with DIAN.

## Problem / Who / Why (must appear in the video)
1. **Problem:** Reconciling Colombia’s third-party tax report and assembling a Form 210 draft is slow and error-prone.
2. **Who it’s for:** A tax-resident natural person filing their own renta — not an accounting firm.
3. **Why it matters:** Missing certificates and silent zeros create real filing risk. RentaLista keeps evidence and human control.

## What judges can try
- Live demo: https://deuhmh4dvlr6i.cloudfront.net/
- EN: `/en/` (default) · ES: `/es/`
- Start the synthetic case → profile → **Prepare draft**
- Cell ledger shows the 25% labor rule, 72 UVT per dependent, art. 241 tax, and the credit balance rounded to thousands (3.709.000 COP on the synthetic case)
- API: `POST /api/v1/cases` · `PUT .../profile` · `POST .../jobs` with `PREPARE_DRAFT` (returns SUCCEEDED; case becomes DRAFT_READY)

## Stack
- Deterministic Form 210 engine (no LLM arithmetic), bilingual es/en cell labels
- FastAPI on Lambda behind CloudFront `/api/v1`
- Next.js 15 static export (es/en)
- Amazon Bedrock AgentCore Runtime hosting the agent entrypoint
- Provisioned, not yet on the public demo path: Strands Agents with Amazon Bedrock (`amazon.nova-micro-v1:0`), AgentCore Gateway Web Search, AgentCore Browser (Live View)

## Open source
- Repo: https://github.com/hetdev/renta-lista-agent
- License: MIT

## Builder ID
Get one at https://profile.aws.amazon.com/ (sign up with email).
Paste the **email** you used: **hetzel30@gmail.com**

## Video
https://www.youtube.com/watch?v=qnakivEdego

## Notes
- Synthetic data only on the public demo
- Fictional reporter for missing-certificate demo: Banco Sintético Andino
- OTP for synthetic portal: 123456 (portal available with the API running locally)
- Demo available free until judging ends (**8 Oct 2026 19:00 COT** / 5:00 p. m. PT)

## Project story
Full Markdown text (inspiration, what it does, how we built it, challenges, learnings, what's next): `docs/devpost-story-en.md`.

## Built with (tags)
python · fastapi · pydantic · openpyxl · pypdf · mangum · aws-lambda · amazon-api-gateway · amazon-cloudfront · amazon-s3 · amazon-bedrock · amazon-bedrock-agentcore · strands-agents · next.js · react · typescript · tailwindcss · uv · pytest · ruff · mypy · playwright

## "Try it out" links
| Label | URL |
|---|---|
| Live demo (EN) | https://deuhmh4dvlr6i.cloudfront.net/en/ |
| Live demo (ES) | https://deuhmh4dvlr6i.cloudfront.net/es/ |
| Source code (MIT) | https://github.com/hetdev/renta-lista-agent |
| Public API health | https://deuhmh4dvlr6i.cloudfront.net/api/v1/health |
| Architecture diagram | https://github.com/hetdev/renta-lista-agent/blob/main/docs/architecture.md |

## Image gallery (3:2, PNG, 1500×1000)
Generated from the live app with `scripts/demo-video`-style automation; files under `docs/gallery/`:
01 cover · 02 landing EN · 03 case created by the API · 04 profile admitted · 05 documents · 06 coverage · 07 draft with cell ledger (EN) · 08 borrador (ES) · 09 architecture diagram on GitHub

## Testing instructions (Devpost field)
See the block below; verified end to end through CloudFront on 14 Sep after `scripts/deploy_api_member.sh` (`GET /draft`, `GET /coverage` and `/documents` included).

```
PUBLIC WEB DEMO (no login, synthetic data only, ~2 minutes)
1. Open https://deuhmh4dvlr6i.cloudfront.net/en/ (Spanish: /es/).
2. Click "Try the demo" → "Create demo case". The green "api" badge means the case was created by the live API; "offline" means the local fallback.
3. "Go to profile" → keep the defaults → "Save profile" → you should see "Profile admitted" (saved through the API) → "Continue".
4. Documents: click "Mark as uploaded" on two items and "Recover in portal" on another to see the human-approval state → "Continue".
5. Coverage: verified vs missing concepts → "Continue to draft".
6. Draft: click "Prepare draft". Expected: taxable base COP 59,154,714, income tax COP 926,000, withholdings COP 4,635,000, credit balance COP 3,709,000. Click "Income tax" to open its evidence (cell 116, art. 241 table, rule version ag2025-0.1.0), then scroll to the Form 210 cell ledger and the disclaimer "Draft for review only. Not filed with DIAN."

PUBLIC API (curl)
BASE=https://deuhmh4dvlr6i.cloudfront.net/api/v1
curl -s -X POST "$BASE/cases?locale=en"        # -> case_id + case_token (send it as X-Case-Token)
curl -s -X PUT "$BASE/cases/<case_id>/profile" -H "Content-Type: application/json" -H "X-Case-Token: <token>" \
  -d '{"resident_2025":true,"not_required_accounting":true,"initial_filing":true,"timely_filing":true,"iva_responsible_dec_31":false,"labor_income_only":true,"national_financial_income":true,"assets_only_colombia":true,"no_foreign_currency":true,"no_excluded_facts":true,"dependents_confirmed":1,"absence_attestations":{"pensiones":true,"dividendos":true,"ganancias_ocasionales":true}}'
curl -s -X POST "$BASE/cases/<case_id>/jobs" -H "Content-Type: application/json" -H "X-Case-Token: <token>" \
  -d '{"command":"PREPARE_DRAFT","idempotency_key":"judge-1"}'          # -> "status":"SUCCEEDED"
curl -s "$BASE/cases/<case_id>" -H "X-Case-Token: <token>"              # -> "status":"DRAFT_READY"
curl -s "$BASE/cases/<case_id>/draft" -H "X-Case-Token: <token>"        # -> engine cells; "saldo_a_favor":3709000
curl -s "$BASE/cases/<case_id>/coverage" -H "X-Case-Token: <token>"     # -> 5 exogenous rows, "must_file":true

RUN LOCALLY (full pipeline on the repo fixtures; Python 3.13 + uv)
git clone https://github.com/hetdev/renta-lista-agent && cd renta-lista-agent
make install && make test                       # 52 tests
uv run python scripts/run_demo_docs.py --xlsx demo/fixtures/reporteExogena2025_demo.xlsx --pdf demo/fixtures/nequi_retencion_demo.pdf
uv run uvicorn rentalista.api.main:app --reload # OpenAPI at http://localhost:8000/docs; GET /api/v1/cases/{id}/draft and /coverage
                                                # synthetic portal: POST /demo-portal/login, POST /demo-portal/otp (code 123456), GET /demo-portal/certificate

NOTES
- All data is synthetic; nothing is filed, signed or paid. The agent never logs in to DIAN.
- The API store is in-memory: a case can disappear if the Lambda is recycled; just create a new one.
- Gateway Web Search and Browser Live View are provisioned but not on the public demo path yet.
```

## Optional bonus blog post
Draft in `docs/blog-post-builder-aws.md` (title includes "Agents for Humans"). Publish on builder.aws, then paste the URL; leave the field empty if not published before submitting.
