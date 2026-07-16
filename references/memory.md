# Memory (never repeat a mistake)

Two tiers. Load before coding. Write on every confirmed lesson. Works the same in Claude Code and Codex — memory lives in files, not in a host-specific store.

## Tiers

1. **Skill memory** (ships with the skill, portable, version-controlled): `memory/best-practices.md`, `memory/style.md`, `memory/lessons.md`. Always-on rules.
2. **Project memory** (per repo): `.poorguy-token/memory/lessons.md`. Repo-specific lessons learned during work.

## Load protocol

Before the first edit in a session, read:

- skill tier: `memory/best-practices.md` + `memory/style.md` + `memory/lessons.md`
- project tier: `.poorguy-token/memory/lessons.md` if it exists

Skip for one-off exact-file tasks that need no conventions. Past mistakes must be in context before coding — this is the "never repeat" guarantee.

## Write protocol (append a lesson when)

- A test/build/lint fails and the root cause is worth remembering.
- The user corrects you.
- You discover a non-obvious project rule: build/test command, framework quirk, env requirement, naming convention.

Repo-specific facts → project memory. Host-wide or language-wide rules → skill memory.

## Lesson shape

Keep terse — terse memory is cheap to reload (see [output.md](output.md)). One line:

```text
- [symptom]: [root cause]. Rule: [do X]. Avoid: [don't Y].
```

Examples:

```text
- tests hung on CI: package.json script used jest --watch. Rule: run `jest --ci`. Avoid: watch mode in scripts.
- edit had no effect: edited generated file under dist/. Rule: edit source only. Avoid: touching build output.
- type error after rename: missed a caller in another file. Rule: fetch callers before rename. Avoid: single-file rename.
```

## Bake best practices (every time)

When a good pattern is confirmed — the user says "yes, do it this way", or a convention solidifies across a task — append it to `memory/best-practices.md` or `memory/style.md`. This is the "engrave it" step. Do it in the same turn the convention is confirmed, not later.

## Keep memory tight

Memory costs input tokens to reload. A bloated memory store is self-defeating.

- One line per lesson. No prose, no story.
- Dedup before append: if a similar lesson exists, merge or replace.
- Cap project lessons around 50; move older ones to `.poorguy-token/memory/archive.md`.
- Never store what the repo, git history, or CLAUDE.md already records.
- Compress skill memory files with the terse style so reload stays cheap.
