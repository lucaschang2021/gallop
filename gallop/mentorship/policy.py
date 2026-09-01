"""Subject policy is data; core progression contains no subject forks."""
from importlib.resources import files
import json

POLICIES=json.loads(files('gallop.schemas').joinpath('mentorship-policies.json').read_text(encoding='utf-8'))

def subject_policy(subject):
    if subject not in POLICIES['subjects']:
        raise ValueError('Unknown mentorship subject')
    return POLICIES['subjects'][subject]
