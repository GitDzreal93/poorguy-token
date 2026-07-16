<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo.svg" width="150" alt="poorguy-token">
  </picture>
</p>

<h1 align="center">poorguy-token</h1>

<p align="center">
  <em>He pays for his own tokens. So he spends none he doesn't have to.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/works%20with-Claude%20Code%20%2B%20Codex-111111?style=flat-square" alt="Claude Code + Codex">
  <img src="https://img.shields.io/badge/axes-5-111111?style=flat-square" alt="5 axes">
  <img src="https://img.shields.io/badge/benchmark-honest%20or%20none-111111?style=flat-square" alt="No fake benchmark">
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT license">
</p>

<p align="center">
  <strong>Read less &middot; Write less &middot; Never make the same mistake twice.</strong><br>
  <sub>The AI coding skill that treats your token bill like it comes out of its own pocket.</sub>
</p>

<p align="center">
  <sub><a href="README.zh.md">中文</a></sub>
</p>

---

You know him. Checks the token counter after every reply. Reads three lines of a file, not three hundred. Writes the answer in the first sentence — the apology never comes. Got burned by that bug last Tuesday; you won't catch him near it again.

**poorguy-token puts him inside your agent.**

It is not another indexer. It is the brain that decides *how little* your agent can read, *how little* it can write, and *which lesson from last time* it must not forget — while keeping every line of code correct.

## Before / after

You ask: *"what calls `UserService.validate`?"*

**Your agent:** greps the repo, opens 9 files, pastes 6 of them into context, then summarizes.

**poorguy:** one graph query, one evidence packet:

```json
{ "summary": "3 callers; checkout path affected",
  "citations": [{ "path": "src/checkout/service.ts", "lines": "42-88", "why": "direct caller" }],
  "next_action": "read cited ranges only" }
```

And on the way out — the reply itself. Same bug, two answers:

**Without poorguy:**

> Sure! I'd be happy to help you with that. The issue you're seeing is likely caused by the auth middleware checking token expiry with a strict less-than comparison instead of less-than-or-equal, which means tokens expire one tick early. Let me walk you through it…
>
> *(~73 output tokens before the fix is named)*

**With poorguy:**

> Token expiry uses `<` not `<=` in `auth/middleware.ts:42`. Tokens die one tick early.
>
> *(~20 tokens. Fix is the first word.)*

Same answer. The apology was never the point.

## How it works — five axes

Before acting, poorguy runs five checks. Each is one reference file, loaded only when the task needs it — so the skill itself stays cheap to keep in context.

| Axis | What it does | Saves |
|---|---|---|
| **1. Read less** | Cheapest context path first: range read → graph query (CodeGraph / GitNexus / graphify) → strict `rg`. | input / context |
| **2. Write less** | Terse prose. Code, errors, paths, and patch anchors are never touched. | output |
| **3. Remember** | Lessons load before the first edit. A mistake happens once. | retries, dead-ends |
| **4. Enforce** | Optional host hooks block fluff replies at the source. | guarantees the above |
| **5. Measure** | Real per-host token counts, so you watch the bill go down. | visibility |

## Frugal, not cheap

Lazy about tokens. Never about correctness.

Validation, error handling, security, data-loss guards, and the exact lines you're about to edit are never on the chopping block. When an action is irreversible, security-sensitive, or order-sensitive, poorguy stops being terse and says it in full. It compresses prose, never code.

And no invented abbreviations — `cfg`/`impl`/`req` save zero tokens (the tokenizer splits them like the full word) and cost clarity. The full word it is.

## Install

Skills load at session start, so install, then **start a new session**.

### Claude Code

```bash
# user-level (every project). symlink keeps your edits live:
ln -s "$(pwd)" ~/.claude/skills/poorguy-token
```

```bash
# or project-level (one repo):
mkdir -p .claude/skills && ln -s "$(pwd)" .claude/skills/poorguy-token
```

Symlink the **whole directory** — `SKILL.md` reaches `references/` and `memory/` by relative path.

