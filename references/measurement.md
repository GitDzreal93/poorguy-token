# Measurement

Use this reference when reporting token/context savings. Never present estimates as exact.

## Host Usage

Prefer the host's own counters and local state. Pick the matching host below; both return the same shape (`tokens_used`, `tokens_source`, `estimated`).

### Codex

Prefer Codex's local state when available:

- `~/.codex/state_5.sqlite`
- `threads.tokens_used`
- `threads.rollout_path`
- `threads.model`
- `threads.reasoning_effort`
- `threads.cli_version`

### Claude Code

Prefer Claude Code's transcript and per-record usage:

- Transcripts: `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`
  - `<encoded-cwd>` is the working directory with `/` replaced by `-`
    (e.g. `/Volumes/dz/code/poorguy-token` -> `-Volumes-dz-code-poorguy-token`).
  - One JSONL file per session, named by session UUID; the current session is the newest file in the project dir.
- Real token counts live on assistant records at `message.usage`:
  - `input_tokens`, `output_tokens`
  - `cache_creation_input_tokens`, `cache_read_input_tokens`
  - `server_tool_use` (e.g. `web_search_requests`, `web_fetch_requests`)
- Session total: sum `input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens` across assistant records. Record `tokens_source` as `claude.usage.message_usage`.
- `/cost` reports total tokens and cost for the current session. `ccusage` (third-party) parses the same transcripts into per-session/daily reports.
- Model, cwd, git SHA, and branch are not stored on every record; capture them once from the environment or the first/last record and attach to the report.

Treat all paths and field names as private implementation details. If a source is missing or unreadable, return partial data with `estimated=true`.

## Context Buckets

When parsing a host transcript (Codex rollout jsonl or Claude Code session jsonl), classify bytes into:

| Bucket | Meaning |
|---|---|
| `user_text_bytes` | User messages |
| `assistant_text_bytes` | Assistant messages |
| `tool_call_bytes` | Tool names and arguments |
| `tool_output_bytes` | Tool results shown to the model |
| `code_context_bytes` | File contents, snippets, diffs, stack traces |
| `non_code_context_bytes` | Docs, web pages, plans, prose |
| `world_state_bytes` | Host-provided state |
| `turn_context_bytes` | Host-provided turn context |
| `repeated_context_bytes` | Duplicate chunks by hash |

Claude Code block -> bucket mapping:

| Transcript block | Bucket |
|---|---|
| `user` message text | `user_text_bytes` |
| `assistant` message text blocks | `assistant_text_bytes` |
| `tool_use` blocks (`name` + `input`) | `tool_call_bytes` |
| `tool_result` blocks (`content`) | `tool_output_bytes` |
| `Read`/tool-returned file contents, snippets, diffs | `code_context_bytes` |
| `attachment` and pasted docs/web pages | `non_code_context_bytes` |

Codex rollout event types map by the same intent; reuse the buckets above.

## Token Estimate Fallback

Use exact host counters first. Otherwise mark estimates clearly:

```text
english_or_code_tokens = ceil(utf8_bytes / 4)
cjk_heavy_tokens = ceil(utf8_bytes / 2)
mixed_tokens = max(ceil(bytes / 4), ceil(cjk_chars * 1.5 + ascii_bytes / 4))
```

## Savings Formula

```text
gross_saved = baseline_estimated_tokens - actual_context_tokens
net_saved = gross_saved - index_cost_amortized_tokens
```

Baseline examples:

- Full-file reads avoided: file bytes converted to estimated tokens.
- Broad grep avoided: expected grep output converted to estimated tokens.
- Repeated query avoided: previous identical packet token count.
- Graph query vs manual search: dependency files in the evidence packet.

## Confidence

- `high`: actual host token count (Codex sqlite `tokens_used` or Claude Code `message.usage` sum) plus parsed transcript data.
- `medium`: parsed context text plus tokenizer or byte estimate.
- `low`: heuristic baseline only.

## Short Report

The `tokens` source label reflects whichever host produced the number. Examples:

Run this from the skill root before the final reply when `poorguy-token` is active:

```bash
python3 scripts/session_report.py
```

It prints a markdown table with session tokens, context window/use/percent, tools, observed skills, memory read/write, elapsed time, and context buckets. Values from host counters are exact for that host; bucket totals are byte/token estimates. Chinese user messages produce Chinese labels.

```text
poorguy-token report
actual tokens: 42,180 (Codex sqlite)
context: 38% of 110k, 18,420 tool-output tokens estimated
saved: 18,820 net estimated tokens
confidence: medium
top saver: CodeGraph avoided 9 full-file reads
```

```text
poorguy-token report
actual tokens: 51,604 (Claude message_usage sum)
context: 47% of 200k, 21,300 tool-output tokens estimated
saved: 14,200 net estimated tokens
confidence: high
top saver: line-range reads avoided 7 full-file reads
```

If actual usage is unavailable:

```text
actual tokens: unknown
estimated context: 37,900 tokens
confidence: low
```
