# Routing

Pick the first route that fits. "Graph backend" everywhere below means **the one backend chosen/detected in [tools.md](tools.md)** — not a specific product. Route every graph-shaped query through it.

| Task | Primary path | Fallback | Skip tools when |
|---|---|---|---|
| Exact file edit | Direct range read | `rg` then range read | User named the file and change is local |
| Diff review | `git diff` first | Graph backend impact query | No diff exists |
| Symbol lookup | Graph backend | Serena or `rg` | Symbol is already in context |
| Shared-function edit | Graph backend (callers/impact) | `rg` + range reads | Function is private and local |
| Execution flow | Graph backend trace | `rg` across call sites | One file contains the flow |
| API route impact | Graph backend | `rg` on route handlers | Route file and callers are known |
| Cross-repo/group impact | Graph backend | `rg` | Repo group is not configured |
| Docs + code question | Graph backend | Direct reads | Docs are tiny or explicitly named |
| PDF/media/schema context | Graph backend | Direct file tool | Single small file is named |
| Large logs | Exact error lines first | Summarize surrounding log | User already supplied the failure |
| Unknown repo exploration | Read-only evidence packet | Graph backend or strict `rg` | Repo has fewer than about 20 files |

A backend's own strengths (CodeGraph = pure code, GitNexus = flows/cross-repo, graphify = mixed media) matter **only at pick time** — see tools.md. Once one is chosen, don't spin up a second backend because a task "fits" another better. If the chosen backend can't answer a query, fall back to `rg`, not to a rival backend.

## Output Budgets

- Exact edit: read the target range plus nearby context only.
- Bug fix: preserve exact error, command, cwd, changed files, and failing assertion.
- Review: inspect `git diff` before repo search.
- Refactor: fetch callers/callees once, then read only cited ranges.
- Architecture answer: prefer summaries and citations over full file bodies.

## Evidence Rules

Each packet should include:

- `summary`: one or two sentences.
- `citations`: paths, line ranges, symbols, and why each matters.
- `next_action`: the smallest useful read/edit/test step.
- `confidence`: `high`, `medium`, or `low`.

Cache repeated packets by repo SHA, tool, query, and intent when local state is already being used.

## Denylist By Default

Do not scan generated or bulky paths unless the user asks:

```text
dist build coverage node_modules vendor .venv __pycache__
*.lock *.min.js snapshots
```

## Stop Rule

Stop exploring once the next step is obvious enough to edit or test. Ask before widening to a whole-repo audit.
