#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-}"
REF="${2:-main}"
[[ -z "$ENVIRONMENT" ]] && { echo "Usage: $0 <dev|prod> [ref]"; exit 1; }
gh workflow run "deploy-aws" --ref "$REF" -f environment="$ENVIRONMENT"
sleep 3
RUN_ID="$(gh run list --workflow "deploy-aws" --branch "$REF" --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID" --exit-status
