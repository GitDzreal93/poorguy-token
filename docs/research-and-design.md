# poorguy-token: Research And Design

Date: 2026-07-16

## Goal

Build a standard Agent Skill that saves tokens during AI coding work by routing
the agent to the cheapest context path:

1. Use existing indexed knowledge when possible.
2. Read exact symbols and line ranges instead of whole files.
3. Avoid repeated grep/read exploration.
4. Track actual session cost and estimate avoided cost.
5. Install missing helper tools on first use, with user-visible safety gates.

V1 is Codex-first. The design keeps host adapters so Claude Code, Cursor,
OpenCode, and other Agent Skills hosts can be added without rewriting routing or
measurement.

## Research Summary

### Direct tool candidates

| Tool | Best for | Why it matters |
|---|---|---|
| CodeGraph | General code intelligence, impact analysis, fast symbol/call lookup | Pre-built graph, MCP integration, auto-sync, benchmarks show fewer reads/tool calls/tokens. |
| GitNexus | Large repos, execution flows, MCP tools, cross-repo/group analysis | Rich CLI + MCP, indexed repos, impact/trace/context tools, editor setup. |
| graphify | Mixed corpora: code + docs + PDFs + media + SQL/schema | Queryable graph output, local AST for code, explicit/inferred edge tags, exportable `graph.json`. |
| Serena | Symbol-aware navigation/editing/refactoring via MCP | LSP/IDE-backed tools, useful when precise symbol operations beat text search. |
| FastContext | Delegated repository exploration | Main agent asks a read-only exploration subagent for compact citations. |
| FastCode | Scouting-first structural navigation | Semantic-structural map, hybrid index, graph navigation, cost-aware context selection. |
| aider repo-map | Always-on lightweight code map | Compact file/symbol map sent with requests; simple baseline idea to reuse. |
| LLMLingua / prompt compressors | Large text compression | Useful only for non-code prose/docs/logs; risky for code anchors and patches. |

### Important findings

- CodeGraph's strongest lesson: one indexed query can replace many `grep` +
  `Read` calls. Its README reports median token reductions of 23-64% across
  sampled repos, with large reductions in file reads and tool calls.
- GitNexus is broader than a graph viewer. It indexes dependencies, call chains,
  clusters, and execution flows, then exposes MCP tools like `context`, `impact`,
  `trace`, and `detect_changes`.
- graphify is the best fit when the user's question crosses code and non-code
  artifacts. It writes `graph.html`, `GRAPH_REPORT.md`, and `graph.json`, so the
  agent can query a reusable graph instead of rereading source material.
- Aider's repo-map is the simplest proven pattern: keep a concise symbol map in
  context so the agent knows what exists before reading files.
- FastContext and ContextSniper point to the same architecture: separate
  exploration from solving. The solver should receive compact evidence packets,
  not every exploration step.
- Token reduction is not automatically cost reduction. Prompt caching, failed
  trajectories, and over-compression can make a smaller prompt more expensive or
  less successful. The metric must be success-adjusted billed cost when the host
  exposes billing data, and estimated token delta only as a fallback.

## Product Shape

This should be a router skill, not another indexer.

Name options:

- `agent-token-saver`
- `context-router`
- `token-aware-context`

Recommended: `agent-token-saver`, because it says the user outcome directly.

## First Use Flow

1. Detect repo root and host agent. V1 treats Codex as the primary host.
2. Detect installed tools:
   - `codegraph --version`
   - `gitnexus --version`
   - `graphify --version`
   - optional: `serena`, `fastcontext`, `aider`
3. If missing, offer install:
   - CodeGraph: `npm i -g @colbymchenry/codegraph` or official installer.
   - GitNexus: `npm i -g gitnexus` preferred over cold `npx` for MCP startup.
   - graphify: `uv tool install graphifyy`.
4. Register project-scoped integrations when supported:
   - `codegraph install` for agent MCP wiring, then `codegraph init`.
   - `gitnexus setup`, then `gitnexus analyze`.
   - `graphify install --project --platform codex` when using Codex.
5. Create local state:
   - `.agent-token-saver/config.json`
   - `.agent-token-saver/session.jsonl`
   - `.agent-token-saver/savings.jsonl`

Global install should require explicit approval because it changes PATH or user
agent configuration.

## Codex-First Host Adapter

Codex gets the first-class implementation because this project is being built in
Codex and local state is available.

Local sources to read:

| Source | Field | Use |
|---|---|---|
| `~/.codex/state_5.sqlite` | `threads.tokens_used` | Best available actual token count per thread. |
| `~/.codex/state_5.sqlite` | `threads.rollout_path` | Locate the session jsonl transcript. |
| `~/.codex/state_5.sqlite` | `threads.model`, `reasoning_effort`, `cli_version` | Segment reports by model and runtime. |
| rollout jsonl | `type=session_meta/event_msg/response_item/world_state/turn_context` | Estimate context, tool output, and conversation bytes. |
| `~/.codex/logs_2.sqlite` | `logs.estimated_bytes` | Fallback runtime log volume, not token usage. |

