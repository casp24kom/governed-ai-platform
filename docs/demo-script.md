# Solution Walkthrough — Governed AI Platform

This walkthrough demonstrates the platform's core capabilities in under three minutes.

## Setup

```bash
export AZ_BASE="https://azure.example.com"
export AWS_BASE="https://aws.example.com"
export API_AUTH_TOKEN="demo-api-token-000000"
```

Replace the example values with your deployed endpoints and valid token.

## Step 1: Health checks

```bash
curl -sS "$AZ_BASE/health"
curl -sS "$AWS_BASE/health"
```

## Step 2: RAG self-test

```bash
curl -sS -X POST "$AZ_BASE/rag/self_test" \
  -H "Content-Type: application/json" -d '{}' | python -m json.tool
```

## Step 3: Data quality evaluation

```bash
curl -sS -X POST "$AZ_BASE/dq/evaluate" \
  -H "Content-Type: application/json" \
  -d @data/dq_samples/dq_fail_payload.json | python -m json.tool
```

## Step 4: Authenticated RAG query

```bash
curl -fsS "$AZ_BASE/rag/query" \
  -H "Authorization: Bearer ${API_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo","question":"What is the isolation procedure before maintenance?","topk":3}'
```

## Demo talking points

- Every interaction is written to Snowflake audit tables.
- RAG responses are generated using Snowflake Cortex.
- Data quality verdicts are deterministic; AI assists with remediation drafting.
- The same app behavior is available on Azure and AWS.
