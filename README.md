# hsr-team-optimizer

用「**单变量实测迭代**」把《崩坏：星穹铁道》的深渊 / 虚构叙事 / 末日幻影打到满星，
并把有限的练度资源投到正确的部位。

一个 agent skill —— 适用于任何能执行 shell、读写文件、联网检索的 AI coding assistant
（pi / opencode / Claude Code / Codex / Cursor / WorkBuddy 等）。

---

## 它是怎么来的

B 站 `BV1Pte46BEST`《【崩铁】花3000让最强AI打深渊！GPT-6能满星吗？》里，
UP 主用前沿模型花了 3 天，把 4.5 虚构叙事星启模式从 **79,520 分**推到 **100,040 分满星**。

那 3 天里真正起作用的是四件事：

1. **单变量**：一次只改一件（换人 / 换遗器主词条 / 换光锥 / 调速度档位），改完实测
2. **量化**：记「战前速度 183.932→190.532」「固定动作伤害 +22.51%」，不记「感觉变强了」
3. **游戏内判据**：用行动轴 / 剩余轮次 / 行动值判断循环快慢，**不用视频时长**
4. **可验收的遗器目标**：部位 + 目标主词条 + 副词条门槛 + 量化意义，且明确标注「未合成」

本 skill 把这四件事固化成规则，并补上视频里没做的**上下文纪律** ——
战报录像和截图先由便宜的视觉模型转成小表格，推理层只看数字，不看像素。

完整拆解见 [`references/case-study.md`](references/case-study.md)。

---

## 推荐模型

主力用 **DeepSeek V4 Flash**。理由：

- **1M 上下文** —— 机制表 + 名册 + 账本可以整段放进去，不用来回裁剪
- **带视觉** —— 角色/遗器截图、战报帧可以直接喂，不需要额外接一个视觉模型
- **有思考档位** —— 采集时降档省上下文，速度演算时升档提质量
- **工具调用稳定** —— 适合跑 P0–P6 这种多轮循环

分工：

| 阶段 | 用哪个 |
|---|---|
| P0 抓攻略 / P1 名册结构化 / P2 基线 | DeepSeek V4 Flash（thinking 降档） |
| P3 候选改动排序 / P4 收敛判断 | DeepSeek V4 Flash（thinking 中档） |
| 战报帧 → 数值（OCR） | DeepSeek V4 Flash 或更便宜的视觉模型 |
| 速度阈值演算 / 遗器量化 / 复盘规范 | DeepSeek V4 Flash（thinking 高档） |
| 卡住时的单次裁决 | 升级到 DeepSeek V4 Pro，只喂结构化表格 |

路由细节见 [`references/model-routing.md`](references/model-routing.md)。

---

## 内容

| 文件 | 作用 |
|---|---|
| `SKILL.md` | 主 skill：七条硬规则 + 七阶段循环 + 输出契约 |
| `references/workflow.md` | 每阶段的输入/动作/产出/判断口径/常见坑 |
| `references/prompt-templates.md` | **可直接复制的提示词**（整期 / 单轮复盘 / 遗器定向） |
| `references/model-routing.md` | 主力模型选型（DeepSeek V4 Flash）+ 分阶段分工 + 上下文纪律 |
| `references/case-study.md` | 视频案例完整拆解（含账单、弯路、收益曲线） |
| `templates/` | 迭代账本、遗器购物清单模板 |
| `scripts/ledger.py` | 零依赖账本 CLI，自动算增量与百分比 |

---

## 快速开始

```bash
# 1. 开局建账本
python scripts/ledger.py init --mode "虚构叙事 立界开篇" \
    --nodes 节点一,节点二,节点三 --star-line 100000

# 2. 记基线（自动战斗打 2-3 次取最高）
python scripts/ledger.py add --baseline --scores 节点一=28000,节点二=27040,节点三=24480

# 3. 每轮只改一件事，实测后记账
python scripts/ledger.py add --change "银狼原头 → 6.6速新头" \
    --hypothesis "战前速度 183.9→190.5，固定动作伤害 +1.7%" \
    --scores 节点一=28000,节点二=29640,节点三=24480 \
    --verdict 部分成立 --note "伤害涨了，但轮次没多"

# 4. 看账本
python scripts/ledger.py show
```

然后把 [`references/prompt-templates.md`](references/prompt-templates.md) 里的主提示词
交给你的 agent，把 `hsr-ledger.json` 当作共享状态。

---

## 核心规则（不可协商）

1. 每一轮只改一件事
2. 无实测不结论；未验证的写【未验证假设】
3. 判据用行动轴 / 剩余轮次 / 战技点 / 固定动作伤害 —— **不用视频时长和观感**
4. 遗器目标必须可验收，且标注「未合成」
5. 先确认库存，不建议用户没有的角色
6. 每轮记一行账
7. 版本相关内容现场抓取，本仓库里的数值只是案例样本

---

## 免责

本仓库不含任何游戏资源，不修改游戏客户端，不提供自动化脚本。
它只规范「人 + AI 怎么一起做决策」，所有实测仍由玩家在游戏内完成。

`references/` 里出现的角色名、分数、门槛均来自上述视频案例（4.5 版本），
**不是当前版本的事实**，请勿直接套用。

## License

MIT
