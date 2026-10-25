"""資料契約的純函式測試 oracle；不是同步 adapter、排程器或模型評分服務。"""
from copy import deepcopy
from datetime import date, datetime
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.tzinfo else None
    except ValueError:
        return None


def event_timestamp(value):
    """允許來源只有日期；僅用於比較，輸出保留原有精度，不補觀看時間。"""
    known = timestamp(value)
    if known is not None:
        return known
    if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        try:
            return (date.fromisoformat(value) - date(1970, 1, 1)).days * 86400
        except ValueError:
            pass
    return None


def resolve_field(observations, field, scope, affects_decision=False):
    """按欄位和完整 scope 選值；保留所有候選及採用值 provenance。"""
    if not scope.get('work_id') or not scope.get('edition_id'):
        raise ValueError('resolution requires work_id and edition_id')
    if field.startswith('progress.') and (not scope.get('run_id') or not scope.get('scope')):
        raise ValueError('progress resolution requires run_id and completion scope')
    if field == 'ownership' and (not scope.get('carrier') or not scope.get('platform')):
        raise ValueError('ownership resolution requires carrier and platform')
    candidates = [deepcopy(item) for item in observations
                  if item.get('field') == field and all(item.get(k) == v for k, v in scope.items())]
    valid = [item for item in candidates if item.get('value') is not None and not item.get('missing')
             and timestamp(item.get('observed_at')) is not None
             and item.get('source') in ('manual', 'manual_file', 'platform', 'inference')]
    if field == 'progress.last_viewed_at':
        valid = [item for item in valid if item['source'] != 'inference'
                 and event_timestamp(item.get('event_at')) is not None and item['value'] == item['event_at']]
    correction = [item for item in valid if item.get('correction') and item.get('reason')
                  and item.get('source') == 'manual' and item.get('explicit')]
    latest = lambda items: max(items, key=lambda item: timestamp(item['observed_at']))
    if correction:
        # 人工修正取代它之前的所有證據；之後的例行同步不能讓被修正的值復活。
        cutoff = timestamp(latest(correction)['observed_at'])
        valid = [latest(correction)] + [item for item in valid if timestamp(item['observed_at']) > cutoff
                                        and not item.get('correction')]
    if field == 'progress.last_viewed_at' and valid:
        most_recent = max(event_timestamp(item['event_at']) for item in valid)
        valid = [item for item in valid if event_timestamp(item['event_at']) == most_recent]
    elif field == 'progress.state':
        # A completion is durable for this run; a rewatch belongs to another run.
        # 但被人工修正掉的完成不算（修正本身的值若不是 completed，之後只有新的 completed 才能再翻回）。
        completed = [item for item in valid if item['value'] == 'completed' and item['source'] != 'inference']
        if completed:
            valid = completed
    elif field == 'progress.last_completed':
        positions = [item for item in valid if isinstance(item['value'], dict)
                     and positive_position(item['value']) and item['source'] != 'inference']
        if positions:
            furthest = max((item['value']['season'], item['value']['episode']) for item in positions)
            valid = [item for item in positions if (item['value']['season'], item['value']['episode']) == furthest]
    elif field == 'ownership':
        manual = [item for item in valid if item['source'] == 'manual' and item.get('explicit')]
        if manual:
            valid = [latest(manual)]
        elif any(item['value'] == 'owned' for item in valid):
            valid = [item for item in valid if item['value'] == 'owned']
    ranks = {'manual_file': 2, 'platform': 1, 'inference': 0}
    def rank(item):
        authority = 3 if item['source'] == 'manual' and item.get('explicit') else ranks.get(item['source'], 2)
        event_time = event_timestamp(item.get('event_at'))
        return authority, event_time if event_time is not None else timestamp(item['observed_at'])
    if not valid:
        return dict(value=None, provenance=None, observations=candidates, unresolved=False, needs_confirmation=False)
    best = max(rank(item) for item in valid)
    top = [item for item in valid if rank(item) == best]
    conflict = any(item['value'] != top[0]['value'] for item in top)
    return dict(value=None if conflict else top[0]['value'], provenance=None if conflict else top[0],
                observations=candidates, unresolved=conflict, needs_confirmation=conflict and affects_decision)


