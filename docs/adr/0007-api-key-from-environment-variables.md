# 0007. API key from environment variables only

- Status: Proposed
- Date: 2026-10-27
- Context: The OpenAI API key must be available to the backend without being committed to version control. Configuration should be environment-driven, consistent with 12-factor apps, and keys must not leak into logs or error messages.
- Decision: Load the OpenAI API key (and other secrets) exclusively from environment variables via Pydantic settings with `SecretStr`; never from config files or source code. Provide `.env.example` (no real secrets) and gitignore `.env`.
- Alternatives considered:
  - Config files containing secrets — rejected because they risk accidental commits and secret leakage in diffs/logs.
  - Hardcoded/default keys — rejected because they are a security vulnerability and block rotation.
  - External secret manager (Vault/KMS) — rejected because it adds infrastructure and operational complexity disproportionate to a local prototype.
- Consequences: Secrets stay out of the repo and are masked by `SecretStr`. Trade-off: developers must create a local `.env`; missing keys block embedding/generation smoke tests (documented, not simulated).