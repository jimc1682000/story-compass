# 安裝與依賴

只複製 skill 目錄即可安裝。本檔、[邊界](boundaries.md)、[設定範本](settings.yaml)、[資料模型](work-edition-model.md) 與其他 references 隨技能一起提供；沒有上一層目錄的必要依賴。

聊天模型是必要能力。公開資訊搜尋選用：無法查證就說明限制，不假稱查過。首次用手動目標與已知作品先試評，連線之後再 opt-in。設定空白用中性預設，缺個人依據只做一般分析、不硬給個人增益分數。

完整分享套件另附空白 seed、作品卡、測試腳本與連線／排程指引；這些不是安裝技能的必要檔案。所有檢查只用 Python 標準函式庫，並以停用 bytecode 的方式執行，避免在交付包留下快取檔。

電子書平台、影視紀錄工具等真實 adapter 均未隨套件提供或實測；資料格式與示意映射不是平台整合。Grok Share Template 只是準備指引，未建立、未實測。模型讀取 Skill 或獨立短提示詞後的輸出品質也未實測。

## 設定契約

[設定範本](settings.yaml) 採 JSON 相容 YAML；null 為未設定，budget.stance 為 unset / borrow_first / balanced / collector。完整套件的同名設定範本必須逐位元組一致，測試會核對。

所有 schedule 項目預設 enabled: false。要啟用，必須有 source、output、IANA timezone、已確認頻率與時間，且 trial_succeeded 與 user_confirmed 均為 true；這只是設定驗證，不提供 scheduler。

cadence 可 daily / weekly / monthly / interval。前三者需 time（HH:MM），weekly 另需 weekday（0＝週一，6＝週日），monthly 另需 day_of_month（1–31）與 missing_day: skip；interval 需 interval_minutes（至少 60），不得同時混入曆日時間欄位。時區未設定時不能偷偷用 UTC 啟用。source 或 output 不繼承模糊預設，必須逐項確認。完整套件的例行任務指引提供停用範本。

report_mode: recommendations 只報 >60；full_list 保留所有分數與待查；sync 只供使用者另接的同步工具，不是本技能提供了 adapter。追一半清單沒有自動提醒。
