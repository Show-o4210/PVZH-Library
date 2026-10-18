"""Bounded retrieval and an inspectable, model-independent plan protocol."""
import json
from pathlib import Path
from core import PlanError,PLAN_FIELDS,exact

def messages(catalog,cases):
    if not 1<=len(cases)<=6:raise ValueError('Use 1..6 requests per API call')
    if len({c['case_id']for c in cases})!=len(cases):raise ValueError('Duplicate case ID')
    if any(not isinstance(c.get('request'),str)or len(c['request'])>4000 for c in cases):raise ValueError('Invalid request length')
    system=Path(__file__).with_name('knowledge.md').read_text(encoding='utf-8')
    context=catalog.retrieve([c['request']for c in cases])
    user=json.dumps({'native_card_context':context,'cases':cases,'output':'JSON object with plans array'},ensure_ascii=False)
    return {'system':system,'user':user,'max_tokens':4096}

def validate_envelope(response,cases):
    if not isinstance(response,dict)or set(response)!={'plans'}or not isinstance(response['plans'],list):raise ValueError('Expected plans envelope')
    plans=response['plans'];expected={c['case_id']for c in cases}
    if any(not isinstance(p,dict)or not isinstance(p.get('case_id'),str)for p in plans):raise ValueError('Each plan requires a case ID')
    if len(plans)!=len(cases)or {p.get('case_id')for p in plans}!=expected:raise ValueError('Response case IDs mismatch')
    return {p['case_id']:p for p in plans}

def generate(catalog,client,case,max_attempts=2):
    """Retry invalid ready plans once, using the real compiler's error only."""
    if max_attempts not in (1,2):raise ValueError('Use at most two generation attempts')
    request=messages(catalog,[case]);attempts=[];feedback=None
    for _ in range(max_attempts):
        user=request['user']
        if feedback:user+='\nCompiler feedback (repair the same request):\n'+json.dumps(feedback,ensure_ascii=False)
        response,meta=client.complete(request['system'],user,request['max_tokens']);attempts.append(meta)
        try:
            plan=validate_envelope(response,[case])[case['case_id']]
            exact(plan,PLAN_FIELDS,'plan')
            if type(plan.get('schema_version'))is not int or plan['schema_version']!=1:raise PlanError('Invalid plan schema')
            if plan.get('status')in ('clarify','unsupported'):
                if plan.get('schema_version')!=1 or not isinstance(plan.get('reason'),str)or not plan['reason'].strip():raise PlanError('Non-ready plan requires schema and reason')
                return plan,attempts
            catalog.compile(plan)
            return plan,attempts
        except (PlanError,ValueError)as error:feedback={'error':str(error),'previous_response':response}
    raise PlanError('Generation rejected after bounded validation attempts: '+feedback['error'])
