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

目前 Repository 鎖定 `typesafe-sdk==0.7.0`，並使用 TypeSafe 的 `jev-latest` 模型別名。

安裝時請保留 Repository 結構，因為 `SKILL.md` 會引用 `../../docs/`。Pi 使用者可將 Repository 放在 `~/.agents/skills/grill-jev/`；Pi 會遞迴載入其中的 `skills/grill-jev/SKILL.md`。

### Windows PowerShell

若已將 key 儲存為 Windows 使用者環境變數，請先載入目前 shell，再啟動 Pi：

```powershell
$env:TYPESAFE_API_KEY = [Environment]::GetEnvironmentVariable('TYPESAFE_API_KEY', 'User')
# 只確認是否存在，不顯示密鑰。
-not [string]::IsNullOrWhiteSpace($env:TYPESAFE_API_KEY)
pi
```

若尚未設定，可避免將密鑰寫入指令歷史：

```powershell
$secret = Read-Host 'TYPESAFE_API_KEY' -AsSecureString
$value = [System.Net.NetworkCredential]::new('', $secret).Password
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', $value, 'User')
$env:TYPESAFE_API_KEY = $value
Remove-Variable value, secret
```

Windows 使用者環境變數以明文保存；不要輸出或提交密鑰。已執行的 Pi 不會取得後續環境變數變更；`/reload` 只重載資源，不會刷新程序環境。請從上述 shell 重新啟動 Pi，或完整關閉並重開終端機／IDE，讓新 shell 繼承已儲存的 key。

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

## Agent 互動規範：Pi、Codex、Claude Code

Agent 應讀取 [SKILL.md](skills/grill-jev/SKILL.md)，並遵守[呈現規範](skills/grill-jev/references/presentation.md)。若所在工具沒有自動發現巢狀 skill，請提供該檔案的完整路徑，要求 agent 讀取；保留 Repository 結構，讓相對引用有效。

1. 依序呈現 **Jev 證據 → Agent 建議 → 使用者決定**。
2. 當所在工具提供且允許使用互動選項工具時，優先使用；先確認實際參數格式，不可假設 Codex、Claude Code 接受 Pi 的 `ask_user_question` 參數。
3. 選項標題放方案 ID／名稱與 Choice 機率；短說明放相同的一至兩項分數及限制警告。**預設不使用長預覽**，重要比較不得只藏在 hidden lines 或展開面板中。
4. 統一說明量尺、方向及遺漏方案訊號；信心、其餘維度及全部警告放在提問前的比較中。若介面放不下全部方案或必要資訊，改用聊天中的精簡表格，請使用者回覆方案 ID，不可默默刪除候選方案。
5. 允許提出替代方案或暫緩；新方案標示為**尚未評估**。點選選項不代表授權實作或自動再次呼叫 Jev。

精簡介面示意（不是特定工具的呼叫格式）：

```text
搜尋／省力：0–4，越高越好。可能遺漏方案：74%。
A：Markdown｜Jev 77% — 搜尋 1.56/4｜省力 2.96/4｜離線違規 7%
B：SQLite  ｜Jev 23% — 搜尋 3.19/4｜省力 0.72/4｜離線違規 4%
C：雲端    ｜Jev  0% — 搜尋 3.41/4｜省力 3.78/4｜警告：離線違規 98%
先討論替代方案 — 尚未評估，暫不再次呼叫 API。
```

數字僅為示意；agent 必須填入當次證據，不可複製範例數值。這是跨工具的內容規範，不保證每種終端都有相同元件或完全不截斷。詳見[整合說明](skills/grill-jev/references/integrations.md)。

### TypeSafe 官方評分規則

[Score](https://docs.typesafe.ai/primitives/score) 對單一維度使用 **2–10 個有順序且能具體區分的等級**。N 級的分數範圍為 **0 到 N−1**；只有五級時才是 0–4。分數是等級編號的機率加權平均，因此可以是小數。例如三級機率 `[0.0, 0.57, 0.43]` 的分數是 `1.43`，量尺為 0–2。

只使用能有意義區分的等級數，不為看似精確而增加級數。高分不一定較好，例如嚴重程度與易維護程度的方向不同。介面必須顯示各維度原始範圍及方向，不能一律寫成滿分 4 分或默默轉成百分比。[Confidence](https://docs.typesafe.ai/confidence) 描述機率分布的集中程度，不是正確率；Choice 機率不是實際成功率；Noul 則是是／否條件的機率，不是等級分數。詳見[評分規準設計](skills/grill-jev/references/evaluation-plan.md)。

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
