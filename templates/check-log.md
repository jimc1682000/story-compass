# 驗證紀錄（範本）

複製到你自己的筆記或發佈 PR 描述裡填寫；套件本身不保存任何一次的結果，交付包內也不留測試產物。

- 日期與時區：
- 套件版本（commit 或 tag）：
- Python 版本：

## 可執行檢查

| 命令 | 結果（數字／通過與否） |
|---|---|
| `python3 -B tests/check_prompt.py` | 靜態檢查 ＿ 項通過，＿ 字元 |
| `python3 -B tests/run_tests.py [--report <套件外>]` | ＿ 個合成 fixtures，失敗 ＿ |
| `python3 -B -m unittest discover -s tests -p 'test_*.py'` | ＿ 項契約測試通過 |
| `python3 -B tools/privacy_check.py --private-patterns <套件外> --catalog-json <套件外> --report <套件外>` | 通用樣式 ＿、私人樣式 ＿（＿ 條）、書庫書名交叉比對 ＿（＿ 個書名）、allowlist／連結／symlink 問題 ＿ |

私人樣式檔與書庫 JSON 一律放在套件外，不提交。沒有提供這兩個輸入時，隱私檢查只跑通用樣式，不能寫成「已完成私人比對」。

## 人工檢視

- [ ] README、ROLE、guides 逐檔看過，沒有擁有者的名字、帳號、倉庫名、主機名、排程時間或時區
- [ ] 新增的檔案都已列入 `ALLOWLIST.txt`
- [ ] 範本與範例裡的作品全部是虛構的

## 真實模型試評

沒做就整段寫「未做」。fixtures 的評論只有類型標籤沒有內文，oracle 通過不等於模型會這樣評；模型試評要另外跑。

| 項目 | 內容 |
|---|---|
| 模型與版本（含 CLI 版本、有無搜尋） | |
| 入口與 prompt／SKILL 版本（commit） | |
| 純提示詞案例（目標充足／目標缺／改編／譯本／虛構作品）各跑幾次、通過幾次 | |
| Skill 敏感案例 09（F 上限）、06b（手動 seed）、12b（拒絕下單）各跑幾次、通過幾次 | |
| 其他案例與發現 | |

## 限制

- 平台 adapter、首次設定流程、分享範本：（實作與實測狀態）
