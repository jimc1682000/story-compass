#!/usr/bin/env python3
"""獨立短 prompt 的靜態範圍檢查；不產生檔案，也不執行模型。

用法：python3 tests/check_prompt.py [--prompt FILE]
只讀 prompt 本身，不讀 Skill、ROLE 或個人資料；不驗收完整技能功能。
通過只代表保留必要提示與界線，不保證模型遵從或評估品質。
"""
import argparse
from pathlib import Path
import re


def check(text):
    checks = {
        "短提示詞（不超過 2500 字元）": bool(text.strip()) and len(text) <= 2500,
        "作品、目標與少量已知作品輸入": all(
            field in text for field in ("作品：", "我的目標：", "少量已知作品：")
        ),
        "五種媒體": all(media in text for media in ("書", "漫畫", "動畫", "電影", "影集")),
        "增益、重複、讀看判斷與版本入口": all(
            term in text for term in ("個人邊際增益不是口碑分", "重複程度", "值得讀／看", "版本／入口")
        ),
        "缺依據時一般分析、不硬算分數": all(
            term in text for term in ("個人依據不足", "一般分析", "不硬算個人增益分數", "資料不足不假裝確定")
        ),
        "A–F 型態、評分行與上限": all(
            term in text
            for term in (
                "A 新大陸", "B 新骨幹", "C 跨連線", "D 加深", "E 整理", "F 再包裝",
                "字母 中文名／分數／作品名", "？ 證據不足／—／作品名",
                "F 最高 40", "E 最高 55", "最高 70", "與價格、口碑無關",
            )
        ),
        "明示排除長期功能": re.search(
            r"不做館藏同步、長期狀態管理、已讀鎖定、排程或完整來源衝突處理", text
        ) is not None,
        "沒有產生物標記或外部檔案依賴": re.search(
            r"來源指紋|請勿手改|build-prompt|SKILL\.md|ROLE\.md|(?:skill|references|templates|catalog)/"
            r"|[\w./-]+\.(?:md|ya?ml|json|py)\b|\]\((?!https?://)[^)]+\)", text
        ) is None,
    }
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", type=Path, default=Path(__file__).resolve().parent.parent / "prompt.md")
    args = parser.parse_args()
    try:
        text = args.prompt.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        parser.exit(1, f"FAIL  無法讀取提示詞：{exc}\n")
    checks = check(text)
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    failures = sum(not ok for ok in checks.values())
    print(f"靜態檢查 {len(checks)} 項，失敗 {failures}；{len(text)} 字元。模型輸出未實測。")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
