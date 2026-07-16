# Style

Loaded before the first edit every session. Seed rules below; fill in per-project conventions as they are confirmed. Append when a convention solidifies. See [references/memory.md](../references/memory.md).

## Code
- Match the surrounding code: naming, indentation, comment density, idiom.
- No invented abbreviations (cfg/impl/req/res/fn) — full word is clearer and costs the same tokens.
- Comments explain why, not what.
- One logical change per patch.
- Prefer the existing pattern over introducing a new dependency.

## Output
- Terse prose to the user; lead with the answer, not the process.
- Never touch code, errors, paths, or patch anchors when compressing.
- No tool-call narration ("Let me...", "Now I'll...").

## Per-project conventions
<!-- Add below as confirmed. Example: -->
- (example) Framework: ___ . Test command: ___ . Build command: ___ .
- (example) Naming: files ___ , components ___ , CSS ___ .
