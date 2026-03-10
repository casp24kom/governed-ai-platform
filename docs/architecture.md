# Architecture Overview

Governed AI Platform is a FastAPI-based application that combines retrieval-augmented generation (RAG), deterministic data quality validation, and AI-assisted drafting inside a governed, auditable framework. It deploys to Azure and AWS using Terraform and GitHub Actions.

## Design Principles

### AI assists; it does not decide
The platform uses Snowflake Cortex for retrieval and response generation, and optionally AWS Bedrock AgentCore for ticket/runbook drafting. Business-critical decisions (data quality verdicts, access control) are handled by deterministic application logic.

### Everything is audited
Every RAG query, every DQ evaluation, and every AI-generated draft is written to Snowflake audit tables for compliance review, debugging, and operational monitoring.

### Cross-cloud, same behavior
The application runs on Azure (Container Apps or App Service) and AWS (App Runner) with the same runtime behavior. Terraform modules handle cloud-specific infrastructure; application code is unchanged between targets.

### Infrastructure is code
Cloud resources are provisioned via Terraform. CI/CD pipelines build, deploy, and destroy environments through GitHub Actions workflows.

## Component Architecture

### FastAPI runtime
Python 3.11+ API service providing health, RAG query, RAG self-test, and DQ evaluation endpoints.

### Snowflake data and AI layer
Hosts knowledge base tables (`KB` schema), Cortex Search service, response generation, and audit tables (`AUDIT` schema).

### Data quality gatekeeper
Evaluates payloads against deterministic validation rules and optionally drafts remediation artefacts via AI.

### Audit subsystem
Writes structured records of platform interactions to Snowflake.

### Azure deployment
Docker image pushed to ACR and deployed to Azure Container Apps or Azure App Service via Terraform and GitHub Actions.

### AWS deployment
Docker image pushed to ECR and deployed to AWS App Runner. Optional Bedrock AgentCore integration is supported.

### CI/CD
Branch-protected GitHub Actions workflows handle deployments and teardown operations.

## Snowflake Object Defaults

| Object | Default name |
|---|---|
| Database | `GOV_AI_PLATFORM` |
| Knowledge schema | `KB` |
| Audit schema | `AUDIT` |
| Application role | `GOV_AI_APP_ROLE` |
| Warehouse | `GOV_AI_WH` |
| Cortex Search service | `KB_SEARCH` |

## Authentication

API access uses bearer token authentication. Snowflake connections use keypair authentication with a base64-encoded private key supplied by environment variable.
