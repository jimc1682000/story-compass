# 地圖養成法（map maintenance）

這份文件管的是**你自己的知識地圖怎麼養**：閱讀路線怎麼開、怎麼更新、總覽怎麼重產、什麼時候該寫書卡。評一部作品值不值得買、看、借（A–F／0–100）見 `skill/SKILL.md`；本文不重複評分規則。

story-compass 只帶規則，不帶資料；地圖倉庫只帶資料，不帶規則。建議倉庫結構見 `connect-github-repo.md`，範本在 `../templates/`。

## 檔案分工

| 檔 | 角色 | 誰改 |
|---|---|---|
| `map/paths.yaml`（範本 `../templates/paths.yaml`） | 路線意圖真相（status、next、position） | 人／助手依規則；薄對帳只准有限自動寫入 |
| `map/OVERVIEW.md` | 投影（狀態表＋拓樸骨架＋人話區塊） | 腳本重產骨架；助手只填標記區塊並做對齊檢查 |
| `catalog/`（索引範本 `../templates/catalog-index.yaml`） | 持有／已讀事實 | 同步工具或手動維護；同步產生的分片勿手改 |
| `logs/reading-ratings.yaml` | 個人讀後感 0–5（參考資料，不是地圖分） | 讀完時寫入 |
| `books/*.yaml`（範本 `../templates/work-card.yaml`） | 少數有註解的作品卡 | 僅在觸發時提議或寫入 |
| `map/nodes.yaml` | 概念節點 | 只從已有作品卡的 concepts 抽取 |
| `reading-lists/*.md`（範本 `../templates/reading-list.md`） | 回答某幾個生活問題的書單 | 開新路線時一起起草 |

## 雙軌（不可混成一個分數）

| 軌 | 問什麼 | 寫在哪 |
|---|---|---|
| 地圖軌 | 這部作品讓地圖多出哪些節點／連線？ | A–F 與 0–100，寫在對話或作品卡 |
| 娛樂／素養軌 | 文筆、節奏、重讀、類型樂趣？ | 讀後感 0–5，寫在 `logs/reading-ratings.yaml` |

讀後感可以決定「可讀／可借／可收藏」，**不得**抬地圖分，也不自動變成 Buy。地圖分不要寫進讀後感檔冒充讀後感。

## 路線模型

路線＝依賴／拓樸：先讀什麼，後面的才讀得懂。它不是書櫃分類，一部作品可以同時出現在兩條路線的 `cross_links`。

### 三層

| `layer` | 意思 |
|---|---|
| `os` | 底層思考工具；其他路線都會映射回來 |
| `path` | 一般主題路線 |
| `entertainment` | 娛樂／素養軌的路線；只記讀後感，不給地圖分 |

### 欄位契約

| 欄位 | 意思 |
|---|---|
| `id`、`title` | 穩定 id（改標題不改 id）；重整拓樸時保留 id |
| `track` | `map` 或 `entertainment` |
| `status` | 見下表 |
| `since`／`until` | 進入目前狀態的日期；結束日選填 |
| `position` | 一句話：這條線現在走到哪 |
| `backbone` | 骨幹作品 id；沒讀這幾部，這條線不算開始 |
| `reading_order`／`reading_order_supplement` | 建議讀序與補充讀序；分開「分數」與「讀序」 |
| `reading_now`／`next_owned`／`wishlist_later` | 正在讀、已擁有未讀的下一部、以後再買 |
| `cross_links` | 關聯路線 id |
| `parent`／`merged_into` | 子線掛父線；併線時寫目的地並把 status 改 `merged` |
| `optional_pair` | 可對讀但非必要的作品 |
| `unskippable` | 不能跳過的作品 id |
| `surgical_buy` | 只為填一個缺口才買的作品 |
| `paused_ok` | 這條線可以長期暫停而不算失敗 |

### 狀態

| 值 | 意思 |
|---|---|
| `active` | 當季注意力主軌 |
| `pending` | 已起草的讀線；**等你說開始讀**才翻成 `active` |
| `queued` | 意向在、尚未當季主攻 |
| `paused` | 暫停 |
| `demoted` | 降噪／高重疊 |
| `merged` | 併入他線（寫 `merged_into`） |
| `archived` | 封存 |

