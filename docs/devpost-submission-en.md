# Devpost submission (English)

## Title
RentaLista: an evidence-first Colombian income tax agent

## Elevator pitch
RentaLista helps a Colombian tax-resident person reconcile third-party exogenous tax data and prepare a **traceable Form 210 draft** with a deterministic engine. Strands Agents orchestrates tools; Amazon Bedrock AgentCore Runtime runs the agent. **It never files with DIAN.**

> Draft for review only. Not filed with DIAN.

## Problem / Who / Why (must appear in the video)
1. **Problem:** Reconciling Colombia’s third-party tax report and assembling a Form 210 draft is slow and error-prone.
2. **Who it’s for:** A tax-resident natural person filing their own renta — not an accounting firm.
3. **Why it matters:** Missing certificates and silent zeros create real filing risk. RentaLista keeps evidence and human control.

## What judges can try
- Live demo: https://deuhmh4dvlr6i.cloudfront.net/
- ES: `/es/` · EN: `/en/`
- Click **Probar caso sintético** → profile → **Prepare draft**
- Cell ledger shows 25% labor (max 240 UVT), 72 UVT/dependent, art. 241 tax, amount payable/credit rounded to thousands
- API: `POST /api/v1/cases` · `PUT .../profile` · `POST .../jobs` with `PREPARE_DRAFT`

## Stack
- Strands Agents + Amazon Bedrock (`amazon.nova-micro-v1:0`)
- AgentCore Runtime, Gateway Web Search, Browser (Live View)
- FastAPI on Lambda behind CloudFront `/api/v1`
- Next.js 15 static export (es/en)
- Deterministic Form 210 engine (no LLM arithmetic)

## Open source
- Repo: https://github.com/hetdev/renta-lista-agent
- License: MIT

## Builder ID
Get one at https://profile.aws.amazon.com/ (sign up with email).
Paste the **email** you used: **hetzel30@gmail.com**

## Video
_(paste YouTube/Vimeo URL, ≤ 5:00)_

## Notes
- Synthetic data only on the public demo
- Fictional reporter for missing-certificate demo: Banco Sintético Andino
- OTP for synthetic portal: 123456
- Demo available free until judging ends (**8 Oct 2026 19:00 COT** / 5:00 p. m. PT)
