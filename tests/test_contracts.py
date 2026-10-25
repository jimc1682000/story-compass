"""回歸與資料契約測試；不呼叫模型、平台或 scheduler。"""
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from contract_rules import add_revisit, resolve_field, resume_position, should_report, unfinished, validate_schedule
from run_tests import evaluate, find_match, same_work

ROOT = Path(__file__).resolve().parent.parent

def load_template(path):
    # The delivered YAML files deliberately use the JSON subset of YAML 1.2.
    return json.loads('\n'.join(line for line in Path(path).read_text().splitlines() if not line.startswith('#')))


def fixture(name='08-genuinely-new.json'):
    return json.loads((ROOT / 'tests/fixtures' / name).read_text())


def skill_references(folder):
    failures = []
    for path in folder.rglob('*.md'):
        for ref in re.findall(r'(?:[\w.-]+/)*[\w.-]+\.(?:md|yaml)\b', path.read_text()):
            target = (path.parent / ref).resolve()
            if not target.is_relative_to(folder.resolve()) or not target.is_file():
                failures.append((path.name, ref))
    return failures


class ScoringAndIdentity(unittest.TestCase):
    def test_missing_personal_basis_fixture06_has_explicit_oracle(self):
        fx = fixture('06-missing-source-data.json')
        self.assertIsNone(fx['expected']['score'])
        out = evaluate(fx)
        self.assertIsNone(out['score'])
        self.assertIsNone(out['action'])
        self.assertEqual(out['analysis_mode'], 'general')

    def test_manual_seed_without_platforms_is_sufficient(self):
        fx = fixture('06b-manual-seed-no-platform.json')
        self.assertTrue(all(source['status'] != 'ok' for source in fx['coverage'].values()))
        self.assertEqual(evaluate(fx)['score'], 64)

    def test_connected_but_empty_records_are_not_personal_evidence(self):
        fx = fixture()
        fx['seed'] = {'goals': [], 'known_works': []}
        self.assertTrue(all(source['status'] == 'ok' for source in fx['coverage'].values()))
        self.assertIsNone(evaluate(fx)['score'])

    def test_ownership_alone_is_not_reading_evidence(self):
        fx = fixture('02-exact-owned-same-edition.json')
        fx['seed']['known_works'] = []
        self.assertIsNone(evaluate(fx)['score'])

    def test_null_blank_seed_does_not_crash_or_score(self):
        fx = fixture()
        fx['seed'] = load_template(ROOT / 'templates/seed.yaml')
        self.assertIsNone(evaluate(fx)['score'])

    def test_e_default_ceiling_55_56_70_71(self):
        for proposed, expected in ((55,55),(56,55),(70,55),(71,55)):
            with self.subTest(proposed=proposed):
                fx = fixture()
                fx['assessment'].update(type='E', proposed_score=proposed, e_topology_index=False)
                self.assertEqual(evaluate(fx)['score'], expected)

    def test_e_topology_ceiling_55_56_70_71(self):
        for proposed, expected in ((55,55),(56,56),(70,70),(71,70),(90,70)):
            with self.subTest(proposed=proposed):
                fx = fixture()
                fx['assessment'].update(type='E', proposed_score=proposed, e_topology_index=True)
                self.assertEqual(evaluate(fx)['score'], expected)

    def test_f_exception_still_requires_reason(self):
        fx = fixture('09-f-high-bar.json')
        self.assertEqual(evaluate(fx)['score'], 40)
        fx['assessment']['f_justification'] = '虛構案例：新增可驗證的對照方法'
        self.assertEqual(evaluate(fx)['score'], 55)

    def test_price_pair_changes_action_but_not_score(self):
        sale, normal = fixture(), fixture()
        normal['assessment']['price']['sale'] = False
        self.assertEqual((evaluate(sale)['score'], evaluate(normal)['score']), (74,74))
        self.assertEqual((evaluate(sale)['action'], evaluate(normal)['action']), ('Buy on Sale','Borrow'))

    def test_ownership_pair_changes_action_but_not_score(self):
        absent, owned = fixture(), fixture()
        card = deepcopy(owned['candidate'])
        card['editions'][0]['personal']['progress']['state'] = 'not_started'
        card['editions'][0]['personal']['holdings'] = [{'carrier':'ebook','platform':'manual','ownership':'owned','preview':False}]
        owned['records'] = [card]
        self.assertEqual((evaluate(absent)['score'], evaluate(owned)['score']), (74,74))
        self.assertEqual((evaluate(absent)['action'], evaluate(owned)['action']), ('Buy on Sale','先讀書庫'))

    def test_library_pair_changes_neither_score_nor_action(self):
        with_library, without_library = fixture(), fixture()
        without_library['assessment'].pop('library_holding')
        self.assertEqual((evaluate(with_library)['score'], evaluate(with_library)['action']),
                         (evaluate(without_library)['score'], evaluate(without_library)['action']))

    def test_nested_budget_uses_actual_published_settings(self):
        fx = fixture('13-budget-borrow-first.json')
        fx['settings'] = load_template(ROOT / 'templates/settings.yaml')
        fx['settings']['budget']['stance'] = 'borrow_first'
        self.assertEqual(evaluate(fx)['action'], 'Borrow')
        fx['settings']['budget']['stance'] = 'balanced'
        self.assertEqual(evaluate(fx)['action'], 'Buy on Sale')

    def test_unrelated_missing_ids_not_duplicates(self):
        fx = fixture()
        target = deepcopy(fx['candidate'])
        target.pop('id')
        other = deepcopy(target)
        other['title'] = '《虛構：完全不同的作品》'
        other['creators'] = ['虛構另一作者']
        self.assertEqual(find_match([other], target, fx['assessment'])[0], 'none')

    def test_published_id_key_does_not_equate_unrelated_records(self):
        fx = fixture()
        other = deepcopy(fx['candidate'])
        other['id'] = 'unrelated-id'
        self.assertEqual(find_match([other], fx['candidate'], fx['assessment'])[0], 'none')

    def test_missing_ids_fall_back_only_with_title_and_creator(self):
        fx = fixture()
        left, right = deepcopy(fx['candidate']), deepcopy(fx['candidate'])
        left.pop('id'); right.pop('id')
        self.assertTrue(same_work(left, right))
        left['creators'] = []
        self.assertFalse(same_work(left, right))
        self.assertFalse(same_work({}, {}))
        self.assertFalse(same_work({'id':' '}, {'id':' '}))

    def test_empty_isbn_and_edition_do_not_create_match(self):
        fx = fixture()
        other = deepcopy(fx['candidate'])
        other['id'] = None
        other['title'] = '《虛構：另一部》'
        other['editions'][0]['isbn'] = ['']
        fx['candidate']['editions'][0]['isbn'] = ['']
        self.assertEqual(find_match([other], fx['candidate'], fx['assessment'])[0], 'none')

    def test_adaptation_has_separate_work_identity(self):
        fx = fixture('04-adaptation.json')
        self.assertNotEqual(fx['records'][0]['id'], fx['candidate']['id'])
        self.assertEqual(fx['records'][0]['adaptation_of'], fx['candidate']['id'])
        self.assertEqual(evaluate(fx)['duplicate'], 'adaptation')
        self.assertEqual(evaluate(fx)['action'], 'Borrow')

    def test_tv_three_outputs_and_price_pair(self):
        fx = fixture()
        fx['candidate']['media'] = 'tv'
        fx['assessment']['reason'] = '虛構：新的敘事視角與已知作品互補'
        out = evaluate(fx)
        self.assertEqual(out['watch_advice']['verdict'], '待看')
        self.assertTrue(out['watch_advice']['reason'])
        self.assertEqual(out['acquisition'], {'status':'unknown','platform':None})
        self.assertEqual(out['collection_value'], {'value':'unknown'})
        fx['assessment']['price']['sale'] = False
        second = evaluate(fx)
        self.assertEqual((out['score'], out['watch_advice']), (second['score'], second['watch_advice']))

    def test_unverified_platform_is_unknown_and_region_limit_preserved(self):
        fx = fixture()
        fx['candidate']['media'] = 'anime'
        fx['assessment']['acquisition'] = {'status':'confirmed','platform':'虛構平台'}
        self.assertEqual(evaluate(fx)['acquisition']['status'], 'unknown')
        fx['assessment']['acquisition'].update(status='region_limited',region='虛構地區',source='synthetic-check',checked_at='2026-01-01T00:00:00Z')
        self.assertEqual(evaluate(fx)['acquisition']['status'], 'region_limited')


