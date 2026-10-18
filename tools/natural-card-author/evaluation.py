"""Independent fixture semantics, normalization, and selected native assertions."""
import copy
from core import KEYWORDS,CORE_BODY,TRIGGERS,component,short,walk

def canonical(plan,catalog):
    if plan['status']!='ready':return {'status':plan['status']}
    faction=catalog.cards[str(plan['base_guid'])]['faction']
    own='plant_hero'if faction=='Plants'else'zombie_hero';enemy='zombie_hero'if faction=='Plants'else'plant_hero'
    card=catalog.compile(plan)
    armor=component(card['entity'],'Armor',True)
    result={'status':'ready','base_guid':plan['base_guid'],'mode':plan['mode'],
        'stats':[card[k]for k in ('displaySunCost','displayAttack','displayHealth')],
        'keywords':sorted(k for k,v in KEYWORDS.items()if component(card['entity'],v,True)),
        'armor':armor['$data']['ArmorAmount']['BaseValue']if armor else 0,
        'name':plan.get('name',catalog.by_guid[plan['base_guid']]['name']),'abilities':[]}
    if plan['mode']=='copy_native':result['source_guid']=plan['source_guid']
    for ability in plan.get('abilities',[]):
        a=copy.deepcopy(ability);a['selection']=a.get('selection','all')
        a['count']=0 if a['selection']=='all'else a.get('count',1)
        a['target']={'own_hero':own,'enemy_hero':enemy}.get(a['target'],a['target'])
        for e in a['effects']:
            if e['type']=='buff':e.setdefault('attack',0);e.setdefault('health',0);e.setdefault('duration','permanent')
            if e['type']=='gain_resource':e.setdefault('duration','end_of_turn')
        result['abilities'].append(a)
    return result

def assert_structure(plan,expected,catalog):
    card=catalog.compile(plan)
    if expected['mode']=='copy_native':
        package=lambda c:[n for n in c['entity']['components']if short(n['$type'])not in CORE_BODY]
        assert package(card)==package(catalog.cards[str(expected['source_guid'])]),'Native ability package differs'
        return
    descriptor=component(card['entity'],'EffectEntitiesDescriptor',True)
    entities=descriptor['$data']['entities']if descriptor else []
    if expected['mode']=='replace':assert len(entities)==len(expected.get('abilities',[]))
    for a,entity in zip(expected.get('abilities',[]),entities):
        assert component(entity,TRIGGERS[a['trigger']])
        ptf=component(entity,'PrimaryTargetFilter')['$data']
        assert ptf['SelectionType']==a.get('selection','all').title()
        if a.get('selection','all')!='all':assert ptf['NumTargets']==a.get('count',1)
        for e in a['effects']:
            if e['type']in ('damage','draw'):
                typ,key=('DamageEffectDescriptor','DamageAmount')if e['type']=='damage'else('DrawCardEffectDescriptor','DrawAmount')
                assert component(entity,typ)['$data'][key]==e['amount']
            if e['type']=='buff':
                d=component(entity,'BuffEffectDescriptor')['$data']
                assert(d['AttackAmount'],d['HealthAmount'])==(e.get('attack',0),e.get('health',0))
            if e['type']=='summon'and a['target']=='own_open_lanes':
                assert ptf['Query']['$data']['IsForTeamupCard']==catalog.cards[str(e['card_guid'])]['isTeamup']
        if a['trigger']=='self_damaged':assert short(component(entity,'TriggerTargetFilter')['$data']['Query']['$type'])=='SelfQuery'
        if a['trigger']=='self_destroyed':assert any(short(n.get('$type',''))=='WillTriggerOnDeathEffectsQuery'for n in walk(entity))
        if a['target']=='adjacent_enemy_fighters':assert any(short(n.get('$type',''))=='InAdjacentLaneQuery'for n in walk(entity))
