# bhp-platform-lab

BHP AI agents demo for an interview — Data & AI Platform Lab (Mining)

Enterprise-style demo showcasing a **production-leaning Data/AI platform pattern**:

- **SOP RAG Assistant** (retrieval + Snowflake-generated response)
- **Data Quality Gatekeeper** (deterministic validation + AI-generated ticket/runbook drafting)

Primary hosting: **Azure Container Apps** (or Azure App Service for Containers).
Optional showcase: **AWS ECS (Fargate) + ALB + EFS** and **AWS Bedrock AgentCore**.

## Repo structure

```
bhp-platform-lab/
  app/
    main.py
    config.py
    snowflake_conn.py
    snowflake_rest_auth.py
    cortex_search_rest.py
    snowflake_rag.py
    dq_gate.py
    agentcore_client.py
    snowflake_audit.py

  data/
    sop_samples/
    dq_samples/
      dq_fail_payload.json

  deploy/
    terraform/
      aws/
      azure/                 # Azure Container Apps + Azure Files (primary)
      azure-appservice/      # Azure App Service (optional)

  scripts/
    ops/
      destroy_aws.sh
      destroy_azure_containerapps.sh
      destroy_azure_appservice.sh   # optional

  docs/
    demo-script.md
    email-to-craig.md

  .github/
    workflows/
      deploy-azure.yml
      deploy-aws.yml
      destroy-aws.yml
      destroy-azure.yml
      destroy-azure-appservice.yml  # optional
    ISSUE_TEMPLATE/
      bug_report.md
      feature_request.md
      config.yml                    # optional
    PULL_REQUEST_TEMPLATE.md
    CODEOWNERS

  requirements.txt
  Dockerfile
  README.md
  LICENSE
  SECURITY.md
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  SUPPORT.md
  .gitignore
```

## What this demonstrates (summary)

- Platform engineering patterns: IaC + CI/CD + teardown, repeatable environments
- "AI where it belongs": drafting/summarisation + retrieval, with deterministic controls
- Auditability: all queries/verdicts written back to Snowflake
- Cross-cloud deployment with consistent behaviour (Azure primary, AWS optional)

## Endpoints

- `GET /health`
- `POST /rag/query`
- `POST /rag/self_test`
- `POST /dq/evaluate`

## Local quick start

Prerequisites

- Python 3.11+
- Docker
- (Optional) Terraform 1.6+ for deployments

### Run locally (FastAPI)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Local validation

```bash
curl -sS http://localhost:8000/health
curl -sS -X POST http://localhost:8000/rag/self_test \
  -H "Content-Type: application/json" -d '{}' | python -m json.tool
```

## Environment variables (minimum)

Set via `.env` locally and GitHub Secrets for CI/CD.

### Snowflake (required)

- SF_ACCOUNT_IDENTIFIER
- SF_ACCOUNT_URL
- SF_USER
- SF_ROLE
- SF_WAREHOUSE
- SF_DATABASE
- SF_SCHEMA
- SF_PUBLIC_KEY_FP
- SF_PRIVATE_KEY_PEM_B64

### Authentication (API)

- JWT/keypair auth is used for API access (see `app/config.py` and docs)

### AgentCore (optional, real invoke)

- AGENTCORE_REGION=ap-southeast-2
- AGENTCORE_RUNTIME_ARN=...

If running AgentCore calls from Azure, also set:

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_SESSION_TOKEN (optional)

## Demo (120 seconds) — Azure + AWS subdomains

Assumes:

- `api-azure.<yourdomain>` → Azure ingress (Container Apps/App Service)
- `api-aws.<yourdomain>` → AWS ALB ingress (ECS)

1. Health checks

```bash
export AZ_BASE="https://api-azure.<yourdomain>"
export AWS_BASE="https://api-aws.<yourdomain>"

 -  asuid.api-azure TXT → Azure verification value
curl -sS "$AWS_BASE/health"
```