### Codex

Copy the core rules from [`SKILL.md`](SKILL.md) into your repo's `AGENTS.md` (Codex reads it every session), or point your config at this directory's skills. Routing, output, and memory work identically; only measurement reads Codex-local state.

## The part that compounds: memory

Skills forget. poorguy doesn't.

Every confirmed mistake, correction, and non-obvious convention gets written as a one-line lesson — loaded before the next edit. The second encounter is free; the mistake never happens a third time.

```text
- type error after rename: missed a caller in another file. Rule: fetch callers before rename. Avoid: single-file rename.
- tests hung on CI: script used jest --watch. Rule: run `jest --ci`. Avoid: watch mode in scripts.
```

Two tiers: **skill memory** (ships with the skill — your hard-won general rules) and **project memory** (`.poorguy-token/memory/`, repo-specific). Both stay terse, because reloading memory costs tokens too — a bloated memory store is self-defeating.

## Optional: make it a harness

A skill is advice the model can ignore on a bad turn. Hooks are enforced. poorguy ships a tested Claude Code `Stop` hook that blocks replies opening with pleasantries and forces a terse retry:

```json
{
  "hooks": {
    "Stop": [{ "matcher": "", "hooks": [{ "type": "command",
      "command": "python3 ~/.claude/skills/poorguy-token/hooks/fluff_guard.py" }] }]
  }
}
```

Codex enforces the same intent through `AGENTS.md` rules (it has fewer native hook points). Hooks are always opt-in — see [`references/harness.md`](references/harness.md).

## The honest numbers

Every token-saver on GitHub leads with a big percentage. poorguy is the one that won't lie to you with a number it made up. Here is the real math:

- **Read less is the big lever.** In long sessions, input and context dwarf output. Skipping nine full-file reads beats any prose trick.
- **Write less cuts output** — roughly tens of percent on verbose replies — but the rules cost **~1–1.5k input tokens per turn**. Net win on long, chatty work; near flat on terse Q&A.
- **The only fully honest number is an A/B on your own usage page.** poorguy ships the measurement to read it — real counts from Codex sqlite/rollout or Claude Code's `message.usage`, with a confidence label.

> **Rule of thumb:** if your normal reply is over ~1.5–2k output tokens, poorguy saves you money. Under that, it saves you reading time — and that part is free.

## Files

```text
poorguy-token/
  SKILL.md                 # the hub: load memory, pick an axis, core rules
  references/              # the five blades, loaded on demand
    routing.md  tools.md  output.md  memory.md  harness.md  measurement.md
  memory/                  # always-on lessons, style, best practices (seeded)
    best-practices.md  style.md  lessons.md
  hooks/fluff_guard.py     # Claude Code Stop hook (tested)
  docs/                    # bilingual architecture + design notes
```

## FAQ

**Why "poorguy"?**
Because someone pays for those tokens, and it's you.

**Does it hurt code quality?**
No. It compresses prose to the user, never code, errors, or the lines being edited. Risky and order-sensitive steps get full sentences.

**Claude Code or Codex?**
Both. Same brain; only the measurement adapter and the hook surface differ.

**Will it remember my codebase's weird build command?**
After the first time, yes. That is the entire point of the memory tier.

**Where's the benchmark?**
There isn't one, and there won't be a fake one. Run your own A/B and check your provider's usage page — that number outranks anything a README could print.

**Do I need CodeGraph / GitNexus / graphify?**
No. Without them poorguy falls back to strict `rg` and range reads and still helps on the write + memory axes. With one installed, the read axis gets sharp.

## License

[MIT](LICENSE). The shortest license that works.

## Star History

<a href="https://www.star-history.com/#GitDzreal93/poorguy-token&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=GitDzreal93/poorguy-token&type=Date&theme=dark">
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=GitDzreal93/poorguy-token&type=Date">
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=GitDzreal93/poorguy-token&type=Date">
 </picture>
</a>
