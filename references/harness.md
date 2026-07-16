# Harness (enforce, not just advise)

A skill is guidance the model can ignore on any given turn. Hooks are enforced by the host — they run every time. This file gives ready-to-paste enforcement for both hosts.

All hooks here are **opt-in**. Pasting them modifies your environment, so show the config and let the user install it. Never auto-write `settings.json` or `config.toml` without approval.

## Claude Code (native hooks)

Claude Code runs hooks defined in `~/.claude/settings.json` (user) or `<repo>/.claude/settings.json` (project). Hook scripts receive a JSON payload on stdin. Exit code 2 blocks the action and feeds stderr back to the model as corrective feedback.

### Fluff guard (Stop hook) — enforces [output.md](output.md)

Block verbose replies and force a terse retry. Script ships with the skill at `hooks/fluff_guard.py`; it only flags opening pleasantries, never long technical answers.

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/skills/poorguy-token/hooks/fluff_guard.py"
          }
        ]
      }
    ]
  }
}
```

If you install the skill as a project skill, point the command at the project path instead.

### Usage log (SessionStart / Stop) — feeds [measurement.md](measurement.md)

Append a row to `.poorguy-token/savings.jsonl` on session end so the savings report has real data. A minimal notify script reads `transcript_path` from stdin, sums `message.usage`, and appends one JSON line. Defer building it until you actually read savings reports — the reference describes the shape, the script is only worth maintaining once the habit exists.

### What not to hard-block

Do not block whole-file `Read` calls or force range-only reads with a hook. Legitimate edits need full files sometimes, and a false block costs more tokens (retries) than it saves. Keep input-side savings in [routing.md](routing.md) as guidance; only output-side fluff is cheap and safe to enforce.

## Codex (rule-based + notify)

Codex has fewer native hook points than Claude Code. Enforcement there is mainly:

- **`AGENTS.md`** in the repo root — Codex reads it every session. Paste the Core Rules block from `../SKILL.md` and the [output.md](output.md) rules in. This is the primary Codex enforcement surface.
- **`~/.codex/config.toml`** `notify` program — runs on session events. Use it to append usage to `.poorguy-token/savings.jsonl` for measurement.
- **`config.toml` `tools`** allowlist — if you want to forbid broad-audit commands (`rg` over the whole repo without filters), Codex can deny tools. Use sparingly; it breaks legitimate exploration.

Codex cannot block a verbose reply mid-turn the way a Claude Code Stop hook can. For Codex, the output.md skill rules + AGENTS.md carry that load.

## Install checklist

1. Show the user the exact config block for their host.
2. Confirm approval before writing any settings file.
3. After install, run one throwaway task to confirm the hook fires (fluff reply → blocked).
4. Record the install in `.poorguy-token/config.json` so re-runs are idempotent.
