#!/usr/bin/env python3
"""Print a poorguy-token session telemetry table."""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


BUCKETS = {
    "user_text_bytes": "用户文本",
    "assistant_text_bytes": "助手文本",
    "tool_call_bytes": "工具调用",
    "tool_output_bytes": "工具输出",
    "world_state_bytes": "环境状态",
    "turn_context_bytes": "轮次上下文",
}

_TOKEN_ENCODER: Any = None

ZH_LABELS = {
    "metric": "指标",
    "value": "值",
    "host": "宿主",
    "session_tokens": "本次会话 token",
    "context": "上下文",
    "tools": "工具",
    "skills": "技能",
    "memory": "记忆",
    "elapsed": "耗时",
    "context_buckets": "上下文桶",
    "none": "未观察到",
    "unknown": "未知",
    "yes": "是",
    "no": "否",
    "read": "读取",
    "write": "写入",
    "session": "会话",
    "turn": "本轮",
}

EN_LABELS = {
    "metric": "metric",
    "value": "value",
    "host": "host",
    "session_tokens": "session tokens",
    "context": "context",
    "tools": "tools",
    "skills": "skills",
    "memory": "memory",
    "elapsed": "elapsed",
    "context_buckets": "context buckets",
    "none": "none",
    "unknown": "unknown",
    "yes": "yes",
    "no": "no",
    "read": "read",
    "write": "write",
    "session": "session",
    "turn": "turn",
}


def utf8_len(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False).encode("utf-8"))


def mixed_token_estimate(byte_count: int, text: str = "") -> int:
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    ascii_bytes = max(byte_count - cjk * 3, 0)
    return max(math.ceil(byte_count / 4), math.ceil(cjk * 1.5 + ascii_bytes / 4))


def text_token_count(text: str) -> int:
    global _TOKEN_ENCODER
    if not text:
        return 0
    if _TOKEN_ENCODER is None:
        try:
            import tiktoken  # type: ignore[import-not-found]

            _TOKEN_ENCODER = tiktoken.get_encoding("o200k_base")
        except Exception:
            _TOKEN_ENCODER = False
    if _TOKEN_ENCODER:
        return len(_TOKEN_ENCODER.encode(text))
    return mixed_token_estimate(len(text.encode("utf-8")), text)


def add_text_bucket(buckets: Counter, token_buckets: Counter, key: str, text: str) -> None:
    buckets[key] += len(text.encode("utf-8"))
    token_buckets[key] += text_token_count(text)


def is_bootstrap_context(text: str) -> bool:
    return text.lstrip().startswith("<environment_context>")


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def mentions_memory_file(text: str) -> bool:
    return any(path in text for path in (
        "memory/best-practices.md",
        "memory/style.md",
        "memory/lessons.md",
        ".poorguy-token/memory/lessons.md",
        ".poorguy-token/memory/archive.md",
    ))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pick_codex_thread(cwd: str | None) -> dict[str, Any] | None:
    db_path = Path.home() / ".codex" / "state_5.sqlite"
    if not db_path.exists():
        return None
    columns = [
        "id",
        "rollout_path",
        "created_at",
        "updated_at",
        "tokens_used",
        "cwd",
        "model",
        "reasoning_effort",
        "cli_version",
        "memory_mode",
    ]
    query = f"select {', '.join(columns)} from threads"
    params: list[Any] = []
    if cwd:
        query += " where cwd = ?"
        params.append(cwd)
    query += " order by recency_at_ms desc, updated_at_ms desc, updated_at desc limit 1"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(query, params).fetchone()
    if not row and cwd:
        return pick_codex_thread(None)
    return dict(zip(columns, row)) if row else None


