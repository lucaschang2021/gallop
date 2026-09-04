"""Executable architecture governance and import-safety tests."""
from pathlib import Path
import os
import runpy
import subprocess
import sys


ROOT = Path(__file__).parents[2]
GATE = runpy.run_path(str(ROOT / 'scripts/check_architecture.py'))


def test_architecture_contract_has_no_introduced_findings():
    report = GATE['audit'](ROOT, GATE['load_contract'](ROOT))
    assert report['introduced'] == []
    assert report['existing'] == []
    assert {row['path'] for row in report['warnings']} >= {
        'gallop/automation/service.py', 'gallop/automation/state.py',
        'gallop/mobile.py', 'gallop/automation/jobs.py'}


def test_gate_detects_forbidden_domain_dependency_and_time(tmp_path):
    source = tmp_path / 'bad_domain.py'
    source.write_text('from gallop.adapters import mock\nfrom datetime import date\ndef decide():\n    return date.today()\n',
                      encoding='utf-8')
    findings = GATE['inspect_module'](source, 'domain', GATE['load_contract'](ROOT)['rules'],
                                      Path('gallop/progression/bad_domain.py'))
    assert {row['rule'] for row in findings} == {'domain-forbidden-import', 'domain-implicit-time'}


def test_gate_detects_domain_module_state_and_import_side_effect(tmp_path):
    source = tmp_path / 'stateful_domain.py'
    source.write_text('cache = {}\nSTATE = load_runtime()\n', encoding='utf-8')
    findings = GATE['inspect_module'](source, 'domain', GATE['load_contract'](ROOT)['rules'])
    assert {row['rule'] for row in findings} == {
        'domain-module-mutable-state', 'domain-import-side-effect'}


def test_gate_detects_package_import_mutation_hazards(tmp_path):
    source = tmp_path / 'runtime.py'
    source.write_text('runtime = {}\nPath("state").mkdir()\n', encoding='utf-8')
    findings = GATE['inspect_runtime_module'](source)
    assert {row['rule'] for row in findings} == {
        'module-mutable-runtime-state', 'suspicious-import-side-effect'}


def test_gate_detects_projection_and_adapter_boundary_crossing(tmp_path):
    projection = tmp_path / 'projection.py'
    projection.write_text('from gallop.automation.store import EventStore\n', encoding='utf-8')
    adapter = tmp_path / 'adapter.py'
    adapter.write_text('from gallop.automation.state import replay\n', encoding='utf-8')
    rules = GATE['load_contract'](ROOT)['rules']
    assert GATE['inspect_module'](projection, 'projection', rules)[0]['rule'] == 'projection-forbidden-import'
    assert GATE['inspect_module'](adapter, 'adapters', rules)[0]['rule'] == 'adapter-forbidden-import'


def test_import_gallop_has_no_filesystem_side_effect(tmp_path):
    before = set(tmp_path.iterdir())
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    subprocess.run([sys.executable, '-c', 'import gallop'], cwd=tmp_path, env=env,
                   check=True, capture_output=True, text=True)
    assert set(tmp_path.iterdir()) == before
