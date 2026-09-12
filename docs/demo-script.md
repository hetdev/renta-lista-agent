# Demo script — RentaLista (4:40)

Pitch the three Devpost questions **literally** in the first 25s, then demo.

## 0:00–0:25 Pitch (English, on screen + voice)

1. **Problem:** Reconciling Colombia’s third-party tax report (exogenous data) and assembling a Form 210 draft is slow and error-prone.
2. **Who it’s for:** A tax-resident natural person filing their own renta — not an accounting firm.
3. **Why it matters:** Missing certificates, silent zeros, and unverified amounts create real filing risk. RentaLista keeps evidence and human control; it never files with DIAN.

On-screen banner: `Borrador para revisión. No ha sido presentado ante la DIAN.`

## 0:25–0:45 Scope & safety
- No DIAN login, no password, no signature, no payment.
- Public demo uses **synthetic data only**.

## 0:45–2:20 Coverage → missing cert → portal search
1. Open https://deuhmh4dvlr6i.cloudfront.net/es/
2. Load synthetic case (`Probar caso sintético`).
3. Show coverage matrix: rows from exogenous Excel; one `DOCUMENT_MISSING`.
4. Portal search: **real** web search for a real reporter name; **seeded directory** for fictional `Banco Sintético Andino` (say this out loud).
5. Show decoys (lookalike domain, shortener) rejected by policy.

## 2:20–3:05 Consent · Live View · OTP handoff
- Approve domain → consent fields → open Live View.
- Agent hits OTP → `take_control` → human types OTP in the browser (not in chat).
- Resume → same Browser session → download certificate → coverage flips to verified.

## 3:05–3:35 Human-in-the-loop tax conflict
- Exogenous vs certificate mismatch → closed question → user chooses → ledger records actor + timestamp.

## 3:35–4:05 Draft + ledger
- `Preparar borrador` → cells from the **deterministic engine** (not the LLM).
- Open one cell (e.g. 92) → formula, 28/139 outside the cap, rule version.
- Saldo a pagar / a favor with invariant (never both).

## 4:05–4:30 Architecture (diagram only)
- Next.js → CloudFront → API  
- Strands agent on **AgentCore Runtime**  
- Gateway **Web Search** + **Browser** Live View  
- Deterministic Form 210 engine (no LLM math)

## 4:30–4:40 Close
- Demo URL + repo URL  
- “Evidence-first. Human-approved. Not filed with DIAN.”

## Recording rules
- Window + diagram only; no desktop/secrets.
- English voice or full English subtitles.
- Same public build as the URL; duration **&lt; 5:00**.
