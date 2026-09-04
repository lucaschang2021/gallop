"""Productive-struggle classification from recorded evidence."""


def classify_struggle(entries, gaps):
    rows = []
    for entry in entries:
        record = entry['record']
        if 'productive_struggle' in record:
            classification = record['productive_struggle']['classification']
        elif record['result'] in {'FAIL', 'UNSOLVED'} and record.get('training_zone') == 'MONSTER_BENCHMARK':
            classification = 'OVERCHALLENGE'
        elif record['result'] in {'FAIL', 'UNSOLVED'} and any(gap['certainty'] == 'POSSIBLE' for gap in gaps):
            classification = 'PREREQUISITE_FAILURE'
        elif record['result'] in {'FAIL', 'UNSOLVED'} and record.get('failure_modes'):
            classification = 'CONCEPTUAL_FAILURE'
        else:
            continue
        rows.append({'classification': classification, 'source_event': entry['event_id'],
                     'training_zone': record.get('training_zone', 'NOT_RECORDED'),
                     'milestones': record.get('productive_struggle', {}).get('milestones', []),
                     'evidence_refs': record.get('productive_struggle', {}).get('evidence_refs', [entry['event_id']])})
    return rows
