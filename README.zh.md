<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo.svg" width="150" alt="poorguy-token">
  </picture>
</p>

<h1 align="center">poorguy-token</h1>

<p align="center">
  <em>他的 token 是自己掏钱买的。所以不该花的一个都不花。</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/支持-Claude%20Code%20%2B%20Codex-111111?style=flat-square" alt="Claude Code + Codex">
  <img src="https://img.shields.io/badge/五个轴-5-111111?style=flat-square" alt="5 axes">
  <img src="https://img.shields.io/badge/benchmark-要么真要么没有-111111?style=flat-square" alt="No fake benchmark">
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT license">
</p>

<p align="center">
  <strong>读得少 &middot; 写得少 &middot; 同一个错绝不犯第二次。</strong><br>
  <sub>把你的 token 账单当成它自己钱包里的钱来花的 AI 编码 skill。</sub>
</p>

<p align="center">
  <sub><a href="README.md">English</a></sub>
</p>

---

你认识他。每条回复发完都瞄一眼 token 计数器。读文件只读三行，不是三百行。第一句话就给答案——客套话永远缺席。上周二被那个 bug 坑过一次；你别想再看他靠近它。

**poorguy-token 把他塞进了你的 agent。**

它不是又一个索引器。它是那个决定你的 agent「**能少读到什么程度**」「**能少写到什么程度**」「**上次的哪条教训绝不能再忘**」的大脑——同时保证每一行代码都正确。

## 改造前后

你问：*「谁调用了 `UserService.validate`？」*

**你的 agent：** grep 全仓库，打开 9 个文件，把其中 6 个粘进上下文，然后总结一番。

**poorguy：** 一次图查询，一个 evidence packet：

```json
{ "summary": "3 个调用方；checkout 路径受影响",
  "citations": [{ "path": "src/checkout/service.ts", "lines": "42-88", "why": "直接调用方" }],
  "next_action": "只读引用到的范围" }
```

到了回复环节——同一个 bug，两种答法：

**没有 poorguy：**

> 好的！很高兴为您解答。您遇到的这个问题很可能是 auth 中间件在检查 token 过期时用了严格小于比较、而不是小于等于，所以 token 会提前一个 tick 过期。让我带您一步步看一下……
>
> *（约 73 个 output token，才说到怎么修）*

**有 poorguy：**

> `auth/middleware.ts:42` 的 token 过期用了 `<` 而不是 `<=`。提前一个 tick 死掉。
>
> *（约 20 token。第一个词就是修复。）*

同一个答案。客套话从来都不是重点。

## 工作原理 —— 五个轴

动手之前，poorguy 跑五道检查。每一道对应一个 reference 文件，**只在任务需要时才加载**——所以 skill 本体留在上下文里很便宜。

| 轴 | 做什么 | 省的是 |
|---|---|---|
| **1. 读得少** | 先走最便宜路径：读行范围 → 图查询（CodeGraph / GitNexus / graphify）→ 严格 `rg`。 | input / context |
| **2. 写得少** | 极简散文。代码、报错、路径、改动锚点永不触碰。 | output |
| **3. 记得住** | 首次编辑前加载教训。错误只发生一次。 | 重试、死路 |
| **4. 强制执行** | 可选宿主 hook，在源头拦掉废话回复。 | 保证以上落地 |
| **5. 量得出** | 按宿主真实 token 计数，让你看着账单往下走。 | 可见性 |

## 省钱，不省工

对 token 懒。对正确性从不懒。

校验、错误处理、安全、防数据丢失，以及你即将改动的那几行——统统不在砍刀范围内。当某个操作不可逆、涉及安全、或对顺序敏感时，poorguy 会停止极简、用完整句子说清楚。它压缩的是散文，绝不是代码。

而且不造缩写——`cfg`/`impl`/`req` 一个 token 都不省（分词器会把它们拆成跟全拼一样），还牺牲可读性。该用全称就用全称。

## 安装

skill 在会话启动时加载，所以装完后**新开一个会话**。

### Claude Code

```bash
# 用户级（所有项目）。软链让你在仓库里的改动立即生效：
ln -s "$(pwd)" ~/.claude/skills/poorguy-token
```

```bash
# 或项目级（单个仓库）：
mkdir -p .claude/skills && ln -s "$(pwd)" .claude/skills/poorguy-token
```

软链**整个目录**——`SKILL.md` 用相对路径引用 `references/` 和 `memory/`。

