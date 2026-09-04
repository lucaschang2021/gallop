"""Progressive mentorship remains advisory, evidence-backed and subject-neutral."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from gallop.automation.protocol import timestamp
from gallop.automation.views import render
from gallop.mentorship import POLICIES, capability, plan, weekly_feedback
from gallop.mentorship.models import CAPABILITY_STATES, SCAFFOLDING
from test_automation import app, put
from test_elite import add, record, sample

def target(**changes):
    value={'schema_version':'1.1','namespace':'integration_tests','integration_test':True,
        'target_id':'north-star-proof','subject':'mathematics','dimension':'Proof Maturity',
        'target_state':'RESEARCH_USABLE','description':'Independent unfamiliar rigorous proof and research use',
        'north_star':True,'prerequisite_refs':[],'created_at':'2026-01-01T08:00:00Z',
        'source':'Explicit synthetic mentorship target'}
    value.update(changes)
    return value

def add_target(app,value=None):
    return add(app,value or target(),'target_capability',False)

def mentorship(app,target_id='north-star-proof'):
    return app.mentorship(target_id)['plans'][0]

def staged(index,level,independence,hint,agent,**changes):
    value=record(index,scaffolding_level=level,training_zone='PRODUCTIVE',
                 independence_class=independence,hint_level=hint,agent_usage=agent)
    value.update(changes)
    return value

def independent(index,**changes):
    return staged(index,'S0','INDEPENDENT',0,'NONE',**changes)

def test_high_target_never_invents_current_or_monster_daily_work(app):
    add_target(app)
    p=mentorship(app)
    assert p['target']['target_state']=='RESEARCH_USABLE'
    assert p['current_capability']['current_state']=='UNKNOWN'
    assert p['training_zone']=='FOUNDATION' and p['scaffolding_level']=='S5'
    assert p['queue_mutation']=='NONE' and app.queue()==[]
    assert p['mentor_role']['role']=='TEACHER'

@pytest.mark.parametrize('changes',[{'target_state':'UNKNOWN'},{'dimension':'Identification'},
    {'subject':'unknown'},{'north_star':'yes'},{'prerequisite_refs':['x','x']},
    {'created_at':'2099-01-01T00:00:00Z'},{'namespace':'learner'},{'integration_test':False}])
def test_target_schema_and_semantics_fail_atomically(app,changes):
    with pytest.raises(ValueError): add_target(app,{**target(),**changes})
    assert not app.store.events()

def test_target_idempotence_and_tutor_optional_extension(app):
    first=add_target(app); before=app.state()
    assert add_target(app)['duplicate'] and app.state()==before
    with pytest.raises(ValueError): add_target(app,{**target(),'description':'Changed target'})
    from test_automation import session
    second={**target(),'target_id':'tutor-target','source':'Synthetic tutor'}
    value=session(progressive_mentorship={'target_capabilities':[second]})
    app.intake(put(app,value))
    assert app.records('target_capability','tutor-target')[0]['confirmed'] is False
    assert app.mentorship('tutor-target')['plans'][0]['current_capability']['current_state']=='UNKNOWN'

def test_scaffolding_fades_one_step_per_matching_evidence(app):
    add_target(app)
    sequence=[('S5','ASSISTED',4,'AI_ASSISTED'),('S4','HINT_2',3,'HINT_ONLY'),
              ('S3','HINT_2',2,'HINT_ONLY'),('S2','HINT_1',1,'HINT_ONLY'),
              ('S1','INDEPENDENT',0,'NONE')]
    expected=['S4','S3','S2','S1','S0']
    for i,(level,ind,hint,agent) in enumerate(sequence,1):
        add(app,staged(i,level,ind,hint,agent))
        assert mentorship(app)['scaffolding_level']==expected[i-1]
    assert mentorship(app)['current_capability']['current_state']=='PARTIALLY_INDEPENDENT'
    assert len(mentorship(app)['current_capability']['scaffolding_evidence_refs'])==5

def test_scaffolding_cannot_jump_or_fade_without_success(app):
    add_target(app)
    add(app,staged(1,'S0','INDEPENDENT',0,'NONE'))
    assert mentorship(app)['scaffolding_level']=='S5'
    fail=staged(2,'S5','UNSOLVED',0,'NONE',result='UNSOLVED')
    add(app,fail)
    assert mentorship(app)['scaffolding_level']=='S5'

def test_high_designed_scaffolding_does_not_count_as_independent_mastery(app):
    add_target(app)
    for i,level in enumerate(('S5','S4','S3'),1): add(app,staged(i,level,'INDEPENDENT',0,'NONE'))
    p=mentorship(app)
    assert p['current_capability']['independent_evidence_count']==0
    assert app.explain('Invariant proof')['mastery_level']==0

def test_novice_to_elite_simulation_builds_path_without_lowering_summit(app):
    add_target(app)
    assert mentorship(app)['training_zone']=='FOUNDATION'
    sequence=[('S5','ASSISTED',4,'AI_ASSISTED'),('S4','HINT_2',3,'HINT_ONLY'),
              ('S3','HINT_2',2,'HINT_ONLY'),('S2','HINT_1',1,'HINT_ONLY'),('S1','INDEPENDENT',0,'NONE')]
    for i,args in enumerate(sequence,1): add(app,staged(i,*args))
    assert mentorship(app)['training_zone']=='PRODUCTIVE'
    for i in (6,7): add(app,independent(i))
    p=mentorship(app); assert p['current_capability']['current_state']=='INDEPENDENT'
    assert p['training_zone']=='STRETCH' and p['progression_action']=='ADD_TRANSFER_TEST'
    tr={'status':'SUCCESS','source_context':'known','target_context':'new','independence_class':'INDEPENDENT',
        'novelty':'NEW_CONTEXT','evidence_refs':['synthetic-transfer']}
    add(app,independent(8,transfer_status=tr,transfer_type='STRUCTURAL_TRANSFER'))
    assert mentorship(app)['current_capability']['current_state']=='TRANSFERRED'
    add(app,independent(9,retention={'delay_days':14,'closed_book':True,'evidence_refs':['delayed-response']}))
    assert mentorship(app)['current_capability']['current_state']=='RETAINED'
    for i in range(10,16):
        changes={'task_type':'RESEARCH','metadata':{'attempt_id':f'attempt-{i}','context_id':f'context-{i}',
                                                  'project_id':'fictional-project','research_component':True}}
        if i==10: changes.update(transfer_status=tr,transfer_type='RESEARCH_TRANSFER')
        if i==15: changes['retention']={'delay_days':30,'closed_book':True,'evidence_refs':['delayed-project']}
        add(app,independent(i,**changes))
    p=mentorship(app)
    assert p['target']['target_state']=='RESEARCH_USABLE' # fixed throughout
    assert p['current_capability']['current_state']=='RESEARCH_USABLE'
    assert p['training_zone']=='MONSTER_BENCHMARK'
    assert p['research_independence']['state']=='RI6'
    zones=['FOUNDATION','PRODUCTIVE','STRETCH','MONSTER_BENCHMARK']
    assert p['queue_mutation']=='NONE' and zones[-1]==p['training_zone']

def test_repeated_monster_failures_are_overchallenge_not_degradation(app):
    add_target(app)
    add(app,independent(1))
    before=app.explain('Invariant proof')['mastery_level']
    for i in (2,3,4):
        add(app,record(i,result='UNSOLVED',independence_class='UNSOLVED',hint_level=0,
            agent_usage='NONE',training_zone='MONSTER_BENCHMARK',difficulty='RESEARCH'))
    p=mentorship(app)
    assert p['progression_action']=='REDUCE_TASK_SPAN' and p['training_zone']=='FOUNDATION'
    assert [s['classification'] for s in p['productive_struggle']].count('OVERCHALLENGE')==3
    assert app.explain('Invariant proof')['mastery_level']==before
    assert p['current_capability']['current_state']=='PARTIALLY_INDEPENDENT'

def test_explicit_productive_failure_preserves_milestone(app):
    add_target(app)
    struggle={'classification':'PRODUCTIVE_FAILURE','reason':'Found the decisive lemma but proof remained incomplete',
              'milestones':['Correct lemma'],'evidence_refs':['fictional-partial-proof']}
    add(app,record(result='PARTIAL',independence_class='UNSOLVED',hint_level=0,
                   agent_usage='NONE',training_zone='STRETCH',productive_struggle=struggle))
    row=mentorship(app)['productive_struggle'][0]
    assert row['classification']=='PRODUCTIVE_FAILURE' and row['milestones']==['Correct lemma']
    assert app.explain('Invariant proof')['mastery_level']==0

@pytest.mark.parametrize('classification',['PRODUCTIVE_FAILURE','PREREQUISITE_FAILURE','OVERCHALLENGE',
                                             'CARELESS_FAILURE','CONCEPTUAL_FAILURE'])
def test_struggle_taxonomy_is_explicit_and_multiple_subject_neutral(app,classification):
    add_target(app)
    r=record(result='FAIL',independence_class='UNSOLVED',hint_level=0,agent_usage='NONE',
             productive_struggle={'classification':classification,'reason':'Synthetic classified failure','evidence_refs':['review']})
    add(app,r)
    assert mentorship(app)['productive_struggle'][0]['classification']==classification

def test_prerequisite_diagnosis_repair_then_retest_without_certifying_target(app):
    link=sample('prerequisite')
    add(app,link,'prerequisite_link')
    t=target(target_id='stats-target',subject='statistics',dimension='Identification',
             description='Independent IV identification',prerequisite_refs=[link['link_id']])
    add_target(app,t)
    for i in (1,2):
        add(app,record(i,subject='statistics',concept='Identification',task_type='HARD_PROBLEM',
            readiness_dimensions=['Identification'],result='FAIL',independence_class='UNSOLVED',hint_level=0,
            agent_usage='NONE',failure_modes=['stats:IDENTIFICATION_GAP']))
    p=app.mentorship('stats-target')['plans'][0]
    assert p['progression_action']=='REPAIR_PREREQUISITE'
    assert p['prerequisite_gaps'][0]['certainty']=='POSSIBLE'
    repair=record(3,subject='mathematics',concept='Probability convergence',task_type='HARD_PROBLEM',
                  readiness_dimensions=['Probability Maturity'])
    add(app,repair)
    p=app.mentorship('stats-target')['plans'][0]
    assert p['prerequisite_gaps'][0]['certainty']=='CLOSED'
    assert p['progression_action']=='RETEST_TARGET'
    assert p['current_capability']['current_state']=='EXPOSED'
    assert app.explain('Identification')['mastery_level']==0

def test_absent_explicit_link_never_invents_prerequisite(app):
    add_target(app)
    for i in (1,2): add(app,record(i,result='FAIL',independence_class='UNSOLVED',hint_level=0,agent_usage='NONE'))
    assert mentorship(app)['prerequisite_gaps']==[]
    assert mentorship(app)['progression_action']!='REPAIR_PREREQUISITE'

def test_explicit_link_without_diagnostic_failure_evidence_stays_unknown(app):
    link=sample('prerequisite'); link.update(link_id='math-linked',source_subject='mathematics',
        source_concept='Invariant proof',target_subject='mathematics',target_concept='Definitions')
    add(app,link,'prerequisite_link')
    add_target(app,target(target_id='linked-target',prerequisite_refs=[link['link_id']]))
    for i in (1,2): add(app,record(i,result='FAIL',independence_class='UNSOLVED',hint_level=0,agent_usage='NONE'))
    gap=app.mentorship('linked-target')['plans'][0]['prerequisite_gaps'][0]
    assert gap['certainty']=='UNKNOWN' and gap['failure_evidence_refs']==[]
    assert app.mentorship('linked-target')['plans'][0]['progression_action']!='REPAIR_PREREQUISITE'

def test_ai_generated_and_no_agent_are_not_equivalent(app):
    t=target(target_id='coding-target',subject='cs-ai',dimension='Coding Independence',
             description='Independent research engineering')
    add_target(app,t)
    generated=sample('cs-generated'); generated['scaffolding_level']='S5'; generated['training_zone']='PRODUCTIVE'
    add(app,generated)
    p=app.mentorship('coding-target')['plans'][0]
    assert p['current_capability']['current_state']=='GUIDED'
    assert p['current_capability']['independent_evidence_count']==0
    no_agent=sample('cs-independent'); no_agent.update(evidence_id='no-agent-comparison',occurred_at='2026-01-02T12:00:00Z',
        scaffolding_level='S1',training_zone='PRODUCTIVE')
    no_agent['metadata']={'attempt_id':'no-agent','context_id':'spec-only'}
    add(app,no_agent)
    p=app.mentorship('coding-target')['plans'][0]
    assert p['current_capability']['current_state']=='PARTIALLY_INDEPENDENT'
    assert p['current_capability']['independent_evidence_count']==1

def test_benchmark_isolation_updates_north_star_not_daily_collapse(app):
    add_target(app)
    add(app,record(result='UNSOLVED',independence_class='UNSOLVED',hint_level=0,agent_usage='NONE',
                   training_zone='MONSTER_BENCHMARK',difficulty='RESEARCH'))
    b=sample('benchmark'); b.update(solved=0,evidence_refs=['e-1'])
    add(app,b,'benchmark')
    p=mentorship(app)
    assert p['current_capability']['current_state']=='EXPOSED' and p['training_zone']=='FOUNDATION'
    views=render(app.state(),'integration_tests')
    assert 'target RESEARCH_USABLE' in views['Gallop/Automation/North Star.md']
    assert 'Monster observations 1' in views['Gallop/Automation/North Star.md']
    assert 'frontier FOUNDATION' in views['Gallop/Automation/Development.md']
    assert 'Daily Development' not in views['Today.md']

def test_weekly_feedback_contains_only_evidence_backed_gains(app):
    add_target(app)
    assert app.mentorship()['weekly_feedback']['items']==[]
    add(app,staged(1,'S5','ASSISTED',4,'AI_ASSISTED'))
    feedback=app.mentorship()['weekly_feedback']
    assert feedback['heading']=='This Week You Gained'
    assert feedback['items'] and feedback['evidence_refs']
    assert all('elite' not in text.lower() for text in feedback['items'])

def test_weekly_feedback_can_report_observed_hint_reduction(app):
    add_target(app)
    add(app,staged(1,'S5','ASSISTED',4,'AI_ASSISTED'))
    add(app,staged(2,'S4','HINT_2',3,'HINT_ONLY'))
    feedback=app.mentorship()['weekly_feedback']
    item=next(text for text in feedback['items'] if 'hint use decreased' in text)
    assert 'level 4 to level 3' in item
    assert len(feedback['evidence_refs'])>=2

def test_subject_policies_are_data_and_share_permanent_principles():
    assert len(POLICIES['principles'])==5 and POLICIES['zones']['default']=='PRODUCTIVE'
    assert set(POLICIES['subjects'])=={'mathematics','statistics','finance','cs-ai'}
    assert all(p['trajectory'] for p in POLICIES['subjects'].values())
    assert POLICIES['subjects']['mathematics']['monster_benchmarks']==['IMC','YAU']
    assert POLICIES['subjects']['cs-ai']['coding_ladder'][-1]=='research engineering'

def test_rc2_manifest_carries_only_explicit_mentorship_request(app,tmp_path):
    from test_automation import accept
    from gallop.adapters.deeptutor import DeepTutorAdapter
    accept(app); q=app.queue()[0]
    request={'desired_independence':'INDEPENDENT','training_zone':'PRODUCTIVE','task_type':'PROOF',
             'scaffolding_policy':{'level':'S3','fading_rule':'Reduce only after confirmed performance'},
             'hint_policy':{'max_level':2},'target_capability_id':'fictional-target'}
    prepared=app.prepare(q['queue_id'],question_count=1,elite=request)
    executable=tmp_path/'controlled-engine'; executable.write_text('test')
    command,_=DeepTutorAdapter(executable).request(prepared['manifest'])
    context=json.loads(command[3].split('\n',1)[1])
    assert context['elite_request']==request
    assert 'current_capability' not in context['elite_request']
    assert app.explain('Continuity')['mastery_level']==0

def test_rc1_evidence_without_targets_has_no_invented_mentorship_projection(app):
    add(app,sample())
    state=app.state()
    assert 'targets' not in state['elite']
    assert app.mentorship()['plans']==[]
    views=render(state,'integration_tests')
    assert 'Gallop/Automation/Development.md' not in views
    assert app.explain('Invariant proof')['mastery_level']==0

@pytest.mark.parametrize('changes',[{'transfer_type':'RESEARCH_TRANSFER'},
    {'retention':{'delay_days':7,'closed_book':True,'evidence_refs':['x']},'independence_class':'ASSISTED','hint_level':4,'agent_usage':'AI_ASSISTED'},
    {'productive_struggle':{'classification':'PRODUCTIVE_FAILURE','reason':'x','evidence_refs':['x']},'result':'PASS'}])
def test_rc2_evidence_cross_field_validation(app,changes):
    with pytest.raises(ValueError): add(app,record(**changes))
    assert not app.store.events()
