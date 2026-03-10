# GitHub Branch Protection Setup

This repo uses CI checks:
- `test` (from `Unit Tests` workflow)
- `audit` (from `Dependency Audit` workflow)

## Apply protection to `main`

Run from repository root:

```bash
./scripts/ops/configure_branch_protection.sh
```

Or explicitly:

```bash
./scripts/ops/configure_branch_protection.sh your-org/governed-ai-platform main
```

## What gets enforced

- Require pull requests before merge
- Require 1 approving review
- Require CODEOWNER review
- Dismiss stale approvals on new commits
- Require status checks to pass before merge:
  - `test`
  - `audit`
- Require conversation resolution
- Disallow force push/delete on `main`
- Enforce rules for admins

## Verify in GitHub UI

`Settings -> Branches -> Branch protection rules -> main`