class ProgressAndConflicts(unittest.TestCase):
    def setUp(self):
        self.scope = {'work_id':'synthetic-work','edition_id':'translation-a','run_id':'initial','scope':'whole'}

    def observation(self, field, value, source='platform', at='2026-02-01T00:00:00Z', **extra):
        return dict(self.scope, field=field, value=value, source=source, observed_at=at, **extra)

    def test_manual_completion_not_downgraded(self):
        observations = [self.observation('progress.state','completed','manual',explicit=True),
                        self.observation('progress.state','in_progress',at='2026-03-01T00:00:00Z')]
        original = deepcopy(observations)
        out = resolve_field(observations,'progress.state',self.scope,True)
        self.assertEqual(out['value'],'completed')
        self.assertEqual(out['provenance']['source'],'manual')
        self.assertEqual(len(out['observations']),2)
        self.assertFalse(out['needs_confirmation'])
        self.assertEqual(original,observations)

    def test_different_edition_or_season_not_a_conflict(self):
        observations = [self.observation('progress.state','completed','manual',explicit=True),
                        dict(self.observation('progress.state','in_progress'),edition_id='translation-b'),
                        dict(self.observation('progress.state','in_progress'),scope='season',season=2)]
        out = resolve_field(observations,'progress.state',self.scope,True)
        self.assertEqual(out['value'],'completed')
        self.assertFalse(out['unresolved'])

    def test_resolution_requires_full_scope(self):
        with self.assertRaises(ValueError):
            resolve_field([], 'progress.state', {'work_id':'w','edition_id':'e'})
        with self.assertRaises(ValueError):
            resolve_field([], 'ownership', {'work_id':'w','edition_id':'e'})

    def test_missing_sync_does_not_remove_ownership_or_history(self):
        scope = {'work_id':'w','edition_id':'e','carrier':'print','platform':'manual'}
        observations = [dict(scope,field='ownership',value='owned',source='manual',explicit=True,observed_at='2026-01-01T00:00:00Z'),
                        dict(scope,field='ownership',value=None,missing=True,source='platform',observed_at='2026-02-01T00:00:00Z')]
        self.assertEqual(resolve_field(observations,'ownership',scope)['value'],'owned')
        observations.append(dict(scope,field='ownership',value='not_owned',source='platform',observed_at='2026-03-01T00:00:00Z'))
        self.assertEqual(resolve_field(observations,'ownership',scope)['value'],'owned')

    def test_ownership_platforms_separate_and_manual_disposal_explicit(self):
        scope = {'work_id':'w','edition_id':'e','carrier':'ebook','platform':'store-a'}
        observations = [dict(scope,field='ownership',value='owned',source='platform',observed_at='2026-01-01T00:00:00Z'),
                        dict(scope,field='ownership',value='not_owned',source='manual',explicit=True,observed_at='2026-02-01T00:00:00Z'),
                        dict(scope,platform='store-b',field='ownership',value='owned',source='platform',observed_at='2026-03-01T00:00:00Z')]
        self.assertEqual(resolve_field(observations,'ownership',scope)['value'],'not_owned')
        self.assertEqual(resolve_field(observations,'ownership',dict(scope,platform='store-b'))['value'],'owned')

    def test_ask_only_if_unresolved_and_affects_decision(self):
        observations = [self.observation('intent.purchase','want'), self.observation('intent.purchase','declined')]
        self.assertFalse(resolve_field(observations,'intent.purchase',self.scope)['needs_confirmation'])
        self.assertTrue(resolve_field(observations,'intent.purchase',self.scope,True)['needs_confirmation'])
        observations.append(self.observation('intent.purchase','declined','manual',explicit=True))
        for _ in range(2):
            self.assertFalse(resolve_field(observations,'intent.purchase',self.scope,True)['needs_confirmation'])

    def test_last_viewed_date_not_taken_from_sync_date(self):
        observed = self.observation('progress.last_viewed_at','2026-02-01T00:00:00Z')
        self.assertIsNone(resolve_field([observed],'progress.last_viewed_at',self.scope)['value'])
        observed['event_at'] = '2026-02-01T00:00:00Z'
        self.assertEqual(resolve_field([observed],'progress.last_viewed_at',self.scope)['value'],observed['event_at'])

    def test_actual_viewing_date_keeps_precision_and_uses_latest_event(self):
        old = self.observation('progress.last_viewed_at','2026-01-01','manual',explicit=True,event_at='2026-01-01')
        newer = self.observation('progress.last_viewed_at','2026-01-10',event_at='2026-01-10')
        out = resolve_field([old,newer],'progress.last_viewed_at',self.scope)
        self.assertEqual(out['value'],'2026-01-10')
        self.assertEqual(out['provenance']['source'],'platform')

    def test_completed_position_never_regresses_from_platform(self):
        observations = [self.observation('progress.last_completed',{'season':1,'episode':10},'manual',explicit=True),
                        self.observation('progress.last_completed',{'season':1,'episode':3},at='2026-03-01T00:00:00Z')]
        self.assertEqual(resolve_field(observations,'progress.last_completed',self.scope)['value']['episode'],10)

    def example(self):
        return load_template(ROOT / 'templates/examples/versions-and-progress.yaml')

    def test_edition_progress_intent_and_holdings_are_independent(self):
        book = self.example()['works'][0]
        a,b = book['editions']
        self.assertEqual(a['personal']['progress']['state'],'completed')
        self.assertEqual(b['personal']['progress']['state'],'not_started')
        self.assertEqual(b['personal']['holdings'][0]['ownership'],'owned')
        self.assertNotIn('status',book)
        self.assertNotIn('status',a)
        b['personal']['intent']['purchase'] = 'declined'
        self.assertEqual(a['personal']['progress']['state'],'completed')
        self.assertEqual(b['personal']['holdings'][0]['ownership'],'owned')

    def test_season_finale_never_increments_blindly(self):
        edition = self.example()['works'][1]['editions'][0]
        edition['personal']['progress'].update(last_completed={'season':1,'episode':12},partial=None)
        self.assertEqual(resume_position(edition), {'position':None,'reason':'待確認'})
        edition['episode_catalog']['positions'].append({'season':2,'episode':1})
        self.assertEqual(resume_position(edition)['position'], {'season':2,'episode':1})

    def test_partial_episode_is_separate_and_resumes_same_episode(self):
        edition = self.example()['works'][1]['editions'][0]
        progress = edition['personal']['progress']
        progress.update(last_completed={'season':1,'episode':3},partial={'season':1,'episode':4,'position_seconds':600})
        self.assertEqual(resume_position(edition)['position'],progress['partial'])
        self.assertEqual(progress['last_completed']['episode'],3)

    def test_rewatch_does_not_erase_completed_history(self):
        edition = self.example()['works'][0]['editions'][0]
        before = deepcopy(edition)
        updated = add_revisit(edition, {'run_id':'reread-1','state':'paused','last_completed':None,'partial':None,'observations':[]})
        self.assertEqual(edition,before)
        self.assertEqual(updated['personal']['progress']['completions'],before['personal']['progress']['completions'])
        self.assertEqual(updated['personal']['progress']['state'],'completed')
        work = self.example()['works'][0]
        work['editions'][0] = updated
        self.assertIn((work['id'],updated['id'],'reread-1',None),unfinished([work]))

    def test_stale_paused_record_is_not_auto_dropped(self):
        example = self.example()
        anime = example['works'][1]
        self.assertIn((anime['id'],anime['editions'][0]['id'],'initial',2),unfinished(example['works']))
        self.assertEqual(anime['editions'][0]['personal']['progress']['state'],'paused')

    def test_season_progress_is_independent_and_recoverable(self):
        example = self.example()
        anime = example['works'][1]
        edition = anime['editions'][0]
        seasons = edition['personal']['progress']['seasons']
        self.assertEqual((seasons[0]['state'],seasons[1]['state']),('completed','paused'))
        self.assertEqual(resume_position(edition,season=2)['position'],{'season':2,'episode':4,'position_seconds':600})
        seasons[0].update(state='paused',last_completed_episode=3)
        pending = unfinished([anime])
        self.assertIn((anime['id'],edition['id'],'initial',1),pending)
        self.assertIn((anime['id'],edition['id'],'initial',2),pending)


