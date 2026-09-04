"""Evidence authority predicates shared by readiness and progression reducers."""
from .primitives import timestamp


def empty_elite():
    return dict(ruleset='elite-v1.1', evidence={}, benchmarks={}, links={},
                readiness={}, readiness_transitions=[])


def evidence_dimensions(record, catalog):
    result = list(record.get('readiness_dimensions', []))
    if record.get('independence_class'):
        label = 'Coding Independence' if record['subject'] == 'cs-ai' else 'Independence'
        if record['subject'] != 'cs-ai' or record['task_type'] in {'CODING', 'NO_AGENT_CODING', 'SYSTEMS_PROBLEM'}:
            result.append(label)
    transfer = record.get('transfer_status', {}).get('status')
    if transfer not in {None, 'NOT_TESTED'} and 'Transfer' in catalog[record['subject']]:
        result.append('Transfer')
    return sorted(set(result))


def quality_sufficient(record):
    solid = {'SOLID', 'STRONG', 'EXCEPTIONAL'}
    if record['task_type'] == 'PROOF':
        return all(record.get('proof_quality', {}).get(key) in solid
                   for key in ('logical_completeness', 'definition_precision', 'condition_awareness'))
    if record['task_type'] == 'DERIVATION':
        return all(record.get('derivation_quality', {}).get(key) in solid
                   for key in ('steps_valid', 'assumption_awareness', 'interpretation'))
    return True


def independent(entry):
    record = entry['record']
    return bool(entry['confirmed'] and record.get('independence_class') == 'INDEPENDENT'
                and record.get('hint_level') == 0
                and record.get('agent_usage') in {'NONE', 'REFERENCE_ONLY'}
                and record.get('evidence_refs'))


def eligible(entry):
    record = entry['record']
    metadata = record.get('metadata', {})
    benchmark_ok = (record.get('assessment_context') != 'BENCHMARK' or
                    bool(record.get('benchmark_source') and metadata.get('closed_book') is True
                         and metadata.get('no_ai') is True and record.get('agent_usage') == 'NONE'))
    designed_support_ok = record.get('scaffolding_level') in {None, 'S1', 'S0'}
    return bool(independent(entry) and designed_support_ok and record['result'] == 'PASS'
                and quality_sufficient(record)
                and record.get('assessment_context') in {'TRAINING', 'FORMATIVE', 'BENCHMARK', 'SUMMATIVE'}
                and metadata.get('context_id') and metadata.get('attempt_id') and benchmark_ok)


def transfer_success(entry):
    record = entry['record']
    return bool(eligible(entry) and record.get('transfer_status', {}).get('status') == 'SUCCESS'
                and record['transfer_status']['independence_class'] == 'INDEPENDENT')


def performances(entries):
    """One attempt cannot become multiple independent performances by changing IDs."""
    groups = {}
    for entry in entries:
        key = entry['record'].get('metadata', {}).get('attempt_id')
        if key:
            groups.setdefault(key, []).append(entry)
    result = []
    for group in groups.values():
        signatures = {(entry['record']['subject'], entry['record']['concept'], entry['record']['task_type'],
                       entry['record']['occurred_at'], entry['record'].get('metadata', {}).get('context_id'))
                      for entry in group}
        if len(signatures) == 1 and all(eligible({**entry, 'confirmed': True}) for entry in group):
            confirmed = next((entry for entry in group if entry['confirmed']), None)
            if confirmed:
                result.append(confirmed)
    return result


def entries_for(state, subject, dimension, catalog):
    elite = state.get('elite', empty_elite())
    return sorted((entry for entry in elite['evidence'].values()
                   if entry['record']['subject'] == subject
                   and dimension in evidence_dimensions(entry['record'], catalog)),
                  key=lambda entry: (timestamp(entry['record']['occurred_at']), entry['event_id']))


def diversity(entries):
    days = {timestamp(entry['record']['occurred_at']).date() for entry in entries}
    contexts = {entry['record'].get('metadata', {}).get('context_id') for entry in entries}
    contexts.discard(None)
    return len(days), len(contexts)


def research_independence(entries):
    research = [entry for entry in entries
                if entry['record']['task_type'] in {'RESEARCH', 'REPLICATION', 'PAPER_READING'}
                or entry['record'].get('metadata', {}).get('research_component') is True]
    assisted = [entry for entry in research if entry['confirmed'] and entry['record']['result'] == 'PASS']
    strong = performances(research)
    state = 'RI0'
    if assisted:
        state = 'RI1'
    if any(entry['record'].get('scaffolding_level') in {'S3', 'S2'} for entry in assisted):
        state = 'RI2'
    if strong:
        state = 'RI3'
    if len(strong) >= 3:
        state = 'RI4'
    if len(strong) >= 4 and any(entry['record'].get('metadata', {}).get('project_id') for entry in strong):
        state = 'RI5'
    if (len(strong) >= 6 and any(transfer_success(entry) for entry in strong)
            and any(entry['record'].get('retention') for entry in strong)):
        state = 'RI6'
    labels = {'RI0': 'DEPENDENT', 'RI1': 'GUIDED', 'RI2': 'STRUCTURED',
              'RI3': 'SEMI_INDEPENDENT', 'RI4': 'INDEPENDENT_COMPONENT',
              'RI5': 'INDEPENDENT_PROJECT', 'RI6': 'RESEARCH_READY'}
    return {'state': state, 'label': labels[state], 'evidence_refs': [entry['event_id'] for entry in research]}


def capability_state(entries):
    confirmed = [entry for entry in entries if entry['confirmed']]
    assisted = [entry for entry in confirmed if entry['record']['result'] == 'PASS'
                and entry['record'].get('independence_class') in {'HINT_1', 'HINT_2', 'ASSISTED'}]
    strong = performances(entries)
    days, contexts = diversity(strong)
    value = 'UNKNOWN'
    if entries:
        value = 'EXPOSED'
    if assisted:
        value = 'GUIDED'
    if strong:
        value = 'PARTIALLY_INDEPENDENT'
    developmental = [entry for entry in strong
                     if entry['record'].get('training_zone') in {None, 'PRODUCTIVE', 'STRETCH'}
                     and entry['record'].get('difficulty') not in {'INTRODUCTORY', 'EASY'}]
    if len(strong) >= 3 and len(developmental) >= 2 and days >= 3 and contexts >= 3:
        value = 'INDEPENDENT'
    if value == 'INDEPENDENT' and any(transfer_success(entry) for entry in strong):
        value = 'TRANSFERRED'
    retained = [entry for entry in strong
                if entry['record'].get('retention', {}).get('delay_days', 0) >= 7
                and entry['record']['retention'].get('closed_book') is True]
    if value in {'INDEPENDENT', 'TRANSFERRED'} and retained:
        value = 'RETAINED'
    research = research_independence(entries)
    if value == 'RETAINED' and research['state'] == 'RI6':
        value = 'RESEARCH_USABLE'
    return value, assisted, strong, retained, research
