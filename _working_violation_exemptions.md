# Substrate violation scan — exemption list

Per `/CLAUDE.md` rule: "Do not add Charter Rider to 3rd-party vendored code
(`lib/`, `vendor/`, `*-fork/`). Apache 2.0 §4 requires preserving original
NOTICE of 3rd-party works."

The following paths matched substrate-violation regex but are exempt as
3rd-party vendored code / build artifacts / binaries:

- `40-engine/kotoba/crates/kotoba-kotodama/py/.venv/**` — Python virtualenv (ruff binary, mypy
  metadata, pygments lib, ast_serialize .so)
- `60-apps/etzhayyim-project-celler/appview/.../etzhayyim-wasm-celler-oilt0wta` —
  WASM binary (compiled artifact)

These should NOT be annotated with `CHARTER-VIOLATION` comments. Future
scans should exclude `.venv/`, `*.so`, `*.wasm`, `node_modules/`,
`dist/`, `build/` from violation reports.
