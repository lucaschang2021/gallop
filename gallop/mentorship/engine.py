"""Deterministic recommendations. It never mutates mastery or schedules work."""
from collections import Counter
from datetime import timedelta

from gallop.automation.elite_protocol import eligible, performances, transfer_success
from gallop.automation.elite_state import dimensions, empty
from gallop.automation.protocol import digest, timestamp
from .models import CAPABILITY_STATES, SCAFFOLDING
from .policy import subject_policy

def _entries(state,subject,dimension):
    elite=state.get('elite',empty())
    return sorted([e for e in elite['evidence'].values() if e['record']['subject']==subject
                   and dimension in dimensions(e['record'])],key=lambda e:(timestamp(e['record']['occurred_at']),e['event_id']))

def _diverse(entries):
    days={timestamp(e['record']['occurred_at']).date() for e in entries}
    contexts={e['record'].get('metadata',{}).get('context_id') for e in entries}
    contexts.discard(None)
    return len(days),len(contexts)

def recommended_scaffolding(entries):
    """Fade one step only after evidence at the currently designed support level."""
    index=0
    refs=[]
    for entry in entries:
        r=entry['record']
        if not entry['confirmed'] or r.get('scaffolding_level')!=SCAFFOLDING[index]:
            continue
        useful=(r['result']=='PASS' and r.get('independence_class') in
                {'ASSISTED','HINT_2','HINT_1','INDEPENDENT'})
        if useful and index<len(SCAFFOLDING)-1:
            refs.append(entry['event_id'])
            index+=1
    return SCAFFOLDING[index],refs

def research_independence(entries):
    research=[e for e in entries if e['record']['task_type'] in {'RESEARCH','REPLICATION','PAPER_READING'}
              or e['record'].get('metadata',{}).get('research_component') is True]
    assisted=[e for e in research if e['confirmed'] and e['record']['result']=='PASS']
    strong=performances(research)
    state='RI0'
    if assisted: state='RI1'
    if any(e['record'].get('scaffolding_level') in {'S3','S2'} for e in assisted): state='RI2'
    if strong: state='RI3'
    if len(strong)>=3: state='RI4'
    if len(strong)>=4 and any(e['record'].get('metadata',{}).get('project_id') for e in strong): state='RI5'
    if len(strong)>=6 and any(transfer_success(e) for e in strong) and any(e['record'].get('retention') for e in strong): state='RI6'
    return {'state':state,'label':{'RI0':'DEPENDENT','RI1':'GUIDED','RI2':'STRUCTURED','RI3':'SEMI_INDEPENDENT',
            'RI4':'INDEPENDENT_COMPONENT','RI5':'INDEPENDENT_PROJECT','RI6':'RESEARCH_READY'}[state],
            'evidence_refs':[e['event_id'] for e in research]}

def _state(entries):
    confirmed=[e for e in entries if e['confirmed']]
    assisted=[e for e in confirmed if e['record']['result']=='PASS' and e['record'].get('independence_class') in {'HINT_1','HINT_2','ASSISTED'}]
    strong=performances(entries)
    days,contexts=_diverse(strong)
    value='UNKNOWN'
    if entries: value='EXPOSED'
    if assisted: value='GUIDED'
    if strong: value='PARTIALLY_INDEPENDENT'
    developmental=[e for e in strong if e['record'].get('training_zone') in {None,'PRODUCTIVE','STRETCH'}
                   and e['record'].get('difficulty') not in {'INTRODUCTORY','EASY'}]
    if len(strong)>=3 and len(developmental)>=2 and days>=3 and contexts>=3: value='INDEPENDENT'
    if value=='INDEPENDENT' and any(transfer_success(e) for e in strong): value='TRANSFERRED'
    retained=[e for e in strong if e['record'].get('retention',{}).get('delay_days',0)>=7
              and e['record']['retention'].get('closed_book') is True]
    if value in {'INDEPENDENT','TRANSFERRED'} and retained: value='RETAINED'
    ri=research_independence(entries)
    if value=='RETAINED' and ri['state']=='RI6': value='RESEARCH_USABLE'
    return value,assisted,strong,retained,ri