Do not depend on these filenames as public API. Wrap them behind
`bin/ats-host-codex` and make failure cheap:

```json
{
  "host": "codex",
  "thread_id": "...",
  "tokens_used": 12345,
  "tokens_source": "codex.sqlite.threads.tokens_used",
  "rollout_path": "...",
  "estimated": false
}
```

Future hosts implement the same JSON contract:

```text
ats-host-detect -> host name
ats-host-usage -> actual or estimated token/cost counters
ats-host-context -> transcript/context byte counters
```

## Routing Rules

Use the first rule that fits:

1. Tiny task, known file, user names exact path: skip external tools, use direct
   file read. Index lookup is overhead.
2. Need symbol/callers/callees/impact in normal code: use CodeGraph first.
3. Need execution flows, MCP tool/resource map, API route impact, group/cross-repo
   questions: use GitNexus.
4. Need code + docs/schema/media, graph visualization, global knowledge graph, or
   reusable artifact: use graphify.
5. Need precise symbol rename/refactor/edit when an LSP is available: use Serena.
6. Need unknown repo exploration before solving: use FastContext-style delegated
   exploration if installed; otherwise emulate with read-only grep/read and return
   citations only.
7. Need large logs/docs pasted into context: compress or summarize, but preserve
   exact error lines and edit anchors.

## Token-Saving Techniques To Include

### Retrieval

- Prefer indexed graph query over file-by-file search.
- Ask for citations: paths, line ranges, symbols, relation type.
- Cap tool output and request summaries first.
- Use structural search before full text search.
- Use `rg --files` before broad `rg` content scans.
- Prefer symbol signatures and call edges over whole files.
- Cache query results per session.
- Avoid querying all tools. Route to one primary tool, fall back only on failure.

### Context Packing

- Keep a working set: files already known relevant, with reason and last line
  ranges read.
- Deduplicate repeated snippets across tool outputs.
- Strip generated files, lockfiles, vendored folders, build artifacts by default.
- Preserve exact text only for code to edit, stack traces, failing assertions, and
  command lines.
- Summarize prose docs, but never summarize patch anchors.
- Keep a "do not reread" list for files whose relevant symbols are already known.

### Agent Behavior

- Separate exploration from solving. Exploration returns evidence packets, not a
  transcript of every search.
- Stop exploration when the marginal value drops: enough evidence to edit/test.
- Prefer one high-signal question to several broad queries.
- Use a cheap model/subagent for exploration when host supports it.
- Avoid spawning subagents that cannot access the index.
- Before editing, fetch callers/impact once to prevent repeated sibling checks.

### Install And Index

- Lazy install: install only the chosen primary tool plus required runtime.
- Lazy index: index the current repo only when the task needs repo-scale context.
- Background refresh when supported, but never block trivial tasks.
- Track index freshness by git SHA and modified file timestamp.

### Measurement

- Actual usage, Codex v1:
  - Read `threads.tokens_used` from `~/.codex/state_5.sqlite` for the current
    thread. This is the primary number.
  - Read `threads.rollout_path` and parse the jsonl to break the session into
    user text, assistant text, tool calls, tool results, world state, and turn
    context.
  - Record model, reasoning effort, CLI version, cwd, git SHA, and branch when
    available.
- Actual usage, other hosts:
  - Read host-provided token/cost stats when available.
  - Otherwise estimate with tokenizer libraries and record `estimated=true`.
- Token estimation fallback:
  - Preferred: use the model tokenizer when available.
  - Cheap fallback: `ceil(utf8_bytes / 4)` for English-heavy text and
    `ceil(utf8_bytes / 2)` for CJK-heavy text. Store the heuristic name.
  - Never pretend this is exact. Report confidence.
- Context size:
  - `context_window_tokens`: configured/model-known maximum when known.
  - `current_thread_tokens`: current `threads.tokens_used` or estimate.
  - `transcript_bytes`: total rollout jsonl payload text bytes.
  - `tool_output_bytes`: bytes from tool result items.
  - `code_context_bytes`: bytes of file contents and code snippets shown to the
    model.
  - `non_code_context_bytes`: docs, logs, web pages, prose, plans.
  - `repeated_context_bytes`: repeated snippets detected by hash.
  - `context_pressure`: `current_thread_tokens / context_window_tokens` when both
    are known.
- Baseline estimate:
  - Count avoided full-file reads using file byte length converted to estimated
    tokens.
  - Count avoided repeated grep output.
  - Compare graph answer tokens vs estimated naive search/read path.
- Savings formula:
  - `gross_saved = baseline_estimated_tokens - actual_context_tokens`
  - `net_saved = gross_saved - indexing_tokens_or_cost_equivalent`
  - amortize indexing across sessions by repo and git SHA.
