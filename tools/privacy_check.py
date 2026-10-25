#!/usr/bin/env python3
"""公開前隱私檢查。只回報「命中數與檔案」，不印出命中的值。

用法：
  python3 tools/privacy_check.py [--private-patterns FILE] [--catalog-json FILE] [--report FILE]

  --private-patterns  每行一個私人字串（擁有者名字、帳號、倉庫名、主機名…）；
                      以 re: 開頭的行視為正規表示式。這個檔案**放在 repo 之外**，不要提交。
  --catalog-json      私人書庫清單（JSON，含 library／wishlist 陣列，每筆有 t 欄位）；
                      用來交叉比對書名，避免把真實持有資料寫進公開檔案。
  --report            把摘要寫到套件外的 Markdown 檔；套件內目的地一律拒絕。

所有檔案（含快取目錄）均納入 allowlist 檢查；全部 UTF-8 文字（含 CSV）都掃描。
拒絕符號連結與非 UTF-8 檔，避免未檢查內容混入交付包。也檢查 Markdown 相對連結。
只用標準函式庫。exit 0＝全部通過。
"""
import argparse, json, pathlib, re, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENERIC = {  # 名稱 → 正規表示式（寫法刻意避免自我命中）
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}",
    "tail_net": r"\b[\w-]+\.ts\.net\b|tail[s]cale|tail[n]et",
    "cgnat_ip": r"\b100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b",
    "private_ip": r"\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
    "token_like": r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|xox[abpr]-[\w-]{10,}|sk-[A-Za-z0-9]{20,}|eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{5,})",
    "long_hex": r"\b[0-9a-f]{32,}\b",
    "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    "abs_private_path": r"/(work" r"space|home/[\w.-]+|Users/[\w.-]+|root)/",
    "agent_store": r"agent" r"-data|routine[s]?/[0-9a-f]{6,}",
    "token_file": r"(refresh|access)_?token\s*[:=]\s*\S{8,}|\.kobo[\w-]*\.json|cookies?\.(txt|json)",
}

def norm(t):
    return re.sub(r"[\s　《》〈〉「」()（）:：·・,，.。!！?？\-—_]", "", unicodedata.normalize("NFKC", t or "")).lower()

def files():
    # 除了 .git/ 之外不忽略任何目錄；symlink 本身也要列出並拒絕，不能跟到套件外。
    return sorted(p for p in ROOT.rglob("*") if (p.is_file() or p.is_symlink())
                  and ".git" not in p.relative_to(ROOT).parts[:-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private-patterns")
    ap.add_argument("--catalog-json")
    ap.add_argument("--report")
    a = ap.parse_args()
    report_path = pathlib.Path(a.report).resolve() if a.report else None
    if report_path and (report_path == ROOT or ROOT in report_path.parents):
        ap.exit(1, "拒絕：--report 必須寫到 repo 外，不能在檢查後新增或改寫包內檔案。\n")

    fs = files()
    rel = {p: p.relative_to(ROOT).as_posix() for p in fs}
    texts, unsupported = {}, []
    for p in fs:
        if p.is_symlink():
            unsupported.append(rel[p])
            continue
        try:
            texts[p] = p.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            unsupported.append(rel[p])
    res = {}

    def hit(cat, p, n):
        if n:
            res.setdefault(cat, {})
            res[cat][rel[p]] = res[cat].get(rel[p], 0) + n

    for name, rx in GENERIC.items():
        r = re.compile(rx, re.I)
        for p, t in texts.items():
            hit("generic:" + name, p, len(r.findall(t)))

    if a.private_patterns:
        pats = [line for line in pathlib.Path(a.private_patterns).read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")]
        for pattern in pats:
            r = re.compile(pattern[3:] if pattern.startswith("re:") else re.escape(pattern), re.I)
            for p, t in texts.items():
                hit("private_pattern", p, len(r.findall(t)))
        res.setdefault("private_pattern", {})

    n_titles = 0
    if a.catalog_json:
        d = json.loads(pathlib.Path(a.catalog_json).read_text(encoding="utf-8"))
        titles = {norm(x.get("t")) for k in ("library", "wishlist") for x in d.get(k, []) if isinstance(x, dict)}
        titles = {t for t in titles if len(t) >= 4}
        n_titles = len(titles)
        for p, t in texts.items():
            hit("catalog_title", p, sum(ti in norm(t) for ti in titles))
        res.setdefault("catalog_title", {})

    allow_path = ROOT / "ALLOWLIST.txt"
    allow = {line.strip() for line in allow_path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")} if allow_path in texts else set()
    not_allowed = sorted(set(rel.values()) - allow)
    missing = sorted(allow - set(rel.values()))
    bad_links = []
    for p, t in texts.items():
        if p.suffix.lower() != ".md":
            continue
        for match in re.finditer(r"\]\(([^)#\s]+)", t):
            target = match.group(1)
            if re.match(r"[a-z]+://", target):
                continue
            dest = (p.parent / target).resolve()
            if (ROOT not in dest.parents and dest != ROOT) or not dest.exists():
                bad_links.append(rel[p])

    ok = not any(res.values()) and not not_allowed and not missing and not bad_links and not unsupported
    out = ["# 隱私檢查摘要（不含命中值）", "",
           f"- 掃描檔案數：{len(fs)}（UTF-8 文字檔 {len(texts)}，包含 CSV 等副檔名）",
           f"- 私人樣式檔：{'有提供' if a.private_patterns else '未提供（只跑通用樣式）'}",
           f"- 書庫書名交叉比對：{'已比對 %d 個書名（長度≥4）' % n_titles if a.catalog_json else '未提供'}", "",
           "| 類別 | 命中總數 | 檔案（次數） |", "|---|---|---|"]
    categories = {"generic:" + k for k in GENERIC} | set(res)
    for cat in sorted(categories):
        found = res.get(cat, {})
        counts = ', '.join(f'{k}({v})' for k, v in sorted(found.items())) or '—'
        out.append(f"| {cat} | {sum(found.values())} | {counts} |")
    out += ["", f"- 不在 ALLOWLIST 的檔案：{len(not_allowed)} {not_allowed if not_allowed else ''}",
            f"- ALLOWLIST 有列但不存在：{len(missing)} {missing if missing else ''}",
            f"- 跳出 repo 或失效的相對連結：{len(bad_links)} {sorted(set(bad_links)) if bad_links else ''}",
            f"- 符號連結或無法掃描的非 UTF-8 檔：{len(unsupported)} {unsupported if unsupported else ''}",
            "", f"**結果：{'通過' if ok else '未通過'}**"]
    txt = "\n".join(out) + "\n"
    if report_path:
        try:
            report_path.write_text(txt, encoding="utf-8")
        except OSError:
            ap.exit(1, "無法寫入套件外報告；本次不回報成功。\n")
    print(txt)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
