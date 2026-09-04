"""Four subject mentorship paths remain isolated and reach readable projections."""
import json
from pathlib import Path

import pytest

from gallop.automation.config import AutomationConfig
from gallop.automation.service import Automation
from gallop.cli import main

def evidence(subject,dimension,concept,index,independence,hint,agent,scaffold,task='HARD_PROBLEM',result='PASS',**extra):
    value={'schema_version':'1.1','namespace':'integration_tests','integration_test':True,
        'evidence_id':f'{subject}-{index}','subject':subject,'concept':concept,'task_type':task,
        'occurred_at':f'2026-01-{index:02d}T12:00:00Z','source':'Synthetic RC2 Golden',
        'result':result,'independence_class':independence,'hint_level':hint,'agent_usage':agent,
        'difficulty':'HARD','evidence_refs':[f'fictional-response-{index}'],'assessment_context':'TRAINING',
        'readiness_dimensions':[dimension],'training_zone':'PRODUCTIVE','scaffolding_level':scaffold,
        'metadata':{'attempt_id':f'{subject}-attempt-{index}','context_id':f'{subject}-context-{index}'}}
    if task=='PROOF': value['proof_quality']={k:'SOLID' for k in ('logical_completeness','definition_precision','condition_awareness')}
    if task=='DERIVATION': value['derivation_quality']={k:'SOLID' for k in ('steps_valid','assumption_awareness','interpretation')}
    value.update(extra); return value

def target(subject,dimension,target_id,refs=()):
    return {'schema_version':'1.1','namespace':'integration_tests','integration_test':True,'target_id':target_id,
        'subject':subject,'dimension':dimension,'target_state':'RESEARCH_USABLE','description':'Fictional high north star',
        'north_star':True,'prerequisite_refs':list(refs),'created_at':'2026-01-01T08:00:00Z','source':'Explicit RC2 Golden target'}

def save(app,value,name):
    path=app.config.root/name; path.write_text(json.dumps(value),encoding='utf-8'); return path

@pytest.fixture
def isolated(tmp_path):
    root=tmp_path/'rc2-isolated'
    untouched=tmp_path/'real-boundary-sentinel'; untouched.write_bytes(b'unchanged')
    app=Automation(AutomationConfig.from_dict({'namespace':'integration_tests','root':str(root),
        'vault':str(root/'vault'),'reader':str(root/'reader/Gallop-Reader'),'export_state':str(root/'export')}))
    yield app,untouched
    app.close()

def add(app,value,kind='elite_evidence'):
    return app.add_record(kind,save(app,value,value.get('evidence_id',value.get('target_id',value.get('link_id','record')))+'.json'),
                          confirm_human=kind=='elite_evidence')

@pytest.mark.parametrize('subject,dimension,concept,task,expected',[
    ('mathematics','Proof Maturity','Unfamiliar proof','PROOF','TRANSFERRED'),
    ('finance','Asset Pricing Theory','Asset-pricing model','DERIVATION','TRANSFERRED'),
    ('cs-ai','Coding Independence','Specification implementation','NO_AGENT_CODING','INDEPENDENT'),
])
def test_math_finance_cs_progressive_golden(isolated,subject,dimension,concept,task,expected):
    app,sentinel=isolated; before=sentinel.read_bytes(); tid=subject+'-north-star'
    add(app,target(subject,dimension,tid),'target_capability')
    first_agent='AI_GENERATED' if subject=='cs-ai' else 'AI_ASSISTED'
    add(app,evidence(subject,dimension,concept,1,'ASSISTED',4,first_agent,'S5','CODING' if subject=='cs-ai' else task))
    guided_task='CODING' if subject=='cs-ai' else task
    add(app,evidence(subject,dimension,concept,2,'HINT_2',3,'HINT_ONLY','S4',guided_task))
    add(app,evidence(subject,dimension,concept,3,'HINT_2',2,'HINT_ONLY','S3',guided_task))
    add(app,evidence(subject,dimension,concept,4,'HINT_1',1,'HINT_ONLY','S2',guided_task))
    add(app,evidence(subject,dimension,concept,5,'INDEPENDENT',0,'NONE','S1',task))
    add(app,evidence(subject,dimension,concept,6,'INDEPENDENT',0,'NONE','S0',task))
    fourth=evidence(subject,dimension,concept,7,'INDEPENDENT',0,'NONE','S0',task)
    if expected=='TRANSFERRED':
        fourth.update(transfer_status={'status':'SUCCESS','source_context':'trained','target_context':'novel',
            'independence_class':'INDEPENDENT','novelty':'NEW_CONTEXT','evidence_refs':['reviewed-transfer']},
            transfer_type='STRUCTURAL_TRANSFER')
    add(app,fourth)
    p=app.mentorship(tid)['plans'][0]
    assert p['current_capability']['current_state']==expected
    assert p['training_zone']=='STRETCH'
    assert p['scaffolding_level']=='S0'
    if subject=='cs-ai':
        assert p['current_capability']['independent_evidence_count']==3
        assert p['current_capability']['assisted_evidence_count']==4
    app.publish()
    reader=app.config.reader
    assert (reader/'Gallop/Automation/Development.md').exists()
    assert (reader/'Gallop/Automation/North Star.md').exists()
    assert expected in (reader/'Gallop/Automation/Development.md').read_text(encoding='utf-8')
    assert not list(reader.rglob('*.json')) and sentinel.read_bytes()==before

