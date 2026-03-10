#!/usr/bin/env bash
set -euo pipefail

# ===== Azure =====
export AZ_RG="${AZ_RG:-rg-governed-ai-platform-dev-aue-app}"
export AZ_WEBAPP="${AZ_WEBAPP:-app-governed-ai-platform-dev-aue-app}"
# Optional (if you have more than one subscription)
export AZ_SUBSCRIPTION="${AZ_SUBSCRIPTION:-sub-governed-ai-platform-dev}"

# ===== Public URLs =====
export URL_AZURE="${URL_AZURE:-https://azure.example.com}"
export URL_AWS="${URL_AWS:-https://aws.example.com}"

# ===== AWS =====
export AWS_REGION="${AWS_REGION:-ap-southeast-2}"
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)}"

# Bedrock Agent ids (fill these in when you want to run invoke tests)
export AGENT_ID="${AGENT_ID:-REPLACE_ME_AGENT_ID}"
export AGENT_ALIAS_ID="${AGENT_ALIAS_ID:-REPLACE_ME_ALIAS_ID}"
export SESSION_ID="${SESSION_ID:-demo-$(date +%s)}"
