# Building RentaLista for the Agents for Humans hackathon: an evidence-first tax agent on Amazon Bedrock AgentCore

*Draft for the optional builder.aws community post. The title must keep the words "Agents for Humans". Publish at https://builder.aws.com/content (sign in with your Builder ID), then paste the public URL into the Devpost field "URL to your Optional Bonus Blog Post". If it is not published before you submit, leave that field empty: it is optional.*

---

Every year, Colombia's tax authority (DIAN) publishes for each taxpayer the *información exógena*: a spreadsheet of what employers, banks and brokers reported about you. Turning it into a correct Formulario 210 means chasing certificates, catching silent zeros, and doing arithmetic where one wrong bracket flips the result from "you owe" to "you are owed". Accounting firms have tooling. A salaried person filing their own return has a PDF instruction manual.

For the **Agents for Humans** hackathon I built [RentaLista](https://github.com/hetdev/renta-lista-agent): an agent that gathers the evidence and prepares a **traceable Form 210 draft**, while a human keeps every decision and nothing is ever filed. Live demo (synthetic data, no login): https://deuhmh4dvlr6i.cloudfront.net/en/

## Design rule number one: the model never does the math

The first decision shaped everything else. Tax amounts are computed by a **deterministic engine**, a set of pure functions over integer pesos:

```python
COP = NewType("COP", int)   # floats are forbidden in the tax domain

def income_tax_cop(taxable_cop: COP, uvt_value: Decimal) -> COP:
    taxable_uvt = Decimal(taxable_cop) / uvt_value
    from_uvt, fixed, rate = bracket_for(taxable_uvt)          # art. 241 table
    tax_uvt = fixed + (taxable_uvt - from_uvt) * rate
    return COP(int((tax_uvt * uvt_value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
```

Every Form 210 cell carries its formula, operands and a rule version (`ag2025-0.1.0`). The language model's job is orchestration and explanation: which document is missing, which question to ask the human, how to explain cell 116. It never invents an amount.

This paid off on day three. My first art. 241 bracket table had wrong fixed amounts: at exactly 1,090 UVT it charged 19 UVT instead of zero, and the cumulative tax went *down* when crossing 4,100 UVT. A unit test that checks continuity at every bracket edge caught it, and fixing the table flipped my synthetic case from "amount payable" to "credit balance". Tax rules need tests against the statute, not against your own snapshot.

## Human-in-the-loop as a state machine

"Ask the user" is not a prompt in RentaLista, it is a state. The case moves through an explicit graph: `PROFILED → DOCUMENTS_UPLOADED → PROCESSING → COVERAGE_INCOMPLETE → PORTAL_APPROVAL_REQUIRED → BROWSER_ACTIVE → BROWSER_USER_ACTION_REQUIRED → DOCUMENT_RECOVERED → ... → DRAFT_READY → APPROVED`. Cycles are intentional: a browser handoff for a one-time password returns to `BROWSER_ACTIVE`, a material conflict returns to `NEEDS_REVIEW`. Jobs that wait for a human release the case lock, so the UI never blocks on the agent.

Document recovery follows the same idea. A portal directory (seeded for the demo) includes deliberate decoys: a lookalike domain, a URL shortener and a paid third-party portal. A deterministic policy rejects them before any browsing, the human approves the domain and the consent fields, and only then does the agent open a browser session. Search queries are checked so they never contain the taxpayer's ID or email.

## What runs on AWS

- **Amazon Bedrock AgentCore Runtime** hosts the agent entrypoint as a CodeZip. The entrypoint accepts a structured command envelope (`PREPARE_DRAFT`, `FIND_MISSING_DOCUMENTS`, `RESUME_AFTER_USER_ACTION`, ...) and rejects free-form prompts.
- **Strands Agents** wraps the engine as a `prepare_draft` tool with **Amazon Bedrock** (Nova Micro) as the model, so the model can orchestrate but never compute.
- **AgentCore Gateway** with the Web Search tool and **AgentCore Browser** with Live View (signed URLs of at most 300 seconds) are provisioned for the certificate-recovery flow; wiring them into the public path is the next step.
- The public demo is a Next.js static export on **Amazon S3** behind **Amazon CloudFront**, with a FastAPI API on **AWS Lambda** under `/api/v1/*`.

## Three things I learned

1. **Put tests where money is.** A golden snapshot, boundary tests on the five filing thresholds (`>` versus `>=` matters), and a test that fails if the UI's demo JSON drifts from the engine output.
2. **Real layouts are messy.** The DIAN exogenous report has banners, threshold rows and repeated NIT columns. Header discovery and float-safe parsing (`str()` → `Decimal` → integer pesos) came before any number could be trusted.
3. **Say what is wired.** The README and the architecture diagram mark solid (implemented) versus dashed (planned). Judges, and future me, deserve to know which arrows are real.

## Try it

- Demo: https://deuhmh4dvlr6i.cloudfront.net/en/ (Spanish at `/es/`)
- Code (MIT): https://github.com/hetdev/renta-lista-agent
- Synthetic data only. *Borrador para revisión. No ha sido presentado ante la DIAN.*
