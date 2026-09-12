# RentaLista Agent — Estado del proyecto

**Actualizado:** 12 de septiembre de 2026 · commit `bd85241`+  
**Hackathon:** [Agents for Humans](https://agentsforhumans.devpost.com) · deadline **14 sep 2026 17:00 PT**  
**Repo:** https://github.com/hetdev/renta-lista-agent

---

## Resumen en una frase

Demo pública bilingüe que ingiere exógena (layout DIAN real) + certificado Nequi, evalúa **obligación de declarar** y produce un **borrador Form 210** con motor determinista (no LLM), orquestado por Strands sobre AgentCore Runtime.

---

## URLs verificadas (HTTP 200)

| Recurso | URL / ID |
|---|---|
| **Demo web** | https://deuhmh4dvlr6i.cloudfront.net/ |
| ES / EN | `/es/` · `/en/` |
| Draft UI | `/es/case/draft/` (celdas del engine) |
| Live View UI | `/es/case/browser/` |
| **API pública** | `POST https://deuhmh4dvlr6i.cloudfront.net/api/v1/cases` |
| Health | `GET /api/v1/health` |
| CloudFront | `EEMC7WEZFXF40` · `deuhmh4dvlr6i.cloudfront.net` |
| S3 web | `rentalista-web-697020387519` |
| Lambda API | `rentalista-api` (cuenta `690968743338`, python3.13 arm64) |
| API Gateway HTTP | `pi4y909mlf` |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` **READY** |
| Gateway + Web Search | `rentalista-websearch2-f29eutucy6` · target `DP0IKFORKR` **READY** |
| Bedrock | `amazon.nova-micro-v1:0` · us-east-1 |
| AWS profile | `rentalista` · cuenta miembro `697020387519` |

---

## Hecho (P0 técnico)

### Dominio y motor
- COP entero sin float en el dominio (`domain/money.py`)
- Máquina de estados con ciclos de Browser
- Obligación AG 2025 (UVT 49.799, operadores `>` / `>=`)
- Casilla 92: 28 y 139 **fuera** del tope 40% / 1.340 UVT
- Tarifa art. 241, invariantes 134/137, casillas 140/141
- **32 tests** en verde (`uv run pytest`)

### Ingestión
- XLSX **layout DIAN real** (header discovery, topes, multi-banner)
- PDF Nequi determinista (`ingestion/pdf_facts.py`)
- Fixtures del demo: `demo/fixtures/reporteExogena2025_demo.xlsx` + `nequi_retencion_demo.pdf`

### Pipeline e2e (fixtures del repo)
```bash
uv run python scripts/run_demo_docs.py \
  --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
  --pdf  demo/fixtures/nequi_retencion_demo.pdf
```

| Resultado | Valor |
|---|---|
| `must_file` | **True** (ingresos ≥ 1.400 UVT y consignaciones > 1.400 UVT) |
| Impuesto neto c116 | **4.824.288** |
| Retenciones c132 | 4.635.000 |
| **Saldo a pagar c134** | **189.288** |
| c92 | 7.529.468 (incluye c28 120.000 + c139 2.609.468) |

### API y jobs
- `POST /cases` → token `X-Case-Token`
- `PUT /profile` → `PROFILED` / `OUT_OF_SCOPE`
- `POST /jobs` `PREPARE_DRAFT` → **`SUCCEEDED`** (lock liberado)
- Portal `/demo-portal` OTP `123456` + expiración de sesión
- Live View endpoint (firma ≤300 s) listo; iframe en `/case/browser`

### Infra
- CloudFront `/api/*` → HTTP API → Lambda (mismo origin que la web)
- AgentCore Runtime CodeZip (30 MB, entry `agent.py`)
- Gateway web-search 1.2.0 con domainFilter (acortadores excluidos)
- Browser session smoke (parada para ahorrar coste)

### Frontend
- Next.js 15 static export es/en
- Draft UI lee `frontend/src/lib/demo-draft.json` **generado del engine**
- `make demo-draft` regenera el JSON

---

## Cómo correr localmente

```bash
make install
make test
make demo-draft          # regenera demo-draft.json desde el engine
uv run uvicorn rentalista.api.main:app --reload
# opcional: NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run build
cd frontend && npm run build
bash scripts/smoke_cloud.sh
```

---

## Pendiente para Devpost (prioridad)

| # | Ítem | Estado | Notas |
|---|---|---|---|
| 1 | **Video ≤ 5:00** | **FALTA** | Guion en `docs/demo-script.md`; pitch 3 frases literales |
| 2 | **Envío Devpost + Builder ID email** | **FALTA** | `docs/compliance-checklist.md` |
| 3 | Live View con sesión Browser real en la demo | Parcial | UI + API listas; falta flujo grabado con OTP |
| 4 | Cobertura / recuperación UI completa | Parcial | Draft y profile sí; coverage documents son mock/enriquecer |
| 5 | Golden vs Programa Ayuda Renta | Manual | Captura una vez; el motor ya es determinista |
| 6 | CSP `frame-src` en CloudFront | FALTA | Necesario si el iframe Live View da error |
| 7 | Bonus builder.aws (0.6 pts) | Opcional | Solo si P0 verde |
| 8 | Lambda en cuenta miembro | Bloqueado | SCP `p-sfdav4bi` aún deniega CreateFunction en `697020387519`; API vive en master |

---

## Code review (ponytail + correctness) — cierre

### Resuelto desde el review anterior
- UI draft ≠ motor → `demo-draft.json` del engine  
- Jobs stuck en `ACCEPTED` → `SUCCEEDED` + lock release  
- Docstring async mentiroso → corregido  
- Portal `expires` sin validar → `_get_session`  
- putProfile “ok” silencioso en mock → `mock: true`  
- XLSX DIAN real no se parseaba → header discovery  
- Demo con montos insuficientes → fixtures que **obligan a declarar**

### Hallazgos abiertos (no bloquean el video si se documentan)
| Sev | Hallazgo | Acción lazy |
|---|---|---|
| Medio | API in-memory (se pierde al reciclar Lambda) | OK para demo; no persistir PII |
| Medio | Live View requiere sesión Browser + IAM del API | Grabar con sesión ya abierta o fallback manual |
| Medio | Tax table hardcodeada vs YAML del rule pack | Documentado; YAML es validado, no cargado |
| Bajo | 3 issues ruff restantes (SIM108 / E501) | Arreglados en este commit o quedan cosméticos |
| Bajo | `_MONEY` regex sin usar en `pdf_facts` | `delete:` si no se usa |
| Bajo | Coverage UI no llama a la API de cobertura | P1 |
| Info | SCP org `p-sfdav4bi` restrictivo | Documentado arriba |

### Ponytail net
Los últimos commits eliminaron inventos de UI y jobs fake. No se añadieron abstracciones nuevas. Neto del último bloque: **+fixtures realistas, −código inventado**.

---

## Próximos pasos sugeridos (orden)

1. **Grabar video** con `docs/demo-script.md` usando https://deuhmh4dvlr6i.cloudfront.net/es/ (saldo 189.288 visible en draft).  
2. Enviar Devpost con Builder ID email + checklist.  
3. Si sobra tiempo: flujo Live View real + CSP CloudFront.

---

## Estructura clave

```
src/rentalista/{domain,tax,ingestion,agent,api,document_recovery,rules}
demo/fixtures/reporteExogena2025_demo.xlsx
demo/fixtures/nequi_retencion_demo.pdf
frontend/src/lib/demo-draft.json
scripts/run_demo_docs.py
docs/{demo-script,compliance-checklist,architecture}.md
```

*Fin del snapshot. Actualizar este archivo al cambiar demo, API o checklist.*
