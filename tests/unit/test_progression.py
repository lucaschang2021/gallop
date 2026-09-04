"""The progression domain is deterministic and independently testable."""
from copy import deepcopy

from gallop.progression import ProgressionContext, calculate_capability, decide
from gallop.progression.mentor_role import determine_mentor_role
from gallop.progression.prerequisites import diagnose_prerequisites
from gallop.progression.scaffolding import recommended_scaffolding
from gallop.progression.struggle import classify_struggle
from gallop.progression.zones import determine_zone


CATALOG = {'mathematics': ['Proof Maturity', 'Independence', 'Transfer']}
POLICY = {'trajectory': ['understand', 'independent proof'],
          'mentor_labels': {'TEACHER': 'Teacher', 'COACH': 'Coach',
                            'DOMAIN_MENTOR': 'Mentor', 'RESEARCH_SUPERVISOR': 'Supervisor',
                            'EVALUATOR': 'Evaluator'}}


def evidence(index=1, **changes):
    record = {'evidence_id': f'evidence-{index}', 'subject': 'mathematics', 'concept': 'Proof',
              'task_type': 'PROOF', 'occurred_at': f'2026-01-0{index}T10:00:00Z',
              'readiness_dimensions': ['Proof Maturity'], 'result': 'PASS',
              'independence_class': 'ASSISTED', 'hint_level': 4, 'agent_usage': 'AI_ASSISTED',
              'scaffolding_level': 'S5', 'training_zone': 'PRODUCTIVE',
              'assessment_context': 'FORMATIVE', 'evidence_refs': [f'response-{index}'],
              'metadata': {'attempt_id': f'attempt-{index}', 'context_id': f'context-{index}'}}
    record.update(changes)
    return {'event_id': f'event-{index}', 'confirmed': True, 'record': record}


def state(*entries):
    return {'elite': {'ruleset': 'elite-v1.1',
                      'evidence': {entry['event_id']: entry for entry in entries},
                      'benchmarks': {}, 'links': {}, 'readiness': {}, 'readiness_transitions': []}}


def target(prerequisite_refs=()):
    return {'event_id': 'target-event', 'confirmed': True,
            'record': {'target_id': 'target', 'subject': 'mathematics', 'dimension': 'Proof Maturity',
                       'target_state': 'RESEARCH_USABLE', 'north_star': True,
                       'prerequisite_refs': list(prerequisite_refs)}}


def test_capability_and_decision_are_repeatable_and_do_not_mutate_inputs():
    history = state(evidence())
    context = ProgressionContext(history, target(), POLICY, CATALOG)
    before = deepcopy(history)
    first = decide(context)
    assert decide(context) == first
    assert history == before
    assert first['current_capability']['current_state'] == 'GUIDED'
    assert first['training_zone'] == 'PRODUCTIVE'
    assert first['queue_mutation'] == 'NONE'


def test_capability_ignores_target_ceiling_and_uses_only_evidence():
    empty = state()
    assert calculate_capability(empty, 'mathematics', 'Proof Maturity', CATALOG)['current_state'] == 'UNKNOWN'
    assert decide(ProgressionContext(empty, target(), POLICY, CATALOG))['training_zone'] == 'FOUNDATION'


def test_scaffolding_fades_exactly_one_matching_step():
    assert recommended_scaffolding([evidence()]) == ('S4', ['event-1'])
    jumped = evidence(scaffolding_level='S0', independence_class='INDEPENDENT', hint_level=0,
                      agent_usage='NONE')
    assert recommended_scaffolding([jumped]) == ('S5', [])


def test_prerequisite_and_struggle_require_explicit_evidence():
    failed = evidence(result='FAIL', independence_class='UNSOLVED', hint_level=0,
                      agent_usage='NONE', failure_modes=['math:DEFINITION_GAP'])
    history = state(failed)
    link = {'event_id': 'link-event', 'confirmed': True,
            'record': {'link_id': 'link', 'source_concept': 'Proof',
                       'target_subject': 'mathematics', 'target_concept': 'Definitions'}}
    history['elite']['links']['link'] = link
    gaps = diagnose_prerequisites(history, target(['link']), [failed])
    assert gaps[0]['certainty'] == 'UNKNOWN'
    rows = classify_struggle([failed], gaps)
    assert rows[0]['classification'] == 'CONCEPTUAL_FAILURE'


def test_zone_and_mentor_role_are_pure_policy_decisions():
    action, zone, design = determine_zone('INDEPENDENT', [], [], [])
    assert (action, zone, design['difficulty']) == ('ADD_TRANSFER_TEST', 'STRETCH', 'HARD')
    assert determine_mentor_role('INDEPENDENT', POLICY) == {
        'role': 'RESEARCH_SUPERVISOR', 'label': 'Supervisor'}
