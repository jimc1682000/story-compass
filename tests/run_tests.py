#!/usr/bin/env python3
"""合成 fixtures 的確定性規則 oracle；逐案結果印到 stdout，Markdown 報告只在 --report 指定 repo 外路徑時寫出。

資料採公開範本的作品／版本欄位；assessment 是測試輸入，不是模型評分結果。
不測模型的心得、翻譯品質、增益判斷或實際平台 adapter。只用標準函式庫。
"""
import json
import pathlib
import re
import sys
import unicodedata
from contract_rules import resolve_field, timestamp

HERE = pathlib.Path(__file__).resolve().parent
TYPE_NAMES = {"A": "新大陸", "B": "新骨幹", "C": "跨連線", "D": "加深", "E": "整理", "F": "再包裝"}
REFUSE = {"mark_watched": "我不會替你標記已看；請你在自己的平台上標記。",
          "mark_read": "我不會替你標記已讀；請你在自己的平台上標記。",
          "purchase": "我不會下單或付款；只提供建議。",
          "subscribe": "我不會替你訂閱；取得方式由你決定。"}


def norm(value):
    return re.sub(r"[《》〈〉「」\s]", "", unicodedata.normalize("NFKC", value or "")).casefold()


def same_work(left, right):
    a, b = (str(item.get('id') or '').strip() for item in (left, right))
    if a and b:
        return a == b
    names = [norm(item.get('title')) for item in (left, right)]
    creators = [sorted(norm(c) for c in item.get('creators', []) if norm(c)) for item in (left, right)]
    return bool(names[0] and creators[0] and names[0] == names[1] and creators[0] == creators[1])


def selected_edition(candidate, assessment):
    return next((edition for edition in candidate.get('editions', [])
                 if edition.get('id') and edition['id'] == assessment.get('edition_id')), None)


def valid_isbns(values):
    result = set()
    for value in values or []:
        if isinstance(value, str) and re.fullmatch(r'\d{13}', value):
            if sum(int(digit) * (1 if index % 2 == 0 else 3) for index, digit in enumerate(value)) % 10 == 0:
                result.add(value)
    return result


def find_match(records, candidate, assessment):
    """回傳 (層級, 作品, 版本)；缺主鍵不是相同，改編是相關作品。"""
    return find_matches(records, candidate, assessment)[0]


def find_matches(records, candidate, assessment):
    """回傳 (最高層級命中, 所有命中清單)；書庫未讀的語意重疊不因為另有更高層級命中而消失。"""
    target = selected_edition(candidate, assessment)
    if target is None:
        return ('none', None, None), []
    hits = []
    best = ('none', None, None)
    ranks = {'none': 0, 'semantic': 1, 'adaptation': 2, 'work_only': 3, 'edition_only': 4, 'exact': 5}
    for work in records:
        for edition in work.get('editions', []):
            personal = edition.get('personal', {})
            holdings = personal.get('holdings', [])
            consumed = personal.get('progress', {}).get('state') in ('in_progress', 'paused', 'completed')
            if holdings and all(holding.get('preview') for holding in holdings) and not consumed:
                continue
            isbn = valid_isbns(edition.get('isbn')) & valid_isbns(target.get('isbn'))
            conflicting_ids = work.get('id') and candidate.get('id') and work['id'] != candidate['id']
            matching_work = same_work(work, candidate) or bool(isbn and not conflicting_ids)
            level = 'none'
            if matching_work:
                if edition.get('id') and target.get('id'):
                    matching_edition = edition['id'] == target['id']
                else:
                    matching_edition = bool(norm(edition.get('label')) and norm(edition.get('label')) == norm(target.get('label'))
                                            and norm(edition.get('translator')) == norm(target.get('translator')))
                matching_edition = matching_edition or bool(isbn)
                level = 'work_only'
                if matching_edition:
                    holding_match = any(not h.get('preview') and h.get('carrier') == assessment.get('carrier')
                                        and (not assessment.get('platform') or h.get('platform') == assessment['platform'])
                                        for h in holdings)
                    level = 'exact' if holding_match else 'edition_only'
            elif ((work.get('adaptation_of') and work['adaptation_of'] == candidate.get('id'))
                  or (candidate.get('adaptation_of') and candidate['adaptation_of'] == work.get('id'))):
                level = 'adaptation'
            elif candidate.get('id') and any(overlap.get('work_id') == candidate['id'] and overlap.get('coverage', 0) >= 0.7
                                             for overlap in work.get('overlaps', [])):
                level = 'semantic'
            if level != 'none':
                hits.append((level, work, edition))
            if ranks[level] > ranks[best[0]]:
                best = level, work, edition
    return best, hits


