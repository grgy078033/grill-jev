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
        "A": {"score": 3.7, "confidence": 0.76},
        "B": {"score": 3.0, "confidence": 0.70},
        "C": {"score": 4.5, "confidence": 0.84}
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