class ReviewRegressions(unittest.TestCase):
    """PR review 指出的三個 oracle 漏洞。"""
    scope = {'work_id': 'w', 'edition_id': 'e', 'run_id': 'initial', 'scope': 'whole'}

    def obs(self, value, source, at, **extra):
        return dict(self.scope, field='progress.state', value=value, source=source, observed_at=at, **extra)

    def test_manual_correction_survives_later_platform_sync(self):
        observations = [self.obs('completed', 'platform', '2026-01-01T00:00:00Z'),
                        self.obs('in_progress', 'manual', '2026-02-01T00:00:00Z', explicit=True, correction=True, reason='誤標'),
                        self.obs('in_progress', 'platform', '2026-03-01T00:00:00Z')]
        out = resolve_field(observations, 'progress.state', self.scope, True)
        self.assertEqual(out['value'], 'in_progress')
        self.assertFalse(out['needs_confirmation'])
        self.assertEqual(len(out['observations']), 3, '被修正的候選值仍保留在 observations')
        # 修正之後出現新的完成證據，才可以再翻回 completed。
        observations.append(self.obs('completed', 'manual', '2026-04-01T00:00:00Z', explicit=True))
        self.assertEqual(resolve_field(observations, 'progress.state', self.scope)['value'], 'completed')

    def test_wishlist_hit_does_not_hide_owned_overlap(self):
        fx = fixture('01-owned-unread-overlap.json')
        wished = deepcopy(fx['candidate'])
        wished['editions'][0]['personal']['intent']['purchase'] = 'want'
        fx['records'].append(wished)
        out = evaluate(fx)
        self.assertEqual(out['duplicate'], 'edition_only')
        self.assertEqual(out['action'], '先讀書庫')
        self.assertTrue(any('海洋法十講' in line for line in out['text']))

    def test_related_work_rejection_is_not_inherited(self):
        fx = fixture('04-adaptation.json')
        anime = fx['records'][0]['editions'][0]['personal']['intent']
        anime.update(purchase='declined', reject_reason='不想買動畫光碟')
        out = evaluate(fx)
        self.assertEqual(out['duplicate'], 'adaptation')
        self.assertEqual(out['action'], 'Borrow')
        self.assertFalse(out['reuses_reject_reason'])
        self.assertFalse(any('不想買動畫光碟' in line for line in out['text']))
        # 同一作品的拒絕仍然沿用。
        fx = fixture('05a-previously-rejected.json')
        self.assertTrue(evaluate(fx)['reuses_reject_reason'])


