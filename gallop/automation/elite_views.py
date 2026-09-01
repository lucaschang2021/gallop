"""Small human-readable projections; raw records, metadata and answers stay private."""
from collections import Counter
import re

from .elite_state import benchmark_summary, readiness_profile
from .state import POLICIES
from gallop.mentorship import plan as mentorship_plan, weekly_feedback


def render_elite(state, namespace):
    from .views import bullets
    from gallop.mobile import SENSITIVE
    elite = state['elite']
    def display(value):
        value = str(value)
        if SENSITIVE.search(value) or re.search(r'(?:[A-Za-z]:[\\/]|/(?:home|Users)/)', value):
            return '[private reference omitted]'
        return value
    warning = ('> Isolated synthetic local preview; never real learner evidence.\n\n'
               if namespace == 'integration_tests' else '')
    evidence = sorted(elite['evidence'].values(), key=lambda e: e['record']['occurred_at'], reverse=True)
    training = []
    for entry in evidence[:30]:
        r = entry['record']
        training.append(f"{display(r['subject'])} / {display(r['concept'])}: {r['task_type']} · {r['result']} · "
            f"{r.get('independence_class', 'NOT_RECORDED')} · hint {r.get('hint_level', 'NOT_RECORDED')} · "
            f"agent {r.get('agent_usage', 'NOT_RECORDED')} · "
            f"{r.get('assessment_context', 'NOT_RECORDED')} · confirmed {entry['confirmed']}")
    rows, homes = [], {}
    for subject in POLICIES:
        profile = readiness_profile(subject, elite)
        lines = [f"{r['dimension']}: {r['status']} / {r['confidence']} · {r['evidence_count']} records"
                 for r in profile['dimensions'] if r['evidence_count']]
        rows.append('## ' + subject + '\n\n' + bullets(lines, 30))
        failures = Counter(mode for e in evidence if e['record']['subject'] == subject
                           for mode in e['record'].get('failure_modes', []))
        benchmarks = sorted([b for b in elite['benchmarks'].values() if b['record']['subject'] == subject],
                            key=lambda b: b['record']['date'])
        recent = ([f"Recent benchmark: {display(benchmarks[-1]['record']['name'])} ({benchmarks[-1]['record']['date']})"]
                  if benchmarks else [])
        distributions = Counter(e['record'].get('independence_class', 'NOT_RECORDED') for e in evidence
                                if e['record']['subject'] == subject)
        homes[subject] = '\n\n## Elite evidence\n\n' + bullets(lines, 3) + '\n\n' + bullets(
            recent + [f"Failure: {m} ({n})" for m, n in failures.most_common(3)] +
            [f"Recorded independence distribution (not a score): {dict(sorted(distributions.items()))}"])
        homes[subject] += '\n\n[[Gallop/Automation/Readiness|Readiness]] · [[Gallop/Automation/Benchmarks|Benchmarks]]\n'
    benchmark_rows = []
    for entry in sorted(elite['benchmarks'].values(), key=lambda b: b['record']['date'])[-20:]:
        b = benchmark_summary(entry, elite)
        def rate(key):
            return 'NOT_RECORDED' if b[key] is None else f'{b[key]:.1%}'
        benchmark_rows.append(f"{b['date']} · {display(b['subject'])} · {display(b['name'])} ({b['benchmark_type']}) · "
            f"independent solve rate {rate('independent_solve_rate')} · partial {rate('partial_solve_rate')} · "
            f"hint dependence {rate('hint_dependence')} ({b['hint_observations']} observations) · "
            f"mean seconds/attempt {b['mean_seconds_per_attempt'] if b['mean_seconds_per_attempt'] is not None else 'NOT_RECORDED'}")
    plans=[mentorship_plan(state,t) for t in elite.get('targets',{}).values()]
    weekly=weekly_feedback(state,plans)
    development=[]; north=[]
    for p in plans:
        c=p['current_capability']; t=p['target']
        development.append(f"{display(t['subject'])} / {display(t['dimension'])}: current {c['current_state']} · "
            f"frontier {p['training_zone']} · scaffold {p['scaffolding_level']} · next {p['progression_action']} · "
            f"gains {len(p['capability_gains'])} · transfer {c['transfer_evidence_count']} · "
            f"open prerequisite gaps {sum(g['certainty'] != 'CLOSED' for g in p['prerequisite_gaps'])}")
        if t['north_star']:
            monster=sum(s['training_zone']=='MONSTER_BENCHMARK' for s in p['productive_struggle'])
            subject_benchmarks=sum(b['record']['subject']==t['subject'] for b in elite['benchmarks'].values())
            north.append(f"{display(t['subject'])} / {display(t['dimension'])}: target {t['target_state']} · "
                f"current {c['current_state']} · unresolved prerequisite gaps "
                f"{sum(g['certainty'] != 'CLOSED' for g in p['prerequisite_gaps'])} · "
                f"Monster observations {monster} · benchmark records {subject_benchmarks}")
        subject=t['subject']
        homes[subject] += '\n\n## Progressive Mentorship\n\n' + bullets([
            f"Current capability: {c['current_state']} ({c['confidence']})",
            f"Current frontier: {p['training_zone']} / {p['scaffolding_level']}",
            f"Next evidence action: {p['progression_action']}",
            f"Mentor role: {p['mentor_role']['label']}",
            f"Recent gains: {len(p['capability_gains'])}",
            f"Transfer evidence: {c['transfer_evidence_count']}",
            f"Open prerequisite repair: {sum(g['certainty'] != 'CLOSED' for g in p['prerequisite_gaps'])}",
        ]) + '\n\n[[Gallop/Automation/Development|Development]]\n'
    result = {
        'Gallop/Automation/Elite Training.md': '# Elite Training\n\n' + warning + bullets(training, 30) + '\n',
        'Gallop/Automation/Readiness.md': '# Readiness\n\n' + warning +
            'Capability evidence, separate from concept mastery. Unlisted evidence is UNKNOWN.\n\n' + '\n\n'.join(rows) + '\n',
        'Gallop/Automation/Benchmarks.md': '# Benchmarks\n\n' + warning +
            'Chronological observations; different formats and conditions are not interchangeable. No medal prediction.\n\n' +
            bullets(benchmark_rows, 20) + '\n',
    }
    if plans:
        result.update({
        'Gallop/Automation/Development.md': '# Daily Development\n\n' + warning +
            'The target ceiling does not set daily difficulty.\n\n## Current Frontiers\n' + bullets(development,30) +
            '\n\n## This Week You Gained\n' + bullets(weekly['items'],30) + '\n',
        'Gallop/Automation/North Star.md': '# Elite North Star\n\n' + warning +
            'Long-range calibration, separate from the default daily dashboard. No award or readiness prediction.\n\n' +
            bullets(north,30) + '\n',
        })
    return result, homes
