# poorguy-token

## English

`poorguy-token` is a Codex-first Agent Skill for reducing token waste during AI
coding work. It routes the agent to the cheapest useful context source:
direct file/range reads, CodeGraph, GitNexus, graphify, or strict `rg` fallback.

The skill is now usable through `SKILL.md`.

### What It Does

- Classifies the task before broad repo exploration.
- Skips index tools for tiny or exact-file tasks.
- Chooses one primary context tool for repo-scale questions.
- Converts tool output into compact evidence packets with citations.
- Reads cited line ranges before whole files.
- Provides token/context savings reporting guidance for Codex sessions.

### Files

- `SKILL.md`: Runtime skill instructions.
- `references/routing.md`: Intent routing, budgets, evidence packet rules.
- `references/tools.md`: Tool selection, detection, install, and fallback policy.
- `references/measurement.md`: Codex usage and savings report guidance.
- `docs/research-and-design.md`: Research notes and product design.
- `docs/detailed-design.md`: Detailed architecture and diagrams.

### Deferred

Executable helper scripts are intentionally deferred. Add them when measurement
or routing commands are used often enough to justify maintaining code.

## 中文

`poorguy-token` 是一个 Codex 优先的 Agent Skill，用来减少 AI 编码任务里的
token 浪费。它会把 agent 路由到成本最低且足够有用的上下文来源：直接读取
文件/行范围、CodeGraph、GitNexus、graphify，或者严格限制输出的 `rg` 兜底。

现在已经可以通过 `SKILL.md` 使用。

### 功能

- 在大范围探索仓库前先判断任务类型。
- 对很小的任务或明确文件路径的修改，跳过索引工具。
- 对仓库级问题只选择一个主要上下文工具。
- 把工具输出压缩成带引用的 evidence packet。
- 优先读取引用到的行范围，而不是整文件。
- 为 Codex session 提供 token/context 节省报告规则。

### 文件

- `SKILL.md`：运行时 skill 指令。
- `references/routing.md`：意图路由、预算和 evidence packet 规则。
- `references/tools.md`：工具选择、检测、安装和兜底策略。
- `references/measurement.md`：Codex 用量和节省报告规则。
- `docs/research-and-design.md`：调研和产品设计。
- `docs/detailed-design.md`：详细架构和流程图。

### 暂缓内容

暂不加入可执行辅助脚本。等路由或测量命令被反复使用、值得维护代码时再补。
