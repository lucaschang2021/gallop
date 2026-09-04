"""Current capability derived only from explicit evidence history."""
from collections import Counter

from .evidence import capability_state, entries_for, transfer_success
from .primitives import digest, timestamp
from .scaffolding import recommended_scaffolding


def calculate_capability(state, subject, dimension, dimension_catalog):
    entries = entries_for(state, subject, dimension, dimension_catalog)
    current, assisted, strong, retained, research = capability_state(entries)
    latest = max(entries, key=lambda entry: timestamp(entry['record']['occurred_at'])) if entries else None
    confidence = 'low' if current in {'UNKNOWN', 'EXPOSED', 'GUIDED', 'PARTIALLY_INDEPENDENT'} else 'medium'
    if current in {'TRANSFERRED', 'RETAINED', 'RESEARCH_USABLE'}:
        confidence = 'high'
    if latest and latest['record']['result'] in {'FAIL', 'UNSOLVED'}:
        confidence = 'low'
    scaffold, fade_refs = recommended_scaffolding(entries)
    by_zone = Counter(entry['record'].get('training_zone', 'NOT_RECORDED') for entry in entries)
    by_difficulty = Counter(entry['record'].get('difficulty', 'NOT_RECORDED') for entry in entries)
    transfers = [entry for entry in strong if transfer_success(entry)]
    hints = [entry['record']['hint_level'] for entry in entries
             if entry['confirmed'] and 'hint_level' in entry['record']]
    return {'capability_id': 'cap-' + digest([subject, dimension])[:24], 'subject': subject,
            'dimension': dimension, 'current_state': current, 'confidence': confidence,
            'evidence_count': len(entries), 'independent_evidence_count': len(strong),
            'assisted_evidence_count': len(assisted),
            'last_updated': latest['record']['occurred_at'] if latest else None,
            'evidence_refs': [entry['event_id'] for entry in entries],
            'recommended_scaffolding': scaffold, 'scaffolding_evidence_refs': fade_refs,
            'research_independence': research, 'evidence_by_zone': dict(sorted(by_zone.items())),
            'evidence_by_difficulty': dict(sorted(by_difficulty.items())),
            'transfer_evidence_count': len(transfers), 'retention_evidence_count': len(retained),
            'observed_hint_levels': hints,
            'evidence_contexts': [
                {'event_id': entry['event_id'],
                 'difficulty': entry['record'].get('difficulty', 'NOT_RECORDED'),
                 'training_zone': entry['record'].get('training_zone', 'NOT_RECORDED'),
                 'scaffolding_level': entry['record'].get('scaffolding_level', 'NOT_RECORDED'),
                 'hint_level': entry['record'].get('hint_level', 'NOT_RECORDED'),
                 'prior_exposure': entry['record'].get('prior_exposure', 'NOT_RECORDED'),
                 'time_spent': entry['record'].get('time_spent', 'NOT_RECORDED'),
                 'task_novelty': entry['record'].get('task_novelty', 'NOT_RECORDED'),
                 'agent_usage': entry['record'].get('agent_usage', 'NOT_RECORDED')}
                for entry in entries]}
