"""Deterministic v1.1 evidence interpretation, separate from the frozen v1 reducer."""
from collections import Counter
from copy import deepcopy

from .elite_protocol import DIMENSIONS, RULESET, eligible, independent, performances, quality_sufficient, transfer_success
from .protocol import digest, timestamp
from .store import JournalConflict


def empty():
    return dict(ruleset=RULESET, evidence={}, benchmarks={}, links={}, readiness={}, readiness_transitions=[])


def dimensions(record):
    result = list(record.get('readiness_dimensions', []))
    if record.get('independence_class'):
        label = 'Coding Independence' if record['subject'] == 'cs-ai' else 'Independence'
        if record['subject'] != 'cs-ai' or record['task_type'] in {'CODING', 'NO_AGENT_CODING', 'SYSTEMS_PROBLEM'}:
            result.append(label)
    if record.get('transfer_status', {}).get('status') not in {None, 'NOT_TESTED'} and 'Transfer' in DIMENSIONS[record['subject']]:
        result.append('Transfer')
    return sorted(set(result))


def related_benchmarks(elite, entries):
    ids = {e['record']['evidence_id'] for e in entries}
    return [b for b in elite['benchmarks'].values() if ids.intersection(b['record']['evidence_refs'])]


def diversity(entries):
    records = [e['record'] for e in entries]
    days = {timestamp(r['occurred_at']).date() for r in records}
    contexts = {r['metadata']['context_id'] for r in records}
    kinds = {r['task_type'] for r in records}
    return len(days), len(contexts), len(kinds), (max(days) - min(days)).days if days else 0


def benchmark_verified(benchmark):
    return (benchmark['confirmed'] and benchmark['record'].get('closed_book') is True
            and benchmark['record'].get('no_ai') is True)


def benchmark_performances(benchmark, entries):
    b = benchmark['record']
    return [e for e in entries if e['record']['evidence_id'] in b['evidence_refs']
            and e['record'].get('assessment_context') == 'BENCHMARK'
            and e['record'].get('benchmark_source') == b['source']]


def profile_dimension(subject, dimension, elite):
    entries = [e for e in elite['evidence'].values() if e['record']['subject'] == subject
               and dimension in dimensions(e['record'])]
    # Group across the whole subject, so a conflicting record cannot be hidden
    # by omitting a readiness-dimension label on the conflicting observation.
    subject_entries = [e for e in elite['evidence'].values() if e['record']['subject'] == subject]
    good_attempts = {e['record']['metadata']['attempt_id'] for e in performances(subject_entries)}
    strong = performances([e for e in entries if e['record'].get('metadata', {}).get('attempt_id') in good_attempts])
    assisted = [e for e in entries if e['confirmed'] and e['record'].get('independence_class') in {'HINT_1', 'HINT_2', 'ASSISTED'}]
    usable_assisted = [e for e in assisted if e['record']['result'] == 'PASS' and quality_sufficient(e['record'])
                       and e['record'].get('evidence_refs') and e['record'].get('agent_usage') not in {None, 'UNKNOWN', 'AI_GENERATED'}]
    benchmarks = related_benchmarks(elite, entries)
    actual_benchmarks = [b for b in benchmarks if benchmark_verified(b) and benchmark_performances(b, strong)]
    transfers = [e for e in strong if transfer_success(e)]
    days, contexts, kinds, span = diversity(strong)
    status, confidence = 'UNKNOWN', 'low'
    reason = 'Insufficient confirmed, attributed performance; missing values remain unrecorded'
    if usable_assisted and dimension not in {'Independence', 'Coding Independence', 'Transfer'}:
        status = 'FOUNDATIONAL'
        reason = 'Assisted performance supports limited familiarity, not independent capability'
    if strong:
        status = 'FOUNDATIONAL'
        reason = 'One confirmed independent performance is a foundation, not established readiness'
    if len(strong) >= 2 and days >= 2 and contexts >= 2:
        status, confidence = 'DEVELOPING', 'medium'
        reason = 'Repeated independent performance on distinct days and contexts'
    if len(strong) >= 3 and days >= 3 and contexts >= 3:
        status = 'SOLID'
        reason = 'At least three independent performances across three days and contexts'
    if len(strong) >= 4 and days >= 4 and contexts >= 3 and transfers:
        status, confidence = 'STRONG', 'high'
        reason = 'At least four independent performances across days with explicit novel-context transfer'
    if len(strong) >= 6 and days >= 5 and contexts >= 4 and kinds >= 3 and span >= 30 and transfers and actual_benchmarks:
        status, confidence = 'ADVANCED', 'high'
        reason = 'Diverse delayed independent performances, explicit transfer and a confirmed closed-book/no-AI benchmark'
    failures = Counter(mode for e in entries for mode in e['record'].get('failure_modes', []))
    if entries and max(entries, key=lambda e: timestamp(e['record']['occurred_at']))['record']['result'] in {'FAIL', 'UNSOLVED'}:
        confidence = 'low'
        reason += '; latest recorded failure lowers confidence without erasing historical evidence'
    if dimension == 'Transfer' and not transfers:
        status, confidence = 'UNKNOWN', 'low'
        reason = 'No confirmed independent transfer in an explicitly novel context'
    return dict(dimension=dimension, status=status, confidence=confidence, evidence_count=len(entries),
                last_updated=max((e['record']['occurred_at'] for e in entries), key=timestamp, default=None),
                evidence_refs=[e['event_id'] for e in entries], reason=reason,
                independent_evidence=[e['event_id'] for e in strong], assisted_evidence=[e['event_id'] for e in assisted],
                benchmark_evidence=[b['event_id'] for b in benchmarks], transfer_evidence=[e['event_id'] for e in transfers],
                failure_modes=dict(sorted(failures.items())))


