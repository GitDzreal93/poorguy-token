# Tools

**One graph backend.** CodeGraph, GitNexus, and graphify are interchangeable alternatives for the same axis. Install **one**, reuse it, let the user override. Never more than one — they overlap, and keeping multiple is pure overhead.

## Decision flow

Run in order; stop at the first hit.

1. **Override** — the user named a backend for this task ("use GitNexus", "用 graphify 查") → use it. No reinstall, no questions.
2. **Persisted choice** — `.poorguy-token/config.json` has `graph_backend` → use it.
3. **Already installed** — `command -v` (below) finds one → reuse the first one found. Do **not** reinstall, do **not** add a second.
4. **Nothing installed AND the task needs repo-scale graph context** — ask the user one question (see *Pick one*), install **only** the recommended backend, persist it.
5. **Not needed** — exact-file edit, tiny task, or repo under ~20 files → skip graph tools; direct range reads + `rg`.

## Detection

```bash
command -v codegraph gitnexus graphify
```

Prints each tool that exists on PATH. Run `--version` only if you need the number.

## Pick one (only when nothing is installed and graph context is actually needed)

Ask what the user mostly does, then install **one** backend:

| Core scenario | Install | Why this one |
|---|---|---|
| Code-only: symbol lookup, callers/callees, impact analysis, shared-function edits | **CodeGraph** | cheapest for pure-code graphs |
| Execution flow, API route impact, cross-repo/group, change detection | **GitNexus** | best at flows + cross-repo |
| Mixed code + docs/schema/PDF/media, or reusable graph artifacts | **graphify** | multimodal; code parses locally via tree-sitter (free, no LLM, nothing leaves the machine) |

Show the one install command and continue with `rg` fallback if the user declines. **Never offer to install a second backend** — a different scenario is not a reason to add one; the chosen backend handles all graph queries (see routing.md).

Install commands — confirm the exact package from each tool's own docs first:

- graphify: `uv tool install graphifyy` then `graphify install --project --platform claude` (skip `--strict`; it blocks raw reads — see harness.md).
- GitNexus / CodeGraph: per their official docs.

## Persist the choice

After detecting or installing, write the chosen backend to `.poorguy-token/config.json`:

```json
{ "graph_backend": "graphify" }
```

Later sessions reuse it and skip detect/install. Update it only when the user picks a different backend.

## Not graph backends (can coexist with the one above)

- **Serena** — optional precise symbol rename/refactor when LSP-backed tooling is already available. Not a graph backend.
- **Direct `rg` / range reads** — tiny tasks, exact paths, missing index, or install declined.

## Index Policy

- Do not index for exact-file edits.
- Index lazily only when repo-scale context is needed.
- Prefer project-scoped setup when supported.
- If an index is stale only outside the task area, use it with lower confidence instead of reindexing.
- Amortize expensive index cost across later sessions for the same repo/SHA.

## Fallback

When the chosen backend is missing, fails, or returns nothing useful:

1. Record the miss in the evidence packet.
2. Use strict `rg --files`, targeted `rg`, and range reads.
3. Keep output capped and cite exact paths/lines.

Do **not** auto-install a different backend on a miss — fall back to `rg`.