def capability(state,subject,dimension):
    entries=_entries(state,subject,dimension)
    current,assisted,strong,retained,ri=_state(entries)
    latest=max(entries,key=lambda e:timestamp(e['record']['occurred_at'])) if entries else None
    confidence='low' if current in {'UNKNOWN','EXPOSED','GUIDED','PARTIALLY_INDEPENDENT'} else 'medium'
    if current in {'TRANSFERRED','RETAINED','RESEARCH_USABLE'}: confidence='high'
    if latest and latest['record']['result'] in {'FAIL','UNSOLVED'}: confidence='low'
    scaffold,fade_refs=recommended_scaffolding(entries)
    by_zone=Counter(e['record'].get('training_zone','NOT_RECORDED') for e in entries)
    by_difficulty=Counter(e['record'].get('difficulty','NOT_RECORDED') for e in entries)
    transfers=[e for e in strong if transfer_success(e)]
    hints=[e['record']['hint_level'] for e in entries if e['confirmed'] and 'hint_level' in e['record']]
    return {'capability_id':'cap-'+digest([subject,dimension])[:24],'subject':subject,'dimension':dimension,
            'current_state':current,'confidence':confidence,'evidence_count':len(entries),
            'independent_evidence_count':len(strong),'assisted_evidence_count':len(assisted),
            'last_updated':latest['record']['occurred_at'] if latest else None,
            'evidence_refs':[e['event_id'] for e in entries],'recommended_scaffolding':scaffold,
            'scaffolding_evidence_refs':fade_refs,'research_independence':ri,
            'evidence_by_zone':dict(sorted(by_zone.items())),
            'evidence_by_difficulty':dict(sorted(by_difficulty.items())),
            'transfer_evidence_count':len(transfers),'retention_evidence_count':len(retained),
            'observed_hint_levels':hints,
            'evidence_contexts':[{'event_id':e['event_id'],'difficulty':e['record'].get('difficulty','NOT_RECORDED'),
                'training_zone':e['record'].get('training_zone','NOT_RECORDED'),
                'scaffolding_level':e['record'].get('scaffolding_level','NOT_RECORDED'),
                'hint_level':e['record'].get('hint_level','NOT_RECORDED'),
                'prior_exposure':e['record'].get('prior_exposure','NOT_RECORDED'),
                'time_spent':e['record'].get('time_spent','NOT_RECORDED'),
                'task_novelty':e['record'].get('task_novelty','NOT_RECORDED'),
                'agent_usage':e['record'].get('agent_usage','NOT_RECORDED')} for e in entries]}

def prerequisite_diagnosis(state,target,entries):
    elite=state.get('elite',empty())
    links=[elite['links'][ref] for ref in target['record'].get('prerequisite_refs',[]) if ref in elite['links']]
    source_concepts={e['record']['concept'] for e in entries}
    failures=[e for e in entries if e['confirmed'] and e['record']['result'] in {'FAIL','UNSOLVED'}]
    diagnostic=[e for e in failures if e['record'].get('failure_modes') or
                e['record'].get('productive_struggle',{}).get('classification')=='PREREQUISITE_FAILURE']
    output=[]
    for entry in links:
        r=entry['record']
        if source_concepts and r['source_concept'] not in source_concepts: continue
        target_entries=[e for e in elite['evidence'].values() if e['record']['subject']==r['target_subject']
                        and e['record']['concept']==r['target_concept']]
        target_strong=performances(target_entries)
        certainty='CLOSED' if target_strong else 'POSSIBLE' if len(diagnostic)>=2 else 'UNKNOWN'
        output.append({'link_id':r['link_id'],'target_subject':r['target_subject'],'target_concept':r['target_concept'],
                       'certainty':certainty,'failure_evidence_refs':[e['event_id'] for e in diagnostic],
                       'failure_modes':dict(Counter(m for e in diagnostic for m in e['record'].get('failure_modes',[]))),
                       'prerequisite_evidence_refs':[e['event_id'] for e in target_entries]})
    return output

def struggle(entries,gaps):
    rows=[]
    for entry in entries:
        r=entry['record']
        if 'productive_struggle' in r:
            classification=r['productive_struggle']['classification']
        elif r['result'] in {'FAIL','UNSOLVED'} and r.get('training_zone')=='MONSTER_BENCHMARK':
            classification='OVERCHALLENGE'
        elif r['result'] in {'FAIL','UNSOLVED'} and any(g['certainty']=='POSSIBLE' for g in gaps):
            classification='PREREQUISITE_FAILURE'
        elif r['result'] in {'FAIL','UNSOLVED'} and r.get('failure_modes'):
            classification='CONCEPTUAL_FAILURE'
        else:
            continue
        rows.append({'classification':classification,'source_event':entry['event_id'],
                     'training_zone':r.get('training_zone','NOT_RECORDED'),
                     'milestones':r.get('productive_struggle',{}).get('milestones',[]),
                     'evidence_refs':r.get('productive_struggle',{}).get('evidence_refs',[entry['event_id']])})
    return rows

def gains(state,subject,dimension):
    entries=_entries(state,subject,dimension)
    result=[]; previous='UNKNOWN'; previous_scaffold='S5'; previous_hint=None; previous_hint_event=None
    for i,entry in enumerate(entries):
        current,*_= _state(entries[:i+1])
        scaffold,_=recommended_scaffolding(entries[:i+1])
        if CAPABILITY_STATES.index(current)>CAPABILITY_STATES.index(previous):
            result.append({'gain_id':'gain-'+digest([entry['event_id'],current])[:24],
                'subject':subject,'dimension':dimension,'before':previous,'after':current,
                'description':f'{dimension} moved from {previous} to {current}',
                'at':entry['record']['occurred_at'],'evidence_refs':[entry['event_id']]})
            previous=current
        if SCAFFOLDING.index(scaffold)>SCAFFOLDING.index(previous_scaffold):
            result.append({'gain_id':'gain-'+digest([entry['event_id'],scaffold])[:24],
                'subject':subject,'dimension':dimension,'before':previous_scaffold,'after':scaffold,
                'description':f'Designed support faded from {previous_scaffold} to {scaffold}',
                'at':entry['record']['occurred_at'],'evidence_refs':[entry['event_id']]})
            previous_scaffold=scaffold
        hint=entry['record'].get('hint_level') if entry['confirmed'] and entry['record']['result']=='PASS' else None
        if hint is not None and previous_hint is not None and hint < previous_hint:
            result.append({'gain_id':'gain-'+digest([entry['event_id'],'hint',hint])[:24],
                'subject':subject,'dimension':dimension,'before':f'HINT_{previous_hint}','after':f'HINT_{hint}',
                'description':f'Observed hint use decreased from level {previous_hint} to level {hint}',
                'at':entry['record']['occurred_at'],'evidence_refs':[previous_hint_event,entry['event_id']]})
        if hint is not None:
            previous_hint,previous_hint_event=hint,entry['event_id']
    return result