def test_statistics_prerequisite_repair_and_retest_golden(isolated):
    app,sentinel=isolated; before=sentinel.read_bytes()
    link={'schema_version':'1.1','namespace':'integration_tests','integration_test':True,'link_id':'iv-covariance',
        'source_subject':'statistics','source_concept':'IV Identification','target_subject':'mathematics',
        'target_concept':'Covariance','relation':'PREREQUISITE','evidence_refs':['explicit-course-map'],
        'created_at':'2026-01-01T08:00:00Z','source':'Explicit synthetic map'}
    add(app,link,'prerequisite_link')
    add(app,target('statistics','Identification','statistics-north-star',[link['link_id']]),'target_capability')
    for i in (1,2):
        add(app,evidence('statistics','Identification','IV Identification',i,'UNSOLVED',0,'NONE','S5',
            result='FAIL',failure_modes=['stats:IDENTIFICATION_GAP']))
    assert app.mentorship('statistics-north-star')['plans'][0]['progression_action']=='REPAIR_PREREQUISITE'
    add(app,evidence('mathematics','Probability Maturity','Covariance',3,'INDEPENDENT',0,'NONE','S1'))
    assert app.mentorship('statistics-north-star')['plans'][0]['progression_action']=='RETEST_TARGET'
    add(app,evidence('statistics','Identification','IV Identification',4,'HINT_2',3,'HINT_ONLY','S5'))
    p=app.mentorship('statistics-north-star')['plans'][0]
    assert p['prerequisite_gaps'][0]['certainty']=='CLOSED'
    assert p['current_capability']['current_state']=='GUIDED'
    assert app.explain('IV Identification')['mastery_level']==0
    app.publish()
    assert 'REPAIR' not in (app.config.reader/'Gallop/Automation/Development.md').read_text(encoding='utf-8')
    assert sentinel.read_bytes()==before

def test_rc2_cli_target_and_mentorship(tmp_path,capsys):
    root=tmp_path/'cli-isolated'; cfg=tmp_path/'config.json'; record_path=tmp_path/'target.json'
    cfg.write_text(json.dumps({'namespace':'integration_tests','root':str(root),'vault':str(root/'vault'),
        'reader':str(root/'reader/Gallop-Reader'),'export_state':str(root/'export')}))
    record_path.write_text(json.dumps(target('finance','Asset Pricing Theory','cli-target')))
    assert main(['--automation-config',str(cfg),'target','add',str(record_path)])==0
    added=json.loads(capsys.readouterr().out); assert added['target_id']=='cli-target'
    assert main(['--automation-config',str(cfg),'mentorship','cli-target'])==0
    report=json.loads(capsys.readouterr().out)
    assert report['plans'][0]['current_capability']['current_state']=='UNKNOWN'
    assert report['plans'][0]['training_zone']=='FOUNDATION'
