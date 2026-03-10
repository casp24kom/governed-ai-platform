# Public Release Notes

## Release Scope

This public release packages **Governed AI Platform** as a reusable reference implementation for cross-cloud governed RAG and policy-gated AI patterns.

## Included

- Neutralized product identity and technical defaults
- Canonical Snowflake naming (`GOV_AI_PLATFORM`, `GOV_AI_APP_ROLE`, `GOV_AI_WH`, `KB_SEARCH`)
- Cross-cloud deployment workflows with neutral public naming
- Updated runbooks and architecture/overview documentation

## Notes for Adopters

- Replace sample hostnames (`*.example.com`) with your own domains
- Configure cloud identities, secrets, and Terraform backend values for your environment
- Review manual migration notes before applying to existing infrastructure