def text_blocks(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                out.append(block["text"])
        return "\n".join(out)
    return ""


def parse_codex(cwd: str | None) -> dict[str, Any]:
    thread = pick_codex_thread(cwd)
    if not thread:
        return {"host": "codex", "error": "missing ~/.codex/state_5.sqlite"}

    rollout = Path(thread["rollout_path"])
    rows = read_jsonl(rollout) if rollout.exists() else []
    buckets = Counter()
    token_buckets = Counter()
    tools = Counter()
    skills = set()
    memory_files = set()
    memory_writes = set()
    last_user_message = ""
    context_window = None
    session_tokens = thread.get("tokens_used") or 0
    prompt_tokens = None
    task_started = None
    last_timestamp = None
    pending_user_message = None

    for row in rows:
        payload = row.get("payload") or {}
        row_type = row.get("type")
        if row.get("timestamp"):
            last_timestamp = row["timestamp"]

        if row_type == "world_state":
            buckets["world_state_bytes"] += utf8_len(payload)
            continue
        if row_type == "turn_context":
            buckets["turn_context_bytes"] += utf8_len(payload)
            continue
        if row_type == "event_msg":
            event_type = payload.get("type")
            if event_type == "task_started":
                task_started = payload.get("started_at") or task_started
                context_window = payload.get("model_context_window") or context_window
            elif event_type == "token_count":
                info = payload.get("info") or {}
                total = info.get("total_token_usage") or {}
                last = info.get("last_token_usage") or {}
                session_tokens = total.get("total_tokens") or session_tokens
                prompt_tokens = last.get("input_tokens") or prompt_tokens
                context_window = info.get("model_context_window") or context_window
            elif event_type == "agent_message":
                add_text_bucket(buckets, token_buckets, "assistant_text_bytes", payload.get("message", ""))
            elif event_type == "user_message":
                last_user_message = payload.get("message", "") or last_user_message
                if last_user_message and not is_bootstrap_context(last_user_message):
                    if last_user_message == pending_user_message:
                        pending_user_message = None
                    else:
                        add_text_bucket(buckets, token_buckets, "user_text_bytes", last_user_message)
                        pending_user_message = None
            continue

        if row_type != "response_item":
            continue

        payload_type = payload.get("type")
        if payload_type == "message":
            role = payload.get("role")
            text = text_blocks(payload.get("content"))
            if role == "user":
                if text and not is_bootstrap_context(text):
                    add_text_bucket(buckets, token_buckets, "user_text_bytes", text)
                    pending_user_message = text
            elif role == "assistant":
                add_text_bucket(buckets, token_buckets, "assistant_text_bytes", text)
            continue
        if payload_type == "function_call":
            name = payload.get("name") or "unknown"
            args = payload.get("arguments") or ""
            tools[name] += 1
            buckets["tool_call_bytes"] += len((name + args).encode("utf-8"))
            for skill in ("poorguy-token", "ponytail"):
                if skill in args:
                    skills.add(skill)
            if "/SKILL.md" in args and "poorguy-token" in args:
                skills.add("poorguy-token")
            if mentions_memory_file(args):
                memory_files.add(args)
                if any(marker in args for marker in ("apply_patch", ">>", "tee ", "cat >")):
                    memory_writes.add(args)
            continue
        if payload_type == "function_call_output":
            output = payload.get("output") or ""
            buckets["tool_output_bytes"] += len(str(output).encode("utf-8"))
            if "/SKILL.md" in output and "poorguy-token" in output:
                skills.add("poorguy-token")

    if not prompt_tokens:
        prompt_tokens = sum(buckets.values()) // 4

    return {
        "host": "codex",
        "thread": thread,
        "rollout": str(rollout),
        "tokens_source": "codex.event_msg.token_count" if rows else "codex.sqlite.threads.tokens_used",
        "session_tokens": session_tokens,
        "context_window": context_window,
        "context_used": prompt_tokens,
        "buckets": dict(buckets),
        "bucket_tokens": dict(token_buckets),
        "tools": tools,
        "skills": sorted(skills),
        "memory_read": bool(memory_files),
        "memory_written": bool(memory_writes),
        "memory_note": "loaded memory files" if memory_files else f"not observed; codex mode={thread.get('memory_mode', 'unknown')}",
        "language": "zh" if has_cjk(last_user_message) else "en",
        "elapsed_seconds": max(0, int(time.time() - (thread.get("created_at") or time.time()))),
        "turn_seconds": max(0, int(time.time() - task_started)) if task_started else None,
        "last_timestamp": last_timestamp,
    }


def claude_project_dir(cwd: str) -> Path:
    return Path.home() / ".claude" / "projects" / cwd.replace("/", "-")


def parse_claude(cwd: str | None) -> dict[str, Any]:
    cwd = cwd or os.getcwd()
    project_dir = claude_project_dir(cwd)
    files = sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {"host": "claude", "error": f"missing transcript in {project_dir}"}
    rows = read_jsonl(files[0])
    buckets = Counter()
    tools = Counter()
    tokens = 0
    skills = set()
    memory_read = False
    memory_written = False
    last_user_message = ""
    started = files[0].stat().st_ctime

    for row in rows:
        message = row.get("message") or row
        role = message.get("role")
        usage = message.get("usage") or {}
        tokens += sum(usage.get(key, 0) or 0 for key in (
            "input_tokens",
            "output_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        ))
        content = message.get("content")
        if role == "user":
            text = text_blocks(content)
            last_user_message = text or last_user_message
            buckets["user_text_bytes"] += utf8_len(content)
        elif role == "assistant":
            buckets["assistant_text_bytes"] += utf8_len(content)
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name = block.get("name") or "unknown"
                    tools[name] += 1
                    buckets["tool_call_bytes"] += utf8_len(block)
                    if "poorguy-token" in json.dumps(block, ensure_ascii=False):
                        skills.add("poorguy-token")
                    block_text = json.dumps(block, ensure_ascii=False)
                    if mentions_memory_file(block_text):
                        memory_read = True
                        if any(marker in block_text for marker in ("apply_patch", ">>", "tee ", "cat >")):
                            memory_written = True
                elif block.get("type") == "tool_result":
                    buckets["tool_output_bytes"] += utf8_len(block)

    context_used = mixed_token_estimate(sum(buckets.values()))
    return {
        "host": "claude",
        "thread": {"cwd": cwd, "model": "unknown", "cli_version": "unknown"},
        "rollout": str(files[0]),
        "tokens_source": "claude.message.usage" if tokens else "estimated.context_bytes",
        "session_tokens": tokens or context_used,
        "context_window": None,
        "context_used": context_used,
        "buckets": dict(buckets),
        "tools": tools,
        "skills": sorted(skills),
        "memory_read": memory_read,
        "memory_written": memory_written,
        "memory_note": "detected from transcript" if memory_read else "not observed",
        "language": "zh" if has_cjk(last_user_message) else "en",
        "elapsed_seconds": max(0, int(time.time() - started)),
        "turn_seconds": None,
        "last_timestamp": None,
    }


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "unknown"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes}m{sec}s"
    if minutes:
        return f"{minutes}m{sec}s"
    return f"{sec}s"


def join_counter(counter: Counter, none: str, limit: int = 6) -> str:
    if not counter:
        return none
    return ", ".join(f"{name} x{count}" for name, count in counter.most_common(limit))


def markdown_table(report: dict[str, Any], lang: str = "auto") -> str:
    labels = ZH_LABELS if (lang == "zh" or (lang == "auto" and report.get("language") == "zh")) else EN_LABELS
    if report.get("error"):
        return f"| {labels['metric']} | {labels['value']} |\n|---|---|\n| {labels['host']} | {report['host']} |\n| error | {report['error']} |"

    context_window = report.get("context_window")
    context_used = report.get("context_used")
    if context_window and context_used is not None:
        context = f"{context_used:,} / {context_window:,} ({context_used / context_window:.1%})"
    else:
        context = f"{context_used:,} / {labels['unknown']}" if context_used is not None else labels["unknown"]

    bucket_bits = []
    bucket_tokens = report.get("bucket_tokens", {})
    for key, label in BUCKETS.items():
        value = report.get("buckets", {}).get(key, 0)
        if value:
            tokens = bucket_tokens.get(key)
            bucket_bits.append(f"{label}~{(tokens if tokens is not None else mixed_token_estimate(value)):,}t")

    memory = (
        f"{labels['read']}: {labels['yes'] if report.get('memory_read') else labels['no']}; "
        f"{labels['write']}: {labels['yes'] if report.get('memory_written') else labels['no']}"
    )
    rows = [
        (labels["host"], report["host"]),
        (labels["session_tokens"], f"{report.get('session_tokens', 0):,} ({report.get('tokens_source')})"),
        (labels["context"], context),
        (labels["tools"], join_counter(report.get("tools", Counter()), labels["none"])),
        (labels["skills"], ", ".join(report.get("skills") or []) or labels["none"]),
        (labels["memory"], memory),
        (labels["elapsed"], f"{labels['session']} {format_duration(report.get('elapsed_seconds'))}; {labels['turn']} {format_duration(report.get('turn_seconds'))}"),
        (labels["context_buckets"], "; ".join(bucket_bits) or labels["unknown"]),
    ]
    out = [f"| {labels['metric']} | {labels['value']} |", "|---|---|"]
    out.extend(f"| {key} | {value} |" for key, value in rows)
    return "\n".join(out)


def self_test() -> None:
    assert mixed_token_estimate(8, "abcd") == 2
    assert format_duration(3661) == "1h1m1s"
    assert "none" == join_counter(Counter(), "none")
    assert mentions_memory_file("sed -n '1,5p' memory/style.md")
    assert not mentions_memory_file("docs mention memory/ generally")
    assert is_bootstrap_context("  <environment_context>\n")
    assert not is_bootstrap_context("user asks about <environment_context>")
    table = markdown_table({
        "host": "codex",
        "session_tokens": 10,
        "tokens_source": "test",
        "context_used": 5,
        "context_window": 100,
        "tools": Counter({"exec": 2}),
        "skills": ["poorguy-token"],
        "memory_read": True,
        "memory_written": False,
        "memory_note": "loaded",
        "elapsed_seconds": 1,
        "turn_seconds": 1,
        "buckets": {"tool_output_bytes": 8},
    })
    assert "| context | 5 / 100 (5.0%) |" in table
    assert "| memory | read: yes; write: no |" in table
    token_table = markdown_table({
        "host": "codex",
        "session_tokens": 10,
        "tokens_source": "test",
        "context_used": 5,
        "context_window": 100,
        "tools": Counter(),
        "skills": [],
        "memory_read": False,
        "memory_written": False,
        "elapsed_seconds": 1,
        "turn_seconds": 1,
        "buckets": {"user_text_bytes": 999},
        "bucket_tokens": {"user_text_bytes": 3},
    }, "zh")
    assert "用户文本~3t" in token_table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("auto", "codex", "claude"), default="auto")
    parser.add_argument("--lang", choices=("auto", "zh", "en"), default="auto")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("ok")
        return 0

    if args.host == "codex":
        report = parse_codex(args.cwd)
    elif args.host == "claude":
        report = parse_claude(args.cwd)
    else:
        report = parse_codex(args.cwd)
        if report.get("error"):
            report = parse_claude(args.cwd)
    print(markdown_table(report, args.lang))
    return 0 if not report.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())
