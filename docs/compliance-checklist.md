# Compliance checklist — Devpost

## Hard requirements
- [x] Public GitHub repo + MIT license
- [x] README (EN) + architecture diagram (`docs/architecture.md`)
- [x] Live URL free, no login (until 2026-10-08 19:00 COT) — HTTP 200 verified 14 Sep
- [x] Video ≤ 5:00 — **YouTube**: https://www.youtube.com/watch?v=qnakivEdego (local `docs/rentalista-demo-live.mp4`, 3:10)
- [x] **Video uploaded** to YouTube (public) — URL above; paste on Devpost
- [x] **3 pitch phrases** (problem / who it's for / why it matters) on the opening card and in the voice-over (0:00–0:30)
- [ ] **Devpost submitted** before 2026-09-14 19:00 COT (internal cut 15:00 COT)
- [x] **AWS Builder ID email** → **hetzel30@gmail.com**
- [x] Track: Everyday Agents only
- [x] Synthetic data only — confirm the ID `1019072850` in `demo/fixtures/reporteExogena2025_demo.xlsx` (and `*2850` in the Nequi PDF) is synthetic; replace it if in doubt

## Do not claim in the video or on the form (not true on the public demo today)
- Web Search / Live View as working: provisioned, not wired; the Live View page is inert in the deployed build. Strands Agents + Bedrock Nova Micro DO orchestrate the engine tool (`scripts/run_strands_agent.py`, transcript in `demo/expected/strands_run.json`, AgentCore entrypoint behind `RENTALISTA_STRANDS=1`), just not on the public HTTP path
- "25% labor max 240 UVT": the statute (art. 206 num. 10, Ley 2277/2022) makes it exempt income capped at 790 UVT inside the 40% limit (DOC.md H1)
- (resolved 14 Sep 16:07 COT) Coverage rows and `GET /draft` now come from the API through CloudFront; the coverage page shows the "Exogenous rows (API)" table for API-created cases

## Pitch phrases (must be in the video)
1. Problem: …
2. Who it’s for: …
3. Why it matters: …

## Resources for the form
| Item | Value |
|---|---|
| Demo | https://deuhmh4dvlr6i.cloudfront.net/ |
| Repo | https://github.com/hetdev/renta-lista-agent |
| Video | https://www.youtube.com/watch?v=qnakivEdego |
| Thumbnail | `docs/thumbnail.png` |
| Builder ID email | **hetzel30@gmail.com** |
| Architecture | `docs/architecture.md` |

## AWS Builder ID — cómo conseguirlo (2 minutos)
1. Abre https://profile.aws.amazon.com/ (o entra a builder.aws.com y haz sign-up)
2. Crea cuenta con **tu email**, nombre y contraseña (también vale Google/Apple)
3. Listo: tu **Builder ID es ese email**
4. En el formulario de Devpost, pega ese **email** (no un nombre, no un ARN)

## Optional
- [ ] builder.aws blog post (title includes **Agents for Humans**) — up to 0.6 pts

## After submit
- [ ] Capture confirmation (`submitted`, not draft)
- [ ] Keep infra until **8 Oct 2026 19:00 COT**