### Codex

把 [`SKILL.md`](SKILL.md) 里的核心规则拷进你仓库的 `AGENTS.md`（Codex 每次会话都会读），或把配置指向本目录的 skills。路由、输出、记忆完全一致；只有度量会读取 Codex 本地状态。

## 会复利的那一部分：记忆

skill 会忘。poorguy 不会。

每一个被确认的错误、纠正、和非显而易见的约定，都会被写成一行 lesson——在下一次编辑前加载。第二次遇到是免费的；错误绝不会有第三次。

```text
- 重命名后类型报错：漏了另一个文件里的调用方。规则：重命名前先拉 callers。避免：单文件重命名。
- CI 上测试卡住：脚本用了 jest --watch。规则：跑 `jest --ci`。避免：脚本里开 watch 模式。
```

两层：**skill 记忆**（随 skill 发布——你辛苦攒下的通用规则）和**项目记忆**（`.poorguy-token/memory/`，仓库专属）。两层都保持极简，因为重载记忆也要花 token——膨胀的记忆库是自我拆台。

## 可选：做成 harness

skill 是模型在状态不好时可以无视的建议。hook 是强制的。poorguy 自带一个测过的 Claude Code `Stop` hook，拦截以客套话开头的回复、要求极简重试：

```json
{
  "hooks": {
    "Stop": [{ "matcher": "", "hooks": [{ "type": "command",
      "command": "python3 ~/.claude/skills/poorguy-token/hooks/fluff_guard.py" }] }]
  }
}
```

Codex 通过 `AGENTS.md` 规则达到同样目的（它的原生 hook 点更少）。hook 一律可选——见 [`references/harness.md`](references/harness.md)。

## 关于数字的诚实

GitHub 上每个省 token 的项目都用一个大百分比开头。poorguy 是唯一不会用编出来的数字骗你的那个。真实账目如下：

- **读得少才是大杠杆。** 长会话里 input 和 context 远大于 output。少读九个整文件，胜过任何文字花活。
- **写得少省 output**——啰嗦回复大约省几十个百分点——但规则本身每回合占 **~1–1.5k input token**。长篇讨论净赚；简短问答基本打平。
- **唯一完全诚实的数字，是你自己在账单页做的 A/B。** poorguy 自带度量去读它——来自 Codex sqlite/rollout 或 Claude Code `message.usage` 的真实计数，并带置信度标注。

> **经验法则：** 你平时的回复若超过 ~1.5–2k output token，poorguy 帮你省钱；不到这个量级，它帮你省阅读时间——而那部分是免费的。

## 文件

```text
poorguy-token/
  SKILL.md                 # 大脑：先加载记忆，选一个轴，核心规则
  references/              # 五把刀片，按需加载
    routing.md  tools.md  output.md  memory.md  harness.md  measurement.md
  memory/                  # 常驻的教训、风格、最佳实践（已播种）
    best-practices.md  style.md  lessons.md
  hooks/fluff_guard.py     # Claude Code 的 Stop hook（已测）
  docs/                    # 中英双语架构 + 设计笔记
```

## 常见问题

**为什么叫 "poorguy"？**
因为那些 token 总得有人买单，而那个人是你。

**会损害代码质量吗？**
不会。它压缩的是发给你的散文，绝不碰代码、报错、或要改的那几行。风险高、对顺序敏感的步骤会用完整句子。

**Claude Code 还是 Codex？**
都行。同一个大脑；只有度量适配器和 hook 接口不同。

**它会记住我仓库里那个奇怪的 build 命令吗？**
第一次之后就会。这正是记忆层存在的全部意义。

**benchmark 在哪？**
没有，也绝不会有假的。自己跑一次 A/B，去看你的账单页——那个数字比任何 README 能印的都权威。

**我必须装 CodeGraph / GitNexus / graphify 吗？**
不必。没有它们，poorguy 回退到严格 `rg` 和行范围读取，「写」和「记忆」两个轴照样帮你。装上一个，「读」这个轴才会锋利。

## License

[MIT](LICENSE)。能用的最短许可证。

## Star History

<a href="https://www.star-history.com/#GitDzreal93/poorguy-token&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=GitDzreal93/poorguy-token&type=Date&theme=dark">
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=GitDzreal93/poorguy-token&type=Date">
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=GitDzreal93/poorguy-token&type=Date">
 </picture>
</a>
