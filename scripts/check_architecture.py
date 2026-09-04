"""Executable Gallop architecture contract and drift gate."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
import tomllib


SUBJECTS = {'mathematics', 'statistics', 'finance', 'cs-ai'}


def load_contract(root: Path) -> dict:
    path = root / 'ARCHITECTURE.toml'
    if not path.is_file():
        raise ValueError('ARCHITECTURE.toml is required')
    with path.open('rb') as stream:
        contract = tomllib.load(stream)
    required = {'contract', 'layers', 'rules', 'growth', 'policy', 'baseline'}
    if not required <= set(contract):
        raise ValueError('Architecture contract sections are incomplete')
    if contract['contract'].get('schema_version') != '1.0':
        raise ValueError('Unsupported architecture contract version')
    if contract['contract'].get('authority') != 'journal':
        raise ValueError('Journal authority cannot be weakened')
    if contract['contract'].get('derived_state_role') != 'cache_projection':
        raise ValueError('Derived state must remain a cache/projection')
    for entries in contract['layers'].values():
        for entry in entries:
            if not (root / entry).exists():
                raise ValueError(f'Architecture layer path does not exist: {entry}')
    for spec in (*contract['growth'], *contract['policy']):
        if not (root / spec['path']).is_file():
            raise ValueError(f'Governed path does not exist: {spec["path"]}')
    return contract


def imports(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module, node.lineno


def matches(module: str, prefixes) -> bool:
    return any(module == prefix or module.startswith(prefix + '.') for prefix in prefixes)


def qualified_call(node: ast.Call) -> str:
    parts = []
    value = node.func
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return '.'.join(reversed(parts))


def finding(rule: str, path: Path, line: int, detail: str) -> dict:
    normalized = path.as_posix()
    return {'id': f'{rule}:{normalized}:{line}', 'rule': rule, 'path': normalized,
            'line': line, 'detail': detail}


def inspect_module(path: Path, layer: str, rules: dict, relative: Path | None = None) -> list[dict]:
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    shown = relative or path
    output = []
    rule_layer = 'adapter' if layer == 'adapters' else layer
    forbidden = rules.get(f'{rule_layer}_forbidden_imports', [])
    for module, line in imports(tree):
        if matches(module, forbidden):
            output.append(finding(f'{rule_layer}-forbidden-import', shown, line, module))
    if layer == 'domain':
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and qualified_call(node) in rules['implicit_time_calls']:
                output.append(finding('domain-implicit-time', shown, node.lineno, qualified_call(node)))
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                names = ([target.id for target in node.targets if isinstance(target, ast.Name)]
                         if isinstance(node, ast.Assign) else
                         [node.target.id] if isinstance(node.target, ast.Name) else [])
                mutable = isinstance(value, (ast.Dict, ast.List, ast.Set))
                if mutable and any(not (name.isupper() or name == '__all__') for name in names):
                    output.append(finding('domain-module-mutable-state', shown, node.lineno, ','.join(names)))
                if isinstance(value, ast.Call):
                    output.append(finding('domain-import-side-effect', shown, node.lineno,
                                          qualified_call(value)))
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                output.append(finding('domain-import-side-effect', shown, node.lineno,
                                      qualified_call(node.value)))
    return output


def inspect_runtime_module(path: Path, relative: Path | None = None) -> list[dict]:
    """Detect import-time mutation hazards across every Gallop module."""
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    shown = relative or path
    output = []
    dangerous = {'open', 'mkdir', 'makedirs', 'write_text', 'write_bytes', 'Popen',
                 'run', 'call', 'check_call', 'check_output', 'bind', 'EventStore', 'Automation'}
    for node in tree.body:
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr)) else None
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = ([target.id for target in node.targets if isinstance(target, ast.Name)]
                     if isinstance(node, ast.Assign) else
                     [node.target.id] if isinstance(node.target, ast.Name) else [])
            if isinstance(value, (ast.Dict, ast.List, ast.Set)) and any(
                    not (name.isupper() or name == '__all__') for name in names):
                output.append(finding('module-mutable-runtime-state', shown, node.lineno, ','.join(names)))
        if isinstance(value, ast.Call):
            call = qualified_call(value)
            if call.rsplit('.', 1)[-1] in dangerous:
                output.append(finding('suspicious-import-side-effect', shown, node.lineno, call))
    return output


def python_files(root: Path, entries):
    for entry in entries:
        path = root / entry
        if path.is_dir():
            yield from sorted(path.rglob('*.py'))
        elif path.suffix == '.py':
            yield path


def validate_policies(root: Path, specifications) -> list[dict]:
    output = []
    for spec in specifications:
        path = root / spec['path']
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            output.append(finding('policy-invalid', Path(spec['path']), 1, type(exc).__name__))
            continue
        shape = spec['shape']
        valid = False
        if shape == 'subject_map':
            valid = set(data) == SUBJECTS and all(
                isinstance(data[name].get('training_types'), list) and data[name].get('folder')
                for name in SUBJECTS)
        elif shape == 'mentorship_catalog':
            valid = (data.get('schema_version') == spec['version']
                     and set(data.get('subjects', {})) == SUBJECTS
                     and all(policy.get('trajectory') and policy.get('mentor_labels')
                             for policy in data['subjects'].values()))
        elif shape == 'dimension_map':
            valid = set(data) == SUBJECTS and all(isinstance(data[name], list) and data[name] for name in SUBJECTS)
        if not valid:
            output.append(finding('policy-invalid', Path(spec['path']), 1,
                                  f'{shape}@{spec["version"]}'))
    return output


def audit(root: Path, contract: dict) -> dict:
    rules = contract['rules']
    violations = []
    for layer in ('domain', 'adapters', 'projection'):
        for path in python_files(root, contract['layers'][layer]):
            violations.extend(inspect_module(path, layer, rules, path.relative_to(root)))
    for path in sorted((root / 'gallop').rglob('*.py')):
        violations.extend(inspect_runtime_module(path, path.relative_to(root)))

    service = ast.parse((root / 'gallop/automation/service.py').read_text(encoding='utf-8'))
    for node in ast.walk(service):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in rules['service_forbidden_methods']:
            violations.append(finding('service-domain-decision', Path('gallop/automation/service.py'),
                                      node.lineno, node.name))
    state = ast.parse((root / 'gallop/automation/state.py').read_text(encoding='utf-8'))
    for node in state.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                node.name.startswith(prefix) for prefix in rules['state_forbidden_prefixes']):
            violations.append(finding('state-progression-decision', Path('gallop/automation/state.py'),
                                      node.lineno, node.name))

    warnings = []
    for spec in contract['growth']:
        path = root / spec['path']
        body = path.read_text(encoding='utf-8').replace('\r\n', '\n')
        size = len(body.encode('utf-8'))
        lines = len(body.splitlines())
        if lines > spec['baseline_lines']:
            violations.append(finding('governed-file-growth', Path(spec['path']), 1,
                                      f'{lines}>{spec["baseline_lines"]} lines; responsibility audit required'))
        if size > spec['soft_bytes']:
            warnings.append({'rule': 'soft-size-warning', 'path': spec['path'], 'bytes': size,
                             'threshold': spec['soft_bytes'], 'role': spec['role']})
        if size > spec['hard_review_bytes']:
            warnings.append({'rule': 'hard-responsibility-review', 'path': spec['path'], 'bytes': size,
                             'threshold': spec['hard_review_bytes'], 'role': spec['role']})
    violations.extend(validate_policies(root, contract['policy']))

    by_id = {item['id']: item for item in violations}
    baseline = set(contract['baseline'].get('existing', []))
    return {'contract_version': contract['contract']['schema_version'],
            'existing': [by_id[key] for key in sorted(set(by_id) & baseline)],
            'introduced': [by_id[key] for key in sorted(set(by_id) - baseline)],
            'resolved': sorted(baseline - set(by_id)), 'warnings': warnings}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        report = audit(args.root, load_contract(args.root))
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(json.dumps({'contract_error': str(exc)}, indent=2))
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report['introduced'] else 0


if __name__ == '__main__':
    sys.exit(main())