class PackagingAndSchedule(unittest.TestCase):
    def test_clean_skill_install_has_all_references(self):
        with tempfile.TemporaryDirectory() as td:
            installed = Path(td) / 'installed-skill'
            shutil.copytree(ROOT / 'skill',installed)
            self.assertEqual(skill_references(installed),[])
            self.assertTrue((installed / 'references/boundaries.md').is_file())
            self.assertTrue((installed / 'references/settings.yaml').is_file())
            with (installed / 'SKILL.md').open('a') as handle:
                handle.write('\n[missing boundary](../ROLE.md)\n')
            self.assertTrue(skill_references(installed))

    def test_settings_copies_identical_and_all_schedules_disabled(self):
        self.assertEqual((ROOT / 'templates/settings.yaml').read_bytes(),(ROOT / 'skill/references/settings.yaml').read_bytes())
        settings = load_template(ROOT / 'templates/settings.yaml')
        for task in settings['schedule'].values():
            self.assertIs(task['enabled'],False)
            self.assertEqual(validate_schedule(task),[])

    def test_active_schedule_requires_explicit_contract(self):
        task = deepcopy(load_template(ROOT / 'templates/settings.yaml')['schedule']['daily_deal'])
        task['enabled'] = True
        self.assertTrue(set(('source','output','timezone','time','trial_succeeded','user_confirmed')) <= set(validate_schedule(task)))
        task.update(source='synthetic-source',output='conversation',timezone='Europe/Lisbon',time='20:00',trial_succeeded=True,user_confirmed=True)
        self.assertEqual(validate_schedule(task),[])
        task['timezone'] = 'Not/AZone'
        self.assertIn('timezone',validate_schedule(task))

    def test_weekly_monthly_and_interval_contracts(self):
        base = dict(enabled=True,source='synthetic',output='conversation',timezone='Etc/UTC',trial_succeeded=True,user_confirmed=True,report_mode='full_list')
        for task in (dict(base,cadence='weekly',time='20:00',weekday=0),
                     dict(base,cadence='monthly',time='20:00',day_of_month=31,missing_day='skip'),
                     dict(base,cadence='interval',interval_minutes=60)):
            self.assertEqual(validate_schedule(task),[])
        self.assertIn('weekday',validate_schedule(dict(base,cadence='weekly',time='20:00',weekday=7)))
        self.assertIn('interval_minutes',validate_schedule(dict(base,cadence='interval',interval_minutes=59)))
        self.assertIn('time',validate_schedule(dict(base,cadence='interval',interval_minutes=60,time='20:00')))

    def test_recommendations_strictly_over_60_vs_complete_report(self):
        self.assertFalse(should_report(60,'recommendations'))
        self.assertTrue(should_report(61,'recommendations'))
        self.assertFalse(should_report(None,'recommendations'))
        for score in (None,0,40,60,61):
            self.assertTrue(should_report(score,'full_list'))


class PrivacyGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / 'package'
        shutil.copytree(ROOT,self.package)

    def run_gate(self,*args):
        return subprocess.run([sys.executable,'-B',str(self.package / 'tools/privacy_check.py'),*map(str,args)],capture_output=True,text=True)

    def add_allowed(self,path,content):
        (self.package / path).write_text(content)
        with (self.package / 'ALLOWLIST.txt').open('a') as handle:
            handle.write(path + '\n')

    def test_clean_package_and_external_report(self):
        before = {p.relative_to(self.package) for p in self.package.rglob('*') if p.is_file()}
        report = Path(self.temp.name) / 'audit.md'
        result = self.run_gate('--report',report)
        self.assertEqual(result.returncode,0,result.stdout + result.stderr)
        self.assertTrue(report.is_file())
        self.assertEqual(before,{p.relative_to(self.package) for p in self.package.rglob('*') if p.is_file()})

    def test_unallowlisted_file_in_cache_directory_is_rejected(self):
        folder = self.package / '__pycache__'
        folder.mkdir()
        (folder / 'unlisted.txt').write_text('synthetic text')
        result = self.run_gate()
        self.assertEqual(result.returncode,1)
        self.assertIn('__pycache__/unlisted.txt',result.stdout)

    def test_allowlisted_csv_is_scanned_for_generic_secrets(self):
        value = 'synthetic' + '@example.invalid'
        self.add_allowed('list.csv','email\n' + value + '\n')
        result = self.run_gate()
        self.assertEqual(result.returncode,1)
        self.assertIn('generic:email',result.stdout)
        self.assertNotIn(value,result.stdout)

    def test_csv_private_patterns_and_synthetic_catalog_are_scanned(self):
        title = 'SYNTHETIC' + '_TITLE_VALUE'
        self.add_allowed('list.csv','title\n' + title + '\n')
        patterns = Path(self.temp.name) / 'patterns.txt'
        patterns.write_text(title + '\n')
        catalog = Path(self.temp.name) / 'catalog.json'
        catalog.write_text(json.dumps({'library':[{'t':title}],'wishlist':[]}))
        result = self.run_gate('--private-patterns',patterns,'--catalog-json',catalog)
        self.assertEqual(result.returncode,1)
        self.assertIn('private_pattern',result.stdout)
        self.assertIn('catalog_title',result.stdout)
        self.assertNotIn(title,result.stdout)

    def test_unknown_extension_text_is_also_scanned(self):
        self.add_allowed('sample.data','synthetic' + '@example.invalid')
        self.assertEqual(self.run_gate().returncode,1)

    def test_package_report_rejected_without_creating_or_overwriting(self):
        new = self.package / 'audit.md'
        self.assertEqual(self.run_gate('--report',new).returncode,1)
        self.assertFalse(new.exists())
        existing = self.package / 'README.md'
        before = existing.read_bytes()
        self.assertEqual(self.run_gate('--report',existing).returncode,1)
        self.assertEqual(existing.read_bytes(),before)

    def test_report_symlink_into_package_rejected(self):
        destination = Path(self.temp.name) / 'link'
        destination.symlink_to(self.package,target_is_directory=True)
        self.assertEqual(self.run_gate('--report',destination / 'audit.md').returncode,1)
        self.assertFalse((self.package / 'audit.md').exists())

    def test_binary_even_allowlisted_is_rejected(self):
        path = self.package / 'sample.bin'
        path.write_bytes(bytes([255,254,0]))
        with (self.package / 'ALLOWLIST.txt').open('a') as handle:
            handle.write('sample.bin\n')
        self.assertEqual(self.run_gate().returncode,1)

    def test_package_symlink_is_rejected(self):
        (self.package / 'link.txt').symlink_to(self.package / 'README.md')
        with (self.package / 'ALLOWLIST.txt').open('a') as handle:
            handle.write('link.txt\n')
        self.assertEqual(self.run_gate().returncode,1)


if __name__ == '__main__':
    unittest.main()
