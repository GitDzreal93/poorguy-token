#!/usr/bin/env python3
"""poorguy-token fluff guard — Claude Code Stop hook.

Reads the last assistant message from the session transcript and blocks
(exit code 2) if it opens with pleasantries/fluff, sending feedback so the
model retries tersely. Only opening fluff triggers a block — code, errors,
paths, and long technical answers are never the trigger. Exit 0 = allow.

Wire it up in ~/.claude/settings.json (or project .claude/settings.json):

    {
      "hooks": {
        "Stop": [{
          "matcher": "",
          "hooks": [{
            "type": "command",
            "command": "python3 ~/.claude/skills/poorguy-token/hooks/fluff_guard.py"
          }]
        }]
      }
    }
"""
import json
import re
import sys

# Only phrases that open a reply with noise. Narrow on purpose — never block
# a technically correct, long answer.
BANNED = [
    r"\bI'd be happy to\b",
    r"\bI am happy to\b",
    r"\bI'd love to\b",
    r"\bI will be happy to\b",
    r"\bLet me know if\b",
    r"\bFeel free to\b",
    r"\bSure!\s",
    r"\bCertainly,\b",
    r"\bOf course,\b",
    r"\bAs an AI\b",
    r"\bI hope this helps\b",
    r"\bHappy to help\b",
    r"\bGreat question\b",
]
RX = re.compile("|".join(BANNED), re.IGNORECASE)


def last_assistant_text(transcript_path):
    text = ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                parts = []
                for block in msg.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                if parts:
                    text = "\n".join(parts)
    except Exception:
        return ""
    return text


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Avoid an infinite retry loop.
    if payload.get("stop_hook_active"):
        sys.exit(0)

    transcript = payload.get("transcript_path")
    if not transcript:
        sys.exit(0)

    text = last_assistant_text(transcript)
    if not text:
        sys.exit(0)

    match = RX.search(text[:500])  # only flag opening fluff
    if match:
        sys.stderr.write(
            "poorguy-token: reply opens with fluff (%r). "
            "Drop pleasantries/filler and lead with the answer. "
            "See references/output.md. Retry terse.\n" % match.group(0)
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