- Report confidence:
  - `high`: host exposes actual tokens and tool logs.
  - `medium`: actual context text captured, tokenizer estimate.
  - `low`: heuristic baseline only.

### Savings Report

End-of-session output should be short:

```text
Agent Token Saver
actual tokens: 42,180 (Codex sqlite)
context pressure: 38% of 110k
tool output: 18,420 estimated tokens
avoided baseline: 61,000 estimated tokens
net saved: 18,820 estimated tokens
confidence: medium
top saver: CodeGraph impact query avoided 9 full-file reads
```

If actual token usage is unavailable:

```text
actual tokens: unknown
estimated context: 37,900 tokens
confidence: low
```

## Skill Architecture

```text
SKILL.md
references/
  routing.md
  tools.md
  measurement.md
  install.md
bin/
  ats-host-detect
  ats-host-codex
  ats-host-usage
  ats-detect
  ats-install
  ats-route
  ats-session-start
  ats-session-end
  ats-token-estimate
```

Keep the first version as shell + JSON state. Add TypeScript/Python only when
shell becomes painful.

## Proposed `SKILL.md` Behavior

1. Start session:
   - detect tools
   - load `.agent-token-saver/config.json`
   - record start timestamp and git SHA
2. Classify user intent:
   - exact file edit
   - symbol lookup
   - impact analysis
   - architecture question
   - docs/media/schema question
   - cross-repo question
   - log/debug question
3. Pick one primary tool.
4. Run the cheapest query.
5. Return a compact evidence packet to the main agent:
   - answer type
   - tool used
   - paths/line ranges
   - confidence
   - recommended next action
6. On session end:
   - collect usage
   - estimate baseline
   - report context size and pressure
   - append local savings record
   - show one short report

## More Token-Saving Methods

These should be encoded as rules, not advice buried in docs:

1. **Intent gate before indexing.** Do not index for exact-path edits, one-line
   fixes, or user-provided snippets.
2. **One primary tool.** Pick one of CodeGraph/GitNexus/graphify first. Fallback
   only after a miss or stale index.
3. **Index freshness check.** If the index git SHA is stale only for files outside
   the task area, proceed and mark confidence lower instead of reindexing.
4. **Evidence packets.** Tool output returned to the main agent must be capped and
   shaped as: finding, file, line range, symbol, why relevant, next action.
5. **Line-range reads.** Read only the line ranges needed after graph lookup.
   Escalate to whole-file only when editing requires local context.
6. **Symbol skeletons first.** Ask for signatures/classes/routes before bodies.
7. **Callers before edits.** For shared functions, fetch callers once before
   patching to avoid sibling bugs and repeated exploration.
8. **Change-diff mode.** When user asks review/debug after edits, analyze `git
   diff` first, not the whole repo.
9. **Output budget by task type.** Architecture answers can be summaries. Bug
   fixes need exact paths and assertions. Refactors need call graph edges.
10. **Cache by query hash.** Same question + same git SHA returns the previous
    evidence packet.
11. **Negative cache.** Remember "searched X, found nothing" to avoid repeated
    misses.
12. **Generated-file denylist.** Ignore `dist`, `build`, lockfiles, vendored code,
    snapshots, coverage, and minified assets unless explicitly asked.
13. **Progressive disclosure references.** Keep `SKILL.md` small. Put long tool
    docs in `references/` and load only the relevant file.
14. **Session compaction checkpoint.** Keep a small `state.md` with current task,
    files, decisions, and open questions so compaction does not force rediscovery.
15. **Error-first debug.** For failures, preserve exact error, command, cwd,
    changed files, and last failing assertion. Drop unrelated logs.
16. **Stop rule.** Once the agent has enough evidence to edit and test, stop
    searching.
17. **Amortize expensive indexes.** Charge index cost across future sessions for
    the same repo/SHA, not all to the first query.
18. **Model tier routing.** Use cheap/local exploration when available, main model
    only for decisions and edits.
19. **Patch-size awareness.** Prefer smaller patches that fix the shared root
    cause. Less code means less future context.
20. **Ask before broadening.** If the router wants to scan the whole repo, ask
    whether the user needs full audit coverage or a task-local answer.

## Open Questions

1. Should first-run install be global by default, or project-scoped first with a
   global opt-in?
2. Should FastContext/FastCode/Serena be part of v1, or listed as optional
   "awesome tools" until the core router works?
3. What name do we want: `agent-token-saver`, `context-router`, or another?

## Recommendation

Build v1 as a Codex-first thin router over CodeGraph, GitNexus, and graphify.
Include Serena, FastContext, FastCode, aider repo-map, and LLMLingua in the
awesome list and optional detectors, but do not install them by default.

Reason: the three requested tools already cover the main routing surface. More
tools increase install failure modes before we have measurement.
