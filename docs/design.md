# poorguy-token Design / 设计

Date: 2026-07-16

---

## English

### One-line positioning

A token-saving **brain** for AI coding: read less, write less, never repeat a
mistake — across Claude Code and Codex — with quality as a guardrail.

### Why a brain, not a router

The first version only routed input (which graph tool to read from). That leaves
two big token sinks open: verbose output, and re-making mistakes the agent
already paid to learn. The redesign attacks all axes through one small `SKILL.md`
that deploys the right "blade" per task (Swiss-army-knife model). Each blade is a
reference loaded only when needed, so the skill stays cheap to keep in context.

### The five axes

| Axis | Lever | Reference | Saves |
|---|---|---|---|
| Read less | route to cheapest context path | `routing.md`, `tools.md` | input / context |
| Write less | terse output, preserve code & anchors | `output.md` | output |
| Never repeat | memory loaded before coding | `memory.md` + `memory/*` | retries, failed trajectories |
| Enforce | host hooks (opt-in) | `harness.md` + `hooks/*` | guarantees the above |
| Measure | real per-host token counts | `measurement.md` | visibility |

### Quality guardrail

Frugality never wins over correctness. Rules that enforce this:

- **Never touch**: code, inline code, errors, stack traces, paths, URLs, commands,
  numbers, API names, and patch anchors.
- **Auto-clarity**: security warnings, irreversible actions, order-sensitive
  multi-step sequences, and anything compression makes ambiguous switch back to
  full sentences.
- Code, commits, and PRs are written normally; only chat prose is terse.

### Memory system

Two tiers, both plain files (host-agnostic):

1. **Skill memory** (version-controlled, ships with the skill): `best-practices.md`,
   `style.md`, `lessons.md`. Always-on rules, seeded with high-value defaults.
2. **Project memory** (per repo): `.poorguy-token/memory/lessons.md`. Repo-specific
   lessons appended during work.

Protocol: load both before the first edit; append a one-line lesson whenever a
test fails, the user corrects the agent, or a non-obvious convention is found.
Memory is kept terse because reloading it costs input tokens — a bloated store is
self-defeating.

### Harness (enforce, not advise)

A skill is guidance; hooks are enforced. `hooks/fluff_guard.py` is a Claude Code
`Stop` hook that blocks replies opening with pleasantries and forces a terse
retry (tested). Codex enforces via `AGENTS.md` rules. Hooks are always opt-in.

### Host support

Routing, output, and memory are host-agnostic. Measurement reads host-local
state: Codex (`~/.codex/` sqlite + rollout jsonl) and Claude Code
(`~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`, `message.usage`).

### Honest numbers

- Read-less is the biggest lever for long sessions (input/context dominates).
- Write-less saves output but costs ~1–1.5k input tokens/turn for the rules —
  net-positive on verbose work, near-zero/negative on terse Q&A.
- The only fully honest test is an A/B against the provider's usage page.

### Directory layout

```text
poorguy-token/
  SKILL.md
  README.md
  references/  routing.md tools.md output.md memory.md harness.md measurement.md
  memory/      best-practices.md style.md lessons.md
  hooks/       fluff_guard.py
  docs/        design.md research-and-design.md detailed-design.md
```

### Deferred

- MCP server, custom indexer.
- Usage-log notify script for Codex/Claude (build when savings reports become a habit).
- Hosts beyond Codex and Claude Code.

---

## 中文

### 一句话定位

给 AI 编码用的**省 token 大脑**：读得少、写得少、不重蹈覆辙——跨 Claude Code
和 Codex——以质量为护栏。

### 为什么是「大脑」而不是「路由器」

第一版只路由 input（读哪个图谱工具）。这留下了两个大 token 漏斗：啰嗦的输出，
以及重复犯已经付出过代价的错误。重新设计后通过一个精简的 `SKILL.md` 按任务
部署合适的「刀片」（瑞士军刀模型）来攻击所有维度。每个刀片都是按需加载的
reference，skill 本身留在上下文里很便宜。

### 五个轴

| 轴 | 杠杆 | reference | 省的是 |
|---|---|---|---|
| 读得少 | 路由到最便宜上下文路径 | `routing.md`、`tools.md` | input / context |
| 写得少 | 极简输出，保留代码与锚点 | `output.md` | output |
| 不重犯 | 编码前加载记忆 | `memory.md` + `memory/*` | 重试、失败轨迹 |
| 强制执行 | 宿主 hook（可选） | `harness.md` + `hooks/*` | 保证以上落地 |
| 度量 | 按宿主真实 token 计数 | `measurement.md` | 可见性 |

### 质量护栏

省 token 永不以正确性为代价。强制规则：

- **永不触碰**：代码、行内代码、报错、堆栈、路径、URL、命令、数字、API 名、改动锚点。
- **auto-clarity**：安全告警、不可逆操作、对顺序敏感的多步操作、压缩后产生歧义的内容，自动切回完整句子。
- 代码、commit、PR 正常写；只有聊天里的散文才极简。

### 记忆系统

两层，都是纯文件（宿主无关）：

1. **skill 记忆**（随 skill 发布、进版本管理）：`best-practices.md`、`style.md`、`lessons.md`。常驻规则，已用高价值默认值播种。
2. **项目记忆**（每仓库）：`.poorguy-token/memory/lessons.md`。工作中追加的仓库专属教训。

协议：首次编辑前加载两层；每当测试失败、用户纠正、或发现非显而易见的约定，追加一行教训。记忆保持极简，因为重载要花 input token——膨胀的记忆库是自我拆台。

### Harness（强制，而非建议）

skill 是指导；hook 是强制。`hooks/fluff_guard.py` 是 Claude Code 的 `Stop`
hook，拦截以客套话开头的回复并要求极简重试（已测试）。Codex 通过
`AGENTS.md` 规则强制。hook 一律可选。

### 宿主支持

路由、输出、记忆都与宿主无关。度量读取宿主本地状态：Codex
（`~/.codex/` sqlite + rollout jsonl）与 Claude Code
（`~/.claude/projects/<编码后的cwd>/<session-id>.jsonl`、`message.usage`）。

### 关于数字的诚实

- 读得少是长会话最大杠杆（input/context 占大头）。
- 写得少省 output，但规则每回合约占 1–1.5k input token——啰嗦工作净赚，简短问答接近打平或亏。
- 最诚实的检验是 A/B，对比账单页。

### 目录结构

```text
poorguy-token/
  SKILL.md
  README.md
  references/  routing.md tools.md output.md memory.md harness.md measurement.md
  memory/      best-practices.md style.md lessons.md
  hooks/       fluff_guard.py
  docs/        design.md research-and-design.md detailed-design.md
```

### 暂缓

- MCP server、自定义索引器。
- Codex/Claude 的用量记录 notify 脚本（等节省报告成为习惯再做）。
- Codex 与 Claude Code 之外的宿主。
