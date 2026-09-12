# RentaLista Agent — Estado del proyecto

**Actualizado:** 11 de septiembre de 2026 · commit `8a596c0` + code review completo + fix tabla art. 241 (working tree, sin commit)  
**Hackathon:** [Agents for Humans](https://agentsforhumans.devpost.com) · deadline **14 sep 2026 17:00 PT**  
**Repo:** https://github.com/hetdev/renta-lista-agent

---

## Resumen en una frase

Demo pública bilingüe con un motor determinista de Formulario 210 (sin LLM) y un pipeline de ingestión (exógena layout DIAN + PDF Nequi) que hoy corre **solo como script local**. La API pública crea casos y guarda el perfil; el resto de la UI es mock, y ningún camino de código invoca Strands, Bedrock ni el Gateway. **La tabla del art. 241 ya está corregida en el repo con tests; la UI desplegada sigue mostrando los números viejos (189.288) hasta reconstruir y subir el frontend.**

---

## Veredicto del code review (11 sep 2026)

**No cumple con todo.** Tres problemas de fondo:

1. **Motor:** tabla art. 241 corregida el 11 sep (B1, con 16 tests); siguen faltando el 25 % exento laboral y el valor legal por dependiente; sin aproximación a miles.
2. **Claims vs realidad:** API, UI, Strands, Gateway, Live View y portal demo estaban documentados como hechos y son mock o no están cableados.
3. **Calidad:** `make verify` en rojo (ruff format, mypy); checklist Devpost sin marcar; sin CI.

Lo que sí está bien: COP entero sin floats, máquina de estados explícita, topes de obligación con UVT 49.799 y operadores correctos (tests en los límites exactos), c28/c139 fuera del tope con test, token de caso hasheado, sin secretos en git, `tsc` limpio, 32 tests en verde, URLs públicas 200, repo público con MIT.

---

## URLs verificadas (HTTP 200, 11 sep)

| Recurso | URL / ID |
|---|---|
| **Demo web** | https://deuhmh4dvlr6i.cloudfront.net/ |
| ES / EN | `/es/` · `/en/` |
| Draft UI | `/es/case/draft/` (snapshot estático del engine, no llama a la API) |
| Live View UI | `/es/case/browser/` (**inerte en el build desplegado**, ver B7) |
| **API pública** | `POST https://deuhmh4dvlr6i.cloudfront.net/api/v1/cases` |
| Health | `GET /api/v1/health` |
| CloudFront | `EEMC7WEZFXF40` · `deuhmh4dvlr6i.cloudfront.net` |
| S3 web | `rentalista-web-697020387519` |
| Lambda API | `rentalista-api` (cuenta `690968743338`, python3.13 arm64; **el handler no está en el repo**) |
| API Gateway HTTP | `pi4y909mlf` |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` READY (ejecuta el entrypoint determinista; sin Strands) |
| Gateway + Web Search | `rentalista-websearch2-f29eutucy6` · target `DP0IKFORKR` READY (**ningún código lo llama**) |
| Bedrock | `amazon.nova-micro-v1:0` · us-east-1 (**ningún código lo invoca**) |
| AWS profile | `rentalista` · cuenta miembro `697020387519` |

Comprobado con curl el 11 sep:
- CloudFront reescribe **cualquier 404**, incluidos los de la API, a `index.html` con 200. `GET /api/v1/cases/{id}` sin token devuelve HTML 200 en público y JSON 404 en local.
- `/demo-portal/*` **no llega al Lambda**: lo sirve S3 y devuelve el index de la SPA.

---

## Qué existe de verdad

| Capa | Implementado y ejercitado | Mock / no cableado |
|---|---|---|
| Motor `tax/` | Obligación (5 topes + IVA), patrimonio, cédula general simplificada, c28, c139, c92 con 28/139 fuera del tope, tarifa art. 241 verificada con tests, 134/137 con invariante, 140/141, atestaciones de ausencia | 25 % exento laboral (art. 206-10), c135 anticipo, c136 sanciones, aproximación a miles |
| Ingestión `ingestion/` | XLSX layout DIAN (header discovery, topes, banner), PDF Nequi determinista | Regex de año no casa con el fixture |
| API `api/` | `POST /cases`, `GET /cases/{id}`, `PUT /profile`, `POST /jobs`, `GET /jobs/{id}`, `live-view`, router `/demo-portal` | Subida de documentos, cobertura, aprobación de portal, consentimiento, recuperación, exportación, `GET draft`. `PREPARE_DRAFT` corre con `amounts={}` y descarta el borrador |
| Agente `agent/` | Entrypoint AgentCore que valida el sobre y llama al motor | `build_agent` (Strands + Bedrock) sin ninguna llamada; Gateway sin cliente; la API no invoca el Runtime |
| Recuperación `document_recovery/` | Proveedor sembrado, política anti-señuelos, política de sesión Browser, query sin PII | Cualquier uso desde la API o el agente |
| Frontend | Landing, demo (crea caso vía API), perfil (PUT vía API), draft desde `demo-draft.json` | Documentos y cobertura en sessionStorage; Live View sin fetch en el build desplegado |
| Infra | CloudFront + S3 (CDK), Lambda + HTTP API (creados a mano) | DynamoDB, S3 documentos, InvokeAgentRuntime desde la API, behavior `/demo-portal/*` |

---

## Pipeline e2e (fixtures del repo, script local)

```bash
uv run python scripts/run_demo_docs.py \
  --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
  --pdf  demo/fixtures/nequi_retencion_demo.pdf
```

| Resultado | Valor (tabla art. 241 corregida, 11 sep) |
|---|---|
| `must_file` | True (ingresos ≥ 1.400 UVT y consignaciones > 1.400 UVT) |
| Renta líquida c93 / c111 | 74.692.002 |
| Impuesto neto c116 | 3.878.107 |
| Retenciones c132 | 4.635.000 |
| **Resultado** | **saldo a favor 756.893** (c134 0 · c137 756.893) |
| c92 | 7.529.468 (intereses vivienda 4.800.000 + c28 120.000 + c139 2.609.468) |

Antes del fix la tabla equivocada daba impuesto 4.824.288 y "saldo a pagar 189.288". `frontend/src/lib/demo-draft.json` y `demo/expected/real_demo_run.json` ya tienen los valores nuevos (`make demo-draft`); **la URL pública sigue mostrando 189.288 hasta `npm run build` + subida a S3 + invalidación de CloudFront**. No grabar el video antes de eso.

---

## Cómo correr localmente

```bash
make install
make test                # 50 tests en verde
make verify              # hoy falla: ruff format (2 archivos) + mypy (16 errores)
uv run uvicorn rentalista.api.main:app --reload
curl -s localhost:8000/demo-portal/     # portal sintético, solo en local
cd frontend && npm run build
```

`make demo-draft` regenera `demo/expected/real_demo_run.json` y `frontend/src/lib/demo-draft.json` con el escenario de los fixtures (módulo `rentalista.ingestion.demo_pipeline`, `case_id` fijo). El test `test_demo_jsons_match_engine` falla si cualquiera de los dos se desvía del engine.

---

## Gates de calidad (11 sep)

| Gate | Resultado |
|---|---|
| `ruff check` | OK |
| `ruff format --check` | 2 archivos sin formatear (`agent/__main__.py`, `ingestion/pdf_facts.py`) |
| `mypy src` (strict) | 16 errores en 6 archivos (stubs yaml/openpyxl; tipos en ingestion, obligation, store, agent) |
| `pytest` | 50 pasan |
| `tsc --noEmit` | OK |
| CI | no existe |

---

## Hallazgos abiertos del code review

### Bloqueantes

| # | Hallazgo | Dónde | Acción |
|---|---|---|---|
| B1 | ~~Tabla art. 241 con impuesto fijo 0/19/135/803/2.307/5.912/10.391 UVT~~ **RESUELTO 11 sep:** ambos archivos con 0/0/116/788/2.296/5.901/10.352, límites exclusivos como el estatuto, redondeo HALF_UP. `tests/unit/tax/test_rates.py`: igualdad con art. 241 y con el YAML, continuidad por tramo, valores conocidos, barrido monótono. JSONs regenerados | `src/rentalista/tax/rates.py`, `rules/ag2025/tax_table.yaml` | Pendiente solo el redeploy del frontend |
| B2 | ~~No se calcula el 25 % exento laboral~~ **RESUELTO 12 sep:** `min(25% c32, 240 UVT)` en casilla 33 (`labor_no_constitutive_25`). Nota: el review citaba tope 790 UVT (art. 206 num. 10); se usó 240 UVT (num. 8 clásico). Verificar contra el instructivo si el perfil lo amerita | `src/rentalista/tax/deductions.py`, `form210.py` | Hecho |
| B3 | ~~c139 52,4 UVT / falta 72 UVT trabajo~~ **RESUELTO 12 sep:** deducción **72 UVT × min(deps,4)** en la cédula de trabajo (casilla 34, `dependent_labor_deduction`). c139 sigue siendo la *adición* 10%×524 UVT a c92 (otra regla, no la misma) | `src/rentalista/tax/deductions.py` | Hecho |
| B4 | Sin aproximación al múltiplo de mil (art. 577 ET); faltan c135 anticipo y c136 sanciones | `src/rentalista/tax/form210.py` | Añadir |
| B5 | `PREPARE_DRAFT` por API corre con `amounts={}`, no guarda ni expone el borrador; el caso queda en PROFILED (reproducido) | `src/rentalista/api/main.py:119` | Ingerir fixtures en servidor, guardar draft, `GET draft`, transición a DRAFT_READY |
| B6 | Sin endpoints de subida, cobertura, portal, consentimiento, recuperación, exportación | `src/rentalista/api/main.py` | Cablear lo mínimo o rebajar README (hecho el 11 sep) |
| B7 | UI documentos/cobertura/draft son mock; Live View desplegada es código muerto (`!API_BASE` con env vacío, el chunk no contiene la llamada) | `frontend/src/app/[locale]/case/browser/browser-content.tsx:41` | Quitar la guarda; documentar el mock |
| B8 | Strands, Bedrock y Web Search no se invocan en ningún camino de código; la API no invoca el Runtime | `src/rentalista/agent/agent.py:56`, `src/rentalista/agent/runtime.py:39` | Cablear o no reclamarlo en el video |
| B9 | Falta el banner "Borrador para revisión. No ha sido presentado ante la DIAN." en la UI (solo hay "No constituye asesoría tributaria") | `frontend/src/messages/*.json` | Añadir |
| B10 | `make verify` en rojo; sin CI | ver gates | Formatear, stubs `types-PyYAML`/`types-openpyxl`, tipos |

### Medios

| # | Hallazgo | Dónde |
|---|---|---|
| M1 | `/demo-portal/*` no enrutado en CloudFront | infra (creada a mano) |
| M2 | CloudFront reescribe los 404 de la API a `index.html` 200; el frontend cae en mock sin avisar | `infra/app.py:44` |
| M3 | Clave de idempotencia global, no por caso (reproducido: el caso B recibe el job del caso A) | `src/rentalista/api/store.py:85` |
| M4 | Jobs distintos de PREPARE_DRAFT quedan en ACCEPTED y retienen el lock 10 min; el siguiente job recibe 409 (reproducido) | `src/rentalista/api/store.py` |
| M5 | `live-view` firma cualquier `session_id` con un token de caso válido | `src/rentalista/api/main.py:167` |
| M6 | ~~`gen_demo_draft.py` generaba el escenario golden~~ **RESUELTO 11 sep:** usa los fixtures vía `demo_pipeline.run_pipeline` y regenera los dos JSON | `scripts/gen_demo_draft.py` |
| M7 | Rule pack YAML validado pero nunca cargado; constantes y tabla duplicadas en código (la tabla ya tiene test de igualdad código = YAML) | `rules/ag2025/`, `src/rentalista/tax/` |
| M8 | Handler Lambda (Mangum) no está en el repo; la API desplegada no se reconstruye desde git | — |
| M9 | `deploy.sh` usa nombre con guion y protocolo MCP para una app HTTP; `build_codezip.sh` no copia `agent.py` (el zip local lo tiene porque se añadió a mano) | `scripts/deploy.sh:41`, `scripts/build_codezip.sh:8` |
| M10 | Fixture XLSX: cabecera "123444 / juan demo" pero las 14 filas llevan el ID `1019072850` y el PDF Nequi termina en `2850`. Confirmar que es sintético | `demo/fixtures/` |
| M11 | El diagrama era Markdown dentro de un `.mmd` (GitHub lo mostraba como texto) y dibujaba DynamoDB/S3 inexistentes. Renombrado a `docs/architecture.md` con sólido = implementado, punteado = planeado | `docs/architecture.md` |

### Bajos

- `src/rentalista/ingestion/pdf_facts.py:62`: la regex de año no casa con "Medellín 2025 Año Gravable"; `year` sale `None`.
- `tests/golden/test_golden_form210.py:68` escribe en `demo/expected/` en cada corrida.
- `src/rentalista/tax/form210.py:27`: factores 0/10/25 % no coinciden con el art. 807 (25/50/75 %); hoy solo afecta a una etiqueta.
- ~~`rates.py` redondeaba HALF_EVEN~~ resuelto 11 sep: HALF_UP como el resto del dominio.
- Cuotas de `Settings` sin usar (200/300 fijos en `store.py`); venv en Python 3.14 con destino 3.13; `.gitignore` con entradas duplicadas.

### Resuelto en revisiones anteriores

UI draft alimentada por JSON del engine · jobs PREPARE_DRAFT ya no quedan en ACCEPTED · docstring async corregido · `expires` del portal validado · `putProfile` marca `mock: true` en offline · XLSX layout DIAN real con header discovery · fixtures que obligan a declarar · tabla art. 241 corregida con tests y JSONs regenerados (11 sep).

---

## Pendiente para Devpost (prioridad)

| # | Ítem | Estado | Notas |
|---|---|---|---|
| 1 | Corregir tabla art. 241 y regenerar números (B1) | **HECHO 11 sep** (sin commit) | Falta `npm run build` + subir a S3 + invalidar CloudFront para que la URL pública muestre saldo a favor 756.893 |
| 2 | Decidir 25 % exento y 72 UVT (B2, B3) | **HECHO 12 sep** | c33 = 25% (tope 240 UVT); c34 = 72 UVT/dep. Demo: impuesto 926.000, saldo a favor 3.709.000 |
| 2b | Redeploy frontend a S3 + CloudFront con los nuevos números | HECHO 12 sep | Verificar en `/es/case/draft/` |
| 3 | Banner DIAN en la UI (B9) | FALTA | Lo exige el guion |
| 4 | Cablear un camino real API a draft o dejar el README rebajado (B5, B6) | FALTA | README ya rebajado el 11 sep |
| 5 | Live View: quitar guarda `API_BASE`; 404 solo en origen S3; behavior `/demo-portal/*` (B7, M1, M2) | FALTA | Solo si sale en el video |
| 6 | `make verify` verde (B10) | FALTA | |
| 7 | Handler Lambda al repo; scripts de deploy (M8, M9) | FALTA | Reproducibilidad |
| 8 | **Video ≤ 5:00** | **FALTA** | Guion en `docs/demo-script.md`; no grabar hasta el redeploy del frontend (hoy muestra 189.288) |
| 9 | **Envío Devpost + Builder ID email** | **FALTA** | `docs/compliance-checklist.md` |
| 10 | Confirmar ID sintético en fixtures (M10) | FALTA | Reemplazar si hay duda |
| 11 | Lambda en cuenta miembro | Bloqueado | SCP `p-sfdav4bi` deniega CreateFunction en `697020387519`; API vive en master |

---

## Estructura clave

```
src/rentalista/{domain,tax,ingestion,agent,api,document_recovery,rules}
demo/fixtures/reporteExogena2025_demo.xlsx
demo/fixtures/nequi_retencion_demo.pdf
frontend/src/lib/demo-draft.json
src/rentalista/ingestion/demo_pipeline.py   # fuente única de los números del demo
scripts/run_demo_docs.py · scripts/gen_demo_draft.py (make demo-draft)
tests/unit/tax/test_rates.py                # tabla art. 241 = estatuto = YAML
docs/{demo-script,compliance-checklist,architecture}.md
```

*Fin del snapshot. Actualizar este archivo al cambiar demo, API o checklist.*
