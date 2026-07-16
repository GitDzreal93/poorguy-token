---
name: poorguy-token
description: Token-saving context router for AI coding agents. Use when Codex is working in a repository and should minimize context, file reads, tool output, and repeated exploration for coding, debugging, review, refactoring, symbol lookup, impact analysis, execution-flow tracing, docs-plus-code questions, large logs, or token/context savings reports.
---

# Poorguy Token

Use this skill to choose the cheapest context path that still gives enough evidence to solve the user's coding task.

## Core Rules

1. Classify the task before reading broadly.
2. Use direct file/range reads for tiny tasks, exact-path edits, and user-provided snippets.
3. Use one primary context tool for repo-scale questions; fall back only after a miss, stale index, or unsupported query.
4. Convert broad tool output into an evidence packet before reasoning on it.
5. Read cited line ranges first; read whole files only when editing requires nearby context.
6. Fetch callers/impact once before changing shared functions.
7. Stop searching when there is enough evidence to edit and test.
8. Ask before global installs, broad repo audits, or expensive reindexing.

## Route

- Read [references/routing.md](references/routing.md) for intent classification, output budgets, evidence packets, and stop rules.
- Read [references/tools.md](references/tools.md) when selecting, detecting, installing, or initializing CodeGraph, GitNexus, graphify, or optional context tools.
- Read [references/measurement.md](references/measurement.md) when the user asks for token savings, context pressure, session reporting, or Codex usage counters.

## Evidence Packet Shape

Return compact evidence in this shape before reading more:

```json
{
  "intent": "impact-analysis",
  "primary_tool": "codegraph",
  "summary": "3 direct callers; checkout path is affected",
  "citations": [
    {
      "path": "src/checkout/service.ts",
      "lines": "42-88",
      "symbol": "validateOrder",
      "why": "direct caller"
    }
  ],
  "next_action": "read cited ranges only",
  "confidence": "high"
}
```

## Local State

Use `.poorguy-token/` only when a session needs persistent routing or savings state:

```text
.poorguy-token/
  sessions/
  cache/
  savings.jsonl
```

Skip local state for one-off exact-file tasks.
