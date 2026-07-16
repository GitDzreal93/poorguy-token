# poorguy-token Benchmark — 2026-07-17

Real A/B measurement. Same task, same model, same harness — only difference is
whether the poorguy-token skill is injected. Token counts come straight from the
model's own counters (`claude -p --output-format json` → `usage` / `modelUsage`).

---

## English

### Setup

- **Model:** `glm-5.2`, via Claude Code 2.1.209 pointed at the GLM Anthropic-compatible endpoint. *Not* Claude Sonnet/Opus, *not* Codex. Results may differ by model and host.
- **Skill arm:** the real shipped files (`SKILL.md` + the reference(s) for the axis) injected through `--append-system-prompt-file`.
- **Baseline arm:** default system prompt only.
- **Write axis:** 3 coding questions, single-shot (`--max-turns 1`), no repo, n=3.
- **Read axis:** 2 exploration tasks in this repo, read-only (`--permission-mode plan`, `--max-turns 12`), **n=1**.

### Results — write axis (generation)

| Task | Baseline out (n=3 mean) | Skill out (n=3 mean) | Δ |
|---|--:|--:|--:|
| W1 (DB pooling) | 1487 | 1139 | **−23%** |
| W2 (CORS fix) | 1151 | 1029 | −11% |
| W3 (code review) | 1306 | 1098 | −16% |
| **Mean output** | **1315** | **1089** | **−17%** |

Output tokens fall ~17% (prose shrinks; code/anchors preserved — as designed).
Cost per single shot is roughly flat to slightly up, because the injected rules
add ~1.5–4k input tokens. In a real session the system prompt is cached after
the first turn, so that input cost is paid once and the output savings dominate.

### Results — read axis (exploration in-repo)

| Task | Metric | Baseline | Skill | Δ |
|---|---|--:|--:|--:|
| R1 (routing map) | input | 33 018 | 12 327 | **−63%** |
| R1 | output | 9 717 | 4 450 | −54% |
| R1 | cost | $0.504 | $0.225 | −55% |
| R2 (host-state fields) | input | 76 109 | 18 938 | **−75%** |
| R2 | output | 16 663 | 5 737 | −66% |
| R2 | cost | $1.019 | $0.278 | −73% |
| **Combined** | **cost** | **$1.52** | **$0.50** | **−67%** |

The baseline over-explores (R2 burned 76k tokens / $1.02 to answer a question
about a 16-file repo). The skill arm routes to line ranges, returns evidence
packets, and writes terse output — cutting context ~71% and cost ~67%. The read
arm benefits from the *whole* skill (routing + terse output), not routing alone.

### Caveats (read them)

1. **Read axis is n=1.** Agentic runs are noisy; treat the ratio as directional, not pinned. The magnitude (50–75%) is large enough that the sign is credible, but the exact number needs more reps.
2. **Small repo (16 files).** The skill's own `routing.md` predicts near-zero savings under ~20 files. We still saw large savings because the baseline over-explores — on a large repo the absolute savings grow, the ratio may differ.
3. **Force-injected.** The skill was guaranteed active. Real auto-trigger fires less than 100% of the time, so real-world savings are ≤ measured.
4. **Model/host.** glm-5.2 in Claude Code. Not representative of Claude or Codex until measured there.
5. **`output_tokens` is cumulative** across all turns; `result_chars` is the final artifact length.

### Reproduce

```bash
python3 scripts/run_benchmark.py write --reps 3
python3 scripts/run_benchmark.py read  --reps 1
```

Raw per-run JSONL: `benchmark/raw/`. Harness: `scripts/run_benchmark.py`. Set
`POORGUY_BENCH_MODEL` to test another model on the same endpoint.

---

## 中文

### 设置

- **模型：** `glm-5.2`，经 Claude Code 2.1.209 指向 GLM 的 Anthropic 兼容端点。**不是** Claude Sonnet/Opus，**不是** Codex。结果可能随模型/宿主不同而变化。
- **skill 组：** 注入真实发布的文件（`SKILL.md` + 对应轴的 reference），用 `--append-system-prompt-file`。
- **baseline 组：** 仅默认系统提示。
- **写轴：** 3 个编码问题，单次生成（`--max-turns 1`），无仓库，n=3。
- **读轴：** 本仓库内 2 个探索任务，只读（`--permission-mode plan`，`--max-turns 12`），**n=1**。

### 结果 —— 写轴（生成）

| 任务 | baseline 输出 (n=3 均值) | skill 输出 (n=3 均值) | Δ |
|---|--:|--:|--:|
| W1（连接池） | 1487 | 1139 | **−23%** |
| W2（CORS 修复） | 1151 | 1029 | −11% |
| W3（代码审查） | 1306 | 1098 | −16% |
| **输出均值** | **1315** | **1089** | **−17%** |

输出 token 降约 17%（散文压缩；代码/锚点保留——按设计）。单次成本基本持平甚至略升，因为注入的规则多了 ~1.5–4k input token。真实会话里系统提示首轮后会被缓存，这笔 input 成本只付一次，省下的 output 占主导。

### 结果 —— 读轴（仓库内探索）

| 任务 | 指标 | baseline | skill | Δ |
|---|---|--:|--:|--:|
| R1（路由映射） | input | 33 018 | 12 327 | **−63%** |
| R1 | output | 9 717 | 4 450 | −54% |
| R1 | 成本 | $0.504 | $0.225 | −55% |
| R2（宿主状态字段） | input | 76 109 | 18 938 | **−75%** |
| R2 | output | 16 663 | 5 737 | −66% |
| R2 | 成本 | $1.019 | $0.278 | −73% |
| **合计** | **成本** | **$1.52** | **$0.50** | **−67%** |

baseline 过度探索（R2 为一个 16 文件仓库的问题烧了 76k token / $1.02）。skill 组路由到行范围、返回 evidence packet、写得极简——上下文降 ~71%、成本降 ~67%。读轴受益于**整个** skill（路由 + 极简输出），不只是路由。

### 局限（请读）

1. **读轴 n=1。** agentic 运行有噪声；把这个比例当方向性而非精确值。幅度（50–75%）够大，方向可信，但精确数字需要更多重复。
2. **小仓库（16 文件）。** skill 自己的 `routing.md` 预测 <20 文件时接近零节省。这里仍大降，是因为 baseline 过度探索——大仓库上绝对节省更大，比例可能不同。
3. **强制注入。** skill 被保证激活。真实自动触发不到 100%，所以真实节省 ≤ 测量值。
4. **模型/宿主。** Claude Code 里的 glm-5.2。不代表 Claude 或 Codex，需分别测量。
5. **`output_tokens` 是累计**跨所有轮次；`result_chars` 是最终产物长度。

### 复现

```bash
python3 scripts/run_benchmark.py write --reps 3
python3 scripts/run_benchmark.py read  --reps 1
```

原始每轮 JSONL：`benchmark/raw/`。harness：`scripts/run_benchmark.py`。设 `POORGUY_BENCH_MODEL` 可在同一端点测其他模型。
