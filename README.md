# Governed AI Platform

**Cross-cloud governed RAG and policy-gated AI reference application.**

Governed AI Platform is a production-leaning reference implementation that demonstrates how to deploy AI capabilities — retrieval-augmented generation (RAG) and AI-assisted drafting — inside a governed, auditable, policy-aware framework. It runs on Azure (primary) and AWS (optional) with consistent behaviour across both clouds.

This is not a toy demo. It implements the patterns that matter in real enterprise AI deployments: deterministic controls around AI outputs, full audit trails written to Snowflake, infrastructure-as-code for repeatable environments, and CI/CD pipelines with teardown automation.

---

## Key capabilities

**SOP Knowledge Assistant** — Retrieval-augmented Q&A powered by Snowflake Cortex Search. Users ask natural-language questions against an ingested knowledge base; the platform retrieves relevant context and generates a Snowflake Cortex-powered response. Every query and response is logged to an audit table.

**Data Quality Gatekeeper** — Deterministic data validation with AI-assisted remediation. Incoming data payloads are evaluated against configurable quality rules. When failures are detected, the verdict is deterministic (not AI-generated), but the platform drafts a remediation ticket and runbook using AI. The AI assists; it does not decide.

**Full audit trail** — Every RAG query, DQ verdict, and AI-generated draft is written back to Snowflake audit tables. This provides traceability for compliance, debugging, and operational review.

**Cross-cloud deployment** — The same application runs on Azure Container Apps (or Azure App Service) and AWS App Runner. Terraform modules and GitHub Actions workflows handle provisioning, deployment, and teardown for both clouds.

**Policy-gated AI** — AI is used where it adds value (summarisation, drafting, retrieval) but is kept inside deterministic guardrails. Business-critical decisions (pass/fail verdicts, access control) remain in application logic, not in model outputs.

---

## Architecture summary

```
┌─────────────────────────────────────────────────────┐
│                   Governed AI Platform               │
│                                                      │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │ RAG      │   │ DQ Gate      │   │ Audit       │ │
│  │ Assistant │   │ (validate +  │   │ (Snowflake  │ │
│  │ (Cortex  │   │  AI draft)   │   │  write-back)│ │
│  │  Search) │   │              │   │             │ │
│  └────┬─────┘   └──────┬───────┘   └──────┬──────┘ │
│       │                │                   │        │
│  ┌────▼────────────────▼───────────────────▼──────┐ │
│  │              FastAPI Runtime                     │ │
│  │         (Python 3.11+ / Uvicorn)                │ │
│  └─────────────────────┬──────────────────────────┘ │
└────────────────────────┼────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
   ┌──────▼──────┐ ┌────▼────┐ ┌──────▼───────┐
   │  Snowflake  │ │  Azure  │ │    AWS       │
   │  (data,     │ │  (ACR,  │ │  (ECR,       │
   │   search,   │ │  App    │ │   App Runner,│
   │   audit)    │ │  Svc /  │ │   Bedrock    │
   │             │ │  Cont.  │ │   AgentCore) │
   │             │ │  Apps)  │ │              │
   └─────────────┘ └─────────┘ └──────────────┘
```

**Runtime:** FastAPI application serving REST endpoints for RAG queries, data quality evaluation, and health checks.

**Data layer:** Snowflake handles knowledge base storage (KB schema), Cortex Search for retrieval, Cortex-generated responses, and audit logging (AUDIT schema).

**Compute — Azure (primary):** Docker image pushed to Azure Container Registry, deployed to Azure Container Apps or Azure App Service for Containers via Terraform and GitHub Actions.

**Compute — AWS (optional):** Docker image pushed to Amazon ECR, deployed to AWS App Runner. Optional integration with AWS Bedrock AgentCore for agent-based AI drafting.

**IaC:** Terraform modules for AWS, Azure Container Apps, and Azure App Service. Separate backend configurations per cloud.