`pending` 仍要出現在總覽的狀態表與拓樸骨架裡。子線可掛 `parent`；不要擅自改父線的 `next_owned`。

### 規則

- `rules.max_active_paths_soft`：同時 `active` 的軟上限，值放設定檔的 `map.max_active_paths_soft`；超過時先建議併線或降級，不硬擋。
- `rules.prefer_merge_over_new`：能併進既有路線就不開新線。
- `rules.diagrams_are_projections`：任何圖都是投影；要改拓樸就改路線檔再重產。

### 掛路徑

每次評估一部作品都要說它服務哪一條路線（或哪幾條的交叉）。沒有合適路線時，提議一條 `pending` 新線並附書單草稿，等你確認；不自動開 `active`。

## 總覽是投影

沒有「一鍵完美投影」，採混合契約：

1. **腳本**重產：路線狀態表、拓樸骨架（依 status／layer／title）。投影內容未變就不寫檔、不更新時間戳。
2. **助手**只填標記區塊（例如當季重點、備註），並做**對齊檢查**：路線檔 ↔ 表／骨架 ↔ 目錄進度。
3. **禁止**手改表或骨架充當真相。
4. 助手**不可**在對齊時默默改路線 status；升級／降級走下面的「建議」流程。

本套件不附重產腳本；自備時至少測這幾個不變量：路線 status 在上表之內、id 唯一、`merged_into`／`parent` 指向存在的路線、`active` 數量不超過軟上限、總覽與腳本輸出一致。

## 節奏

### A. 薄對帳（跟著目錄同步）

只在目錄同步**成功**後執行。

**可自動寫入**

1. 新完成／狀態變更命中某路線的 `reading_now`／`next_owned` → 搬作品 id（移出 next、更新進度）。
2. 刪掉「已完成但仍留在 next」的過期條目。
3. 重產總覽骨架（保留標記區塊）。

**不可自動寫入，只能建議**

- 路線 `demoted`／`paused`
- `queued` → `active`；`pending` → `active` 同樣只在你說開始讀之後才改

建議要**多信號**才提出（例如該線 next／reading 清空且長期無進度；或 queued 線已買未讀堆積且你近期連續點名）。單次讀完一部不夠。

**同步失敗**：跳過薄對帳，只報失敗；不要改薄對帳規則本身。

**通知**：有寫入或有建議才短訊；同步失敗只報失敗；否則維持「同步成功就安靜」。

### B. 深更新（讀完／你點名）

1. 更新相關路線進度（移出 reading／next，必要時改 `position` 一句話）。
2. 提出 1–3 部下一部候選，優先已買未讀。
3. 重產總覽。
4. 記 **0–5 讀後感**到 `logs/reading-ratings.yaml`（個人體感，不是地圖分）。

### C. 作品卡／節點觸發

預設不寫。

- 讀後感 **≥ 4** → **提議**開／更新作品卡（仍先問你）。
- 套書系列讀完，或路線段落完成 → 提醒沉澱（訊息要標明是「套書」還是「路線段落」）。
- 節點只從已有作品卡的 `concepts` 抽取；不憑空發明。

## 讀後感 log 格式

```yaml
# 個人讀後感 0–5，參考資料；不是地圖 A–F／0–100。
ratings:
  - title: 《虛構：海的邊界》
    score: 4
    date: 2026-01-01
    path_id: example-foundation   # 選填
    note: 一句話（可空）
```

## 與筆記系統分庫

地圖倉庫＝來源／擁有／路線證據；你的筆記系統＝可重用思想。用作品卡的 `notes_url`、ISBN、slug 或節點 id 橋接；地圖倉庫不存筆記全文，筆記系統不存持有清單。

## 舊格式對照

既有地圖若用單層 `status` 加 `platforms[]`，對照到 schema_version 2 的方式見 `../skill/references/work-edition-model.md` 的「單層 status 舊格式對照」。本套件不遷移任何人的現有資料。

## 助手檢查清單（摘要）

1. 同步目錄。失敗 → 只報失敗、跳過薄對帳；結束。
2. 薄對帳路線（只准搬作品 id／清過期 next）。
3. 重產總覽（腳本須認識 `pending`）。
4. 多信號才產生 demote／升 active **建議**（`pending` → `active` 等你說開始讀）。
5. 有寫入或建議才短訊；否則安靜。
