"""Explicit-link prerequisite diagnosis."""
from collections import Counter

from .evidence import empty_elite, performances


def diagnose_prerequisites(state, target_entry, entries):
    elite = state.get('elite', empty_elite())
    links = [elite['links'][ref] for ref in target_entry['record'].get('prerequisite_refs', [])
             if ref in elite['links']]
    source_concepts = {entry['record']['concept'] for entry in entries}
    failures = [entry for entry in entries
                if entry['confirmed'] and entry['record']['result'] in {'FAIL', 'UNSOLVED'}]
    diagnostic = [entry for entry in failures if entry['record'].get('failure_modes')
                  or entry['record'].get('productive_struggle', {}).get('classification') == 'PREREQUISITE_FAILURE']
    output = []
    for entry in links:
        record = entry['record']
        if source_concepts and record['source_concept'] not in source_concepts:
            continue
        target_entries = [candidate for candidate in elite['evidence'].values()
                          if candidate['record']['subject'] == record['target_subject']
                          and candidate['record']['concept'] == record['target_concept']]
        certainty = 'CLOSED' if performances(target_entries) else 'POSSIBLE' if len(diagnostic) >= 2 else 'UNKNOWN'
        output.append({'link_id': record['link_id'], 'target_subject': record['target_subject'],
                       'target_concept': record['target_concept'], 'certainty': certainty,
                       'failure_evidence_refs': [candidate['event_id'] for candidate in diagnostic],
                       'failure_modes': dict(Counter(mode for candidate in diagnostic
                                                     for mode in candidate['record'].get('failure_modes', []))),
                       'prerequisite_evidence_refs': [candidate['event_id'] for candidate in target_entries]})
    return output
