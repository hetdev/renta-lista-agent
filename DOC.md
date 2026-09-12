# RentaLista Agent — Estado del proyecto

**Fecha:** 12 de septiembre de 2026  
**Hackathon:** [Agents for Humans](https://agentsforhumans.devpost.com) · Deadline 14 sep 2026 5:00 p. m. PT  
**Repo:** https://github.com/hetdev/renta-lista-agent  
**Commit HEAD:** `dfde50d`

---

## Resumen ejecutivo

Aplicación web bilingüe que prepara un **borrador trazable del Formulario 210** (AG 2025) para una persona natural residente fiscal en Colombia. No inicia sesión en DIAN, no firma ni presenta.

> Borrador para revisión. No ha sido presentado ante la DIAN.

| Criterio Devpost | Estado |
|---|---|
| Strands Agents obligatorio | OK — tool `prepare_draft`, entrypoint AgentCore |
| AgentCore (opcional, suma puntos) | Runtime READY · Gateway + Web Search READY · Browser probado |
| Demo funcional en video | Parcial — UI pública sí; Live View embebido no |
| Repo público + MIT | OK |
| README + diagrama | OK |
| Video ≤ 5 min | **Pendiente** |
| Builder ID | **Pendiente** (email del Builder ID) |

---

## URLs y recursos

| Recurso | Valor |
|---|---|
| **Demo pública (HTTPS)** | https://deuhmh4dvlr6i.cloudfront.net/ |
| ES | https://deuhmh4dvlr6i.cloudfront.net/es/ |
| EN | https://deuhmh4dvlr6i.cloudfront.net/en/ |
| Demo case flow | `/es/demo/` → `/es/case/profile/` → `documents` → `coverage` → `draft` |
| S3 web (website) | `rentalista-web-697020387519` |
| CloudFront dist | `EEMC7WEZFXF40` · `deuhmh4dvlr6i.cloudfront.net` |
| AWS account | `697020387519` · user `rentalista-dev` · profile **`rentalista`** |
| Región | `us-east-1` |
| Bedrock model | `amazon.nova-micro-v1:0` (~$0.035 / $0.14 por 1M tokens) |
| AgentCore Runtime | `rentalista_agent-xznI3y9jcZ` · status **READY** |
| Runtime ARN | `arn:aws:bedrock-agentcore:us-east-1:697020387519:runtime/rentalista_agent-xznI3y9jcZ` |
| AgentCore Gateway | `rentalista-websearch2-f29eutucy6` · **READY** |
| Web Search target | `DP0IKFORKR` · connector `web-search` v`1.2.0` · **READY** |
| Cognito (JWT del gateway) | pool `us-east-1_2zj7OAMkV` · client `434fg9jlgkcaqon2manntpfd26` |
| CodeZip S3 | `s3://rentalista-agentcore-697020387519/agent/rentalista-agent.zip` (~30 MB) |
| OTP portal sintético | `123456` |
| Plan de proyecto | `renta-lista-plan-v2.md` (v2.1 en `/Volumes/external/rentalista/`) |

---

## Qué está implementado

### 1. Dominio y dinero
- `src/rentalista/domain/` — enums, modelos Pydantic, **COP entero** (sin float en dominio), máquina de estados con ciclos (`state_machine.py`)
- Frontera `Decimal(str(...))` / `cop_from_float_like` para openpyxl

### 2. Motor tributario determinista
- `src/rentalista/tax/` — obligación (UVT 2025 = **49.799**, operadores `>` / `>=`), patrimonio, trabajo/capital, factura 1% (tope 240 UVT), **casilla 92** con 28 y 139 **fuera** del límite 40% / 1.340 UVT, tarifa art. 241, saldo, invariantes 134/137
- `calculate_form210(ConfirmedTaxFacts) -> Draft210` puro
- Casillas 140 (sin marcar) y 141 (cero) con razón

### 3. Reglas
- `rules/ag2025/` — `manifest.yaml`, `constants.yaml`, `tax_table.yaml`, `deductions.yaml`
- Validador: `uv run python -m rentalista.rules.validator rules/ag2025` → **OK**

### 4. Ingestión
- Lectura exógena XLSX (`openpyxl`), guard zip-bomb, columnas DIAN (reporta / NIT / concepto / valor / uso)
- Fixtures: `demo/generate_demo_data.py`, `demo/fixtures/exogena_2025_sintetica.xlsx`

### 5. Document recovery (política)
- `PortalSearchProvider` + `SeededDemoProvider` (`demo/portal_directory.json` con señuelos)
- Query máx. 200 chars, sin PII del contribuyente (NIT del reportante permitido)
- Política: rechaza HTTP, acortadores (`bit.ly`, `tinyurl`, …), lookalikes
- Browser: expiración de sesión → `MANUAL_UPLOAD_REQUIRED`; Live View máx. 300 s

### 6. API
- FastAPI: `POST /api/v1/cases`, token `X-Case-Token` (hash en servidor), profile, jobs con **idempotencia**, **lock** de 10 min, **`WAITING_USER` libera lock**, 409 / 503
- Portal sintético: `/demo-portal/` login + OTP + `GET /certificate`

### 7. Agente
- Entrypoint AgentCore: rechaza `prompt` libre; acepta `{case_id, job_id, command}`
- Smoke cloud: invoke → **`DRAFT_READY`** (saldo a pagar 337.009 COP en el payload de prueba)
- Tool `prepare_draft` (Strands) delega al motor; el LLM no calcula impuestos

### 8. Frontend
- Next.js 15 · `output: 'export'` · solo `[locale]` (`es`/`en`) · `trailingSlash`
- Pantallas: landing, demo, profile, documents, coverage, draft
- Token en `sessionStorage`; `case_id` en query
- Build: `cd frontend && npm run build` → `out/es`, `out/en`

### 9. Infra
- CodeZip: `scripts/build_codezip.sh` (uv, aarch64, Python 3.13)
- Deploy/smoke: `scripts/deploy.sh`, `scripts/smoke_cloud.sh`
- CDK opcional: `infra/app.py` (web stack)
- CloudFront → S3 website (origen público para demo sintética)

### 10. Calidad
- **31 tests** en verde (`uv run pytest`)
- Ruff limpio
- Golden snapshot: `demo/expected/form210_snapshot.json`

---

## Comandos útiles

```bash
cd /Volumes/external/agents-for-humans/renta-lista-agent

# Tests
make install && make test

# API local
uv run uvicorn rentalista.api.main:app --reload

# Frontend
cd frontend && npm install && npm run build

# Smoke AWS (Bedrock + AgentCore lists)
bash scripts/smoke_cloud.sh

# Invocar runtime (payload plano, sin wrapper "input")
# aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn <ARN> \
#   --runtime-session-id <33+ chars> --payload <base64(json)> /tmp/out.bin
```

### Invocación de ejemplo (runtime)

Payload JSON (luego base64):

```json
{
  "case_id": "…uuid…",
  "job_id": "…uuid…",
  "command": "PREPARE_DRAFT",
  "profile": { "resident_2025": true, "...": true },
  "amounts": { "salarios": 80000000, "ingresos_brutos": 80000000 },
  "dependents": 1,
  "previous_filing": "FIRST"
}
```

Respuesta: `accepted: true` + `result.status: DRAFT_READY` + celdas.

---

## AWS / SCP (importante)

La cuenta está en una **AWS Organization** (`o-aad3d173qy`, master `690968743338`).  
El SCP `p-sfdav4bi` (`AdvancedModeRegionRestrictionSecurityControlPolicy`) es una **allowlist regional** de `us-east-1`.

Se añadieron al `NotAction` (vía perfil `rentalista-dev2` en la master):

- `bedrock-agentcore*` (Runtime / Gateway / Browser)
- `s3:*` (bucket web + CodeZip)
- `cognito-idp:*` (JWT del Gateway)
- `cloudfront:*`

**No tocar ese SCP sin necesidad.** Si algo deja de funcionar, revisar `p-sfdav4bi` desde la cuenta master.

---

## Pendiente para Devpost (priorizado)

| # | Ítem | Por qué |
|---|---|---|
| 1 | **Video ≤ 5:00** con pitch literal (problema / para quién / por qué importa) + demo | Requisito duro |
| 2 | Envío Devpost + **Builder ID = email** | Requisito duro |
| 3 | **API pública** detrás de CloudFront (`/api/*` → Lambda/URL) | Hoy la UI usa mock si no hay API |
| 4 | **Live View embebido** en `/case/browser/` (iframe + renovación 300 s) | Diferenciador del video |
| 5 | Golden vs **Programa Ayuda Renta** (captura manual versionada) | Credibilidad del motor |
| 6 | Demo path end-to-end en la URL pública sin mock | Judges “not required to test” pero el video sí |
| 7 | Bonus builder.aws (opcional 0.6 pts) | Solo si P0 verde |

### Guion de video sugerido (4:40)

| Tiempo | Contenido |
|---|---|
| 0:00–0:25 | **Problem** · **Who** · **Why** (3 frases literales) |
| 0:25–0:45 | Alcance y seguridad: sin credenciales DIAN |
| 0:45–2:20 | Exógena → cobertura → faltante → búsqueda (real + sembrado) |
| 2:20–3:05 | Consentimiento · Live View · handoff OTP · reanudación |
| 3:05–3:35 | Discrepancia + human-in-the-loop |
| 3:35–4:05 | Borrador + saldo + ledger de una casilla |
| 4:05–4:30 | Arquitectura: Strands + AgentCore + motor determinista |
| 4:30–4:40 | Cierre + URL demo |

---

## Decisiones de diseño clave

1. **LLM no calcula impuestos** — solo orquesta; el motor es puro y determinista.  
2. **Async sin SQS** — AgentCore Runtime + `add_async_task` / `WAITING_USER`.  
3. **Browser TTL 30 min** — si expira en handoff → carga manual (no cuelga el job).  
4. **Portal sintético** same-origin en CloudFront `/demo-portal/*` (plan); hoy vive en la API local.  
5. **Datos solo sintéticos** en demo pública; nombres de bancos reales solo como reportantes.

---

## Riesgos abiertos

| Riesgo | Mitigación |
|---|---|
| Jueces no prueban y solo ven el video | P0 = exactamente lo que enseña el video |
| Cuota Bedrock / Browser | Budget + topes globales; kill switch en `quotas.py` (parcial) |
| API no desplegada aún | Desplegar Lambda+API GW o URL del runtime detrás de CloudFront |
| Live View iframe / CSP | CloudFront response headers con `frame-src` a `bedrock-agentcore.*` |
| Org SCP restrictivo | Documentado arriba; no ampliar regiones |

---

## Estructura del repo

```
renta-lista-agent/
├── README.md
├── LICENSE (MIT)
├── NOTICE.md
├── DOC.md                 ← este archivo
├── agent.py               ← entrypoint AgentCore CodeZip
├── pyproject.toml
├── rules/ag2025/
├── demo/                  ← fixtures, portal_directory, expected/
├── docs/architecture.mmd
├── frontend/              ← Next.js 15 export
├── infra/                 ← CDK opcional
├── scripts/               ← build_codezip, deploy, smoke_cloud
├── src/rentalista/
│   ├── domain/ tax/ rules/ ingestion/
│   ├── document_recovery/ agent/ api/
└── tests/                 ← unit, integration, golden (31 tests)
```

---

## Checklist de entrega Devpost

- [ ] Video público YouTube/Vimeo ≤ 5:00 (demo + pitch 3 puntos)
- [ ] Repo público con MIT detectable (hecho)
- [ ] README en inglés con prueba para jueces (hecho, refinar)
- [ ] Diagrama de arquitectura (hecho: Mermaid)
- [ ] URL live sin login hasta 8 oct 2026 5:00 p. m. PT (hecho CloudFront)
- [ ] AWS Builder ID (email)
- [ ] Track único: Everyday Agents
- [ ] Cero PII real en demo/video/logs
- [ ] Captura de confirmación Devpost `submitted`

---

*Documento generado tras la implementación de las etapas 0–5 + despliegue AgentCore/Gateway/CloudFront.*
