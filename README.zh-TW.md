[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

# grill-jev

**Jev 負責判斷，Agent 負責推理，使用者負責最終決定。**

`grill-jev` 是一個可攜式的 Agent Skill，用於在規劃與 Grill 工作流程中評估候選方案。

```text
問題 + 候選方案
      ↓
   grill-jev
      ↓
     Jev
      ↓
Choice + Scores + 約束檢查
      ↓
Agent 解釋取捨
      ↓
使用者做出最終決定
```

## 功能

- 評估多個候選方案；
- 從多個相關維度比較不同方案；
- 檢查硬性約束；
- 檢查是否可能遺漏重要候選方案；
- 將 Jev 的判斷與 Agent 自己的建議分開；
- 可與 `grill-with-docs` 或其他規劃 Skill 搭配使用。

它的設計目標是相容 Pi、Codex、Claude Code，以及其他支援 Agent Skills 的工具。

## 安裝

```bash
python -m pip install -r requirements.txt
export TYPESAFE_API_KEY='your-api-key'
```

目前 Repository 鎖定 `typesafe-sdk==0.6.0`，並使用 TypeSafe 的 `jev-latest` 模型別名。

接著將 `skills/grill-jev` 安裝或複製到你的 Agent Skills 目錄中。

## 使用方式

準備：

- `DecisionState`：目前目標、限制、已確定決策、事實與候選方案；
- `EvaluationPlan`：用來比較候選方案的評估維度。

`examples/` 中提供了範例。

Dry-run：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/product/decision-state.json \
  --plan examples/product/evaluation-plan.json \
  --dry-run
```

實際評估：

```bash
python skills/grill-jev/scripts/grill_jev.py \
  --state examples/product/decision-state.json \
  --plan examples/product/evaluation-plan.json
```

如果 Jev 無法使用，預設會回傳 `status: "degraded"` 與 `agent_reasoning` 降級指示，而不是中斷整個規劃流程。

## 輸出範例

以下為模擬結果節選：

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

完整模擬輸出：`examples/product/example-output.json`。

## 與 grill-with-docs 搭配

```text
grill-with-docs
  → 產生問題與候選方案
  → grill-jev 評估這些方案
  → Agent 解釋評估結果
  → 使用者做出選擇
  → grill-with-docs 繼續後續流程
```

## 文件

- [Schema 說明](docs/schema.md)
- [判定規則](docs/decision-policy.md)
- [grill-with-docs 資料契約](docs/grill-with-docs-contract.md)
- [相容性](docs/compatibility.md)

## License

MIT
