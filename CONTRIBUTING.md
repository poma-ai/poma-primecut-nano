# Contributing to poma-primecut-nano

Thanks for your interest! poma-primecut-nano is a small OSS library maintained by POMA AI GmbH. Contributions are welcome.

## Bug reports

Open a [GitHub Issue](https://github.com/poma-ai/poma-primecut-nano/issues/new) with:

- What you expected to happen
- What actually happened (include any error output or stack trace)
- Minimal steps to reproduce — ideally a small document fragment + expected vs actual chunk output
- Your OS and `python --version`
- The output of `pip show poma-primecut-nano`

## Pull requests

1. Fork the repo and create a branch off `main` (e.g. `fix/heading-detection`, `feat/new-chunkset-strategy`).
2. Keep changes focused — one concern per PR.
3. Install dev dependencies: `pip install -e '.[dev]'`
4. Run tests: `pytest` — all existing tests must pass. Add tests for new behavior.
5. Match existing style (4-space indent, type hints where practical, zero runtime dependencies — the library is intentionally dep-free).
6. Write a clear commit message — brief imperative is great.
7. Open the PR against `main`.

Expect a review within a few days. If a PR sits longer than a week, feel free to ping in a comment.

## Scope

poma-primecut-nano is the open "nano" tier of POMA's PrimeCut chunker. It covers hierarchical chunking via Markdown headings and heuristic indentation. Features that require LLM assistance, OCR, or format conversion (PDF, DOCX, etc.) live in the commercial PrimeCut and are out of scope here.

## Releases

Releases are published to PyPI via GitHub Actions when a version tag is pushed. Maintainers bump `version` in `pyproject.toml` AND `__version__` in the package's `__init__.py` — both in lockstep.

## Security

Please **do not** file security vulnerabilities as public issues. See [SECURITY.md](./SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).
