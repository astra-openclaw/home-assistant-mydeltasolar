# Redaction and Safe Capture Policy

Use this policy for all authenticated MyDeltaSolar inspection.

## Never commit or share

- Plaintext passwords.
- Cookies, session IDs, CSRF tokens, auth headers, or browser storage.
- Raw screenshots containing private account details unless Robert explicitly approves.
- Raw full payload dumps with plant IDs, serial numbers, exact locations, image URLs, account emails, or unique identifiers.
- HAR files or browser network exports.

## Allowed in repo docs

- Endpoint paths without host secrets, e.g. `/web/process_gtop_plot.php`.
- Request parameter names and non-sensitive values, e.g. `unit=day`, `is_all_plants=1`.
- Redacted response schemas: keys, types, list lengths, sample shapes.
- Units and conversion formulas.
- Sanitized examples with fake IDs/serials if needed.
- Evidence dates and confidence labels.

## Raw capture handling

If raw payloads are needed temporarily:

1. Keep them outside the git repo in a private scratch path.
2. Do not paste them into prompts for subagents.
3. Summarize into redacted schemas before documentation.
4. Delete raw captures when no longer needed, unless Robert asks to archive them securely.
5. Before any commit/push, run `git diff --cached` and a secret scan/search for likely sensitive strings.

## Subagent boundary

Subagents may inspect local source files and sanitized docs. They must not receive credentials, cookies, raw authenticated payloads, private screenshots, or secret-bearing logs.
