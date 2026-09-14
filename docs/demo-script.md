# Demo script — RentaLista (4:40)

> **Estado 14 sep 2026 (segunda revisión, ver DOC.md):** el video final es `docs/rentalista-demo-live.mp4` (**3:10**, grabación real con Playwright + narración EN, scripts en `scripts/demo-video/`); este guion es la versión larga y solo se grabaron las escenas demoables. Demoable hoy en la URL pública: landing, crear caso y perfil vía API, borrador con el snapshot del motor (**saldo a favor 3.709.000**, c33/c34 en el ledger) y banner DIAN en footer y borrador. **No demoable hoy:** cobertura desde la API (el Lambda de CloudFront es un build anterior; la UI muestra el mock local), Live View (página inerte en el build desplegado), portal `/demo-portal` (no enrutado en CloudFront) y Strands / Bedrock / Gateway (sin código que los invoque). No afirmar "máximo 240 UVT" para el 25 % laboral (hallazgo H1).

Pitch the three Devpost questions **literally** in the first 25s, then demo.

## 0:00–0:25 Pitch (English, on screen + voice)

1. **Problem:** Reconciling Colombia’s third-party tax report (exogenous data) and assembling a Form 210 draft is slow and error-prone.
2. **Who it’s for:** A tax-resident natural person filing their own renta — not an accounting firm.
3. **Why it matters:** Missing certificates, silent zeros, and unverified amounts create real filing risk. RentaLista keeps evidence and human control; it never files with DIAN.

On-screen banner: `Borrador para revisión. No ha sido presentado ante la DIAN.` (ya en la UI: footer y página de borrador)

## 0:25–0:45 Scope & safety
- No DIAN login, no password, no signature, no payment.
- Public demo uses **synthetic data only**.

## 0:45–2:20 Coverage → missing cert → portal search (**no demoable hoy**)
1. Open https://deuhmh4dvlr6i.cloudfront.net/en/
2. Load the synthetic case.
3. Show coverage matrix: rows from exogenous Excel; one `DOCUMENT_MISSING`. *(hoy: mock local; `GET /coverage` devuelve 5 filas fijas pero no está en el Lambda de CloudFront)*
4. Portal search: **real** web search for a real reporter name; **seeded directory** for fictional `Banco Sintético Andino` (say this out loud). *(hoy: solo el proveedor sembrado, en tests)*
5. Show decoys (lookalike domain, shortener) rejected by policy. *(hoy: solo en tests)*

## 2:20–3:05 Consent · Live View · OTP handoff (**no demoable hoy**)
- Approve domain → consent fields → open Live View.
- Agent hits OTP → `take_control` → human types OTP in the browser (not in chat).
- Resume → same Browser session → download certificate → coverage flips to verified.

## 3:05–3:35 Human-in-the-loop tax conflict (**no demoable hoy**)
- Exogenous vs certificate mismatch → closed question → user chooses → ledger records actor + timestamp.

## 3:35–4:05 Draft + ledger (demoable)
- `Prepare draft` → cells from the **deterministic engine** (not the LLM). *(hoy: snapshot `demo-draft.json` generado por el motor; `GET /draft` existe pero no en el Lambda de CloudFront)*
- Open one cell (e.g. 92) → formula, 28/139 outside the cap, rule version.
- Saldo a pagar / a favor with invariant (never both). *(saldo a favor 3.709.000 con las reglas actuales; provisional, ver H1/H2 en DOC.md)*

## 4:05–4:30 Architecture (diagram only)
- Next.js → CloudFront → API  
- **AgentCore Runtime** runs the deterministic entrypoint *(Strands no está cableado)*
- Gateway **Web Search** + **Browser** Live View *(recursos creados, sin código que los use)*
- Deterministic Form 210 engine (no LLM math)

## 4:30–4:40 Close
- Demo URL + repo URL  
- “Evidence-first. Human-approved. Not filed with DIAN.”

## Recording rules
- Window + diagram only; no desktop/secrets.
- English voice or full English subtitles.
- Same public build as the URL; duration **&lt; 5:00**.
- Do not show anything as working that is marked *no demoable hoy* unless it has been wired and verified in the public URL first.
