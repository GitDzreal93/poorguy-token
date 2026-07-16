# Routing

Pick the first route that fits.

| Task | Primary path | Fallback | Skip tools when |
|---|---|---|---|
| Exact file edit | Direct range read | `rg` then range read | User named the file and change is local |
| Diff review | `git diff` first | Graph impact query | No diff exists |
| Symbol lookup | CodeGraph | Serena or `rg` | Symbol is already in context |
| Shared-function edit | CodeGraph impact/callers | GitNexus impact | Function is private and local |
| Execution flow | GitNexus trace/context | CodeGraph | One file contains the flow |
| API route impact | GitNexus | CodeGraph | Route file and callers are known |
| Cross-repo/group impact | GitNexus | graphify | Repo group is not configured |
| Docs + code question | graphify | Direct reads | Docs are tiny or explicitly named |
| PDF/media/schema context | graphify | Direct file tool | Single small file is named |
| Large logs | Exact error lines first | Summarize surrounding log | User already supplied the failure |
| Unknown repo exploration | Read-only evidence packet | CodeGraph or strict `rg` | Repo has fewer than about 20 files |

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
