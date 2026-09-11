# RentaLista Agent

Evidence-first Colombian income tax agent for **Agents for Humans** hackathon.

Builds a traceable draft of Formulario 210 (año gravable 2025) for a Colombian tax-resident natural person using:

- **Strands Agents** as the real orchestrator
- **Amazon Bedrock AgentCore** Runtime, Gateway Web Search, and Browser
- A **deterministic tax engine** separate from the LLM
- Synthetic demo data only (public demo)

## Status

Early implementation. See plan `renta-lista-plan-v2.md` (v2.1).

## Quick start

```bash
make install
make test
```

## License

MIT