1. RAG self-test (proves Snowflake connectivity + audit insert)

```bash
curl -sS -X POST "$AZ_BASE/rag/self_test" \
  -H "Content-Type: application/json" -d '{}' | python -m json.tool

curl -sS -X POST "$AWS_BASE/rag/self_test" \
  -H "Content-Type: application/json" -d '{}' | python -m json.tool
```

1. DQ gate (FAIL example) + AI ticket/runbook draft

If AgentCore is not configured, a safe mocked draft is returned so the demo still works.

```bash
curl -sS -X POST "$AZ_BASE/dq/evaluate" \
  -H "Content-Type: application/json" \
  -d @data/dq_samples/dq_fail_payload.json | python -m json.tool

curl -sS -X POST "$AWS_BASE/dq/evaluate" \
  -H "Content-Type: application/json" \
  -d @data/dq_samples/dq_fail_payload.json | python -m json.tool
```

1. What to say while showing Snowflake

- "Every query/verdict is written to Snowflake audit tables for traceability."
- "The demo response text is Snowflake-generated (Cortex), not hard-coded."
- "The DQ verdict is deterministic; AI only drafts the ticket/runbook."

## DNS (Azure DNS) — two subdomains

You will typically create:

- `api-azure` CNAME → Azure default hostname (Container Apps/App Service)
- `asuid.api-azure` TXT → Azure verification value
- `api-aws` CNAME → AWS ALB DNS name
- AWS ACM validation CNAME(s) in Azure DNS for `api-aws` certificate issuance

## CI/CD (GitHub Actions)

Workflows:

- Deploy Azure (build → push to ACR → Terraform apply)
- Deploy AWS (build → push to ECR → Terraform apply)
- Destroy Azure / Destroy AWS (manual confirmation to prevent accidents)

## Production Run Command Sheet (AWS + Azure + Rollback)

Use this exact sequence after merging changes to `main`.

1. Preflight (sync + stop any stuck deploys)

```bash
cd /Users/aleksypyrz/Documents/GitHub/bhp-platform-lab
git checkout main
git pull origin main

# Optional: cancel in-progress Azure deploy run
RUN_ID="$(gh run list --workflow deploy-azure-appservice-runtime.yml --branch main --limit 1 --json databaseId,status -q '.[] | select(.status==\"in_progress\") | .databaseId')"
if [ -n "$RUN_ID" ]; then gh run cancel "$RUN_ID"; fi
```

2. AWS config check (required for functional RAG/eval/security)

```bash
gh variable list --env dev
gh secret list --env dev
```

Required AWS-side GitHub env config for `deploy-apprunner.yml`:
- Vars: `AWS_REGION`, `AWS_ROLE_ARN`, `APP_RUNNER_SERVICE_ARN`, `ECR_REPOSITORY`, `APP_ENV`
- Vars: `KB_CHUNKS_TABLE`, `TOPIC_TEMPLATES_TABLE`
- Vars: `SF_ACCOUNT_IDENTIFIER`, `SF_ACCOUNT_URL`, `SF_USER`, `SF_ROLE`, `SF_WAREHOUSE`, `SF_DATABASE`, `SF_SCHEMA`, `SF_PUBLIC_KEY_FP`
- Vars (optional): `SF_SECRET_NAME`, `SF_SECRET_ID`, `AGENTCORE_REGION`, `AGENTCORE_ENDPOINT`, `AGENTCORE_AGENT_ID`, `DATA_DIR`
- Secrets: `SF_PRIVATE_KEY_PEM_B64`, `API_AUTH_TOKEN`, `DEBUG_API_TOKEN`

3. Deploy AWS (`aws.gitpushandpray.ai`)

```bash
gh workflow run deploy-apprunner.yml --ref main -f environment=dev
sleep 5
RUN_ID="$(gh run list --workflow deploy-apprunner.yml --branch main --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID" --exit-status
```

