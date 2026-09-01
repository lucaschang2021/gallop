"""v1.1 recording contracts. Unknown telemetry is never filled with success defaults."""
from datetime import date
from importlib.resources import files
import json

from gallop.core.validation import validate_protocol
from gallop.mobile import check_path
from .protocol import now, parse, timestamp


def resource(name):
    return json.loads(files('gallop.schemas').joinpath(name).read_text(encoding='utf-8'))


DIMENSIONS = resource('readiness-dimensions.json')
RULESET = 'elite-v1.1'
SCHEMAS = {'elite_evidence': 'elite-evidence.schema.json', 'benchmark': 'benchmark.schema.json',
           'prerequisite_link': 'prerequisite-link.schema.json', 'target_capability':'target-capability.schema.json'}
IDENTITIES = {'elite_evidence': 'evidence_id', 'benchmark': 'benchmark_id', 'prerequisite_link': 'link_id',
              'target_capability':'target_id'}
TIMES = {'elite_evidence': 'occurred_at', 'benchmark': 'date', 'prerequisite_link': 'created_at',
         'target_capability':'created_at'}


def failure_registry(extension=None):
    registry = resource('failure-modes.json')
    if extension:
        additions = parse(check_path(extension).read_bytes())
        validate_protocol('failure-registry.schema.json', additions)
        for namespace, modes in additions.items():
            registry.setdefault(namespace, []).extend(m for m in modes if m not in registry.get(namespace, []))
    return {namespace + ':' + mode for namespace, modes in registry.items() for mode in modes}


def event_time(kind, record):
    return record['date'] + 'T00:00:00Z' if kind == 'benchmark' else record[TIMES[kind]]


def validate(kind, record, *, namespace, registry=None):
    validate_protocol(SCHEMAS[kind], record)
    if record.get('namespace', namespace) != namespace:
        raise ValueError('Elite record namespace mismatch')
    if 'integration_test' in record and record['integration_test'] != (namespace == 'integration_tests'):
        raise ValueError('Elite record integration flag mismatch')
    if timestamp(event_time(kind, record)) > timestamp(now()):
        raise ValueError('Future evidence is not recorded performance')
    if kind == 'elite_evidence':
        validate_evidence(record, registry if registry is not None else failure_registry())
    elif kind == 'benchmark':
        date.fromisoformat(record['date'])
        total, attempted = record.get('problems_total'), record.get('attempted')
        solved, partial = record.get('solved'), record.get('partial')
        if total is not None and attempted is not None and attempted > total:
            raise ValueError('Attempted exceeds total')
        bound = attempted if attempted is not None else total
        if bound is not None and any(v is not None and v > bound for v in (solved, partial)):
            raise ValueError('Outcome count exceeds available problems')
        if bound is not None and solved is not None and partial is not None and solved + partial > bound:
            raise ValueError('Solved and partial categories must not overlap')
        if 'score' in record and 'max_score' in record and record['score'] > record['max_score']:
            raise ValueError('Score exceeds maximum')
        if record['benchmark_type'] == 'CLOSED_BOOK' and record.get('closed_book') is False:
            raise ValueError('Closed-book benchmark contradicts its context')
        if record['benchmark_type'] == 'NO_AGENT' and record.get('no_ai') is False:
            raise ValueError('No-agent benchmark contradicts its context')
    elif kind == 'target_capability':
        if record['dimension'] not in DIMENSIONS[record['subject']]:
            raise ValueError('Target dimension does not belong to its subject')
    elif (record['source_subject'], record['source_concept']) == (record['target_subject'], record['target_concept']):
        raise ValueError('An explicit cross-concept link cannot refer to itself')
    return record