def owned_unread(edition):
    personal = edition.get('personal', {})
    owned = any(h.get('ownership') == 'owned' and not h.get('preview') for h in personal.get('holdings', []))
    return owned and personal.get('progress', {}).get('state') != 'completed'


def has_personal_basis(fx):
    seed = fx.get('seed', {})
    goals = seed.get('goals') or fx.get('settings', {}).get('goals', [])
    has_goal = any((item.get('question') or '').strip() for item in goals if isinstance(item, dict))
    known = any(item.get('title') and (item.get('progress', {}).get('state') in ('completed', 'in_progress', 'paused')
                                     or item.get('verdict')) for item in seed.get('known_works', []))
    consumed = any(edition.get('personal', {}).get('progress', {}).get('state') in ('completed', 'in_progress', 'paused')
                   for work in fx.get('records', []) for edition in work.get('editions', []))
    return bool(has_goal and (known or consumed))


def band_action(score, sale, budget):
    if score is None:
        return None
    if score <= 40:
        return "Skip"
    if score <= 60:
        return "Borrow"
    if budget == "borrow_first":
        return "Buy on Sale" if score >= 81 and sale else "Borrow"
    if score <= 80:
        return "Buy on Sale" if sale else "Borrow"
    return "Buy"


def acquisition(assessment):
    info = assessment.get('acquisition', {})
    if (info.get('status') in ('confirmed', 'region_limited') and info.get('platform') and info.get('region')
            and info.get('source') and timestamp(info.get('checked_at')) is not None):
        return dict(info)
    return {'status': 'unknown', 'platform': None}


def evaluate(fx):
    out = {'refused': False, 'performed_external_action': False, 'text': []}
    request = fx['request']
    if request in REFUSE:
        out.update(refused=True)
        out['text'].append(REFUSE[request])
        return out
    if request == 'resolve_observations':
        resolution = resolve_field(fx['observations'], fx['field'], fx['scope'], fx.get('affects_decision', False))
        out.update(final_status=resolution['value'], needs_confirmation=resolution['needs_confirmation'])
        return out
    candidate, assessment = fx['candidate'], fx['assessment']
    out['gaps'] = sorted(key for key, value in fx.get('coverage', {}).items() if value.get('status') != 'ok')
    if out['gaps']:
        out['text'].append('在已提供的來源中查不到；查不到≠沒買／沒看。缺口：' + '、'.join(out['gaps']))
    (level, hit_work, hit_edition), hits = find_matches(fx.get('records', []), candidate, assessment)
    out['duplicate'] = level
    basis = has_personal_basis(fx)
    reviews = [review for review in assessment.get('reviews', []) if review != 'publisher_copy']
    if not basis or not reviews or selected_edition(candidate, assessment) is None:
        out.update(score=None, label='證據不足暫不評分', action=None,
                   analysis_mode='general' if not basis else 'insufficient_work_evidence')
        out['text'].append('？ 證據不足／—／' + candidate['title'])
        if not basis:
            out['text'].append('個人依據不足；可做一般分析，不硬給個人增益分數。')
        return out
    score = assessment['proposed_score']
    if type(score) not in (int, float) or not 0 <= score <= 100:
        raise ValueError('proposed_score must be in 0..100')
    if assessment['type'] == 'F' and not assessment.get('f_justification'):
        score = min(score, 40)
    if assessment['type'] == 'E':
        score = min(score, 70 if assessment.get('e_topology_index') else 55)
    out.update(score=score, analysis_mode='personal',
               score_line=f"{assessment['type']} {TYPE_NAMES[assessment['type']]}／{score}／{candidate['title']}")
    budget = fx.get('settings', {}).get('budget', {}) or {}
    if not isinstance(budget, dict) or budget.get('stance', 'unset') not in ('unset', 'borrow_first', 'balanced', 'collector'):
        raise ValueError('settings requires budget.stance')
    action = band_action(score, bool(assessment.get('price', {}).get('sale')), budget.get('stance', 'unset'))
    out['reuses_reject_reason'] = False
    # 先讀書庫：任何一個已擁有未讀的同版本／語意重疊命中都算，不只看最高層級那一筆。
    shelf = next(((w, e) for lv, w, e in hits if lv in ('exact', 'edition_only', 'semantic') and owned_unread(e)), None)
    if hit_edition:
        personal = hit_edition.get('personal', {})
        progress, intent = personal.get('progress', {}), personal.get('intent', {})
        if shelf:
            action = '先讀書庫'
            out['text'].append('書庫已有：' + shelf[0]['title'])
        elif level in ('exact', 'edition_only') and progress.get('state') == 'completed':
            action = 'Skip'
        # 拒絕理由只在候選本身（同作品）上沿用；改編或語意重疊的作品各有自己的購買意願。
        if intent.get('purchase') == 'declined' and level in ('exact', 'edition_only', 'work_only'):
            if assessment.get('new_evidence'):
                out['mentions_new_evidence'] = True
                out['text'].append('曾拒絕，但有新證據：' + assessment['new_evidence'])
            else:
                action = 'Skip'
                out['reuses_reject_reason'] = True
                out['text'].append('沿用拒絕理由：' + (intent.get('reject_reason') or '待查'))
    if level == 'work_only':
        out.update(editions_distinct=True, evaluates='edition_gain')
    elif level == 'adaptation':
        out['text'].append('已看改編≠已讀原作；分開評估相關作品的剩餘增益。')
    for key in ('adaptations', 'entry_version', 'origin'):
        if assessment.get(key):
            out[key] = assessment[key]
    if assessment.get('library_holding'):
        out['text'].append('館藏：' + assessment['library_holding'] + '（只回報）')
    out['action'] = action
    if candidate['media'] in ('anime', 'film', 'tv'):
        advice = '優先看' if score >= 81 else '待看' if score >= 61 else '先試看' if score >= 41 else '跳過'
        out.update(action=None, watch_advice={'verdict': advice, 'reason': assessment.get('reason', '依增益與重疊規則的測試傾向')},
                   acquisition=acquisition(assessment), collection_value=assessment.get('collection_value') or {'value': 'unknown'})
    return out

