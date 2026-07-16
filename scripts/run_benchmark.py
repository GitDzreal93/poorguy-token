#!/usr/bin/env python3
"""poorguy-token A/B benchmark.

Runs the same coding task with the poorguy-token skill injected (via
--append-system-prompt-file) vs a plain baseline, captures exact token usage
and cost from `claude -p --output-format json`, and logs every run.

Honest by construction:
  - the "skill" arm injects the REAL shipped files (SKILL.md + references),
    not a paraphrase;
  - the baseline gets the default system prompt only;
  - usage numbers come straight from the model's own counters.

Usage:
  python3 scripts/run_benchmark.py write            # write-less axis
  python3 scripts/run_benchmark.py read             # read-less axis
  python3 scripts/run_benchmark.py write --quick    # 1 task x 1 rep (smoke)
  python3 scripts/run_benchmark.py write --reps 3
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.environ.get("POORGUY_BENCH_MODEL", "glm-5.2")
RAW = os.path.join(REPO, "benchmark", "raw")
os.makedirs(RAW, exist_ok=True)


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def skill_prompt(axis):
    """Concatenate the real shipped files the skill would load for this axis."""
    if axis == "write":
        files = ["SKILL.md", "references/output.md"]
    else:
        files = ["SKILL.md", "references/routing.md", "references/tools.md",
                 "references/output.md", "memory/best-practices.md"]
    body = "\n\n".join(f"# === {f} ===\n{read(f)}" for f in files)
    return (
        "The poorguy-token skill is ACTIVE for this session. Follow its rules "
        "strictly: terse output, read line ranges not whole files, one primary "
        "tool, evidence packets, never touch code/errors/anchors.\n\n" + body
    )


def run_claude(prompt, cwd, max_turns, system_file, permission_mode=None):
    cmd = ["claude", "-p", "--output-format", "json", "--model", MODEL,
           "--max-turns", str(max_turns)]
    if system_file:
        cmd += ["--append-system-prompt-file", system_file]
    if permission_mode:
        cmd += ["--permission-mode", permission_mode]
    t0 = time.time()
    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                          cwd=cwd, timeout=900)
    wall = time.time() - t0
    try:
        data = json.loads(proc.stdout)
    except Exception:
        data = {"parse_error": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    return data, wall, proc.returncode


WRITE_TASKS = [
    {"id": "W1", "max_turns": 1,
     "prompt": "Explain how database connection pooling works, why it matters, "
               "and show a minimal Node.js example using the `pg` package with a Pool."},
    {"id": "W2", "max_turns": 1,
     "prompt": "I keep getting a CORS error in the browser when my React app calls "
               "my Express API. Explain what causes CORS errors and show how to fix "
               "it, including the middleware."},
    {"id": "W3", "max_turns": 1,
     "prompt": "Review this Python function for bugs and suggest improvements. "
               "Explain your reasoning.\n\n"
               "def parse_config(path):\n"
               "    with open(path) as f:\n"
               "        lines = f.readlines()\n"
               "    cfg = {}\n"
               "    for line in lines:\n"
               "        k, v = line.split('=')\n"
               "        cfg[k] = v\n"
               "    return cfg"},
]

READ_TASKS = [
    {"id": "R1", "max_turns": 12, "cwd": REPO, "permission_mode": "plan",
     "prompt": "Map how the poorguy-token skill decides which reference file to "
               "load for a task. List the files and the specific line ranges that "
               "define the routing, and cite them as path:line. Do not edit anything."},
    {"id": "R2", "max_turns": 12, "cwd": REPO, "permission_mode": "plan",
     "prompt": "Find every place the skill reads host-specific state for token "
               "measurement. List the exact fields per host (Codex, Claude Code) "
               "with path:line citations. Do not edit anything."},
]


def axis_tasks(axis):
    return WRITE_TASKS if axis == "write" else READ_TASKS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("axis", choices=["write", "read"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    reps = 1 if args.quick else args.reps
    tasks = axis_tasks(args.axis)
    if args.quick:
        tasks = tasks[:1]

    sys_text = skill_prompt(args.axis)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        tf.write(sys_text)
        skill_file = tf.name

    runs = []
    for task in tasks:
        for arm in ["baseline", "skill"]:
            for r in range(reps):
                sys_file = skill_file if arm == "skill" else None
                cwd = task.get("cwd") or tempfile.mkdtemp()
                print(f"[{args.axis}] {task['id']} {arm} rep{r} ...", flush=True)
                data, wall, rc = run_claude(
                    task["prompt"], cwd, task["max_turns"], sys_file,
                    task.get("permission_mode"))
                mu = (data.get("modelUsage") or {}).get(MODEL, {})
                rec = {
                    "axis": args.axis, "task": task["id"], "arm": arm, "rep": r,
                    "model": MODEL, "rc": rc, "wall_s": round(wall, 1),
                    "input_tokens": mu.get("inputTokens") or data.get("usage", {}).get("input_tokens"),
                    "cache_read": mu.get("cacheReadInputTokens"),
                    "cache_create": mu.get("cacheCreationInputTokens"),
                    "output_tokens": mu.get("outputTokens") or data.get("usage", {}).get("output_tokens"),
                    "cost_usd": data.get("total_cost_usd"),
                    "num_turns": data.get("num_turns"),
                    "result_chars": len(data.get("result", "") or ""),
                }
                runs.append(rec)
                print("   -> in=%s out=%s cost=%s turns=%s chars=%s" % (
                    rec["input_tokens"], rec["output_tokens"], rec["cost_usd"],
                    rec["num_turns"], rec["result_chars"]), flush=True)

    out = os.path.join(RAW, f"runs-{args.axis}-{int(time.time())}.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    print("\n=== summary (%s, model=%s) ===" % (args.axis, MODEL))
    print("task  arm       out_tokens(mean)  input_tokens(mean)  cost$(mean)")
    for task in tasks:
        for arm in ["baseline", "skill"]:
            rs = [x for x in runs if x["task"] == task["id"] and x["arm"] == arm]
            if not rs:
                continue
            mo = sum(x["output_tokens"] or 0 for x in rs) / len(rs)
            mi = sum(x["input_tokens"] or 0 for x in rs) / len(rs)
            mc = sum(x["cost_usd"] or 0 for x in rs) / len(rs)
            print(f"{task['id']:<5} {arm:<9} {mo:>15.0f} {mi:>19.0f} {mc:>11.5f}")
    # delta
    print("\n--- output-token delta (skill vs baseline) ---")
    for task in tasks:
        b = [x for x in runs if x["task"] == task["id"] and x["arm"] == "baseline"]
        s = [x for x in runs if x["task"] == task["id"] and x["arm"] == "skill"]
        if b and s:
            bo = sum(x["output_tokens"] or 0 for x in b) / len(b)
            so = sum(x["output_tokens"] or 0 for x in s) / len(s)
            d = (so - bo) / bo * 100 if bo else 0
            print(f"{task['id']}: {bo:.0f} -> {so:.0f} output tokens ({d:+.0f}%)")
    print(f"\nraw -> {out}")
    os.unlink(skill_file)


if __name__ == "__main__":
    main()
