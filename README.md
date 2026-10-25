# story-compass（敘脈者）

> 授權：**MIT**（見文末）。地圖側範本：[knowledge-map-template](https://github.com/jimc1682000/knowledge-map-template)。
> 分享套件 schema_version：`2`（不遷移或修改任何人的既有書庫）

## 這是什麼

story-compass（中文名「敘脈者」）是一個用**個人知識地圖的邊際增益**來判斷故事與知識作品的角色：電子書、紙本、漫畫、動畫、電影、影集。
它回答的不是「這部好不好」，而是「**對這位讀者／觀眾，現在**值不值得買、看、借，還是跳過」。

- 個人邊際增益不是口碑分，**與價格無關**；價格只改變行動建議。
- 三個入口皆可先用目標與少量已知作品起步，不強迫平台連線；完全缺個人依據時只做一般分析、不硬給個人增益分數。Skill／Bot 保留完整評分規範，純提示詞不必給數字。
- 查不到資料時直說「資料缺口」，**查不到 ≠ 沒買／沒看**。

## 與 knowledge-map 的關係

兩個東西互為表裡，分開也能用，一起用效果最好。

- **story-compass 是羅盤**：方法、判斷規則、skill、prompt。回答「這部作品對我**現在**值不值得買、看、借或跳過」。不含任何人的資料。
- **knowledge-map 是地圖**：你自己的資料。已讀／已看、持有、購買意願、進度、拒絕理由、概念節點、閱讀路線。回答「我已經走到哪裡」。不含判斷規則。

| 用法 | 得到什麼 | 缺什麼 |
|---|---|---|
| 只有羅盤（純提示詞） | 一次性評估，靠你當下給的目標與幾部已知作品 | 每次從零開始；不會記得你拒絕過什麼、書庫裡有什麼 |
| 只有地圖 | 一份結構整齊的書庫與路線清單 | 不會告訴你下一部該不該買；去重要自己做 |
| 羅盤讀地圖（建議） | 去重、先讀書庫、版本／譯本比較、沿用拒絕理由、回報資料覆蓋與缺口 | — |
| 羅盤回寫地圖（選用） | 新閱讀路線與概念節點以 pending 起草，等你確認 | 不自動啟用、不替你改平台狀態 |

資料格式契約（作品 → 版本 → 載體／平台；進度／意願／持有分欄）只寫一份，在 `skill/references/work-edition-model.md`；地圖遵循它，不另定規則。地圖側有自己的範本 repo [**knowledge-map-template**](https://github.com/jimc1682000/knowledge-map-template)：按「Use this template」生成你的私人地圖倉庫，裡面有目錄結構、總覽重產腳本與資料不變量測試。建議結構見 `guides/connect-github-repo.md`，怎麼養見 `guides/map-maintenance.md`，空白範本在 `templates/`。地圖是個人資料，建議放**私人倉庫**，取什麼名字都行。

## 三個入口

| 入口 | 給誰 | 需要什麼 | 從哪開始 |
|---|---|---|---|
| 1. 純提示詞 | 只想試一次評估的人 | 任一聊天模型＋作品、目標、少量已知作品（不知道可留空） | [`prompt.md`](prompt.md) |
| 2. 技能（Skill） | 已有支援 SKILL.md 的代理環境 | 只把 `skill/` 整個資料夾放進技能目錄，內含必要設定與邊界 | [`skill/SKILL.md`](skill/SKILL.md) |
| 3. Grok Bot 角色 | 想要長期使用、接書櫃與影視紀錄的人 | Grok Bot＋（選用）自己的 Git 倉庫 | [`guides/grok-bot-first-run.md`](guides/grok-bot-first-run.md) |

`prompt.md` 是獨立維護的短提示詞，直接修改，不由 Skill 產生，也不要求三個入口功能相同。貼上這一份即可評估閱讀／觀看增益、重複程度、值得讀看與否，必要時比較版本入口；不需其他檔案。

純提示詞不承擔館藏同步、長期狀態管理、已讀鎖定、排程或完整來源衝突處理。`skill/SKILL.md`、`skill/references/` 與 `ROLE.md` 繼續描述較完整的 Skill／Bot 用法。

安裝 Skill 不依賴上一層的 ROLE、templates 或純提示詞。`skill/references/settings.yaml` 與完整套件的 `templates/settings.yaml` 保持相同，測試核對兩份；完整套件的 YAML 範本採 JSON 相容語法，欄位規則見 references。

主動推薦／提醒只報 **>60**；使用者要求完整清單時所有分數與待查皆列出，低分不當推薦。指定單一作品仍照實回答。排程全數停用，時間／頻率／時區契約不代表已建立任務。

## 支援範圍與限制

規範、測試與真實整合分開寫；文件或 oracle 不等於實際 adapter 或模型驗證。

| 項目 | 狀態 |
|---|---|
| 純提示詞的一次性作品評估（書、漫畫、動畫、電影、影集） | 獨立、自足；`tests/check_prompt.py` 只做靜態檢查，模型輸出**未實測** |
| 書（電子書／紙本／有聲書）評估方法：A–F、0–100、F 預設上限 40、E 預設 55／索引例外 70 | 已定義（`skill/`、`skill/references/scoring-rubric.md`）；分數合理性**未由模型試評** |
| 漫畫、動畫、電影、影集的評估方法 | 已定義評估與影視三段輸出規範（`skill/references/cross-media.md`）；模型品質**未實測** |
| 作品／版本／載體／平台資料模型；進度／購買意願／持有分欄；紙本欄位；舊格式對照 | 已定義（`skill/references/work-edition-model.md`、`templates/work-card.yaml`）；不遷移任何人的書庫 |
| 按欄位處理來源衝突、完成保護、重看歷史、季／集進度 | 已定義（`skill/references/status-mapping.md`）；純函式 oracle 測試，沒有平台寫入或提醒 |
| 地圖養成：路線欄位契約、總覽投影、薄對帳／深更新節奏、書單格式、目錄索引 | 已定義（`guides/map-maintenance.md`、`templates/paths.yaml`、`templates/reading-list.md`、`templates/catalog-index.yaml`）；總覽重產腳本**未附** |
| 初次使用：目標與少量已知作品先試評；無個人依據只做一般分析 | 已定義（`templates/seed.yaml`、`guides/grok-bot-first-run.md`）；真實 Grok 流程**未實測** |
| 主動推薦 >60 與完整報告不漏低分 | Skill、ROLE、routines、測試一致 |
| 電子書平台書櫃同步（`data_sources.library_export`） | **本套件未附實作**，只有以一個平台為例的連線指引與規則（`guides/connect-kobo.md`） |
| 影視紀錄同步（`data_sources.watch_history_export`） | **本套件未附實作**，只有唯讀連線指引（`guides/connect-yamtrack.md`） |
| 其他平台（讀墨、Google Play 圖書、HyRead、串流平台等）同步 | **未實作**；可手動填資料 |
| 例行任務（特價、即將下架、精選、同步） | 只有**預設停用**的範本與啟用前契約（`guides/routines.md`）；沒有 scheduler |
| Grok Share Template | 只有準備指引（`guides/share-template-prep.md`）；未建立、未實測 |
| 隱私檢查 | `tools/privacy_check.py`：全檔 allowlist、全 UTF-8 文字、套件外報告；私人樣式與書庫交叉比對需另外提供輸入 |
| 驗收測試 | fixtures 與 `tests/test_contracts.py` 測**確定性 oracle、資料與封裝契約、隱私檢查器**；assessment 為合成輸入，模型實際評分品質**未實測** |

## 檔案地圖

```
story-compass/
  README.md              本檔
  ROLE.md                角色定義：職責、語氣、界線
  prompt.md              獨立短提示詞（直接維護）
  skill/SKILL.md         核心方法（唯一技能）
  skill/references/      評分、資料模型、衝突、跨媒體、資料覆蓋、設定與邊界（安裝自足）
  templates/             空白設定、手動 seed、作品卡、路線檔、書單、目錄索引、驗證紀錄與全虛構 examples
  guides/                連線指引、首次設定、地圖養成法、分享範本準備、選用例行任務
  tests/                 純提示詞靜態檢查＋Skill 確定性規則的合成範例與測試
  tools/privacy_check.py 公開前的隱私檢查
  ALLOWLIST.txt          允許公開的檔案清單
  .github/workflows/     CI：跑下面「維護」的四個命令
```

## 維護

```bash
python3 -B tests/check_prompt.py    # 純提示詞的自足性、長度與範圍靜態檢查（不改寫檔案）
python3 -B tests/run_tests.py     # fixtures 的確定性 oracle；逐案印到 stdout，--report 只能寫到 repo 外
python3 -B -m unittest discover -s tests -p 'test_*.py' -v  # 乾淨安裝、邊界、成對案例、資料及隱私反例
python3 -B tools/privacy_check.py  # 最後執行：通用隱私、allowlist、UTF-8 全文字與連結檢查
```

只依賴 Python 3.9+ 標準函式庫。用 `-B` 避免產生 bytecode；快取目錄內檔案也須通過 allowlist，不能當作交付包的忽略區。所有 UTF-8 文字（含 CSV、其他副檔名）都掃描，符號連結與非 UTF-8 檔拒絕。測試與隱私檢查的報告都只能寫到 repo 外，交付包內不留產物；每次的結果用 `templates/check-log.md` 記在套件外。私人樣式與私人書庫交叉比對需另提供輸入，不因通用掃描通過而視為已完成。

修改純提示詞時，直接編輯 `prompt.md` 並跑靜態檢查即可；不做完整 Skill 同步驗收。舊產生器已移除，仍可由 Git 歷史還原；還原執行會覆蓋獨立提示詞。靜態檢查不能證明模型實際輸出品質。

## 授權

**MIT**，整個 repo（文件、提示詞、技能、範本、程式）都適用，全文見 [`LICENSE`](LICENSE)。
