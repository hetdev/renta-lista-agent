# RentaLista Agent — Estado del proyecto

**Actualizado:** 14 de septiembre de 2026 · HEAD `ecd3a9b`  
**Hackathon:** [Agents for Humans](https://agentsforhumans.devpost.com) · **deadline hoy 14 sep 2026 19:00 COT** (oficial: 5:00 p. m. Pacific)  
**Repo:** https://github.com/hetdev/renta-lista-agent

---

## Qué es

Demo pública bilingüe (es/en) que:

1. Ingiere exógena (layout DIAN) + certificado Nequi  
2. Evalúa **obligación de declarar** (UVT 2025)  
3. Calcula borrador Form 210 con **motor determinista** (no LLM)  
4. Orquesta con **Strands** sobre **AgentCore Runtime** + Gateway Web Search + Browser  

> Borrador para revisión. No ha sido presentado ante la DIAN.

---

## URLs verificadas (HTTP 200)

| Recurso | URL / ID |
|---|---|
| **Demo ES** | https://deuhmh4dvlr6i.cloudfront.net/es/ |
| **Demo EN** | https://deuhmh4dvlr6i.cloudfront.net/en/ |
| Draft UI | `/es/case/draft/` · `/en/case/draft/` |
| Live View UI | `/es/case/browser/` |
| **API** | `https://deuhmh4dvlr6i.cloudfront.net/api/v1/health` |
| CloudFront | `EEMC7WEZFXF40` |
| S3 web | `rentalista-web-697020387519` |
| Lambda API | `rentalista-api` (cuenta master `690968743338`) |
| API Gateway HTTP | `pi4y909mlf` |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` **READY** |
| Gateway Web Search | `rentalista-websearch2-f29eutucy6` + target `DP0IKFORKR` **READY** |
| Bedrock | `amazon.nova-micro-v1:0` · us-east-1 |
| AWS profile | `rentalista` · miembro `697020387519` |

---

## Hecho (P0 técnico)

### Motor tributario (determinista)
| Regla | Implementación |
|---|---|
| UVT 2025 | 49.799 (Res. 193/2024) |
| Obligación | operadores `>` / `>=` exactos |
| Tabla art. 241 | 0 / 0·19% / 116·28% / 788·33% / 2296·35% / 5901·37% / 10352·39% |
| 25% laboral no constitutivo | casilla 33 · máx. **240 UVT** |
| 72 UVT / dependiente (trabajo) | casilla 34 · máx. 4 |
| c92 | 28 y 139 **fuera** del tope 40% / 1.340 UVT |
| Redondeo | art. 577 → miles (impuesto, retenciones, saldos) |
| Anticipo art. 807 | FIRST 0% · SECOND 25% · LATER 75% |
| Casillas 135–136 | anticipo declarado + sanciones (0 MVP) |
| Invariantes | c134 y c137 no ambos positivos |
| **i18n** | etiquetas **es/en** de todas las casillas (`tax/i18n.py`) |

### Demo e2e (fixtures del repo)
```
must_file = True
c32 salarios           89.250.000
c33 25% (cap 240 UVT)  11.951.760
c34 72 UVT × 1 dep      3.585.528
c116 impuesto (red. mil)  926.000
c132 retenciones        4.635.000
c137 saldo a favor      3.709.000
```

### API pública
- `POST /cases?locale=es|en` → token — **OK**
- `PUT /profile` → `PROFILED` — **OK**
- `POST /jobs` `PREPARE_DRAFT` → **`SUCCEEDED`** — **OK**
- `GET /draft` · `POST /documents` · `GET /coverage` — en código y en OpenAPI del zip; el API Gateway desplegado aún no los expone de forma fiable (store in-memory + deploy). Para el video: UI draft con `demo-draft.json` del engine
- Live View: endpoint en el API; requiere `bedrock-agentcore` en el zip de Lambda y una sesión Browser activa
- Portal `/demo-portal` OTP `123456`

### Infra extra (14 sep)
- Lambda **cuenta miembro** `rentalista-api` (SCP ya permite CreateFunction)
- API Gateway HTTP `lnfsntpv6j`
- CSP `frame-src` AgentCore en CloudFront
- CI local en `.github/workflows/ci.yml` (no se pushea: el token OAuth no tiene scope `workflow`)

### Frontend
- Next.js 15 static export es/en
- Draft UI: resumen + **ledger bilingüe** + disclaimer DIAN
- Coverage/documents: UI lista; cobrellama a la API si responde, si no mock local
- `demo-draft.json` con `labels.es/en` y `disclaimer.es/en`

### Calidad
- **52 tests** · ruff OK  
- `make demo-draft` regenera JSONs desde el engine  

---

## Qué falta (orden para el deadline de hoy)

| # | Ítem | Prioridad | Notas |
|---|---|---|---|
| **1** | **Video ≤ 5:00** | **CRÍTICO** | Requisito Devpost. Guion: `docs/demo-script.md`. Grabar con saldo 3.709.000 y c33/c34 visibles |
| **2** | **Envío Devpost + Builder ID (email)** | **CRÍTICO** | `docs/compliance-checklist.md`. Corte interno 15:00 COT · deadline **19:00 COT** |
| 3 | Live View real en el video | Alto | Endpoint listo; abrir sesión Browser y pegar `?session=` en `/case/browser/` |
| 4 | Cobertura UI → API | Medio | UI lista; API route en código; GW aún parcial — usar mock si falla |
| 5 | Golden vs Ayuda Renta | Bajo | Manual una vez |
| 6 | CSP `frame-src` CloudFront | **HECHO** | Response headers policy `rentalista-csp` |
| 7 | Bonus builder.aws | Opcional | 0.6 pts |
| 8 | Lambda en cuenta miembro | **HECHO** | `rentalista-api` + `lnfsntpv6j` |
| 9 | CI GitHub Actions | Hecho local | `.github/workflows/ci.yml`; push requiere scope `workflow` en el PAT |

---

## Cómo correr

```bash
make install && make test
make demo-draft          # regenera demo-draft.json
uv run uvicorn rentalista.api.main:app --reload
cd frontend && npm run build

# e2e fixtures
uv run python scripts/run_demo_docs.py \
  --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
  --pdf  demo/fixtures/nequi_retencion_demo.pdf
```

OTP portal sintético: **`123456`**

---

## Resumen del code review (cerrado)

### Resuelto
UI draft = motor · jobs SUCCEEDED · 25% laboral + 72 UVT/dep · art. 241 · art. 577 · art. 807 · i18n es/en · XLSX DIAN real · fixtures que obligan a declarar · API pública CloudFront · disclaimer DIAN · portal expiry · Gateway + Runtime READY

### Abierto (no bloquea el envío si el video es honesto)
- API in-memory (se pierde al reciclar Lambda)  
- Coverage/documents aún mock en UI  
- Rule pack YAML validado, no cargado en runtime  
- SCP org impide Lambda en la cuenta miembro  
- 240 UVT (no 790) para el 25% — verificar si el video menciona el tope  

---

## Checklist Devpost

- [ ] Video público ≤ 5:00 (demo + pitch 3 frases)
- [ ] Devpost `submitted` antes de **19:00 COT** (oficial: 5:00 p. m. Pacific)
- [ ] Builder ID = **hetzel30@gmail.com**
- [ ] Repo público MIT (hecho)
- [ ] README EN + diagrama (hecho)
- [ ] URL live sin login hasta 8 oct (hecho)
- [ ] Track único: Everyday Agents
- [ ] Solo datos sintéticos (hecho)

---

*Actualizar este archivo al cambiar demo, API o checklist.*
