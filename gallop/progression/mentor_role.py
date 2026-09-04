"""Mentor role follows demonstrated capability, never the target ceiling."""


def determine_mentor_role(state_name, subject_policy):
    role = {'UNKNOWN': 'TEACHER', 'EXPOSED': 'TEACHER', 'GUIDED': 'COACH',
            'PARTIALLY_INDEPENDENT': 'DOMAIN_MENTOR', 'INDEPENDENT': 'RESEARCH_SUPERVISOR',
            'TRANSFERRED': 'RESEARCH_SUPERVISOR', 'RETAINED': 'RESEARCH_SUPERVISOR',
            'RESEARCH_USABLE': 'EVALUATOR'}[state_name]
    return {'role': role, 'label': subject_policy['mentor_labels'][role]}
