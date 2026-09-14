# RentaLista Agent — Estado del proyecto

**Actualizado:** 14 de septiembre de 2026 · HEAD `ab6a212` · segunda revisión de código (verificado con curl, pytest, ruff, mypy, tsc)  
**Hackathon:** [Agents for Humans](https://agentsforhumans.devpost.com) · **deadline hoy 14 sep 2026 19:00 COT** (oficial: 5:00 p. m. Pacific)  
**Repo:** https://github.com/hetdev/renta-lista-agent

---

## Qué es

Demo pública bilingüe (en por defecto, es) que:

1. Ingiere exógena (layout DIAN) + certificado Nequi (fixtures sintéticos del repo)
2. Evalúa **obligación de declarar** (UVT 2025)
3. Calcula borrador Form 210 con **motor determinista** (no LLM), etiquetas es/en, redondeo a miles
4. Sirve UI estática + API de caso / perfil / borrador detrás de CloudFront

El **AgentCore Runtime** ejecuta el entrypoint determinista. **Strands, el modelo Bedrock, el Gateway Web Search y el Browser están aprovisionados (READY) pero ningún camino de código público los invoca.** Decirlo así en el video y en Devpost.

> Borrador para revisión. No ha sido presentado ante la DIAN.

---

## Qué falta HOY (orden)

| # | Ítem | Estado | Notas |
|---|---|---|---|
| 1 | **Video subido** | **HECHO**: https://www.youtube.com/watch?v=qnakivEdego (`docs/rentalista-demo-live.mp4`, 3:10, demo real con narración EN; scripts en `scripts/demo-video/`) | Pegar la URL en Devpost |
| 2 | **Enviar Devpost + Builder ID email** | FALTA | Corte interno 15:00 COT · límite 19:00 COT; capturar confirmación `submitted` |
| 3 | **API pública con `/draft`, `/coverage`, `/documents`** | **HECHO 14 sep 16:07 COT** | `bash scripts/deploy_api_member.sh` copió el paquete del Lambda master al miembro (`rentalista-api`, mismo CodeSha256). Verificado por CloudFront: `GET /draft` 200 con saldo a favor 3.709.000, `GET /coverage` 200 con 5 filas, `POST /documents` 201 |
| 4 | Quitar "max 240 UVT" del pitch | Hecho en `docs/devpost-submission-en.md` | El 25 % laboral es renta exenta con tope **790 UVT** (art. 206 num. 10, Ley 2277/2022); el motor usa 240 UVT y lo trata como no constitutivo (H1). No mencionar el tope en el video |
| 5 | Live View en `/case/browser/` | No demoable | La página desplegada sigue con la guarda `!API_BASE` (env vacío): el chunk no contiene la llamada a `live-view`. Solo si se quiere mostrar: quitar la guarda, rebuild, subir |
| 6 | `make verify` | Rojo | `ruff format` 3 archivos (`agent/__main__.py`, `ingestion/pdf_facts.py`, `tax/form210.py`), mypy 17 errores. Tests 52 en verde, `ruff check` OK, `tsc` OK |
| 7 | Confirmar ID sintético | Pendiente | `demo/fixtures/reporteExogena2025_demo.xlsx` lleva `1019072850` en las 14 filas (la cabecera dice 123444); el PDF Nequi termina en `2850` |

---

## URLs verificadas (14 sep, curl)

| Recurso | URL / ID | Estado |
|---|---|---|
| **Demo EN (por defecto)** | https://deuhmh4dvlr6i.cloudfront.net/en/ | 200; la raíz redirige a `/en/` |
| **Demo ES** | https://deuhmh4dvlr6i.cloudfront.net/es/ | 200 |
| Draft UI | `/en/case/draft/` · `/es/case/draft/` | 200; chunk desplegado con 3.709.000 / 926.000 / c33 / c34 y banner DIAN |
| Live View UI | `/en/case/browser/` | 200 pero inerte (sin fetch a `live-view`) |
| **API** | `https://deuhmh4dvlr6i.cloudfront.net/api/v1/` | `health`, `POST /cases`, `PUT /profile`, `POST /jobs` (SUCCEEDED, caso DRAFT_READY), `GET /draft` (200, saldo a favor 3.709.000), `GET /coverage` (200, 5 filas), `POST/GET /documents` (201) — todo OK desde el redeploy de las 16:07 COT |
| 404 de la API | | Ya devuelve JSON 404 (antes CloudFront lo convertía en `index.html` 200) |
| CSP | | `frame-src` y `connect-src` para `*.bedrock-agentcore.us-east-1.amazonaws.com`; `x-frame-options: SAMEORIGIN` |
| `/demo-portal/*` | | 404 HTML: no está enrutado en CloudFront; solo con la API local |
| CloudFront | `EEMC7WEZFXF40` | |
| S3 web | `rentalista-web-697020387519` | |
| Lambda API master | `pi4y909mlf` (cuenta `690968743338`) | **Código actual** (`/draft`, `/coverage` OK) |
| Lambda API miembro | `rentalista-api` · `lnfsntpv6j` (cuenta `697020387519`) | Origen de CloudFront; **código actual** desde el 14 sep 16:07 COT (mismo paquete que el master, vía `scripts/deploy_api_member.sh`) |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` | READY; ejecuta el entrypoint determinista |
| Gateway Web Search | `rentalista-websearch2-f29eutucy6` · target `DP0IKFORKR` | READY; sin cliente en el código |
| Bedrock | `amazon.nova-micro-v1:0` · us-east-1 | sin invocación en el código |
| AWS profile | `rentalista` · miembro `697020387519` | |

---

## Hecho (verificado)

### Motor tributario (determinista, `src/rentalista/tax/`)

| Regla | Implementación | Estado |
|---|---|---|
| UVT 2025 | 49.799 (Res. 193/2024) | OK |
| Obligación | 5 topes + IVA, operadores `>` / `>=` exactos, tests en los límites | OK |
| Tabla art. 241 | 0 / 0·19 % / 116·28 % / 788·33 % / 2296·35 % / 5901·37 % / 10352·39 %, límites exclusivos, HALF_UP; igualdad código = YAML con test | OK (corregida 11 sep) |
| c92 | 28 y 139 fuera del tope 40 % / 1.340 UVT | OK |
| Redondeo art. 577 | c116, c130, c131, c132, c134, c137 a miles | OK (parcial: el resto de casillas sin redondear) |
| c135 / c136 | anticipo declarado + sanciones (0 en MVP) | Presentes (ver H4) |
| i18n | etiquetas es/en de todas las casillas (`tax/i18n.py`), locale por caso | OK |
| 25 % laboral (c33) | min(25 % c32, 240 UVT) como **no constitutivo**, fuera del tope | **Revisar (H1)** |
| 72 UVT / dependiente (c34) | 72 UVT × min(dep, 4), fuera del tope | OK, pero **duplicado con c139 (H2)** |
| Anticipo art. 807 | FIRST 0 % · SECOND 25 % · LATER 75 % | **Revisar (H3)** |

### Demo e2e (fixtures del repo, `make demo-draft`)

```
must_file = True   (ingresos ≥ 1.400 UVT; consignaciones > 1.400 UVT)
c32 salarios               89.250.000
c33 25 % (cap 240 UVT)     11.951.760
c34 72 UVT × 1 dep          3.585.528
c92 exentas+deducc          7.529.468   (vivienda 4.800.000 + c28 120.000 + c139 2.609.468)
c93 renta líquida          59.154.714
c116 impuesto (red. mil)      926.000
c132 retenciones            4.635.000
c137 saldo a favor          3.709.000
```

`test_demo_jsons_match_engine` garantiza que `frontend/src/lib/demo-draft.json` y `demo/expected/real_demo_run.json` son exactamente esto. La UI desplegada ya lo muestra.

### API (`src/rentalista/api/main.py`)

- `POST /cases?locale=en|es` → token · `GET /cases/{id}` · `PUT /profile` → PROFILED
- `POST /jobs` `PREPARE_DRAFT` → SUCCEEDED, caso DRAFT_READY, borrador guardado en memoria con los montos de los fixtures (o el snapshot congelado si el zip no trae openpyxl)
- `GET /draft` · `GET /coverage` (5 filas fijas) · `POST/GET /documents` — en producción detrás de CloudFront desde el 14 sep 16:07 COT (verificado e2e)
- `GET .../live-view` (firma ≤ 300 s; requiere `bedrock-agentcore` en el zip y una sesión Browser)
- Portal `/demo-portal` OTP `123456` (solo local)
- Store in-memory: se pierde al reciclar el Lambda; clave de idempotencia global (no por caso)

### Frontend

- Next.js 15 static export, **en por defecto**, es
- Draft: resumen + ledger bilingüe (c33, c34, c92, c116, c132, c134, c137) + disclaimer DIAN; usa el snapshot `demo-draft.json`, no llama a `GET /draft`
- Coverage/documents: llaman a la API si el caso no es mock; con la API redeployada, cobertura muestra la tabla "Exogenous rows (API)" (5 filas) además del inventario local, y "Mark as uploaded" registra el documento vía `POST /documents`
- Footer con "Borrador para revisión. No ha sido presentado ante la DIAN."

### Infra (14 sep)

- Lambda en cuenta miembro creado (el SCP ya permite CreateFunction), API Gateway `lnfsntpv6j`; el 14 sep a las 16:07 COT recibió el paquete actual del master con `scripts/deploy_api_member.sh` (verifica `GET /draft` por CloudFront y hace rollback si falla)
- CSP `frame-src` AgentCore en CloudFront (policy `rentalista-csp`)
- CloudFront ya no reescribe los 404 de la API
- CI: `.github/workflows/ci.yml` existe solo en local (gitignored; el PAT no tiene scope `workflow`), así que el repo público no tiene CI

### Calidad (14 sep)

| Gate | Resultado |
|---|---|
| `pytest` | 52 pasan |
| `ruff check` | OK |
| `ruff format --check` | 3 archivos sin formatear |
| `mypy src` (strict) | 17 errores en 7 archivos (stubs yaml/openpyxl; `agent/agent.py` 5, `ingestion/exogenous_xlsx.py` 6, `tax/obligation.py` 2, `api/main.py`, `api/store.py`, `rules/validator.py`, `agent/runtime.py` 1 c/u) |
| `tsc --noEmit` | OK |
| `rentalista-rules rules/ag2025` | OK |

---

## Hallazgos abiertos (revisión 14 sep)

### Motor: reglas nuevas con base legal dudosa (no bloquean el envío si el video no las afirma)

| # | Hallazgo | Dónde | Efecto en el demo | Arreglo |
|---|---|---|---|---|
| H1 | El 25 % laboral es **renta exenta** del art. 206 **num. 10**, tope **790 UVT** anuales (Ley 2277/2022), calculada tras restar INCRNGO, deducciones y otras exentas, y **entra en el tope del 40 % / 1.340 UVT**. El código lo trata como no constitutivo con tope 240 UVT (el 240 es el del 1 % factura) y lo resta antes del tope | `tax/deductions.py:16-30`, `tax/form210.py:107-118` | c33 sería ~19 M como exenta dentro del tope, no 11,95 M fuera | Cap 790, moverlo a `rentas_exentas_candidatas` de c92 y sacarlo de los INCRNGO; regenerar JSONs y tests |
| H2 | Dependientes **contados dos veces**: c34 (72 UVT, art. 336 num. 3, correcto y fuera del tope) **y** c139 "10 % × 524 UVT" (sin base legal identificada) | `tax/form210.py:167-171`, `tax/deductions.py:83-92` | 2.609.468 de deducción extra → impuesto ~500 k menor | Poner c139 en 0 o sustituirla por el art. 387 inc. 2 (10 % de ingresos laborales, máx. 32 UVT/mes, dentro del tope) |
| H3 | Art. 807: primer año **25 %**, segundo **50 %**, siguientes 75 %. El código usa 0 / 25 / 75 | `tax/form210.py:45-56`, `rules/ag2025/constants.yaml:15-17` | Ninguno hoy (25 % × 926.000 < retenciones → 0) | Corregir porcentajes |
| H4 | c135 muestra el anticipo **declarado del año anterior** (duplica c130) en vez del anticipo **para el año siguiente**; verificar además la numeración 133–137 contra el instructivo | `tax/form210.py:228-234` | Ninguno hoy (anticipo sugerido 0) | Usar `anticipo_sugerido` = % × impuesto neto − retenciones, mínimo 0 |
| H5 | El comentario cita "art. 206 num. 8" para el 25 % | `tax/deductions.py:16` | Doc | num. 10 |

Con H1 y H2 corregidos el demo sigue dando **saldo a favor**, del orden de 4,6 M (aprox.): la conclusión del video no cambia, el número sí.

### Producto / infra

- **P1** ~~CloudFront → Lambda miembro con build anterior~~ resuelto el 14 sep 16:07 COT (ítem 3 de "Qué falta").
- **P2** Live View UI inerte en el build desplegado (`browser-content.tsx:41`, guarda `!API_BASE`).
- **P3** `/demo-portal/*` no enrutado; Strands / Bedrock / Gateway sin uso en código; la API no invoca el Runtime.
- **P4** Clave de idempotencia global (`api/store.py:85`); los jobs distintos de PREPARE_DRAFT quedan ACCEPTED con lock de 10 min; `live-view` firma cualquier `session_id`.
- **P5** Handler Lambda (Mangum) no está en el repo; `deploy.sh` (nombre con guion, protocolo MCP) y `build_codezip.sh` (no copia `agent.py`) no reproducen lo desplegado.
- **P6** Rule pack YAML validado, no cargado (la tabla art. 241 sí tiene test de igualdad).
- **P7** La regex de año en `pdf_facts.py:62` no casa con el fixture; el test golden escribe en `demo/expected/`.

### Resuelto desde el 11 sep

Tabla art. 241 + tests · números UI = motor (test) · banner DIAN en UI · API con `PREPARE_DRAFT` real, DRAFT_READY, `GET /draft`, `GET /coverage` y `/documents` en producción · CloudFront 404 JSON · CSP frame-src · i18n es/en · redondeo art. 577 · `make demo-draft` coherente · diagrama `.md` · video demo real grabado con Playwright + narración (`scripts/demo-video/`).

---

## Cómo correr

```bash
make install && make test      # 52 tests
make demo-draft                # regenera real_demo_run.json y demo-draft.json
uv run uvicorn rentalista.api.main:app --reload     # API + portal local
cd frontend && npm run build

uv run python scripts/run_demo_docs.py \
  --xlsx demo/fixtures/reporteExogena2025_demo.xlsx \
  --pdf  demo/fixtures/nequi_retencion_demo.pdf
```

OTP portal sintético: **`123456`**

---

## Checklist Devpost

- [x] Repo público MIT
- [x] README EN + diagrama (`docs/architecture.md`)
- [x] URL live sin login hasta 8 oct (200 el 14 sep)
- [x] Solo datos sintéticos (pendiente confirmar el ID `1019072850`)
- [x] Video grabado ≤ 5:00 (`docs/rentalista-demo-live.mp4`, 3:10, demo real con narración)
- [x] Video **subido**: https://www.youtube.com/watch?v=qnakivEdego
- [x] 3 frases del pitch en la tarjeta inicial y en la narración (0:00–0:30)
- [ ] Devpost `submitted` antes de **19:00 COT**
- [ ] Builder ID = **hetzel30@gmail.com** en el formulario
- [ ] Track único: Everyday Agents

---

*Actualizar este archivo al cambiar demo, API o checklist.*
