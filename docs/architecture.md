# RentaLista architecture

Solid arrows and nodes: implemented and exercised by code in this repo.
Dashed arrows and nodes: planned, not wired yet (state at the 11 Sep 2026 code review, see DOC.md).

```mermaid
flowchart TB
  User["User browser"] --> CF["CloudFront"]
  CF --> S3Web["S3 static Next.js es/en"]
  CF -->|"/api/v1/* (API 404s rewritten to index.html 200)"| API["FastAPI on Lambda, in-memory store"]
  API --> Engine["Deterministic Form 210 engine"]
  API --> Portal["demo-portal synthetic OTP (local API only)"]
  Script["scripts/run_demo_docs.py"] --> Ingest["XLSX DIAN layout + Nequi PDF ingestion"]
  Ingest --> Engine
  RT["AgentCore Runtime rentalista_agent"] --> Entry["agent.py entrypoint: validate + run_command"]
  Entry --> Engine
  Engine --> Draft["Draft210 + per-cell formula"]

  CF -.->|"/demo-portal/* not routed"| Portal
  API -.-> DDB[("DynamoDB cases/jobs")]
  API -.-> S3Data[("S3 documents")]
  API -.->|"InvokeAgentRuntime"| RT
  Entry -.-> Strands["Strands agent (build_agent, never called)"]
  Strands -.-> Bedrock["Amazon Bedrock Nova Micro"]
  Strands -.-> Rec["Document recovery agent"]
  Rec -.-> GW["AgentCore Gateway Web Search"]
  Rec -.-> Br["AgentCore Browser + Live View"]
  Br -.-> Portal

  classDef planned stroke-dasharray:5 5,stroke:#888,color:#555;
  class DDB,S3Data,Strands,Bedrock,Rec,GW,Br planned;
```