def readiness_profile(subject, elite):
    return dict(schema_version='1.1', subject=subject,
                dimensions=[profile_dimension(subject, d, elite) for d in DIMENSIONS[subject]])


def update_readiness(state, event):
    elite = state['elite']
    for subject in DIMENSIONS:
        for row in readiness_profile(subject, elite)['dimensions']:
            if not row['evidence_refs']:
                continue
            key = digest([subject, row['dimension']])[:24]
            prior = elite['readiness'].get(key)
            if prior != row:
                elite['readiness_transitions'].append(dict(profile_key=key, source_event=event['event_id'],
                    subject=subject, dimension=row['dimension'], before=prior['status'] if prior else 'UNKNOWN',
                    after=row['status'], confidence=row['confidence'], evidence_count=row['evidence_count'],
                    evidence_refs=row['evidence_refs'], reason=row['reason']))
                elite['readiness'][key] = row


def apply(state, event, update):
    payload = event['payload']
    if payload.get('ruleset') != RULESET or type(payload.get('confirmed')) is not bool:
        raise JournalConflict('Unsupported Elite ruleset or confirmation envelope')
    elite = state.setdefault('elite', empty())
    r = payload['record']
    entry = dict(record=deepcopy(r), confirmed=payload['confirmed'], event_id=event['event_id'])
    if event['kind'] == 'elite_evidence':
        if r['evidence_id'] in elite['evidence']:
            raise JournalConflict('Duplicate elite evidence identity')
        prior_entries = [e for e in elite['evidence'].values() if e['record']['subject'] == r['subject'] and e['record']['concept'] == r['concept']]
        before_count = len(performances(prior_entries))
        elite['evidence'][r['evidence_id']] = entry
        current_entries = prior_entries + [entry]
        strong = performances(current_entries)
        def action(item):
            for mode in r.get('failure_modes', []):
                if mode not in item['weakness_tags']:
                    item['weakness_tags'].append(mode)
            if entry['confirmed'] and r['result'] in {'FAIL', 'UNSOLVED'}:
                item['mistake_count'] += 1
                item['mistakes'].append(dict(source=event['event_id'], detail=r['result'], failure_modes=r.get('failure_modes', [])))
                item['confidence'] = 'low'
            if entry['confirmed'] and r['result'] in {'PASS', 'FAIL', 'PARTIAL', 'UNSOLVED'} and r.get('independence_class') != 'SOLUTION_SEEN':
                if not item['last_practiced'] or timestamp(r['occurred_at']) > timestamp(item['last_practiced']):
                    item['last_practiced'] = r['occurred_at']
            item['observations'].append(dict(source=event['event_id'], kind='elite_evidence',
                                             independence_class=r.get('independence_class', 'NOT_RECORDED')))
            reason = 'Recorded provenance; assisted/unknown/solution-seen work cannot independently raise mastery'
            if eligible(entry) and len(strong) > before_count:
                days, contexts, kinds, span = diversity(strong)
                transfer = any(transfer_success(e) for e in strong)
                benchmark = any(benchmark_verified(b) and benchmark_performances(b, strong)
                                for b in related_benchmarks(elite, strong))
                cap = 0
                if len(strong) >= 2 and days >= 2 and contexts >= 2:
                    cap = 1
                if len(strong) >= 3 and days >= 3 and kinds >= 2 and contexts >= 2:
                    cap = 2
                if len(strong) >= 4 and days >= 3 and kinds >= 2 and contexts >= 3 and transfer:
                    cap = 3
                if len(strong) >= 5 and days >= 4 and kinds >= 3 and contexts >= 3 and transfer and benchmark:
                    cap = 4
                if len(strong) >= 6 and days >= 5 and contexts >= 4 and kinds >= 3 and span >= 30 and transfer and benchmark and any(e['record']['task_type'] == 'ORAL_EXAM' for e in strong):
                    cap = 5
                old = item['mastery_level']
                item['mastery_level'] = max(old, min(old + 1, cap))
                if cap:
                    item['confidence'] = 'medium' if cap < 3 else 'high'
                reason = ('Distinct independent performances support at most one level; Elite ruleset 1.1'
                          if item['mastery_level'] > old else 'Insufficient diverse, delayed independent Elite evidence for a promotion')
            return reason
        update(event, r['subject'], r['concept'], action)
    elif event['kind'] == 'benchmark':
        if r['benchmark_id'] in elite['benchmarks']:
            raise JournalConflict('Duplicate benchmark identity')
        elite['benchmarks'][r['benchmark_id']] = entry
    elif event['kind'] == 'target_capability':
        targets=elite.setdefault('targets',{})
        if r['target_id'] in targets:
            raise JournalConflict('Duplicate target capability identity')
        targets[r['target_id']] = entry
        return
    else:
        if r['link_id'] in elite['links']:
            raise JournalConflict('Duplicate prerequisite link identity')
        elite['links'][r['link_id']] = entry
    update_readiness(state, event)