**CI/CD:** GitHub Actions workflows for build, deploy, and destroy operations across both clouds. Branch protection enforces PR review, status checks, and CODEOWNER approval before merge.

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/rag/query` | RAG knowledge query (authenticated) |
| `POST` | `/rag/self_test` | Connectivity and audit self-test |
| `POST` | `/dq/evaluate` | Data quality evaluation with AI-drafted remediation |

---

## Repo structure

```
governed-ai-platform/
├── app/                          # FastAPI application
│   ├── main.py                   # App entry point
│   ├── config.py                 # Configuration and env loading
│   ├── snowflake_conn.py         # Snowflake connection management
│   ├── snowflake_rest_auth.py    # Snowflake REST auth (keypair)
│   ├── cortex_search_rest.py     # Cortex Search REST client
│   ├── snowflake_rag.py          # RAG query logic
│   ├── dq_gate.py                # Data quality gatekeeper
│   ├── agentcore_client.py       # AWS Bedrock AgentCore client
│   └── snowflake_audit.py        # Audit trail write-back
│
├── data/
│   ├── sop_samples/              # Sample knowledge base documents
│   └── dq_samples/               # Sample DQ payloads
│
├── deploy/
│   └── terraform/
│       ├── aws/                  # AWS App Runner infrastructure
│       ├── azure/                # Azure Container Apps (primary)
│       └── azure-appservice/     # Azure App Service (alternative)
│
├── scripts/ops/                  # Operational scripts (deploy, destroy, verify)
├── docs/                         # Runbooks and operational docs
├── governed_ai_platform_tests/   # Integration and smoke tests
│
├── .github/
│   ├── workflows/                # CI/CD: deploy and destroy workflows
│   ├── ISSUE_TEMPLATE/           # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
│
├── Dockerfile
├── requirements.txt
├── LICENSE                       # MIT
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SUPPORT.md
└── README.md
```

---

## Getting started

### Prerequisites

- Python 3.11+
- Docker
- Snowflake account with Cortex Search enabled
- (Optional) Terraform 1.6+ for cloud deployments
- (Optional) AWS and/or Azure accounts for cross-cloud hosting

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verify locally

```bash
curl -sS http://localhost:8000/health

curl -sS -X POST http://localhost:8000/rag/self_test \
  -H "Content-Type: application/json" -d '{}' | python -m json.tool
```

### Environment variables

Set via `.env` locally or GitHub Secrets for CI/CD.

**Snowflake (required):** `SF_ACCOUNT_IDENTIFIER`, `SF_ACCOUNT_URL`, `SF_USER`, `SF_ROLE`, `SF_WAREHOUSE`, `SF_DATABASE`, `SF_SCHEMA`, `SF_PUBLIC_KEY_FP`, `SF_PRIVATE_KEY_PEM_B64`

**API authentication:** JWT/keypair auth (see `app/config.py`)

**AWS Bedrock AgentCore (optional):** `AGENTCORE_REGION`, `AGENTCORE_RUNTIME_ARN`, plus AWS credentials if calling from Azure

---

## Deployment options

| Target | Method | Workflow |
|---|---|---|
| Azure Container Apps (primary) | Terraform + GitHub Actions | `deploy-azure` |
| Azure App Service | Terraform + GitHub Actions | `deploy-appservice` |
| AWS App Runner | Terraform + GitHub Actions | `deploy-aws` |

Each deployment target has a corresponding destroy workflow for teardown. See `docs/deployment-runbook.md` for full operational instructions.

### Cost note

This platform is designed for controlled cloud hosting. Infrastructure costs accrue while resources are running, even idle. Deploy for demonstrations or testing, then tear down using the provided destroy scripts or workflows.

### Teardown

```bash
# Local teardown
CONFIRM_DESTROY_AZURE=YES scripts/ops/destroy_azure_containerapps.sh
CONFIRM_DESTROY_AWS=YES scripts/ops/destroy_aws.sh
```

Or run the `destroy-azure` / `destroy-aws` workflows from GitHub Actions with manual confirmation.

---

## Why this project exists

Most AI demos skip the hard parts: auditability, deterministic controls, cross-cloud parity, and production-grade infrastructure. Governed AI Platform exists to demonstrate that these concerns can be addressed in a single, coherent implementation.

It is a reference application — intended to show how governed AI should be built, not just that AI can be called from an API. The patterns here (policy-gated AI, full audit trails, IaC-driven multi-cloud deployment, CI/CD with branch protection) are the patterns that matter when AI moves from prototype to production.

---

## What this demonstrates

- **Platform engineering discipline:** Infrastructure-as-code, CI/CD pipelines, automated teardown, branch protection, and repeatable environments across two clouds.
- **Governed AI patterns:** AI is used for retrieval and drafting; deterministic logic handles decisions. Every interaction is audited.
- **Cross-cloud deployment:** The same application image deploys to Azure and AWS with cloud-specific Terraform modules and workflows.
- **Production-leaning architecture:** Snowflake as a governed data layer, keypair authentication, environment-based configuration, and operational runbooks.
- **Separation of concerns:** AI assists where it adds value. Business logic stays in code. Audit trails are non-negotiable.

---

## CI/CD

GitHub Actions workflows handle the full lifecycle:

- **Build and deploy** to Azure (ACR → Container Apps or App Service) and AWS (ECR → App Runner)
- **Destroy** workflows with manual confirmation gates to prevent accidental teardown
- **Branch protection** enforces PR review, status checks (`test`, `audit`), and CODEOWNER approval

See `docs/github-branch-protection.md` for setup details.

---

## Security

- Never commit secrets (`.env`, `.tfvars`, keys, tokens)
- Report vulnerabilities via `SECURITY.md`
- API endpoints are authenticated via JWT/keypair
- Snowflake access uses keypair authentication

---

## License

MIT
