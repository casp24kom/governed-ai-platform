#!/usr/bin/env bash
set -euo pipefail
ENVIRONMENT="${1:-}"
REF="${2:-main}"
[[ -z "$ENVIRONMENT" ]] && { echo "Usage: $0 <dev|prod> [ref]"; exit 1; }
gh workflow run "Deploy App Runner" --ref "$REF" -f environment="$ENVIRONMENT"
sleep 3
RUN_ID="$(gh run list --workflow "Deploy App Runner" --branch "$REF" --limit 1 --json databaseId -q '.[0].databaseId')"
gh run watch "$RUN_ID" --exit-status