def prerequisite_gaps(state, subject, concept):
    result = []
    for entry in state.get('elite', empty())['links'].values():
        r = entry['record']
        if r['source_subject'] != subject or r['source_concept'] != concept:
            continue
        target = next((c for c in state['concepts'].values() if c['subject'] == r['target_subject'] and c['concept'] == r['target_concept']), None)
        result.append(dict(link_id=r['link_id'], relation=r['relation'], target_subject=r['target_subject'],
            target_concept=r['target_concept'], target_mastery=target['mastery_level'] if target else None,
            evidence_refs=r['evidence_refs'], gap='INFORMATIONAL_LINK' if r['relation'] != 'PREREQUISITE' else
            'NOT_RECORDED' if target is None else 'LOW_RECORDED_MASTERY' if target['mastery_level'] < 2 else 'NO_LOW_MASTERY_FLAG',
            curriculum_action='NONE'))
    return result


def concept_evidence(state, subject, concept):
    elite = state.get('elite', empty())
    entries = [e for e in elite['evidence'].values() if e['record']['subject'] == subject and e['record']['concept'] == concept]
    return dict(independent_evidence=[e['event_id'] for e in performances(entries)],
        assisted_evidence=[e['event_id'] for e in entries if e['record'].get('independence_class') in {'HINT_1', 'HINT_2', 'ASSISTED', 'SOLUTION_SEEN'}],
        unconfirmed_evidence=[e['event_id'] for e in entries if not e['confirmed']],
        benchmark_evidence=[b['event_id'] for b in related_benchmarks(elite, entries)],
        transfer_evidence=[e['event_id'] for e in entries if transfer_success(e)],
        failure_modes=dict(Counter(m for e in entries for m in e['record'].get('failure_modes', []))),
        prerequisite_gaps=prerequisite_gaps(state, subject, concept), evidence_refs=[e['event_id'] for e in entries])


