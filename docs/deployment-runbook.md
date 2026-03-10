# Deployment Runbook — Governed AI Platform

This runbook covers deployment and validation across supported cloud targets.

## Supported Deployment Targets

| Target | Role | Workflow |
|---|---|---|
| Azure Container Apps | Primary | `deploy-azure` |
| Azure App Service for Containers | Alternative | `deploy-appservice` |
| AWS App Runner | Optional | `deploy-aws` |

## Deployment Model

Deployments follow a consistent pattern:
- Build and push container image to cloud registry (ACR or ECR)
- Apply/update runtime infrastructure
- Run smoke tests and health checks

Recommended flow: PR -> checks pass -> merge to `main` -> run deployment workflow.

## Prerequisites

- GitHub environment variables and secrets configured per target
- Snowflake objects aligned with defaults: `GOV_AI_PLATFORM`, `GOV_AI_APP_ROLE`, `GOV_AI_WH`, `KB_SEARCH`
- Terraform backend storage ready for target environment
- DNS records configured if using custom domains

Set an example token variable for runbook commands:

```bash
export API_AUTH_TOKEN="demo-api-token-000000"
```

Replace with your real value in operational use.

## 1) AWS App Runner

Prereqs (GitHub env vars/secrets):
- `AWS_REGION`
- `AWS_ROLE_ARN`
- `APP_RUNNER_SERVICE_ARN`
- `ECR_REPOSITORY`
- `APP_ENV`
- `API_AUTH_TOKEN` (secret)
- `DEBUG_API_TOKEN` (secret)

Deploy:

```bash
cd /path/to/governed-ai-platform
gh workflow run deploy-aws --ref main -f environment=dev
sleep 5
RUN_ID="$(gh run list --workflow deploy-aws --branch main --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID" --exit-status
```

Smoke test:

```bash
curl -fsS https://aws.example.com/health
curl -fsS https://aws.example.com/rag/query \
  -H "Authorization: Bearer ${API_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## 2) Azure App Service for Containers

Prereqs (GitHub env vars/secrets):
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `ACR_LOGIN_SERVER`
- `ACR_REPOSITORY`
- `AZURE_APP_SERVICE_NAME`
- `AZURE_APP_SERVICE_RESOURCE_GROUP`
- `APP_ENV`
- `API_AUTH_TOKEN` (secret)
- `DEBUG_API_TOKEN` (secret)

Deploy:

```bash
cd /path/to/governed-ai-platform
./scripts/ops/deploy_azure_appservice_via_gh.sh dev
```

Manual equivalent:

```bash
gh workflow run deploy-appservice --ref main -f environment=dev
```

Smoke test (if this target backs `azure.example.com`):

```bash
curl -fsS https://azure.example.com/health
curl -fsS https://azure.example.com/rag/query \
  -H "Authorization: Bearer ${API_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## 3) Azure Container Apps

Prereqs (GitHub env vars/secrets):
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `ACR_LOGIN_SERVER`
- `ACR_REPOSITORY`
- `AZURE_CONTAINER_APP_NAME`
- `AZURE_CONTAINER_APP_RESOURCE_GROUP`
- `APP_ENV`
- `API_AUTH_TOKEN` (secret)
- `DEBUG_API_TOKEN` (secret)

Deploy:

```bash
cd /path/to/governed-ai-platform
./scripts/ops/deploy_azure_containerapps_via_gh.sh dev
```

Manual equivalent:

```bash
gh workflow run deploy-azure --ref main -f environment=dev
```

Smoke test (if this target backs `azure.example.com`):

```bash
curl -fsS https://azure.example.com/health
curl -fsS https://azure.example.com/rag/query \
  -H "Authorization: Bearer ${API_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## Warm-up Window (Important)

Expect 2-8 minutes of transient `503`/`504` responses after deployment while containers initialize and probes pass.

```bash
for i in {1..60}; do
  echo "[$i] AWS=$(curl -s -o /dev/null -w '%{http_code}' https://aws.example.com/health) AZURE=$(curl -s -o /dev/null -w '%{http_code}' https://azure.example.com/health)"
  sleep 10
done
```

```bash
curl --max-time 15 -i https://aws.example.com/health
curl --max-time 15 -i https://azure.example.com/health
```

## Full Redeploy Guidance

1. Run `deploy-aws`.
2. Run the active Azure workflow for `azure.example.com`:
   - `deploy-appservice` or `deploy-azure`
3. If both Azure runtimes are active, deploy both.
4. Re-run smoke tests on both public URLs.

## Routing Check

`azure.example.com` should map to exactly one active Azure runtime at a time (App Service or Container Apps). If DNS points elsewhere, deployment can succeed but traffic may still route to old infrastructure.
