"""Evidence boundaries, compatibility and deterministic progression, using fictional work."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from gallop.automation.elite_protocol import DIMENSIONS, failure_registry, resource, validate
from gallop.automation.elite_state import benchmark_summary, empty, readiness_profile
from gallop.automation.protocol import digest
from gallop.automation.service import Automation
from gallop.automation.state import replay
from gallop.automation.store import JournalConflict
from gallop.automation.views import render
from gallop.core.validation import validate_protocol
from test_automation import app, accept, put, result, session, work

EXAMPLES = Path(__file__).parents[2] / 'examples/elite'


def sample(name='mathematics'):
    return json.loads((EXAMPLES / (name + '.json')).read_text(encoding='utf-8'))


def record(index=1, **changes):
    r = sample()
    r.update(evidence_id='e-' + str(index), occurred_at=f'2026-01-{index:02d}T12:00:00Z',
             task_type='HARD_PROBLEM', assessment_context='TRAINING')
    r['metadata'] = dict(context_id='context-' + str(index), attempt_id='attempt-' + str(index))
    r.update(changes)
    return r


def add(app, r, kind='elite_evidence', confirmed=True):
    return app.add_record(kind, put(app, r), confirm_human=confirmed)


def dimension(app, name='Proof Maturity', subject='mathematics'):
    return app.readiness(subject=subject, dimension=name)


def test_v10_frozen_oracle_exact_replay_and_prefixes():
    oracle = json.loads((Path(__file__).parents[1] / 'fixtures/v1-replay.json').read_text(encoding='utf-8'))
    assert oracle['baseline_commit'] == 'c8d0dfdcdee1dd002688ebf43d20bd2b48766fc8'
    actual = replay(oracle['events'])
    assert actual == oracle['expected_state']
    assert 'elite' not in actual
    assert max(c['mastery_level'] for c in actual['concepts'].values()) == 2
    prior = ''
    for event in oracle['events']:
        assert event['previous_hash'] == prior
        assert digest({k:v for k,v in event.items() if k != 'hash'}) == event['hash']
        prior = event['hash']
    assert render(actual, 'integration_tests') == render(oracle['expected_state'], 'integration_tests')


def test_all_readiness_dimensions_unknown_without_mutation(app):
    before = app.state()
    profiles = app.readiness()
    assert [len(p['dimensions']) for p in profiles] == [15, 18, 20, 25]
    for profile in profiles:
        validate_protocol('readiness-profile.schema.json', profile)
        assert all(r['status'] == 'UNKNOWN' and r['confidence'] == 'low' and
                   r['evidence_count'] == 0 and not r['evidence_refs'] for r in profile['dimensions'])
    assert app.state() == before
    with pytest.raises(ValueError, match='ambiguous'):
        app.readiness(dimension='Independence')


@pytest.mark.parametrize('changes', [
    {'independence_class':'INDEPENDENT','hint_level':5},
    {'independence_class':'SOLUTION_SEEN','hint_level':0},
    {'independence_class':'HINT_1','hint_level':3},
    {'independence_class':'HINT_2','hint_level':4},
    {'independence_class':'ASSISTED','hint_level':1},
    {'agent_usage':'AI_GENERATED'}, {'agent_usage':'AI_ASSISTED'}, {'agent_usage':'HINT_ONLY'},
    {'task_type':'NO_AGENT_CODING','agent_usage':'REFERENCE_ONLY'},
    {'independence_class':'UNSOLVED','result':'PASS'}, {'hint_level':6}, {'time_spent':-1},
    {'proof_quality':{'logical_completeness':99}}, {'failure_modes':['stats:NEW_UNREGISTERED']},
    {'failure_modes':['not-a-namespace']}, {'readiness_dimensions':['Identification']},
    {'occurred_at':'2099-01-01T00:00:00Z'}, {'occurred_at':'2026-01-01T00:00:00'},
    {'namespace':'learner'}, {'integration_test':False}, {'metadata':{'attempt_id':False}},
])
def test_invalid_evidence_fails_closed_atomically(app, changes):
    with pytest.raises(ValueError):
        add(app, record(**changes))
    assert not app.store.events()
    assert app.store.db.execute('SELECT count(*) FROM raw_inputs').fetchone()[0] == 1


def test_missing_fields_remain_absent_not_independent(app):
    r = {k:v for k,v in record().items() if k in {'schema_version','evidence_id','subject','concept','task_type','occurred_at','source','result'}}
    add(app,r)
    stored = app.records('elite_evidence')[0]['record']
    assert stored == r and 'agent_usage' not in stored
    assert app.explain(r['concept'])['mastery_level'] == 0
    assert dimension(app)['status'] == 'UNKNOWN'


@pytest.mark.parametrize('name,hint,agent,outcome', [
    ('HINT_1',1,'HINT_ONLY','PASS'), ('HINT_2',2,'HINT_ONLY','PASS'),
    ('HINT_2',3,'HINT_ONLY','PASS'), ('ASSISTED',4,'AI_ASSISTED','PASS'),
    ('SOLUTION_SEEN',5,'NONE','PASS'), ('UNSOLVED',0,'NONE','UNSOLVED'),
])
def test_assistance_never_independent_mastery(app,name,hint,agent,outcome):
    for i in range(1,4):
        add(app,record(i, independence_class=name,hint_level=hint,agent_usage=agent,result=outcome))
    assert app.explain('Invariant proof')['mastery_level'] == 0
    assert dimension(app,'Independence')['status'] == 'UNKNOWN'
    assert dimension(app)['status'] in {'UNKNOWN','FOUNDATIONAL'}


def test_solution_seen_exception_requires_reason_and_never_credit(app):
    r=record(independence_class='SOLUTION_SEEN',hint_level=0)
    r['metadata']['hint_consistency_reason']='Solution was read separately; hint button was never used.'
    add(app,r)
    assert app.explain(r['concept'])['mastery_level'] == 0
    assert app.explain(r['concept'])['last_practiced'] is None


def test_registry_extension_is_additive_and_replay_ignores_current_registry(app):
    extension=put(app,{'custom':['SPARSE_EXPERIENCE']},'registry.json')
    app.config=replace(app.config,failure_modes=extension)
    r=record(failure_modes=['custom:SPARSE_EXPERIENCE','math:PROOF_INCOMPLETE'])
    add(app,r)
    before=app.state()
    app.config=replace(app.config,failure_modes=None)
    assert app.state()==before
    assert 'custom:SPARSE_EXPERIENCE' in app.explain(r['concept'])['weakness_tags']
    assert 'core:TIME_MANAGEMENT' in failure_registry(extension)
    with pytest.raises(ValueError):
        add(app,record(2,failure_modes=['custom:SPARSE_EXPERIENCE']))


def test_idempotence_conflict_and_readiness_audit(app):
    r=record()
    first=add(app,r)
    before=app.state()
    assert add(app,r)['duplicate']
    assert app.state()==before
    assert first['event_id'] in dimension(app)['evidence_refs']
    with pytest.raises(JournalConflict):
        add(app,{**r,'result':'FAIL'})
    assert app.state()==before
    events=app.store.events()
    assert any(e['kind']=='readiness_transition' for e in events)
    with pytest.raises(JournalConflict,match='Missing readiness'):
        replay([e for e in events if e['kind']!='readiness_transition'])
    altered=deepcopy(events)
    next(e for e in altered if e['kind']=='readiness_transition')['payload']['after']='ADVANCED'
    with pytest.raises(JournalConflict):
        replay(altered)
    assert app.rebuild_state()['replaced']


def test_duplicate_attempt_and_unconfirmed_attestation(app):
    r=record()
    add(app,r,confirmed=False)
    assert dimension(app)['status']=='UNKNOWN'
    add(app,{**r,'evidence_id':'explicit-human-attestation'},confirmed=True)
    assert len(dimension(app)['independent_evidence'])==1
    for i in range(3):
        add(app,{**r,'evidence_id':f'duplicate-{i}'})
    assert len(dimension(app)['independent_evidence'])==1
    assert app.explain(r['concept'])['mastery_level']==0
    bad=deepcopy(r)
    bad.update(evidence_id='later-assistance-disclosure',independence_class='ASSISTED',hint_level=4,agent_usage='AI_ASSISTED')
    add(app,bad)
    assert not dimension(app)['independent_evidence']
    assert dimension(app,'Independence')['status']=='UNKNOWN'


def test_repeated_context_or_single_day_never_creates_readiness(app):
    for i in range(1,5):
        r=record(i)
        r['metadata']['context_id']='same-template'
        add(app,r)
    assert dimension(app)['status']=='FOUNDATIONAL'
    assert app.explain('Invariant proof')['mastery_level']==0


def transfer():
    return dict(status='SUCCESS',source_context='trained-template',target_context='novel-context',
                independence_class='INDEPENDENT',novelty='NEW_CONTEXT',evidence_refs=['reviewed-transfer-response'])


@pytest.mark.parametrize('change', [{'novelty':'NEAR_IDENTICAL'}, {'target_context':'trained-template'},
                                    {'evidence_refs':[]}, {'independence_class':'INDEPENDENT','source_context':''}])
def test_transfer_requires_novelty_and_provenance(app,change):
    with pytest.raises(ValueError):
        add(app,record(transfer_status={**transfer(),**change}))


def test_progression_diversity_transfer_benchmark_and_failure(app):
    for i in range(1,4):
        add(app,record(i,task_type='HARD_PROBLEM' if i<3 else 'ORAL_EXAM'))
    assert app.explain('Invariant proof')['mastery_level']==2
    assert dimension(app)['status']=='SOLID'
    fourth=record(4,transfer_status=transfer())
    add(app,fourth)
    assert app.explain('Invariant proof')['mastery_level']==3
    assert dimension(app)['status']=='STRONG'
    b=sample('benchmark')
    b['evidence_refs']=['e-4']  # A normal training record is not a benchmark performance.
    add(app,b,'benchmark')
    add(app,record(5,task_type='BENCHMARK',assessment_context='BENCHMARK',benchmark_source=b['source'],
                   metadata={'attempt_id':'attempt-5','context_id':'context-5','closed_book':True,'no_ai':True}))
    assert app.explain('Invariant proof')['mastery_level']==3
    b2={**b,'benchmark_id':'actual-benchmark','date':'2026-01-05','evidence_refs':['e-5']}
    add(app,b2,'benchmark')
    assert app.explain('Invariant proof')['mastery_level']==3  # Recording a benchmark cannot promote.
    sixth=record(6,task_type='ORAL_EXAM',occurred_at='2026-02-08T12:00:00Z')
    add(app,sixth)
    assert dimension(app)['status']=='ADVANCED'
    assert app.explain('Invariant proof')['mastery_level']==4  # At most one level per performance.
    add(app,record(7,result='FAIL',occurred_at='2026-02-09T12:00:00Z',failure_modes=['math:PROOF_INCOMPLETE']))
    assert app.explain('Invariant proof')['mastery_level']==4
    assert app.explain('Invariant proof')['confidence']=='low'
    assert dimension(app)['confidence']=='low'
    assert dimension(app)['evidence_refs'] and dimension(app)['reason']


def test_proof_quality_not_inferred_from_passing_score(app):
    for i in range(1,4):
        r=record(i,task_type='PROOF')
        r.pop('proof_quality')
        add(app,r)
    assert dimension(app)['status']=='UNKNOWN'
    assert app.explain('Invariant proof')['mastery_level']==0


@pytest.mark.parametrize('benchmark_type',['IMC','YAU','MINI_CONTEST','CLOSED_BOOK','ORAL','NO_AGENT','COURSE_EXAM','CUSTOM'])
def test_benchmark_without_score_is_first_class(app,benchmark_type):
    add(app,sample())
    b=sample('benchmark')
    b['benchmark_type']=benchmark_type
    add(app,b,'benchmark')
    summary=app.records('benchmark')[0]['summary']
    assert summary['score'] is None
    assert summary['independent_solve_rate']==1
    assert summary['hint_dependence']==0
    assert summary['mean_seconds_per_attempt']==1200
    assert app.explain('Invariant proof')['mastery_level']==0


@pytest.mark.parametrize('changes',[{'attempted':2},{'solved':2},{'partial':1},{'score':10,'max_score':5},
                                     {'benchmark_type':'CLOSED_BOOK','closed_book':False}])
def test_benchmark_impossible_counts_rejected(app,changes):
    add(app,sample())
    before=app.state()
    with pytest.raises(ValueError):
        add(app,{**sample('benchmark'),**changes},'benchmark')
    assert app.state()==before


def test_benchmark_missing_denominators_and_context_not_fabricated(app):
    add(app,record())
    b=sample('benchmark')
    b['evidence_refs']=['e-1']
    for key in ('problems_total','attempted','solved','partial','duration'):
        b.pop(key)
    add(app,b,'benchmark')
    summary=app.records('benchmark')[0]['summary']
    assert summary['independent_solve_rate'] is None and summary['partial_solve_rate'] is None
    assert summary['mean_seconds_per_attempt'] is None
    assert summary['independent_performances']==0


def test_explicit_links_readonly_no_curriculum_and_no_invented_gap(app):
    add(app,sample('statistics'))
    assert not app.explain('Identification')['elite']['prerequisite_gaps']
    queue=app.queue()
    add(app,sample('prerequisite'),'prerequisite_link')
    explanation=dimension(app,'Identification','statistics')
    assert explanation['prerequisite_gaps'][0]['gap']=='NOT_RECORDED'
    assert explanation['prerequisite_gaps'][0]['curriculum_action']=='NONE'
    assert app.queue()==queue
    link=sample('prerequisite')
    link.update(link_id='informational-only',relation='RELATED')
    add(app,link,'prerequisite_link')
    assert app.explain('Identification')['elite']['prerequisite_gaps'][1]['gap']=='INFORMATIONAL_LINK'


def test_tutor_extension_optional_unconfirmed_atomic_and_legacy_unchanged(app):
    r=record()
    value=session(elite_evidence=[r])
    accept(app,value)
    assert len(app.records('elite_evidence'))==1
    assert not app.records('elite_evidence')[0]['confirmed']
    assert dimension(app)['status']=='UNKNOWN'
    before=app.state()
    assert accept(app,value)['duplicate']
    assert app.state()==before
    bad=session(session_id='invalid-extension',elite_evidence=[sample('finance')])
    with pytest.raises(ValueError):
        accept(app,bad)
    assert app.state()==before


def test_human_result_extension_is_not_double_counted(app):
    q,p=work(app)
    r=record(concept=q['concept'])
    data=result(q,p)
    data['elite_evidence']=[r]
    app.ingest_result(put(app,data),confirm_human=True)
    concept=app.explain(q['concept'])
    assert concept['successes']==[]
    assert len(concept['elite']['independent_evidence'])==1
    assert concept['mastery_level']==0
    assert app.ingest_result(put(app,data),confirm_human=True)['duplicate']


def test_result_extension_conflicting_hint_is_atomic(app):
    q,p=work(app)
    r=record(concept=q['concept'],independence_class='HINT_2',hint_level=3,agent_usage='HINT_ONLY')
    data=result(q,p)
    data['elite_evidence']=[r]
    before=app.state()
    with pytest.raises(ValueError):
        app.ingest_result(put(app,data),confirm_human=True)
    assert app.state()==before


def test_manifest_optional_metadata_is_request_not_telemetry(app,tmp_path):
    from gallop.adapters.deeptutor import DeepTutorAdapter
    accept(app)
    q=app.queue()[0]
    prepared=app.prepare(q['queue_id'],question_count=1,elite=sample('request-policy'))
    executable=tmp_path/'fake-engine'
    executable.write_text('controlled test')
    adapter=DeepTutorAdapter(executable)
    command,_=adapter.request(prepared['manifest'])
    assert 'elite_request' in command[3] and 'desired_independence' in command[3]
    decoded=adapter.decode(prepared['manifest'],json.dumps({'questions':[{'question':'Controlled prompt'}]}))
    assert 'hint_level' not in decoded and 'agent_usage' not in decoded and 'time_spent' not in decoded
    observed=adapter.decode(prepared['manifest'],json.dumps({'questions':[{
        'question':'Observed prompt','hint_level':2,'time_spent':45,'agent_usage':'HINT_ONLY'}]}))
    assert observed['telemetry']==[{'question_id':'q1','hint_level':2,'time_spent':45,'agent_usage':'HINT_ONLY'}]
    assert 'telemetry' not in decoded
    assert app.explain('Continuity')['mastery_level']==0
    with pytest.raises(JournalConflict):
        app.prepare(q['queue_id'],elite={'desired_independence':'ASSISTED'})


def test_elite_views_keep_metadata_answers_and_private_paths_out(app):
    r=record()
    r['metadata']['private_answer']='DO_NOT_PROJECT_THIS_ANSWER'
    r['evidence_refs']=['private-response-reference']
    add(app,r)
    original=render(app.state(),'integration_tests')['Today.md']
    app.publish()
    content='\n'.join(p.read_text(encoding='utf-8') for p in app.config.reader.rglob('*.md'))
    assert 'DO_NOT_PROJECT_THIS_ANSWER' not in content
    assert 'private-response-reference' not in content
    assert (app.config.reader/'Gallop/Automation/Readiness.md').exists()
    assert not list(app.config.reader.rglob('*.json')) and not list(app.config.reader.rglob('*.sqlite3'))
    assert render(app.state(),'integration_tests')['Today.md']==original
    assert app.publish()['written']==0
