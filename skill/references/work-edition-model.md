# 作品、版本、載體與平台（schema_version 2）

本輪只定義分享套件的資料規範、合成範例與測試；不遷移私人書庫，也沒有平台 adapter。

| 層 | 主鍵與用途 | 個人狀態放哪裡 |
|---|---|---|
| 作品 | `id`；`media` 為 book / manga / anime / film / tv | `summary` 只由版本彙整，不可當狀態真相來源 |
| 版本 | `editions[].id`，在同作品內唯一；譯本、修訂版、剪輯版等 | `personal.progress` 與 `personal.intent` 各自保存 |
| 載體 | `personal.holdings[].carrier`：ebook / print / audio / streaming / disc / digital / other | 只表示取得形式，不替代作品類型或閱讀進度 |
| 平台 | `personal.holdings[].platform`；如某書店、串流平台、manual | 每個版本＋載體＋平台各自記 `ownership` 及來源時間 |

改編另建作品卡，用 `adaptation_of` 指向原作 `id`；不是把動畫當成小說的一個 edition。不同譯本仍在同一作品下。看完改編不代表原作已讀。

## 版本內的個人欄位

- `progress.state`：unknown / not_started / in_progress / paused / dropped / completed。已擁有不會把它改為 completed；拒買也不會抹掉進度。
- `progress.seasons[]`：連續作品各季獨立 `{number, state, last_completed_episode, partial_episode, last_viewed_at}`；partial_episode 是 `{episode, position_seconds}`。不能讓一季 completed 蓋掉另一季 paused。版本總進度只作彙整或使用者明確的全版本判斷；重看 run 也可有獨立 seasons。
- `progress.last_completed`：最後完整看完的 `{season, episode}`；單本書／電影可留 null。
- `progress.partial`：正在看但未看完的 `{season, episode, position_seconds}`；時間點選填，不算已完整看完。
- `progress.last_viewed_at`：只有來源確知的實際觀看日期才記；不能拿同步／觀察時間代替。
- `progress.completions[]`：完成歷史，每筆含 `run_id`、`scope`（whole / season / episode）、可選 season / episode、`event_at`（可未知）、`source`、`observed_at`。
- `progress.revisits[]`：重讀／重看另記 `{run_id, state, last_completed, partial, observations}`，不清空歷史 completions。
- `intent.purchase`：unknown / want / declined / undecided；declined 必填 `reject_reason`。它是購買意願，不是讀看進度。
- `intent.worth_owning`、`worth_rereading`：true / false / null，與是否讀過或持有分開。
- `holdings[]`：每筆 `{carrier, platform, ownership, preview, source, observed_at}`。ownership 為 unknown / owned / borrowed / not_owned；預覽不算持有。不同平台的持有不互相覆蓋。紙本（`carrier: print`）可另填 `shelf`（實體位置）、`loaned_to`（借出對象，空＝在自己手上）、`loaned_at`（`YYYY-MM-DD`）、`condition`（new / fine / good / fair / poor / unknown）；電子書與有聲書不填這些欄位。
- `observations[]`：欄位觀察紀錄，格式見 [狀態與衝突規則](status-mapping.md)。保留採用與未採用的來源，不只留最後一個值。

所有 null 都是未知，不是 false、沒買、沒看或刪除。空陣列也不代表個人從未接觸該領域。

作品層可選 `notes_url`：指向你筆記系統裡對應筆記的 URL 或相對路徑；作品卡不貼筆記全文，筆記系統不存持有清單。

## 身分與去重

1. 非空 ISBN（僅有效 ISBN-13）可辨識書籍版本；ISBN 不是作品主鍵。
2. 優先用非空作品 `id`。兩個已知且不同的 id 不因同名而合併；缺 id 才以非空正規化書名＋創作者比對。兩邊缺 id **不算相同**；只有同名、缺創作者也不足以判同一作品。
3. 版本用非空 edition id 或明確 label＋translator；不可把兩個空版本當相同。持有比對還要分載體、平台。
4. 再做有具體依據的語意重疊。只命中作品、不命中版本，評估換版本的增益；改編只標相關作品並比較剩餘增益，不套用原作的已讀狀態。
5. 未讀持有可把行動改為「先讀書庫」，不能因此虛降增益分數。館藏可借閱與個人持有也是不同資料。

`episode_catalog` 包含 verified、source、observed_at、positions；只有來源與查核時間都已知才能 verified: true，positions 是明確的觀看順序，不是自行推算。

## 紙本入庫

紙本由人手動維護，不被任何平台同步覆寫；同一作品的紙本與電子版落在同一張作品卡、同一個版本（ISBN 不同時仍同作品，用 holdings 分載體）。

1. 掃或手打 ISBN-13，從公開書目補 metadata；不發明 ISBN。
2. 去重：先查 ISBN／書名是否已在目錄或作品卡；已有電子版就在同一版本加一筆 `carrier: print` 的 holding。
3. 更新手動維護的紙本目錄檔（ISBN 陣列、選填 shelf／condition）。
4. 需要知識註解或紙本細節時才寫／改作品卡。
5. 不把書檔或整頁掃描放進倉庫。

## 單層 status 舊格式對照

既有地圖若用一本書一筆、單層 `status` 加 `platforms[]` 的舊格式，對照如下；本套件不遷移任何人的資料，對照只是讓兩種格式能互讀。

| 舊格式 | schema_version 2 |
|---|---|
| `status: read` | `editions[].personal.progress.state: completed`（加一筆 completions） |
| `status: owned_unread` | `progress.state: not_started` ＋ `holdings[].ownership: owned` |
| 平台標記「閱讀中」 | `progress.state: in_progress`；若人工已確認完成則不降級 |
| `status: wishlist` | `intent.purchase: want`；holdings 不加 owned |
| `status: borrowed` | `holdings[].ownership: borrowed`（讀過則 progress 另記 completed） |
| `status: dropped` | `progress.state: dropped` |
| `status: rejected` ＋ `reject_reason` | `intent.purchase: declined` ＋ `intent.reject_reason` |
| `worth_owning` | `intent.worth_owning` |
| `platforms[].{name, owned}` | 每個平台一筆 `holdings[].{platform, carrier, ownership}` |
| `translator`／`edition` 寫在書卡 notes | `editions[].translator`／`editions[].label` |
| `isbn` 陣列（書卡）；目錄只收通過檢查碼的 ISBN-13，專有編號另存 | `editions[].isbn` 只收有效 ISBN-13；平台專有 id 與產品 id 另存在 holdings 或目錄分片，不混入 isbn |
| 平台同步 merge 保留既有 ISBN／專有 id | 同步只補不刪：既有 isbn、專有 id、產品 id 保留，除非重新查證有更新 |

舊格式的單層 status 無法表達「同作品兩個譯本各自的進度」，這正是 v2 分版本的原因；對照時以版本為單位重建，不要把整本的 status 套到每個版本。

完整套件另附空白作品卡、路線檔、書單與目錄索引範本及全虛構範例；只安裝 skill 時，本文件已包含必要欄位契約，不依賴外部範本。
