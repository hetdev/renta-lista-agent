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
