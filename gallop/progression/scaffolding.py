"""Deterministic assistance fading."""
from .models import SCAFFOLDING


def recommended_scaffolding(entries):
    """Fade one step only after evidence at the currently designed support level."""
    index = 0
    refs = []
    for entry in entries:
        record = entry['record']
        if not entry['confirmed'] or record.get('scaffolding_level') != SCAFFOLDING[index]:
            continue
        useful = (record['result'] == 'PASS'
                  and record.get('independence_class') in {'ASSISTED', 'HINT_2', 'HINT_1', 'INDEPENDENT'})
        if useful and index < len(SCAFFOLDING) - 1:
            refs.append(entry['event_id'])
            index += 1
    return SCAFFOLDING[index], refs
