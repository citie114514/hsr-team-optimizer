# 模型选择与上下文纪律

## 一、主力：DeepSeek V4 Flash

**默认就用它。** 本机可用的 DeepSeek V4 Flash 入口：

| provider | 模型 id | 视觉 | 上下文 | 说明 |
|---|---|---|---|---|
| `deepseek` | `deepseek-flash` | ✅ | 1M | 官方直连（DeepSeek V4.1 Flash），首选 |
| `workbuddy` | `cn:deepseek-v4.1-flash` | ✅ | 1M / 出 393K | 本地网关 |
| `workbuddy` | `cn:deepseek-v4-flash` | ❌ | 1M / 出 50K | 无视觉 |
| `qoder-cn` | `DeepSeek-Flash` | ✅ | 1M | 额度池 |
| `trae` | `DeepSeek-V4-Flash-Official` | ❌ | 1M | 额度池 |

选它的四个理由：

1. **1M 上下文** —— 机制表 + 名册 + 账本可以整段放进去，不用来回裁剪。
   崩铁配队需要同时看到「三队的角色」「每个角色的速度」「本期机制」，短上下文的模型会被迫丢信息。
2. **带视觉** —— 角色/遗器截图、战报帧可以直接喂，不必额外接一个视觉模型。
   但注意：**能喂 ≠ 该喂**（见第四节）。
3. **有思考档位** —— `low / high / xhigh`。采集整理时降档，速度演算时升档，一个模型走完全程。
4. **工具调用稳定** —— P0–P6 是多轮循环，模型要能可靠地反复读写 `hsr-ledger.json`。

## 二、按阶段分工

| 阶段 | 模型 | 思考档位 | 备注 |
|---|---|---|---|
| P0 抓攻略 + 摘要 | `deepseek-flash` | `low` | 长输入短输出，不需要推理 |
| P1 名册结构化 | `deepseek-flash` | `low` | 结构化输出 |
| 战报帧 → 数值（OCR） | `deepseek-flash` | `low` | 只要数字，不要它解释画面 |
| P2 基线记账 | `deepseek-flash` | `low` | 纯记录 |
| P3 候选改动排序 | `deepseek-flash` | `high` | 需要权衡三队整体 |
| P4 收敛判断 | `deepseek-flash` | `high` | 判断增益是否在噪声内 |
| 速度阈值演算 | `deepseek-flash` | `xhigh` | 「6.6 速球能否让银狼 183.9→190.5 并多打一轮」 |
| P5 遗器目标量化 | `deepseek-flash` | `xhigh` | 要把副词条门槛换算成分数增量 |
| P6 复盘规范修正 | `deepseek-flash` | `xhigh` | 把「为什么这次判断错了」抽象成规则 |

**一个模型 + 调档位**，比「多个模型来回切」更省事，也不会出现模型之间对同一份数据的理解不一致。

## 三、什么时候升级

只有三种情况值得升级到 **DeepSeek V4 Pro**（`deepseek-v4-pro`）或其它强推理模型：

1. **速度阈值演算连续两轮算错**。这类题是纯数学，flash 档偶尔会在多角色速度排序上翻车。
2. **两个候选改动之间反复摇摆**，需要一次性的全局裁决。
3. **配队收敛但分数仍差得多**，需要重新审视机制理解是否错了。

升级时的铁律：**只喂结构化表格，不喂原始素材**。

```bash
pi --provider deepseek --model deepseek-v4-pro --print "<把 P0 机制表 + P1 名册表 + 账本贴进来>"
```

## 四、上下文纪律（比换模型重要得多）

崩铁配队这个任务的上下文膨胀得极快：三队 × 4 人 × 遗器 × 每轮分数。
一旦每轮都重贴整份名册，第 30 轮时的输入会是第 1 轮的几十倍。

**三条纪律：**

1. **落盘**。P0 的机制表存 `hsr-intel.md`，P1 的名册存 `hsr-roster.md`，
   P6 的规范存 `hsr-review-spec.md`。后续每轮只引用文件名 + 变化量。
2. **像素不进推理层**。战报帧先用视觉模型转成
   「行动轴 / 剩余轮次 / 关键伤害数字」的小表格，再把表格交给推理。
   `deepseek-flash` 能看图，但**不要让同一段视频反复过模型**。
3. **账本独立于对话**。用 `scripts/ledger.py` 维护 `hsr-ledger.json`，
   需要历史时读文件，不要靠对话记忆。这也是 P6 复盘规范能跨期复用的前提。

**稳定前缀要放在最前面。** 把 system prompt + 本期机制表 + 名册表拼成一个长期不变的前缀，
每轮只在尾部追加「本轮改动 + 实测数据」。DeepSeek 的缓存读单价是输入价的 2%
（`deepseek-flash` 输入 0.3、缓存读 0.006），命中缓存后这部分几乎不花钱。
反过来，如果每轮都改动前缀（比如重排名册顺序、改标题措辞），缓存全部失效。

## 五、额度池作为补充

本机还有一批走订阅额度的 provider，边际成本为 0，适合跑量大的采集工作：

| provider | 可用模型（节选） |
|---|---|
| `qoder-cn` | Auto, GLM-5.3-Flash, GLM-5.3, DeepSeek-Flash, Qwen3.8-Max/Flash, Kimi-K3, MiniMax-M2.7 …（14 个） |
| `qoder` | Qwen3.8-Max, Qwen3.8-Flash |
| `trae` | Seed-Evolving, Seed-2.1-Pro/Turbo, step-5-preview, glm-5.3, deepseek-v4.1-flash, kimi-k3 …（15 个） |
| `trae-global` | 7 个 fallback 模型 |
| `workbuddy` | `cn:*` / `global:*` 全系 |
| `freellmapi` | `auto` |

用途：P0 抓攻略、批量摘要、格式转换这类「量大但不需要判断」的活。
查额度用 `/qoder-usage`、`/trae-usage`；查目录见 skill `pi-connect-model-catalog`。

## 六、单价参考

单位 **USD / 1M tokens**，格式 `输入 / 输出 / 缓存读`。
数据来自 `~/.pi/agent/models-store.json` 与 `pi --list-models`（2026-10-04）。

| 模型 | 视觉 | 输入 | 输出 | 缓存读 |
|---|---|---|---|---|
| `deepseek-flash` | ✅ | 0.3 | 1.2 | **0.006** |
| `deepseek-v4-pro` | ❌ | 1.32 | 3.96 | **0.044** |
| `xiaomi mimo-v2.6-flash` | ✅ | 0.14 | 0.28 | 0.0028 |
| `zai glm-5.3-flash` | ✅ | 0.15 | 0.5 | 0.03 |
| `zai glm-5.3` | ❌ | 1.4 | 4.4 | 0.26 |

`deepseek-flash` 不是最便宜的一档，但它是**能力/成本/视觉/上下文四者平衡最好的一档** ——
比它便宜的要么没视觉，要么上下文短，要么推理档位不够。

⚠️ `workbuddy` 网关的模型在本地 `models.json` 里没有 `cost` 字段，
按量计费未知 —— 当成「额度内免费」用，但**不要假设它有缓存折扣**。
