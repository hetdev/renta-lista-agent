# RentaLista Agent

**RentaLista: an evidence-first Colombian income tax agent**  
Built for the [Agents for Humans](https://agentsforhumans.devpost.com) hackathon.

Helps a Colombian tax-resident natural person gather missing certificates, reconcile third-party exogenous information, and prepare a **traceable draft** of Formulario 210 (año gravable 2025). It does **not** log in to DIAN, sign, file, or pay.

> Borrador para revisión. No ha sido presentado ante la DIAN.

## What it does

1. Ingests synthetic exogenous Excel + certificates  
2. Maps every reported row to an evidence coverage item  
3. Recovers a missing certificate via portal search + assisted browser (OTP handoff)  
4. Reconciles conflicts with human confirmation  
5. Calculates Form 210 with a **deterministic engine** (no LLM arithmetic)  
6. Exports a draft with per-cell ledger  

## Architecture

See [docs/architecture.mmd](docs/architecture.mmd).

- **Strands Agents** orchestrates tools  
- **Amazon Bedrock AgentCore** Runtime + Gateway Web Search + Browser  
- **Amazon Bedrock** model `amazon.nova-micro-v1:0` (us-east-1)  
- Deterministic tax engine in `src/rentalista/tax/`  
- Synthetic demo portal at `/demo-portal/*`  

## Quick start

```bash
# Python
make install
make test

# API locally
uv run uvicorn rentalista.api.main:app --reload

# Demo portal
curl -s localhost:8000/demo-portal/

# Frontend
cd frontend && npm install && npm run build
```

## Demo (synthetic data only)

```bash
scripts/smoke_cloud.sh
```

1. Create a case (`POST /api/v1/cases`)  
2. Submit profile (admission questions)  
3. Upload exogenous workbook  
4. Discover missing certificate → approve portal → consent → OTP handoff in Live View  
5. Download certificate from `/demo-portal/certificate` after OTP `123456`  
6. Prepare draft → review cells → export  

OTP for the synthetic portal: **`123456`**.

## Judge notes

- No login required for the public demo  
- All taxpayer data is synthetic  
- Entity names of banks may be real; the missing-reporter entity is fictional (`Banco Sintético Andino`)  
- Seeded portal directory includes deliberate decoys (lookalike domain, shortener, paid third-party)  

## License

MIT — see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
