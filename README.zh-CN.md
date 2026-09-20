[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

# grill-jev

**Jev 负责判断，Agent 负责推理，用户负责最终决定。**

`grill-jev` 是一个可移植的 Agent Skill，用于在规划和 Grill 工作流中评估候选方案。

```text
问题 + 候选方案
      ↓
   grill-jev
      ↓
     Jev
      ↓
Choice + Scores + 约束检查
      ↓
Agent 解释取舍
      ↓
用户做出最终决定
```

## 功能

- 评估多个候选方案；
- 从多个相关维度比较不同方案；
- 检查硬性约束；
- 检查是否可能遗漏重要候选方案；
- 将 Jev 的判断与 Agent 自己的建议分开；
- 可与 `grill-with-docs` 或其他规划 Skill 搭配使用。

它的设计目标是兼容 Pi、Codex、Claude Code 以及其他支持 Agent Skills 的工具。

## 安装

```bash
python -m pip install -r requirements.txt
export TYPESAFE_API_KEY='your-api-key'
```

目前仓库锁定 `typesafe-sdk==0.7.0`，并使用 TypeSafe 的 `jev-latest` 模型别名。

安装时请保留仓库结构，因为 `SKILL.md` 会引用 `../../docs/`。Pi 用户可将仓库放在 `~/.agents/skills/grill-jev/`；Pi 会递归加载其中的 `skills/grill-jev/SKILL.md`。

### Windows PowerShell

如果已将 key 保存为 Windows 用户环境变量，请先加载到当前 shell，再启动 Pi：

```powershell
$env:TYPESAFE_API_KEY = [Environment]::GetEnvironmentVariable('TYPESAFE_API_KEY', 'User')
# 只确认是否存在，不显示密钥。
-not [string]::IsNullOrWhiteSpace($env:TYPESAFE_API_KEY)
pi
```

如果尚未设置，可避免将密钥写入命令历史：

```powershell
$secret = Read-Host 'TYPESAFE_API_KEY' -AsSecureString
$value = [System.Net.NetworkCredential]::new('', $secret).Password
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', $value, 'User')
$env:TYPESAFE_API_KEY = $value
Remove-Variable value, secret
```

Windows 用户环境变量以明文保存；不要输出或提交密钥。已运行的 Pi 不会取得后续环境变量变更；`/reload` 只重新加载资源，不会刷新进程环境。请从上述 shell 重新启动 Pi，或完整关闭并重开终端／IDE，让新 shell 继承已保存的 key。

## 使用方式

准备：

- `DecisionState`：当前目标、约束、已确定决策、事实和候选方案；
- `EvaluationPlan`：用于比较候选方案的评估维度。

`examples/` 中提供了示例。

Dry-run：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/product/decision-state.json \
  --plan examples/product/evaluation-plan.json \
  --dry-run
```

实际评估：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/product/decision-state.json \
  --plan examples/product/evaluation-plan.json
```

如果 Jev 无法使用，默认会返回 `status: "degraded"` 和 `agent_reasoning` 降级指示，而不是中断整个规划流程。

## Agent 交互规范：Pi、Codex、Claude Code

Agent 应读取 [SKILL.md](skills/grill-jev/SKILL.md)，并遵守[呈现规范](skills/grill-jev/references/presentation.md)。如果所在工具没有自动发现嵌套 skill，请提供该文件的完整路径，要求 agent 读取；保留仓库结构，让相对引用有效。

1. 依次呈现 **Jev 证据 → Agent 建议 → 用户决定**。
2. 当所在工具提供且允许使用交互选项工具时，优先使用；先确认实际参数格式，不可假设 Codex、Claude Code 接受 Pi 的 `ask_user_question` 参数。
3. 选项标题放方案 ID／名称与 Choice 概率；短描述放相同的一至两项分数及约束警告。**默认不使用长预览**，重要比较不得只藏在 hidden lines 或展开面板中。
4. 统一说明量尺、方向及遗漏方案信号；置信度、其余维度及全部警告放在提问前的比较中。如果界面放不下全部方案或必要信息，改用聊天中的精简表格，请用户回复方案 ID，不可默默删除候选方案。
5. 允许提出替代方案或暂缓；新方案标记为**尚未评估**。选择选项不代表授权实现或自动再次调用 Jev。

精简界面示意（不是特定工具的调用格式）：

```text
搜索／省力：0–4，越高越好。可能遗漏方案：74%。
A：Markdown｜Jev 77% — 搜索 1.56/4｜省力 2.96/4｜离线违规 7%
B：SQLite  ｜Jev 23% — 搜索 3.19/4｜省力 0.72/4｜离线违规 4%
C：云端    ｜Jev  0% — 搜索 3.41/4｜省力 3.78/4｜警告：离线违规 98%
先讨论替代方案 — 尚未评估，暂不再次调用 API。
```

数字仅为示意；agent 必须填入当次证据，不可复制示例数值。这是跨工具的内容规范，不保证每种终端都有相同组件或完全不截断。详见[集成说明](skills/grill-jev/references/integrations.md)。

### TypeSafe 官方评分规则

[Score](https://docs.typesafe.ai/primitives/score) 对单一维度使用 **2–10 个有顺序且能具体区分的等级**。N 级的分数范围为 **0 到 N−1**；只有五级时才是 0–4。分数是等级编号的概率加权平均，因此可以是小数。例如三级概率 `[0.0, 0.57, 0.43]` 的分数是 `1.43`，量尺为 0–2。

只使用能有意义区分的等级数，不为看似精确而增加级数。高分不一定更好，例如严重程度与易维护程度的方向不同。界面必须显示各维度原始范围及方向，不能一律写成满分 4 分或默默转成百分比。[Confidence](https://docs.typesafe.ai/confidence) 描述概率分布的集中程度，不是正确率；Choice 概率不是实际成功率；Noul 则是是／否条件的概率，不是等级分数。详见[评分标准设计](skills/grill-jev/references/evaluation-plan.md)。

## 输出示例

以下为模拟结果节选：

```json
{
  "status": "ok",
  "overall_choice": {
    "choice": "A",
    "confidence": 0.79,
    "probabilities": {"A": 0.58, "B": 0.11, "C": 0.31}
  },
  "dimensions": {
    "user-friction": {
      "options": {
        "A": {"score": 3.07, "confidence": 0.76},
        "B": {"score": 2.59, "confidence": 0.70},
        "C": {"score": 3.57, "confidence": 0.84}
      }
    }
  },
  "constraint_checks": {
    "offline": {
      "options": {
        "B": {
          "violation_probability": 0.94,
          "status": "violation"
        }
      }
    }
  },
  "missing_alternative": {
    "probability": 0.18,
    "status": "complete_enough"
  }
}
```

完整模拟输出：`examples/product/example-output.json`。

## 与 grill-with-docs 搭配

```text
grill-with-docs
  → 产生问题和候选方案
  → grill-jev 评估这些方案
  → Agent 解释评估结果
  → 用户做出选择
  → grill-with-docs 继续后续流程
```

## 文档

- [Schema 说明](docs/schema.md)
- [判定规则](docs/decision-policy.md)
- [grill-with-docs 数据契约](docs/grill-with-docs-contract.md)
- [兼容性](docs/compatibility.md)

## License

MIT