def benchmark_summary(entry, elite):
    b = entry['record']
    records = [elite['evidence'][eid] for eid in b['evidence_refs'] if eid in elite['evidence']]
    strong = benchmark_performances(entry, performances(records))
    count = len(strong)
    total = b.get('problems_total')
    # Only a complete, explicitly identified set of attempted problems supports a rate.
    attempts = {e['record'].get('metadata', {}).get('attempt_id') for e in records}
    coverage_complete = (bool(records) and None not in attempts and len(attempts) == b.get('attempted')
                         and all(e['record'].get('assessment_context') == 'BENCHMARK'
                                 and e['record'].get('benchmark_source') == b['source'] for e in records))
    independent_rate = (count / total if total and coverage_complete and benchmark_verified(entry)
                        and all(e['confirmed'] for e in records) and count <= b.get('solved', total) else None)
    known_hints = [e['record']['hint_level'] for e in records if 'hint_level' in e['record']]
    return dict(benchmark_id=b['benchmark_id'], name=b['name'], subject=b['subject'], benchmark_type=b['benchmark_type'],
        source=b['source'], date=b['date'], confirmed=entry['confirmed'],
        independent_solve_rate=independent_rate,
        independent_performances=count, coverage_complete=coverage_complete,
        partial_solve_rate=b['partial'] / total if total and 'partial' in b else None,
        reported_solve_rate=b['solved'] / total if total and 'solved' in b else None,
        hint_dependence=sum(h > 0 for h in known_hints) / len(known_hints) if known_hints else None,
        hint_observations=len(known_hints), linked_evidence_count=len(records),
        mean_seconds_per_attempt=b['duration'] / b['attempted'] if b.get('attempted') and 'duration' in b else None,
        proof_quality=[e['record']['proof_quality'] for e in records if 'proof_quality' in e['record']],
        failure_modes=dict(Counter(m for e in records for m in e['record'].get('failure_modes', []))),
        topic_weaknesses=sorted({e['record']['concept'] for e in records if e['record'].get('failure_modes')}),
        score=b.get('score'), max_score=b.get('max_score'), evidence_refs=b['evidence_refs'],
        interpretation='Observed records only; rates use explicit denominators, not award predictions')


def rolling_benchmarks(entries, elite, window=5):
    """Comparable recent observations, never a forecast or mixed-format average."""
    groups = {}
    result = []
    for entry in sorted(entries, key=lambda e: (e['record']['date'], e['record']['benchmark_id'])):
        r = entry['record']
        key = tuple(r.get(k) for k in ('subject', 'benchmark_type', 'source', 'closed_book', 'no_ai'))
        summary = benchmark_summary(entry, elite)
        group = groups.setdefault(key, [])
        group.append(summary)
        recent = group[-window:]
        result.append({**entry, 'summary': summary, 'rolling_trend': {
            'window_limit': window, 'benchmark_ids': [b['benchmark_id'] for b in recent],
            'dates': [b['date'] for b in recent],
            'independent_solve_rates': [b['independent_solve_rate'] for b in recent],
            'partial_solve_rates': [b['partial_solve_rate'] for b in recent],
            'hint_dependence': [b['hint_dependence'] for b in recent],
            'mean_seconds_per_attempt': [b['mean_seconds_per_attempt'] for b in recent],
            'interpretation': 'Same subject, type, source and conditions only; missing observations stay null. No forecast.'}})
    return result
