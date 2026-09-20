[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

# grill-jev

**Jev 负责判断，Agent 负责推理，用户负责最终决定。**

`grill-jev` 是一个可移植的 Agent Skill，用于在规划和 Grill 工作流中评估候选方案。

它会把一个决策转化为结构化的 Jev 评估结果：

```text
问题 + 候选方案
      ↓
   grill-jev
      ↓
     Jev
      ↓
Choice + Score + 约束检查
      ↓
Agent 解释取舍
      ↓
用户做出最终决定
```

## 功能

`grill-jev` 可以：

- 评估多个候选方案；
- 从多个相关维度比较不同方案；
- 检查硬性约束；
- 检查当前候选方案是否可能遗漏重要选项；
- 将 Jev 的判断与 Agent 自己的建议分开；
- 与 `grill-with-docs` 或其他自定义 Agent Skills 搭配使用。

它的设计目标是兼容 Pi、Codex、Claude Code 以及其他支持 Agent Skills 的工具。

## 安装

安装 TypeSafe SDK：

```bash
python -m pip install typesafe-sdk
```

设置 TypeSafe API Key：

```bash
export TYPESAFE_API_KEY='your-api-key'
```

然后将 `skills/grill-jev` 目录安装或复制到你的 Agent Skills 目录中。

## 使用方式

准备两份资料：

- `DecisionState`：描述当前目标、约束、已确定的决策和候选方案；
- `EvaluationPlan`：描述需要从哪些维度评估这些候选方案。

仓库中的 `examples/` 目录提供了示例。

先进行 dry-run：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json \
  --dry-run
```

进行真实 Jev 评估：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json
```

## 与 grill-with-docs 搭配

常见流程：

```text
grill-with-docs
  → 产生问题和候选方案
  → grill-jev 评估这些方案
  → Agent 解释评估结果
  → 用户做出选择
  → grill-with-docs 继续后续流程
```

## License

MIT
