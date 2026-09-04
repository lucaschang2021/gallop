"""Validated policy-data loading outside the progression domain."""
from importlib.resources import files
import json


def _resource(name):
    return json.loads(files('gallop.schemas').joinpath(name).read_text(encoding='utf-8'))


def _load_policies():
    policies = _resource('mentorship-policies.json')
    if policies.get('schema_version') != '1.1':
        raise ValueError('Unsupported mentorship policy version')
    required = {'mathematics', 'statistics', 'finance', 'cs-ai'}
    if set(policies.get('subjects', {})) != required:
        raise ValueError('Mentorship policy subjects are incomplete')
    if not all(policy.get('trajectory') and policy.get('mentor_labels')
               for policy in policies['subjects'].values()):
        raise ValueError('Mentorship subject policy is incomplete')
    return policies


POLICIES = _load_policies()
READINESS_DIMENSIONS = _resource('readiness-dimensions.json')


def subject_policy(subject):
    if subject not in POLICIES['subjects']:
        raise ValueError('Unknown mentorship subject')
    return POLICIES['subjects'][subject]
