"""Export UI/provider JSON Schema; native semantic checks still run in core."""
import json
from pathlib import Path
from core import TRIGGERS,TARGETS,KEYWORDS,EFFECT_FIELDS

def schema():
    effects=[]
    for kind,fields in EFFECT_FIELDS.items():
        properties={'type':{'const':kind}}
        for field in fields:
            if field=='duration':value={'enum':['permanent','end_of_turn']}
            elif field=='stat':value={'enum':['attack','health','cost']}
            else:value={'type':'integer','minimum':1 if field=='card_guid'else 0 if field=='value'or(field=='amount'and kind in ('damage','heal','draw'))else -100,'maximum':2147483647 if field=='card_guid'else 100}
            properties[field]=value
        required=['type']+([next(iter(fields))]if kind in ('damage','heal','draw','summon','conjure','transform')else['stat','value']if kind=='set_stat'else['amount']if kind=='gain_resource'else[])
        effects.append({'type':'object','additionalProperties':False,'properties':properties,'required':required})
    ability={'type':'object','additionalProperties':False,'required':['trigger','target','effects'],
        'properties':{'trigger':{'enum':list(TRIGGERS)},'target':{'enum':TARGETS},'selection':{'enum':['all','manual','random']},
                      'count':{'type':'integer','minimum':1,'maximum':5},'effects':{'type':'array','minItems':1,'maxItems':8,'items':{'oneOf':effects}}}}
    result={'$schema':'https://json-schema.org/draft/2020-12/schema','title':'PVZH native-only card plan v1','type':'object',
        'additionalProperties':False,'required':['schema_version','status'],
        'properties':{'schema_version':{'const':1,'type':'integer'},'case_id':{'type':'string'},
            'status':{'enum':['ready','unsupported','clarify']},'reason':{'type':'string'},
            'base_guid':{'type':'integer','minimum':1},'source_guid':{'type':'integer','minimum':1},
            'name':{'type':'string','minLength':1,'maxLength':80},'mode':{'enum':['keep','replace','append','copy_native']},
            'stats':{'type':'object','additionalProperties':False,'properties':{k:{'type':'integer','minimum':1 if k=='health'else 0,'maximum':100}for k in ('cost','attack','health')}},
            'keywords':{'type':'array','uniqueItems':True,'items':{'enum':list(KEYWORDS)}},'armor':{'type':'integer','minimum':0,'maximum':20},
            'abilities':{'type':'array','maxItems':8,'items':ability}},
        'allOf':[{'if':{'properties':{'status':{'const':'ready'}}},'then':{'required':['base_guid','mode']},'else':{'required':['reason']}},
            {'if':{'properties':{'mode':{'const':'copy_native'}},'required':['mode']},'then':{'required':['source_guid']},'else':{'properties':{'source_guid':False}}},
            {'if':{'properties':{'mode':{'enum':['keep','copy_native']}},'required':['mode']},'then':{'properties':{'abilities':{'maxItems':0}}}},
            {'if':{'properties':{'mode':{'enum':['keep','append','copy_native']}},'required':['mode']},'then':{'properties':{'keywords':False,'armor':False}}}],
        '$comment':'Reference existence, native baseline, allowed target/effect pairings, same faction and duplicate component rules are enforced by core.py.'}
    return result

if __name__=='__main__':Path(__file__).with_name('plan.schema.json').write_text(json.dumps(schema(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
