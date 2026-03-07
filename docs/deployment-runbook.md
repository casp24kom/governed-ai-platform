# Deployment Runbook (AWS + Azure)

This solution can run on:
- AWS App Runner (`aws.gitpushandpray.ai`)
- Azure endpoint (`azure.gitpushandpray.ai`) on either:
  - Azure App Service for Containers
  - Azure Container Apps

Use branch-protected flow first: PR -> checks pass -> merge to `main`.

## 1) AWS App Runner (recommended command path)

Prereqs (GitHub environment vars/secrets):
- `AWS_REGION`
- `AWS_ROLE_ARN`
- `APP_RUNNER_SERVICE_ARN`
- `ECR_REPOSITORY`
- `APP_ENV`
- `API_AUTH_TOKEN` (secret)
- `DEBUG_API_TOKEN` (secret)

Deploy:

```bash
cd /Users/aleksypyrz/Documents/GitHub/bhp-platform-lab
gh workflow run deploy-apprunner.yml --ref main -f environment=dev
sleep 5
RUN_ID="$(gh run list --workflow deploy-apprunner.yml --branch main --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID" --exit-status
```

Smoke test:

```bash
curl -fsS https://aws.gitpushandpray.ai/health
curl -fsS https://aws.gitpushandpray.ai/rag/query \
  -H "Authorization: Bearer <API_AUTH_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## 2) Azure App Service for Containers

Prereqs (GitHub environment vars/secrets):
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
cd /Users/aleksypyrz/Documents/GitHub/bhp-platform-lab
./scripts/ops/deploy_azure_appservice_via_gh.sh dev
```

Manual equivalent:

```bash
gh workflow run deploy-azure-appservice-runtime.yml --ref main -f environment=dev
```

Smoke test (if this target backs `azure.gitpushandpray.ai`):

```bash
curl -fsS https://azure.gitpushandpray.ai/health
curl -fsS https://azure.gitpushandpray.ai/rag/query \
  -H "Authorization: Bearer <API_AUTH_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## 3) Azure Container Apps

Prereqs (GitHub environment vars/secrets):
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
cd /Users/aleksypyrz/Documents/GitHub/bhp-platform-lab
./scripts/ops/deploy_azure_containerapps_via_gh.sh dev
```

Manual equivalent:

```bash
gh workflow run deploy-azure-containerapps-runtime.yml --ref main -f environment=dev
```

Smoke test (if this target backs `azure.gitpushandpray.ai`):

```bash
curl -fsS https://azure.gitpushandpray.ai/health
curl -fsS https://azure.gitpushandpray.ai/rag/query \
  -H "Authorization: Bearer <API_AUTH_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## Full redeploy guidance

For a full solution redeploy after app code changes:
1. Deploy AWS App Runner (`deploy-apprunner.yml`).
2. Deploy the active Azure runtime for `azure.gitpushandpray.ai`:
   - App Service workflow OR Container Apps workflow.
3. If both Azure runtimes are active, deploy both.
4. Re-run smoke tests on both public URLs.

## Important routing check

`azure.gitpushandpray.ai` should point to exactly one active Azure runtime at a time (App Service or Container Apps).
If DNS/ingress points elsewhere, deployment can succeed but traffic may still hit old infrastructure.
