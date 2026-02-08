# Security & Secret Handling

This document summarizes how to handle secrets and sensitive information in the Scoreboard app.

## What counts as a secret
- Email credentials used for diagnostic notifications: SMTP server, port, username, password, and recipient list.
- Wi‑Fi network credentials entered via the Internet Connection screen (SSID and password).
- Any future API tokens or credentials (none are required today for the listed data sources).

## Current state
- Email settings are defined in code at `helper_functions/email.py`. Do not commit real credentials. Prefer local-only edits or environment variables when support is added.
- Error emails may include a ZIP of recent log files to aid troubleshooting. Avoid sharing logs publicly as they may contain operational context.

## Recommendations
- Never commit real secrets to version control.
- Keep any locally customized `helper_functions/email.py` changes (with real SMTP credentials) out of PRs/commits.
- Use environment variables for secrets once support is enabled. An example template is provided in `.env.example`. Do not commit an actual `.env`.
- Be mindful of screenshots or logs that could expose SSID/password or other sensitive values.

## Future improvements (planned)
- Load email configuration from environment variables (e.g., `.env`) so secrets are not stored in code.
- Expand logging redaction to ensure sensitive values never appear in logs.
