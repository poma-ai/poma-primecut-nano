# Security Policy

## Reporting a vulnerability

Please **do not** report security issues via public GitHub issues.

Use GitHub's [Private Vulnerability Reporting](https://github.com/poma-ai/poma-primecut-nano/security/advisories/new) to send a confidential report directly to the maintainers.

We aim to acknowledge reports within 72 hours and issue fixes or mitigations within 14 days for confirmed high-severity issues.

## Scope

poma-primecut-nano is a pure-Python library with no runtime dependencies. It reads text input, produces chunk and chunkset output, and performs no I/O of its own. Security-relevant areas include:

- Parsing malformed or adversarial Markdown / indented text
- Regex patterns that could be crafted for catastrophic backtracking
- Integer overflow or unbounded memory growth on large inputs

Bugs in documentation or test fixtures are not security issues — report those as regular issues.

## Supported versions

Only the latest released version on PyPI receives security updates.
