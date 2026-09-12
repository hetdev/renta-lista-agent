# Demo script — RentaLista (4:40)

> **Estado 11 sep 2026 (code review, ver DOC.md):** las escenas 0:45–3:35 (cobertura desde Excel, búsqueda real de portal, Live View con OTP, conflicto con ledger) **no son demoables** en la URL pública: la UI de documentos/cobertura es mock, la página Live View desplegada no llama a la API, `/demo-portal/*` no está enrutado en CloudFront y ningún código invoca Strands, Bedrock ni el Gateway. O se cablean antes de grabar, o se narran sobre el diagrama sin mostrarlas como funcionando. La tabla art. 241 ya está corregida en el repo (el demo da saldo a favor 756.893); la URL pública muestra 189.288 hasta reconstruir y subir el frontend: hacerlo antes de grabar. El banner DIAN de abajo todavía no existe en la UI.

Pitch the three Devpost questions **literally** in the first 25s, then demo.

## 0:00–0:25 Pitch (English, on screen + voice)

1. **Problem:** Reconciling Colombia’s third-party tax report (exogenous data) and assembling a Form 210 draft is slow and error-prone.
2. **Who it’s for:** A tax-resident natural person filing their own renta — not an accounting firm.
3. **Why it matters:** Missing certificates, silent zeros, and unverified amounts create real filing risk. RentaLista keeps evidence and human control; it never files with DIAN.

On-screen banner: `Borrador para revisión. No ha sido presentado ante la DIAN.` (**pendiente en la UI**, hallazgo B9)

## 0:25–0:45 Scope & safety
- No DIAN login, no password, no signature, no payment.
- Public demo uses **synthetic data only**.

## 0:45–2:20 Coverage → missing cert → portal search (**no demoable hoy**)
1. Open https://deuhmh4dvlr6i.cloudfront.net/es/
2. Load synthetic case (`Probar caso sintético`).
3. Show coverage matrix: rows from exogenous Excel; one `DOCUMENT_MISSING`. *(hoy: tabla fija en sessionStorage, no viene del Excel)*
4. Portal search: **real** web search for a real reporter name; **seeded directory** for fictional `Banco Sintético Andino` (say this out loud). *(hoy: solo el proveedor sembrado, en tests)*
5. Show decoys (lookalike domain, shortener) rejected by policy. *(hoy: solo en tests)*

## 2:20–3:05 Consent · Live View · OTP handoff (**no demoable hoy**)
- Approve domain → consent fields → open Live View.
- Agent hits OTP → `take_control` → human types OTP in the browser (not in chat).
- Resume → same Browser session → download certificate → coverage flips to verified.

## 3:05–3:35 Human-in-the-loop tax conflict (**no demoable hoy**)
- Exogenous vs certificate mismatch → closed question → user chooses → ledger records actor + timestamp.

## 3:35–4:05 Draft + ledger (demoable con el snapshot estático)
- `Preparar borrador` → cells from the **deterministic engine** (not the LLM). *(hoy: JSON estático generado por el engine, no una llamada a la API)*
- Open one cell (e.g. 92) → formula, 28/139 outside the cap, rule version.
- Saldo a pagar / a favor with invariant (never both). *(con la tabla corregida el demo da saldo a favor 756.893; redeploy del frontend pendiente)*

## 4:05–4:30 Architecture (diagram only)
- Next.js → CloudFront → API  
- Strands agent on **AgentCore Runtime** *(el Runtime ejecuta el entrypoint determinista; Strands no está cableado)*
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