4. Deploy Azure App Service (`azure.gitpushandpray.ai`)

```bash
./scripts/ops/deploy_azure_appservice_via_gh.sh dev
```

5. Verify both public endpoints

```bash
curl -i https://aws.gitpushandpray.ai/health
curl -i https://azure.gitpushandpray.ai/health
```

6. Verify protected RAG endpoint (both surfaces)

```bash
curl -fsS https://aws.gitpushandpray.ai/rag/query \
  -H "Authorization: Bearer <API_AUTH_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'

curl -fsS https://azure.gitpushandpray.ai/rag/query \
  -H "Authorization: Bearer <API_AUTH_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

7. Rollback / recovery (Azure first)

```bash
SUB="0ef3ed97-e9ee-44dd-935a-da97870fe303"
RG="rg-bhp-platformlab-dev-aue-app"
APP="app-bhp-platformlab-dev-aue-gitpushandpray"

az account set --subscription "$SUB"
az webapp config container delete -g "$RG" -n "$APP"
az webapp config set -g "$RG" -n "$APP" --linux-fx-version "PYTHON|3.12"
az webapp config set -g "$RG" -n "$APP" \
  --startup-file "gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000 --timeout 120"
az webapp config appsettings set -g "$RG" -n "$APP" --settings WEBSITES_PORT=8000 SCM_DO_BUILD_DURING_DEPLOYMENT=true
az webapp restart -g "$RG" -n "$APP"
curl -i https://azure.gitpushandpray.ai/health
```

8. Rollback / recovery (AWS App Runner)

```bash
aws apprunner start-deployment \
  --service-arn arn:aws:apprunner:ap-southeast-2:184574354141:service/bhp-platformlab-agentcore/dff966ad32e649acbdfacc1aac8c85c9 \
  --region ap-southeast-2

curl -i https://aws.gitpushandpray.ai/health
```

## Cost controls (important)

This project is designed for demo-only cloud hosting:

- Spin up for a demo → capture evidence → destroy the same day
- ALB/ECS/EFS incur cost (or consume credits) while running, even idle

## One-click teardown

Local (fast)

```bash
CONFIRM_DESTROY_AZURE=YES scripts/ops/destroy_azure_containerapps.sh
CONFIRM_DESTROY_AWS=YES scripts/ops/destroy_aws.sh
```

GitHub Actions (manual)

Run workflows:

- `destroy-azure-containerapps` (type DESTROY-AZURE)
- `destroy-aws` (type DESTROY-AWS)

## Security

- Never commit secrets (.env, .tfvars, keys, tokens)
- Report vulnerabilities via SECURITY.md

______________________________________________________________________

## License

MIT
\- api-aws CNAME → AWS ALB DNS name
\- AWS ACM validation CNAME(s) in Azure DNS for api-aws certificate issuance

## CI/CD (GitHub Actions)

Workflows:
\- Deploy Azure (build → push to ACR → Terraform apply)
\- Deploy AWS (build → push to ECR → Terraform apply)
\- Destroy Azure / Destroy AWS (manual confirmation to prevent accidents)

## Cost controls (important)

This project is designed for demo-only cloud hosting:
\- Spin up for a demo → capture evidence → destroy the same day
\- ALB/ECS/EFS incur cost (or consume credits) while running, even idle

## One-click teardown

Local (fast)
CONFIRM_DESTROY_AZURE=YES scripts/ops/destroy_azure_containerapps.sh
CONFIRM_DESTROY_AWS=YES scripts/ops/destroy_aws.sh

GitHub Actions (manual)

Run workflows:
\- destroy-azure-containerapps (type DESTROY-AZURE)
\- destroy-aws (type DESTROY-AWS)

## Security

```
-  Never commit secrets (.env, .tfvars, keys, tokens)
-  Report vulnerabilities via SECURITY.md
```

⸻

## License

MIT
