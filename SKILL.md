---
name: poorguy-token
description: Token-saving brain for AI coding agents (Claude Code and Codex). Use when the agent should minimize tokens on both axes — READ less via one graph backend (CodeGraph/GitNexus/graphify — pick one, reuse what's installed), line-range reads, and evidence packets, and WRITE less via terse output with no fluff — for coding, debugging, review, refactoring, symbol lookup, impact analysis, execution-flow tracing, docs, or large logs. Also use to load or bake memory so coding mistakes are never repeated and best practices persist, to install enforcement hooks, or to report token/context savings.
---

# Poorguy Token

Token-saving brain for AI coding. Attacks cost on every axis: read less, write less, never repeat a mistake, enforce when asked. Works in Claude Code and Codex.

## Load memory first

Before the first edit, read `memory/best-practices.md`, `memory/style.md`, `memory/lessons.md`, and (if present) `.poorguy-token/memory/lessons.md`. Past mistakes must be in context before coding — the "never repeat" guarantee. See [references/memory.md](references/memory.md). Skip for one-off exact-file tasks.

## Axes → reference

Load only the blade the task needs.

| Axis | Goal | Read |
|---|---|---|
| Read less | cheapest context path | [references/routing.md](references/routing.md) |
| Graph tools | one backend — reuse or pick one of CodeGraph / GitNexus / graphify | [references/tools.md](references/tools.md) |
| Write less | terse output, keep accuracy | [references/output.md](references/output.md) |
| Memory | mistakes never repeated, best practices baked | [references/memory.md](references/memory.md) |
| Harness | enforce via hooks (opt-in) | [references/harness.md](references/harness.md) |
| Measure | token/context/savings report | [references/measurement.md](references/measurement.md) |

## Core rules

1. Classify the task before reading broadly.
2. Direct range read for tiny or exact-path edits; skip index tools.
3. **One graph backend per project** (CodeGraph / GitNexus / graphify): reuse what's installed, install one only if nothing is present and repo-scale context is needed, never all three. The user's explicit pick always wins. See [references/tools.md](references/tools.md). Fall back to `rg` only after a miss, stale index, or unsupported query.
4. Convert broad tool output into an evidence packet before reasoning on it.
5. Read cited line ranges first; whole file only when editing requires nearby context.
6. Fetch callers/impact once before changing shared functions.
7. Terse prose; never touch code, errors, paths, or patch anchors.
8. Stop searching once evidence is enough to edit and test. Ask before widening to a whole-repo audit.
9. Ask before global installs, broad repo audits, or expensive reindexing.
10. On any confirmed mistake, correction, or convention, append to memory.
11. Before every final reply while this skill is active, run `python3 scripts/session_report.py` from the skill root and append its markdown table. If the script is unavailable, print a compact manual table with available token/context/tool/skill/memory/elapsed facts and mark unknowns.
12. If the user writes in Chinese, reply in Chinese and render telemetry labels in Chinese too.

## Evidence packet

Return compact evidence in this shape before reading more:

```json
{
  "intent": "impact-analysis",
  "primary_tool": "codegraph",
  "summary": "3 direct callers; checkout path affected",
  "citations": [
    {"path": "src/checkout/service.ts", "lines": "42-88", "symbol": "validateOrder", "why": "direct caller"}
  ],
  "next_action": "read cited ranges only",
  "confidence": "high"
}
```

## Hosts

Routing, output, and memory are host-agnostic. Only measurement reads host-local state.

- Codex: session state in `~/.codex/` (sqlite + rollout jsonl). Enforcement via `AGENTS.md`.
- Claude Code: transcripts in `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`, real token counts on assistant records at `message.usage`. Enforcement via `settings.json` hooks.

## Local state

Use `.poorguy-token/` only when a session needs persistent routing, savings, or project memory:

```text
.poorguy-token/
  config.json          # graph_backend choice + install record (see references/tools.md, harness.md)
  sessions/
  cache/
  savings.jsonl
  memory/
    lessons.md
    archive.md
```

Skip local state for one-off exact-file tasks.