def positive_position(value):
    return all(type(value.get(key)) is int and value[key] > 0 for key in ('season', 'episode'))


def resume_position(edition, season=None):
    progress = edition['personal']['progress']
    if season is not None:
        seasonal = next((item for item in progress.get('seasons', []) if item['number'] == season), None)
        if seasonal is None:
            return dict(position=None, reason='待確認')
        progress = dict(partial=dict(season=season, **seasonal['partial_episode']) if seasonal.get('partial_episode') else None,
                        last_completed=dict(season=season, episode=seasonal['last_completed_episode'])
                        if seasonal.get('last_completed_episode') else None)
    partial = progress.get('partial')
    if partial and positive_position(partial):
        return dict(position=deepcopy(partial), reason='續看本集')
    last = progress.get('last_completed')
    catalog = edition.get('episode_catalog', {})
    positions = catalog.get('positions', [])
    if not (catalog.get('verified') and catalog.get('source') and timestamp(catalog.get('observed_at')) is not None
            and all(positive_position(item) for item in positions)):
        return dict(position=None, reason='待確認')
    if last in positions:
        index = positions.index(last)
        if index + 1 < len(positions):
            return dict(position=deepcopy(positions[index + 1]), reason='已確認目錄的下一集')
    return dict(position=None, reason='待確認')


def add_revisit(edition, revisit):
    result = deepcopy(edition)
    progress = result['personal']['progress']
    if not revisit.get('run_id') or revisit['run_id'] == 'initial':
        raise ValueError('rewatch requires a distinct run_id')
    if any(run['run_id'] == revisit['run_id'] for run in progress['revisits']):
        raise ValueError('duplicate run_id')
    progress['revisits'].append(deepcopy(revisit))
    return result


def unfinished(records):
    result = []
    for work in records:
        for edition in work['editions']:
            progress = edition['personal']['progress']
            for run_id, run in [('initial', progress)] + [(run['run_id'], run) for run in progress.get('revisits', [])]:
                if run.get('seasons'):
                    result.extend((work['id'], edition['id'], run_id, season['number']) for season in run['seasons']
                                  if season['state'] in ('in_progress', 'paused'))
                elif run['state'] in ('in_progress', 'paused'):
                    result.append((work['id'], edition['id'], run_id, None))
    return result


def should_report(score, mode):
    if mode == 'full_list':
        return True
    if mode == 'recommendations':
        return isinstance(score, (int, float)) and not isinstance(score, bool) and score > 60
    return False


def validate_schedule(task):
    """只驗證啟用前契約，絕不建立或啟用任務。"""
    if not task.get('enabled'):
        return []
    errors = []
    for key in ('source', 'output', 'timezone', 'cadence'):
        if not task.get(key):
            errors.append(key)
    for key in ('trial_succeeded', 'user_confirmed'):
        if task.get(key) is not True:
            errors.append(key)
    try:
        ZoneInfo(task.get('timezone') or '')
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        errors.append('timezone')
    cadence = task.get('cadence')
    if cadence in ('daily', 'weekly', 'monthly'):
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', task.get('time') or ''):
            errors.append('time')
        if task.get('interval_minutes') is not None:
            errors.append('interval_minutes')
        if cadence == 'weekly' and (type(task.get('weekday')) is not int or not 0 <= task['weekday'] <= 6):
            errors.append('weekday')
        if cadence == 'monthly':
            if type(task.get('day_of_month')) is not int or not 1 <= task['day_of_month'] <= 31:
                errors.append('day_of_month')
            if task.get('missing_day') != 'skip':
                errors.append('missing_day')
    elif cadence == 'interval':
        value = task.get('interval_minutes')
        if type(value) is not int or value < 60:
            errors.append('interval_minutes')
        for key in ('time', 'weekday', 'day_of_month'):
            if task.get(key) is not None:
                errors.append(key)
    else:
        errors.append('cadence')
    if task.get('report_mode') not in ('full_list', 'recommendations', 'sync'):
        errors.append('report_mode')
    return sorted(set(errors))
