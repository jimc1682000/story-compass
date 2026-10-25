# 連線指引：自己的知識地圖倉庫（Git）

| 項目 | 狀態 |
|---|---|
| 建議結構 | 已定義（本檔） |
| 範本 | `templates/` |
| 自動建立倉庫 | **未實作**；請自己建立 |

## 建議結構（沿用擁有者倉庫的慣例，已去除個人資料）

```
<your-repo>/
  README.md
  schema.md            狀態、欄位、去重規則（可從 skill/references 複製）
  catalog/             擁有清單（平台同步＋手動紙本）；同步產生的分片勿手改
    index.yaml         總數、來源、最後同步時間（範本 templates/catalog-index.yaml）
    print.json         紙本，手動維護，不被同步覆寫
    excluded-previews.json  被排除的預覽／試讀本清單
    history/           每週快照
  books/               只有需要註解（概念、拒絕理由、紙本細節）的作品才寫卡（範本 templates/work-card.yaml）
  map/
    paths.yaml         閱讀路線（真相來源）；新路線一律 pending（範本 templates/paths.yaml）
    nodes.yaml         概念節點（只從讀過的作品抽）
    OVERVIEW.md        路線總覽（paths.yaml 的投影，腳本重產骨架）
  logs/
    reading-ratings.yaml  讀後感 0–5（參考資料，不是地圖分）
  reading-lists/       書單；開頭先寫它回答哪些人生問題（範本 templates/reading-list.md）
```

怎麼養這些檔（薄對帳、深更新、總覽投影、作品卡觸發）見 `map-maintenance.md`。

## 原則

- 建議設為**私人倉庫**；擁有清單、閱讀狀態都是個人資料。
- 不放書檔、整頁掃描、憑證。
- 敘脈者對倉庫的改動用**分支＋合併請求**提出，由你合併；不直接改主分支（建議，視你的環境而定）。
- 不要為擁有清單中每一本都產生空白書卡。

## 敘脈者需要的權限

讀取倉庫內容；若要讓它提出更新，再給建立分支與合併請求的權限。不需要刪除或管理權限。
