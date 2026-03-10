# Governed AI Platform Overview

**Governed AI Platform** is a cross-cloud reference application that demonstrates how to build AI-powered capabilities inside a governed, auditable, enterprise-grade framework.

## The Problem It Addresses

Production AI systems need more than model calls. They require deterministic controls, auditability, repeatable infrastructure, and consistent deployment patterns across cloud environments.

## What It Does

### 1) SOP Knowledge Assistant
Natural-language Q&A over an ingested knowledge base using Snowflake Cortex Search and Cortex-generated responses. Interactions are written to audit tables.

### 2) Data Quality Gatekeeper
Deterministic validation of input payloads with AI-assisted remediation drafting. The pass/fail decision is deterministic application logic; AI drafts follow-up artefacts only.

## How It Is Built

- Runtime: FastAPI (Python 3.11+), containerized with Docker
- Data and AI: Snowflake (Cortex Search, Cortex response generation, audit tables)
- Azure deployment: ACR to Container Apps or App Service via Terraform
- AWS deployment: ECR to App Runner with optional Bedrock AgentCore
- CI/CD: GitHub Actions with branch protection

## Why It Matters

This project demonstrates governed AI engineering patterns in practice: deterministic controls, complete audit trails, cross-cloud portability, infrastructure-as-code, and operational runbooks suitable for enterprise-style environments.