def check(fx, out):
    exp, fails = fx["expected"], []
    for k, v in exp.items():
        if k == "must_say":
            if not any(v in t for t in out["text"]): fails.append(f"缺少用語「{v}」")
        elif k == "phrase_required":
            if not any(v in t for t in out["text"]): fails.append(f"缺少用語「{v}」")
        elif k == "phrase_forbidden":
            bad = [p for p in v if any(p in t for t in out["text"])]
            if bad: fails.append(f"出現禁用語 {bad}")
        elif k == "requires_fields":
            miss = [f for f in v if not out.get(f)]
            if miss: fails.append(f"缺必填欄位 {miss}")
        elif k == "gaps":
            if sorted(v) != out.get("gaps"): fails.append(f"gaps={out.get('gaps')} 預期 {sorted(v)}")
        elif out.get(k) != v:
            fails.append(f"{k}={out.get(k)!r} 預期 {v!r}")
    return fails

def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", help="Markdown 報告輸出路徑；必須在 repo 外，套件內不留產物")
    a = ap.parse_args()
    report_path = pathlib.Path(a.report).resolve() if a.report else None
    root = HERE.parent.resolve()
    if report_path and (report_path == root or root in report_path.parents):
        ap.exit(1, "拒絕：--report 必須寫到 repo 外，套件內不保留測試產物。\n")
    rows, n_fail = [], 0
    for p in sorted((HERE / "fixtures").glob("*.json")):
        fx = json.loads(p.read_text(encoding="utf-8"))
        out = evaluate(fx)
        fails = check(fx, out)
        n_fail += bool(fails)
        rows.append((p.stem, fx["desc"], "PASS" if not fails else "FAIL", "；".join(fails) or "—", out))
    lines = ["# 驗收測試結果", "", "由 `tests/run_tests.py` 產生。測的是確定性 oracle；assessment 為合成輸入，模型與真實 adapter **未實測**。", "",
             f"合計：{len(rows)} 件，通過 {len(rows)-n_fail}，失敗 {n_fail}", "",
             "| 案例 | 說明 | 結果 | 失敗原因 | 關鍵輸出 |", "|---|---|---|---|---|"]
    for stem, desc, res, why, out in rows:
        key = {k: out[k] for k in ("duplicate", "score", "action", "refused", "final_status", "needs_confirmation", "analysis_mode", "gaps") if k in out}
        lines.append(f"| {stem} | {desc} | {res} | {why} | `{json.dumps(key, ensure_ascii=False)}` |")
    if report_path:
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for stem, _, res, why, _ in rows:
        print(f"{res}  {stem}  {why}")
    print(f"合計 {len(rows)}，失敗 {n_fail}")
    sys.exit(1 if n_fail else 0)

if __name__ == "__main__":
    main()
