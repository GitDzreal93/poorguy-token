# Lessons (never repeat)

Terse. One line per lesson. Dedup before append.
Format: `- [symptom]: [root cause]. Rule: [do X]. Avoid: [don't Y].`
See [references/memory.md](../references/memory.md).

<!-- Seed examples — replace with real lessons as they happen. Repo-specific -->
<!-- lessons live in .poorguy-token/memory/lessons.md, not here. -->

- build failed locally but passed CI: Node version mismatch. Rule: check `.nvmrc`/`package.json#engines`. Avoid: assuming the global node version.
- edit had no effect: edited a generated file under `dist/`. Rule: edit source only. Avoid: touching build output.
- type error after a rename: missed a caller in another file. Rule: fetch callers before renaming. Avoid: single-file rename.
- flaky test: depended on wall-clock time/order. Rule: inject a clock or use deterministic fixtures. Avoid: `Date.now()`/`sleep` in tests.
- merge conflict reappeared: two patches edited the same shared util. Rule: fetch callers/impact before editing shared code. Avoid: editing blind.
- fix reverted next session: the lesson was never written down. Rule: append to memory on any confirmed mistake. Avoid: solving and moving on silently.
- agent reached for a second graph backend: CodeGraph/GitNexus/graphify overlap. Rule: reuse the installed/persisted backend; install one only if none present. Avoid: installing more than one.
