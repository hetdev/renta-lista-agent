# Devpost compliance checklist

## Required
- [x] Public GitHub repo with MIT license visible (verified 11 Sep: repo public, LICENSE MIT)
- [x] README (EN) + architecture diagram (`docs/architecture.md`, mermaid)
- [ ] Video ≤ 5:00 on YouTube/Vimeo (public): demo + pitch (problem / who / why)
- [x] Live demo URL free, no login, until **2026-10-08 17:00 PT** (https://deuhmh4dvlr6i.cloudfront.net/ returns 200; keep it up)
- [ ] AWS Builder ID = **email** used to create it
- [ ] Track: **Everyday Agents** only
- [ ] Synthetic data only in demo/video (see blocker on ID `1019072850` below)
- [ ] Submitted before **2026-09-14 17:00 PT** (internal cut 15:00 COT)

## Blockers found in the 11 Sep 2026 code review (fix before recording)
Details and file references in `DOC.md`, section "Hallazgos abiertos".
- [x] Art. 241 bracket table corrected (11 Sep) in `src/rentalista/tax/rates.py` and `rules/ag2025/tax_table.yaml`; 16 unit tests in `tests/unit/tax/test_rates.py`; `demo-draft.json` and `real_demo_run.json` regenerated (saldo a favor 756.893)
- [ ] Rebuild and redeploy the frontend so the public URL stops showing "saldo a pagar 189.288" (still the deployed snapshot)
- [ ] Decide the 25 % exempt labor income (art. 206-10) and 72 UVT per dependent (art. 336-3): implement, or state "not computed" in UI and DOC
- [ ] On-screen banner "Borrador para revisión. No ha sido presentado ante la DIAN." present in the UI
- [ ] Confirm the ID `1019072850` in `demo/fixtures/reporteExogena2025_demo.xlsx` (and `*2850` in the Nequi PDF) is synthetic, or replace it
- [ ] Do not claim Strands / Bedrock / Web Search / Live View as working in the video unless wired: today no code path invokes them and the deployed Live View page is inert
- [ ] `/demo-portal/*` is not routed through CloudFront; add a behavior or demo the portal locally only
- [ ] `make verify` green (ruff format, mypy) before the final commit

## Pitch phrases (must be audible/on screen)
1. Problem: …
2. Who it’s for: …
3. Why it matters: …

## Live resources (record in submission)
| Item | Value |
|---|---|
| Demo | https://deuhmh4dvlr6i.cloudfront.net/ |
| Repo | https://github.com/hetdev/renta-lista-agent |
| Video | _(paste)_ |
| Builder ID email | _(paste)_ |

## Judges not required to test
Video + README must stand alone. Engine numbers in UI must match `demo-draft.json` (enforced by `test_demo_jsons_match_engine`); the deployed build must be rebuilt from the corrected JSON.
