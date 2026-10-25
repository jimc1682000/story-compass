# 個人狀態與按欄位處理來源衝突

已定案。適用同一作品＋版本；進度另分首次／重看 run，持有另分載體＋平台。不同版本、run 或平台不是同一欄位的衝突，不跨範圍覆蓋。

## 觀察紀錄

每筆至少有 `field`、`value`、`source`、`observed_at`；`work_id` 與 `edition_id` 用來核對所屬版本。`source` 為 manual / manual_file / platform / inference。`explicit` 表示人工明確確認；`event_at` 是事件實際時間，未知就 null。`observed_at` 是得知／同步時間，必須含時區。修正錯誤時另記 `correction: true` 及理由。

進度觀察帶 `run_id`（首次為 initial）與 scope；季／集還帶 season／episode，以免整部與單季互相覆蓋。持有觀察帶 `carrier`、`platform`。完成 scope 要說清 whole / season / episode；完成一集或一季不等於全作品完成。版本內 `personal.observations` 保留所有候選值與來源，輸出採用值時同時保留該筆 provenance；不靜默覆蓋。

## 各欄位的採用規則

| 欄位 | 規則 |
|---|---|
| 進度／完成 | 人工明確完成不被平台低進度覆蓋；可靠完成紀錄保留。人工修正須明說原因，不刪歷史。重看進度寫新 run，不把首次完成降回 in_progress |
| 最後完整集數 | 同一 run 保留已確認的最遠完整位置；較低平台進度不倒退，人工明確修正除外。partial 另存，不能冒充完整位置 |
| 追看／暫停／棄追 | 人工明確選擇優先，平台的新狀態可作候選；單純久未更新不是 dropped。完成一季只更新該季／集範圍 |
| 持有 | 分載體／平台；正面持有證據只說該來源。同步缺漏／失敗不產生 not_owned、刪除或「沒買」。明確處分可記 not_owned，但不影響進度 |
| 購買意願、拒絕理由、收藏價值 | 人工決定優先；平台清單缺項不能取消想要或拒絕。是否持有不推出是否想買／值得收藏 |
| 最後觀看日期 | 只採來源給出的實際事件日期，保留原精度並取最新事件；只有日期就不補時間，只知道同步時間則保持未知 |

同一欄位一般先取人工明確確認，再取手動檔，再取實際平台證據；同級比較事件與觀察時間。這不是套用整筆紀錄的全域排序：完成保護、不同平台持有與事件日期限制優先適用。推論不得改寫已確認值。

資料不明時保留候選值與缺口；僅在**無法判斷且會影響推薦或既有紀錄**時問一個具體問題，否則維持未知或既有確認值。來源失敗不等於負面證據。

## 外部匯出欄位的示意對應

以下是規範示例，不是已實作或實測的 adapter；實際欄位需以使用者提供的匯出資料確認。

| 輸入示例 | 進度候選值 | 不能推論的事 |
|---|---|---|
| ReadyToRead / Planning | not_started | 已買、值得買、從未讀過其他版本 |
| Reading / In progress | in_progress | 首次完成需要被撤銷 |
| Finished / Completed | completed（確認 scope） | 同原作全部改編、全部季均完成 |
| Paused / Dropped | paused / dropped | 因舊快照而改掉較新的人工選擇 |
| 匯出缺項、同步失敗 | 不新增負面值 | not_owned、未讀、刪除 |

預覽不算擁有；外部封存／移除只反映平台狀態，不直接刪掉個人持有與完成歷史。較新的完讀日期只是重讀候選，不直接加次數；若有必要確認，保存決定避免重複問。

## 季、集與找回進度

- `progress.seasons[]` 各季分別記 state、最後完整集數與 partial_episode；一季完成不清掉其他季的暫停／追看。找回清單要列出尚未完成的季與 run，不能只看全劇最後位置。
- `last_completed` 與 `partial` 分開，episode / season 為正整數；特別篇用已確認目錄辨識，不能自己編號。
- 下一集只能取 `episode_catalog.verified: true` 的 `positions`（明確觀看順序）；有 partial 就回到該集。季末缺下一季目錄時回報「待確認」，不能把最後一集直接 +1。
- 最後觀看日期未知就留 null。可應使用者要求找出 state 為 in_progress / paused 的清單，列版本、最後完整位置與 partial；不自動標棄追，也不啟用提醒。

## 概念節點與閱讀路線

節點只從實際讀過／看過的作品抽出。路線狀態為 active / queued / paused / demoted / merged / archived / pending；新建一律 pending，等使用者確認才 active；軟上限見 [設定](settings.yaml)。