def validate_evidence(record, registry):
    independence, hint, agent = (record.get(k) for k in ('independence_class', 'hint_level', 'agent_usage'))
    reason = record.get('metadata', {}).get('hint_consistency_reason')
    allowed_hints = {'INDEPENDENT': {0}, 'HINT_1': {1}, 'HINT_2': {2, 3}, 'ASSISTED': {4},
                     'SOLUTION_SEEN': {5}, 'UNSOLVED': set(range(6))}
    exceptional_solution = independence == 'SOLUTION_SEEN' and hint == 0 and isinstance(reason, str) and reason.strip()
    if independence and hint is not None and hint not in allowed_hints[independence] and not exceptional_solution:
        raise ValueError('Independence class contradicts hint level')
    if independence == 'INDEPENDENT' and agent in {'HINT_ONLY', 'AI_ASSISTED', 'AI_GENERATED'}:
        raise ValueError('Independent work contradicts recorded AI assistance')
    if independence in {'HINT_1', 'HINT_2'} and agent in {'AI_ASSISTED', 'AI_GENERATED'}:
        raise ValueError('Substantial AI assistance cannot be classified as a limited hint')
    if record['task_type'] == 'NO_AGENT_CODING' and agent not in {None, 'NONE', 'UNKNOWN'}:
        raise ValueError('No-agent coding contradicts AI involvement')
    if independence == 'UNSOLVED' and record['result'] == 'PASS':
        raise ValueError('Unsolved work cannot be passing evidence')
    if any(mode not in registry for mode in record.get('failure_modes', [])):
        raise ValueError('Unregistered failure mode; explicitly extend the registry first')
    if any(d not in DIMENSIONS[record['subject']] for d in record.get('readiness_dimensions', [])):
        raise ValueError('Readiness dimension does not belong to this subject')
    if ('Coding Independence' in record.get('readiness_dimensions', [])
            and record['task_type'] not in {'CODING', 'NO_AGENT_CODING', 'SYSTEMS_PROBLEM'}):
        raise ValueError('Coding independence requires an actual coding or systems task')
    for key in ('context_id', 'attempt_id'):
        value = record.get('metadata', {}).get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError('Context and attempt IDs must be explicit nonempty strings')
    for key in ('closed_book', 'no_ai'):
        if key in record.get('metadata', {}) and type(record['metadata'][key]) is not bool:
            raise ValueError('Benchmark context flags must be explicit booleans')
    transfer = record.get('transfer_status', {})
    if record.get('transfer_type') and transfer.get('status') in {None, 'NOT_TESTED'}:
        raise ValueError('Transfer type requires tested transfer evidence')
    if record.get('retention') and (record.get('independence_class') != 'INDEPENDENT'
                                    or record.get('result') != 'PASS'):
        raise ValueError('Retention requires an independent passing performance')
    struggle = record.get('productive_struggle', {})
    if struggle and record['result'] not in {'PARTIAL','FAIL','UNSOLVED'}:
        raise ValueError('Productive-struggle classification requires partial or unsuccessful work')
    if transfer.get('status') in {'FAILED', 'PARTIAL', 'SUCCESS'}:
        if not all(transfer.get(k) for k in ('source_context', 'target_context', 'independence_class', 'evidence_refs')):
            raise ValueError('Tested transfer requires contexts, independence and provenance')
    if transfer.get('status') == 'SUCCESS':
        if (transfer.get('novelty') != 'NEW_CONTEXT' or transfer['source_context'] == transfer['target_context']):
            raise ValueError('Near-identical exercises cannot establish transfer success')
        if transfer['independence_class'] == 'INDEPENDENT' and independence != 'INDEPENDENT':
            raise ValueError('Independent transfer conflicts with the recorded performance')


def quality_sufficient(record):
    solid = {'SOLID', 'STRONG', 'EXCEPTIONAL'}
    if record['task_type'] == 'PROOF':
        return all(record.get('proof_quality', {}).get(k) in solid
                   for k in ('logical_completeness', 'definition_precision', 'condition_awareness'))
    if record['task_type'] == 'DERIVATION':
        return all(record.get('derivation_quality', {}).get(k) in solid
                   for k in ('steps_valid', 'assumption_awareness', 'interpretation'))
    return True


def independent(entry):
    r = entry['record']
    return bool(entry['confirmed'] and r.get('independence_class') == 'INDEPENDENT'
                and r.get('hint_level') == 0 and r.get('agent_usage') in {'NONE', 'REFERENCE_ONLY'}
                and r.get('evidence_refs'))


def eligible(entry):
    r = entry['record']
    metadata = r.get('metadata', {})
    benchmark_ok = (r.get('assessment_context') != 'BENCHMARK' or
                    bool(r.get('benchmark_source') and metadata.get('closed_book') is True and metadata.get('no_ai') is True
                         and r.get('agent_usage') == 'NONE'))
    designed_support_ok = r.get('scaffolding_level') in {None, 'S1', 'S0'}
    return bool(independent(entry) and designed_support_ok and r['result'] == 'PASS' and quality_sufficient(r)
                and r.get('assessment_context') in {'TRAINING', 'FORMATIVE', 'BENCHMARK', 'SUMMATIVE'}
                and metadata.get('context_id') and metadata.get('attempt_id') and benchmark_ok)


def transfer_success(entry):
    return bool(eligible(entry) and entry['record'].get('transfer_status', {}).get('status') == 'SUCCESS'
                and entry['record']['transfer_status']['independence_class'] == 'INDEPENDENT')


def performances(entries):
    """One attempt cannot become multiple independent performances by changing IDs."""
    groups = {}
    for entry in entries:
        r = entry['record']
        key = r.get('metadata', {}).get('attempt_id')
        if key:
            groups.setdefault(key, []).append(entry)
    result = []
    for group in groups.values():
        # A later human attestation may confirm an identical unconfirmed observation.
        # Contradictory assistance, context or date never becomes a second performance.
        signatures = {(e['record']['subject'], e['record']['concept'], e['record']['task_type'],
                       e['record']['occurred_at'], e['record'].get('metadata', {}).get('context_id')) for e in group}
        if len(signatures) == 1 and all(eligible({**e, 'confirmed': True}) for e in group):
            confirmed = next((e for e in group if e['confirmed']), None)
            if confirmed:
                result.append(confirmed)
    return result
