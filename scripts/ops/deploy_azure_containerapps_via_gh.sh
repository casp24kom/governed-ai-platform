#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-}"
if [[ -z "$ENVIRONMENT" ]]; then
  echo "Usage: $0 <dev|prod> [--ref <branch>]"
  exit 1
fi
shift

REF="main"
if [[ "${1:-}" == "--ref" ]]; then
  REF="${2:-main}"
fi

gh workflow run deploy-azure-containerapps-runtime.yml --ref "$REF" -f environment="$ENVIRONMENT"
sleep 5
RUN_ID="$(gh run list --workflow deploy-azure-containerapps-runtime.yml --branch "$REF" --limit 1 --json databaseId -q '.[0].databaseId')"
echo "RUN_ID=$RUN_ID"
gh run watch "$RUN_ID" --exit-status
