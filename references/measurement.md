# Measurement

Use this reference when reporting token/context savings. Never present estimates as exact.

## Codex Usage

Prefer Codex's local state when available:

- `~/.codex/state_5.sqlite`
- `threads.tokens_used`
- `threads.rollout_path`
- `threads.model`
- `threads.reasoning_effort`
- `threads.cli_version`

Treat these filenames as private implementation details. If they are missing or unreadable, return partial data with `estimated=true`.

## Context Buckets

When parsing a rollout jsonl, classify bytes into:

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

- `high`: actual Codex token count plus parsed rollout data.
- `medium`: parsed context text plus tokenizer or byte estimate.
- `low`: heuristic baseline only.

## Short Report

```text
poorguy-token report
actual tokens: 42,180 (Codex sqlite)
context: 38% of 110k, 18,420 tool-output tokens estimated
saved: 18,820 net estimated tokens
confidence: medium
top saver: CodeGraph avoided 9 full-file reads
```

If actual usage is unavailable:

```text
actual tokens: unknown
estimated context: 37,900 tokens
confidence: low
```
