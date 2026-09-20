[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

# grill-jev

**Jev 負責判斷，Agent 負責推理，使用者負責最終決定。**

`grill-jev` 是一個可攜式的 Agent Skill，用於在規劃與 Grill 工作流程中評估候選方案。

它會把一個決策轉換成結構化的 Jev 評估結果：

```text
問題 + 候選方案
      ↓
   grill-jev
      ↓
     Jev
      ↓
Choice + Score + 約束檢查
      ↓
Agent 解釋取捨
      ↓
使用者做出最終決定
```

## 功能

`grill-jev` 可以：

- 評估多個候選方案；
- 從多個相關維度比較不同方案；
- 檢查硬性約束；
- 檢查目前候選方案是否可能遺漏重要選項；
- 將 Jev 的判斷與 Agent 自己的建議分開；
- 與 `grill-with-docs` 或其他自訂 Agent Skills 搭配使用。

它的設計目標是相容 Pi、Codex、Claude Code，以及其他支援 Agent Skills 的工具。

## 安裝

安裝 TypeSafe SDK：

```bash
python -m pip install typesafe-sdk
```

設定 TypeSafe API Key：

```bash
export TYPESAFE_API_KEY='your-api-key'
```

接著將 `skills/grill-jev` 目錄安裝或複製到你的 Agent Skills 目錄中。

## 使用方式

準備兩份資料：

- `DecisionState`：描述目前目標、限制、已確定的決策與候選方案；
- `EvaluationPlan`：描述要從哪些維度評估這些候選方案。

Repository 中的 `examples/` 目錄提供了範例。

先進行 dry-run：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json \
  --dry-run
```

進行實際 Jev 評估：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/game-design/decision-state.json \
  --plan examples/game-design/evaluation-plan.json
```

## 與 grill-with-docs 搭配

常見流程：

```text
grill-with-docs
  → 產生問題與候選方案
  → grill-jev 評估這些方案
  → Agent 解釋評估結果
  → 使用者做出選擇
  → grill-with-docs 繼續後續流程
```

## License

MIT
