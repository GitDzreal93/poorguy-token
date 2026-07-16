# Best Practices

Loaded before the first edit every session. Terse on purpose — cheap to reload. Append when a practice is confirmed. See [references/memory.md](../references/memory.md).

## Token
- Read line ranges, not whole files. Whole file only when editing needs nearby context.
- One graph tool per repo-scale question. Fallback only after a miss.
- `git diff` before repo search for review/debug after edits.
- Fetch callers once before editing shared functions.
- Skip index tools for exact-path edits.
- Denylist generated/vendor paths unless asked: dist build coverage node_modules vendor .venv __pycache__ *.lock *.min.js.

## Correctness
- Reproduce a bug before fixing. Preserve exact error + command + cwd + failing assertion.
- Prefer a root-cause fix over caller-by-caller guards.
- Run the project's verify/test command before declaring done; report real results.
- Smaller patch = less future context and fewer regressions.

## Workflow
- Classify intent before broad exploration.
- Stop exploring once evidence is enough to edit and test.
- Ask before global installs, broad audits, expensive reindexing.
- Convert broad tool output to an evidence packet before reasoning on it.
