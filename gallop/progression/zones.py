"""Training-zone and task-design decisions."""


def determine_zone(state_name, entries, gaps, struggles):
    possible = next((gap for gap in gaps if gap['certainty'] == 'POSSIBLE'), None)
    closed = next((gap for gap in gaps if gap['certainty'] == 'CLOSED'), None)
    overchallenge = sum(row['classification'] == 'OVERCHALLENGE' for row in struggles)
    if possible:
        action, zone = 'REPAIR_PREREQUISITE', 'FOUNDATION'
    elif closed and not any(entry['record']['result'] == 'PASS' for entry in entries[-1:]):
        action, zone = 'RETEST_TARGET', 'PRODUCTIVE'
    elif overchallenge >= 2 and state_name not in {'INDEPENDENT', 'TRANSFERRED', 'RETAINED', 'RESEARCH_USABLE'}:
        action, zone = 'REDUCE_TASK_SPAN', 'FOUNDATION'
    elif state_name in {'UNKNOWN', 'EXPOSED'}:
        action, zone = 'MAINTAIN', 'FOUNDATION'
    elif state_name == 'GUIDED':
        action, zone = 'REDUCE_SCAFFOLDING', 'PRODUCTIVE'
    elif state_name == 'PARTIALLY_INDEPENDENT':
        action, zone = 'INCREASE_NOVELTY', 'PRODUCTIVE'
    elif state_name == 'INDEPENDENT':
        action, zone = 'ADD_TRANSFER_TEST', 'STRETCH'
    elif state_name == 'TRANSFERRED':
        action, zone = 'ADD_RETENTION_TEST', 'STRETCH'
    elif state_name == 'RETAINED':
        action, zone = 'MOVE_TO_RESEARCH_MODE', 'STRETCH'
    else:
        action, zone = 'MAINTAIN', 'MONSTER_BENCHMARK'
    design = {'FOUNDATION': {'difficulty': 'INTRODUCTORY', 'novelty': 'VARIANT', 'ambiguity': 'LOW'},
              'PRODUCTIVE': {'difficulty': 'MEDIUM', 'novelty': 'NEW_CONTEXT', 'ambiguity': 'MODERATE'},
              'STRETCH': {'difficulty': 'HARD', 'novelty': 'UNFAMILIAR', 'ambiguity': 'HIGH'},
              'MONSTER_BENCHMARK': {'difficulty': 'RESEARCH', 'novelty': 'OPEN_ENDED',
                                    'ambiguity': 'VERY_HIGH'}}[zone]
    return action, zone, design