def plan(state,target_entry):
    target=target_entry['record']; subject=target['subject']; dimension=target['dimension']
    current=capability(state,subject,dimension); entries=_entries(state,subject,dimension)
    gaps=prerequisite_diagnosis(state,target_entry,entries); struggles=struggle(entries,gaps)
    possible=next((g for g in gaps if g['certainty']=='POSSIBLE'),None)
    closed=next((g for g in gaps if g['certainty']=='CLOSED'),None)
    over=sum(s['classification']=='OVERCHALLENGE' for s in struggles)
    state_name=current['current_state']
    if possible: action,zone='REPAIR_PREREQUISITE','FOUNDATION'
    elif closed and not any(e['record']['result']=='PASS' for e in entries[-1:]): action,zone='RETEST_TARGET','PRODUCTIVE'
    elif over>=2 and state_name not in {'INDEPENDENT','TRANSFERRED','RETAINED','RESEARCH_USABLE'}: action,zone='REDUCE_TASK_SPAN','FOUNDATION'
    elif state_name in {'UNKNOWN','EXPOSED'}: action,zone='MAINTAIN','FOUNDATION'
    elif state_name=='GUIDED': action,zone='REDUCE_SCAFFOLDING','PRODUCTIVE'
    elif state_name=='PARTIALLY_INDEPENDENT': action,zone='INCREASE_NOVELTY','PRODUCTIVE'
    elif state_name=='INDEPENDENT': action,zone='ADD_TRANSFER_TEST','STRETCH'
    elif state_name=='TRANSFERRED': action,zone='ADD_RETENTION_TEST','STRETCH'
    elif state_name=='RETAINED': action,zone='MOVE_TO_RESEARCH_MODE','STRETCH'
    else: action,zone='MAINTAIN','MONSTER_BENCHMARK'
    design={'FOUNDATION':{'difficulty':'INTRODUCTORY','novelty':'VARIANT','ambiguity':'LOW'},
            'PRODUCTIVE':{'difficulty':'MEDIUM','novelty':'NEW_CONTEXT','ambiguity':'MODERATE'},
            'STRETCH':{'difficulty':'HARD','novelty':'UNFAMILIAR','ambiguity':'HIGH'},
            'MONSTER_BENCHMARK':{'difficulty':'RESEARCH','novelty':'OPEN_ENDED','ambiguity':'VERY_HIGH'}}[zone]
    role={'UNKNOWN':'TEACHER','EXPOSED':'TEACHER','GUIDED':'COACH','PARTIALLY_INDEPENDENT':'DOMAIN_MENTOR',
          'INDEPENDENT':'RESEARCH_SUPERVISOR','TRANSFERRED':'RESEARCH_SUPERVISOR',
          'RETAINED':'RESEARCH_SUPERVISOR','RESEARCH_USABLE':'EVALUATOR'}[state_name]
    policy=subject_policy(subject)
    return {'target':target,'current_capability':current,'training_zone':zone,
            'scaffolding_level':current['recommended_scaffolding'],'progression_action':action,
            'progression_reason':f'Evidence-backed {state_name}; target {target["target_state"]} does not set current capability',
            'prerequisite_gaps':gaps,'productive_struggle':struggles,'capability_gains':gains(state,subject,dimension),
            'mentor_role':{'role':role,'label':policy['mentor_labels'][role]},
            'research_independence':current['research_independence'],
            'task_design':{**design,'independence_destination':'INDEPENDENT'},
            'subject_policy_reference':{k:v for k,v in policy.items() if k!='mentor_labels'},
            'queue_mutation':'NONE','north_star':target['north_star']}

def weekly_feedback(state,plans):
    gains_all=[g for p in plans for g in p['capability_gains']]
    if not gains_all: return {'heading':'This Week You Gained','items':[],'evidence_refs':[]}
    end=max(timestamp(g['at']) for g in gains_all); start=end-timedelta(days=6)
    recent=[g for g in gains_all if timestamp(g['at'])>=start]
    return {'heading':'This Week You Gained','items':[g['description'] for g in recent],
            'evidence_refs':[ref for g in recent for ref in g['evidence_refs']]}
