# 選用例行任務規範（範本，全部停用）

只有資料契約與測試，沒有 scheduler 或平台 adapter。先試評，之後使用者另行 opt-in 才處理排程；本套件不自動啟用任務或提醒。

## 時間與頻率契約

設定在 `templates/settings.yaml` 的 schedule（與技能內設定範本一致）。每項啟用前都要確認 source、output、IANA timezone、cadence 與所需時間欄位，且 trial_succeeded、user_confirmed 均為 true。未填時區不能用 UTC 悄悄啟用。

- daily：time，24 小時 HH:MM。
- weekly：time ＋ weekday（0＝週一至 6＝週日）。
- monthly：time ＋ day_of_month（1–31）；missing_day 固定 skip，當月無該日就略過。
- interval：interval_minutes，整數且至少 60；不混用 time、weekday、day_of_month。

範本只標明頻率種類，沒有預設執行時間。同步來源不可用時保留最近成功快照並標日期；失敗或缺項不變成沒買／沒看。連續失敗 2 次暫停該同步候選，等使用者處理，不改其他來源狀態。

## 輸出模式與門檻

主動推薦／提醒只報分數 **>60**。使用者明確選擇 full_list 完整清單時，所有分數與待查都保留，低分不可當推薦；recommendations 模式只報 >60，沒有就安靜。sync 模式只報必要錯誤／需確認事項，不把個人狀態變更當推薦。

| 停用範本 | cadence | report_mode | 行為規範 |
|---|---|---|---|
| daily_deal | daily | full_list | 只在使用者選擇完整特價清單報告後使用；逐本評估，標真當日特價；推薦連結只給 >60 |
| delisting | monthly | recommendations | 逐頁確認真正到期日，不用活動截止日代替；只主動報 >60 |
| weekly_picks | weekly | full_list | 完整書單全列，低分一行、待查明說；深入推薦僅 >60 |
| library_sync | daily | sync | 自備書櫃平台的唯讀清單工具；預覽不算擁有，完成不倒退，重讀另記、必要時確認 |
| watch_history_sync | daily | sync | 自備影視紀錄工具的唯讀匯出；季集與日期遵循技能規範，不寫回平台 |

書籍館藏只回報，不改增益或評估行動；影視取得方式只輕量確認，不逐一查館藏。價格可改取得行動，不改增益。追一半清單只在提出要求時產生，不附自動追看提醒。

## 試跑紀錄

記任務、來源、頻率、時間、時區、輸出位置、試跑時間與成功／失敗原因、使用者確認。沒有 adapter 或執行環境時保持 enabled: false，不能記成試跑成功。
