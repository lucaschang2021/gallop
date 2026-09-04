"""Four fictional end-to-end flows; every output stays in a temporary local namespace."""
import json
from pathlib import Path

import pytest

from gallop.automation.config import AutomationConfig
from gallop.automation.service import Automation
from gallop.automation.state import replay
from gallop.cli import main

EXAMPLES = Path(__file__).parents[2] / 'examples/elite'


@pytest.mark.parametrize('subject,sample_name,concept,dimension,status', [
    ('mathematics','mathematics','Invariant proof','Proof Maturity','FOUNDATIONAL'),
    ('statistics','statistics','Identification','Identification','FOUNDATIONAL'),
    ('finance','finance','Asset pricing derivation','Asset Pricing Theory','FOUNDATIONAL'),
    ('cs-ai','cs-independent','Binary search','Coding Independence','FOUNDATIONAL'),
])
def test_four_subject_golden_cli_projection_and_isolation(tmp_path,capsys,subject,sample_name,concept,dimension,status):
    root=tmp_path/'validation'
    sentinel=tmp_path/'untouched-learner.json'
    sentinel.write_text('{"mastery": 4, "owner": "fictional"}')
    baseline=sentinel.read_bytes()
    config=tmp_path/'configuration.json'
    config.write_text(json.dumps(dict(root=str(root),vault=str(root/'vault'),
        reader=str(root/'reader/Gallop-Reader'),export_state=str(root/'export'),namespace='integration_tests')))
    def command(*args):
        assert main(['--automation-config',str(config),*args])==0
        return json.loads(capsys.readouterr().out)
    first=command('evidence','add',str(EXAMPLES/(sample_name+'.json')),'--confirm-human')
    assert not first['duplicate']
    assert command('evidence','show')[0]['confirmed']
    if subject=='mathematics':
        command('benchmark','add',str(EXAMPLES/'benchmark.json'),'--confirm-human')
        benchmark=command('benchmark','show')[0]
        assert benchmark['summary']['independent_solve_rate']==1
        assert benchmark['summary']['score'] is None
        assert command('readiness','explain',dimension,'--subject',subject)['benchmark_evidence']
    elif subject=='statistics':
        assert not command('explain',concept)['elite']['prerequisite_gaps']
        command('prerequisite','add',str(EXAMPLES/'prerequisite.json'))
        assert command('prerequisite','show')[0]['record']['relation']=='PREREQUISITE'
        assert command('explain',concept)['elite']['failure_modes']=={'stats:IDENTIFICATION_GAP':1}
    elif subject=='finance':
        report=command('explain',concept)
        assert report['elite']['assisted_evidence'] and not report['elite']['independent_evidence']
    else:
        independent=command('readiness','explain',dimension,'--subject',subject)
        command('evidence','add',str(EXAMPLES/'cs-generated.json'),'--confirm-human')
        generated=command('explain','Generated binary search')
        assert not generated['elite']['independent_evidence']
        assert generated['mastery_level']==0
        after=command('readiness','explain',dimension,'--subject',subject)
        assert after['independent_evidence']==independent['independent_evidence']
        assert len(after['assisted_evidence'])==1
    readiness=command('readiness','explain',dimension,'--subject',subject)
    assert readiness['status']==status and readiness['confidence']=='low'
    assert readiness['evidence_refs'] and readiness['reason']
    assert command('explain',concept)['mastery_level']==0
    assert command('cycle')['publish']['written']>0
    reader=root/'reader/Gallop-Reader'
    for name in ('Elite Training.md','Benchmarks.md','Readiness.md'):
        body=(reader/'Gallop/Automation'/name).read_text(encoding='utf-8')
        assert 'Isolated synthetic local preview' in body
        assert not any(term in body for term in ('private_answer','context_id','attempt_id'))
    assert dimension in (reader/'Gallop/Automation/Readiness.md').read_text(encoding='utf-8')
    assert not list(reader.rglob('*.sqlite3')) and not list(reader.rglob('*.json'))
    assert command('publish')['written']==0
    assert command('evidence','add',str(EXAMPLES/(sample_name+'.json')),'--confirm-human')['duplicate']
    assert command('rebuild-state')['replaced']
    app=Automation(AutomationConfig.load(config))
    try:
        assert replay(app.store.events())==app.state()
        assert app.config.binding is None and reader.is_relative_to(root)
    finally:
        app.close()
    assert sentinel.read_bytes()==baseline


def test_synthetic_elite_cannot_enter_learner_or_cloud(tmp_path):
    vault=tmp_path/'private-vault'
    (vault/'.obsidian').mkdir(parents=True)
    root=tmp_path/'private-events'
    config=AutomationConfig(root,vault,tmp_path/'Gallop-Reader',root/'export','learner')
    app=Automation(config)
    try:
        for name,kind in [('mathematics','elite_evidence'),('benchmark','benchmark'),('prerequisite','prerequisite_link')]:
            with pytest.raises(ValueError,match='Synthetic/integration'):
                app.add_record(kind,EXAMPLES/(name+'.json'),confirm_human=True)
        assert not app.store.events() and not config.reader.exists()
        assert list(vault.iterdir())==[vault/'.obsidian']
    finally:
        app.close()
    isolated=tmp_path/'integration'
    with pytest.raises(ValueError):
        AutomationConfig.from_dict(dict(root=str(isolated),vault=str(vault),reader=str(tmp_path/'Gallop-Reader'),
                                         export_state=str(isolated/'export'),namespace='integration_tests'))
