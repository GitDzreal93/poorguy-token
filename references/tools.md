# Tools

Use one primary tool per task.

## Detection

Check only the tools relevant to the route:

```bash
codegraph --version
gitnexus --version
graphify --version
```

Use `command -v <tool>` when `--version` is unsupported.

## Selection

- CodeGraph: code-only symbol lookup, callers/callees, impact analysis, shared-function edits.
- GitNexus: execution flow, API route impact, cross-repo/group questions, change detection.
- graphify: mixed code/docs/schema/PDF/media context and reusable graph artifacts.
- Serena: optional precise symbol rename/refactor when LSP-backed tooling is already available.
- Direct `rg`/range reads: tiny tasks, exact paths, missing indexes, or install denied.

## Install Policy

Ask before global installs or agent configuration changes. Show the command first and continue with direct fallback if the user declines.

Common install patterns may include npm or uv tool installs, but confirm the package name from the user's project docs or the tool's official docs before running them. Do not cold-install optional tools just to answer a tiny task.

## Index Policy

- Do not index for exact-file edits.
- Index lazily only when repo-scale context is needed.
- Prefer project-scoped setup when supported.
- If an index is stale only outside the task area, use it with lower confidence instead of reindexing.
- Amortize expensive index cost across later sessions for the same repo/SHA.

## Fallback

When the chosen tool is missing or fails:

1. Record the miss in the evidence packet.
2. Use strict `rg --files`, targeted `rg`, and range reads.
3. Keep output capped and cite exact paths/lines.
