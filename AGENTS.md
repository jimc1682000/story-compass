# story-compass

## 用途

以個人知識地圖評估作品的邊際增益；方法位於 `skill/`，範本與指引位於 `templates/`、`guides/`。

## 驗證

```sh
python3 -B tests/check_prompt.py
python3 -B tests/run_tests.py
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B tools/privacy_check.py
```

## 邊界

- 新增檔案先加進 `ALLOWLIST.txt`，再跑 `tools/privacy_check.py`。
- 指令都加 `-B`，不在 repo 內留 bytecode；測試與檢查報告只寫到 repo 外。
- 知識地圖是個人資料，放在使用者自己的私人倉庫，不放進這個 repo。細節見 [README.md](README.md)。
