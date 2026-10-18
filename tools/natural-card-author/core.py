"""Native-only, source-derived card compiler. No network or device access."""
import copy
import csv
import hashlib
import io
import json
from collections import Counter,defaultdict
from pathlib import Path

TRIGGERS={
    'play':'PlayTrigger','turn_start':'TurnStartTrigger','self_damaged':'DamageTrigger',
    'self_deals_damage':'DamageTrigger','self_destroyed':'DiscardFromPlayTrigger',
    'own_fighter_played':'PlayTrigger','other_own_fighter_played':'PlayTrigger',
    'enemy_fighter_played':'PlayTrigger','own_draw':'DrawCardTrigger',
    'lane_combat_start':'LaneCombatStartTrigger','lane_combat_end':'LaneCombatEndTrigger',
    'continuous':'Continuous'}
TARGETS=['self','event_target','own_hero','enemy_hero','plant_hero','zombie_hero',
    'own_fighters','enemy_fighters','all_fighters','other_own_fighters',
    'lane_enemy_fighters','adjacent_enemy_fighters','self_and_adjacent_own',
    'own_open_lanes','self_lane']
KEYWORDS={'aquatic':'Aquatic','teamup':'Teamup','deadly':'Deadly','frenzy':'Frenzy',
    'strikethrough':'Strikethrough','truestrike':'Truestrike','untrickable':'Untrickable',
    'gravestone':'PlaysFaceDown','double_strike':'GrantedTriggeredAbilities'}
KW_TEXT={'aquatic':'[aquatic]','teamup':'[teamup]','deadly':'[deadly]','frenzy':'[frenzy]',
    'strikethrough':'[strikethrough]','truestrike':'[truestrike]','untrickable':'[untrickable]',
    'gravestone':'[gravestone]','double_strike':'[doublestrike]'}
EFFECT_FIELDS={
    'damage':{'amount'},'heal':{'amount'},'draw':{'amount'},'buff':{'attack','health','duration'},
    'freeze':set(),'destroy':set(),'bounce':set(),'extra_attack':set(),
    'summon':{'card_guid'},'conjure':{'card_guid'},'transform':{'card_guid'},
    'set_stat':{'stat','value'},'gain_resource':{'amount','duration'}}
CORE_BODY={'Card','Attack','Health','SunCost','Plants','Zombies','Rarity','Subtypes','Tags'}
PLAN_FIELDS={'case_id','schema_version','status','reason','base_guid','name','stats','keywords','armor','mode','source_guid','abilities'}

class PlanError(ValueError):
    pass

def short(value):return value.split(',')[0].rsplit('.',1)[-1]
def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from walk(child)
    elif isinstance(value,list):
        for child in value:yield from walk(child)
def exact(value,allowed,where):
    if not isinstance(value,dict):raise PlanError(where+' must be object')
    unknown=set(value)-set(allowed)
    if unknown:raise PlanError(where+' unknown fields: '+','.join(sorted(unknown)))
def number(value,where,low=-100,high=100):
    if type(value)is not int or not low<=value<=high:raise PlanError(where+' integer out of range')
    return value
def component(entity,name,optional=False):
    found=[c for c in entity['components']if short(c['$type'])==name]
    if len(found)!=1:
        if optional and not found:return None
        raise PlanError('Expected one component '+name)
    return found[0]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def bundle_text(path,name):
    import UnityPy
    env=UnityPy.load(Path(path).read_bytes());found=[]
    for obj in env.objects:
        if obj.type.name=='TextAsset':
            tree=obj.read_typetree()
            if tree['m_Name']==name:found.append((obj,tree))
    if len(found)!=1:raise PlanError('Expected exactly one TextAsset '+name)
    value=found[0][1]['m_Script']
    return value.decode('utf-8')if isinstance(value,bytes)else value

class NativeCatalog:
    def __init__(self,cards,cn_text,input_fingerprint=None):
        self.cards=cards;self.cn_text=cn_text
        self.cn={r[0]:r[1]for r in csv.reader(io.StringIO(cn_text,newline=''))if len(r)==2 and r[0]}
        self.fingerprint=input_fingerprint or {}
        self.templates={};self.fields=defaultdict(set);self.strings=defaultdict(set);self.origins=defaultdict(set)
        self.component_types={}
        for guid,card in cards.items():
            for n in walk(card):
                if '$type'not in n:continue
                typ=n['$type'];name=short(typ)
                if name in self.templates and self.templates[name]['$type']!=typ:raise PlanError('Ambiguous native type '+name)
                self.templates.setdefault(name,copy.deepcopy(n));self.fields[typ].update(n['$data']);self.origins[name].add(int(guid))
                for key,value in n['$data'].items():
                    if isinstance(value,str):self.strings[typ,key].add(value)
                    if key=='ComponentType'and isinstance(value,str):self.component_types[short(value)]=value
                if name=='GrantAbilityEffectDescriptor':
                    v=n['$data'].get('GrantableAbilityType','')
                    if str(v).isdigit()and int(v)>=1000:raise PlanError('Private runtime rule in input; use original baseline')
            for n in card['entity']['components']:self.component_types.setdefault(short(n['$type']),n['$type'])
        self.catalog_rows=[]
        for guid,c in cards.items():
            prefab=c.get('prefabName')or''
            self.catalog_rows.append({'guid':int(guid),'name':self.cn.get(prefab+'_name',prefab or guid),
                'faction':c['faction'],'fighter':c['isFighter'],'usable':c['usable'],
                'stats':[c['displaySunCost'],c['displayAttack'],c['displayHealth']],
                'description':self.cn.get(prefab+'_longDesc','')})
        self.by_guid={r['guid']:r for r in self.catalog_rows}

    @classmethod
    def from_directory(cls,path):
        path=Path(path)
        cards=json.loads(bundle_text(path/'card_data_1','cards'))
        digest=hashlib.sha256(json.dumps(cards,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
        baselines=json.loads(Path(__file__).with_name('native-baselines.json').read_text(encoding='utf-8'))
        if digest not in {r['canonical_cards_sha256']for r in baselines['baselines']}:
            raise PlanError('Unknown native baseline: inspect this game revision before adding a verified profile')
        return cls(cards,
            bundle_text(path/'cn_8','LocalizedStrings'),
            {n:sha(path/n)for n in ('card_data_1','cn_8')})

    def node(self,name,**data):
        if name not in self.templates:raise PlanError('No native template: '+name)
        result=copy.deepcopy(self.templates[name]);typ=result['$type']
        if not set(data)<=self.fields[typ]:raise PlanError('Unknown native fields for '+name)
        result['$data'].update(data);return result

    def has(self,name):
        if name not in self.component_types:raise PlanError('Unknown component type '+name)
        return self.node('HasComponentQuery',ComponentType=self.component_types[name])
    def all(self,*queries):return self.node('CompositeAllQuery',queries=list(queries))
    def notq(self,q):return self.node('NotQuery',Query=q)

    def retrieve(self,requests,limit=20):
        text=' '.join(requests)
        grams=lambda s:{s[i:i+2]for i in range(max(0,len(s)-1))}
        wanted=grams(text)
        def score(row):
            name=row['name'];desc=row['description']
            return (100 if name and name in text else 0)+(80 if str(row['guid'])in text else 0)+len(wanted&grams(name))*5+len(wanted&grams(desc))*.15
        selected=sorted(self.catalog_rows,key=score,reverse=True)[:limit]
        for guid in (326,350):
            if guid in self.by_guid and not any(r['guid']==guid for r in selected):selected.append(self.by_guid[guid])
        return selected

    def capabilities(self):
        return {'schema_version':1,'native_only':True,'baseline':self.fingerprint,
            'triggers':TRIGGERS,'targets':TARGETS,'effects':{k:sorted(v)for k,v in EFFECT_FIELDS.items()},
            'keywords':KEYWORDS,'modes':['keep','replace','append','copy_native'],
            'source_provenance':{name:sorted(self.origins[name])for name in set(TRIGGERS.values())},
            'limits':['usable fighter bases only','same-faction native-copy packages',
                      'manual selection only on play','one native component type per entity',
                      'bounce has no following action in same ability','runtime gameplay not inferred from compilation']}

    def query(self,name,faction):
        own=faction;enemy='Zombies'if own=='Plants'else'Plants'
        fighters=lambda fac:self.all(self.has(fac),self.node('TargetableInPlayFighterQuery'))
        hero=lambda fac:self.all(self.has('Player'),self.has(fac))
        if name=='self':return self.node('SelfQuery')
        if name=='event_target':return self.node('TargetQuery')
        if name in ('own_hero','enemy_hero','plant_hero','zombie_hero'):
            return hero({'own_hero':own,'enemy_hero':enemy,'plant_hero':'Plants','zombie_hero':'Zombies'}[name])
        if name=='own_fighters':return fighters(own)
        if name=='enemy_fighters':return fighters(enemy)
        if name=='all_fighters':return self.node('TargetableInPlayFighterQuery')
        if name=='other_own_fighters':return self.all(fighters(own),self.notq(self.node('SelfQuery')))
        if name=='lane_enemy_fighters':return self.all(fighters(enemy),self.node('InSameLaneQuery',OriginEntityType='Self'))
        if name=='adjacent_enemy_fighters':return self.all(fighters(enemy),self.node('InAdjacentLaneQuery',Side='Either'))
        if name=='self_and_adjacent_own':return self.node('CompositeAnyQuery',queries=[self.node('SelfQuery'),self.all(fighters(own),self.node('InAdjacentLaneQuery',Side='Either'))])
        if name=='self_lane':return self.node('SameLaneQuery')
        if name=='own_open_lanes':return self.node('OpenLaneQuery',PlayerFactionType=self.component_types[own],IsForTeamupCard=False)
        raise PlanError('Unsupported target '+str(name))

    def effect(self,data):
        if not isinstance(data,dict)or not isinstance(data.get('type'),str)or data.get('type')not in EFFECT_FIELDS:raise PlanError('Unsupported effect')
        kind=data['type'];exact(data,EFFECT_FIELDS[kind]|{'type'},'effect '+kind)
        amount=lambda:number(data.get('amount'),'amount')
        effect=lambda name,**kw:self.node(name+'EffectDescriptor',**kw)
        if kind in ('damage','heal','draw'):
            value=number(data.get('amount'),'amount',0,100)
            return effect({'damage':'Damage','heal':'Heal','draw':'DrawCard'}[kind],**{{'damage':'DamageAmount','heal':'HealAmount','draw':'DrawAmount'}[kind]:value})
        if kind=='buff':
            duration=data.get('duration','permanent')
            if duration not in ('permanent','end_of_turn'):raise PlanError('Unsupported duration')
            return effect('Buff',AttackAmount=number(data.get('attack',0),'buff attack'),HealthAmount=number(data.get('health',0),'buff health'),BuffDuration={'permanent':'Permanent','end_of_turn':'EndOfTurn'}[duration])
        if kind in ('freeze','destroy','bounce','extra_attack'):
            return effect({'freeze':'Slow','destroy':'DestroyCard','bounce':'ReturnToHandFromPlay','extra_attack':'ExtraAttack'}[kind])
        if kind in ('summon','conjure','transform'):
            guid=number(data.get('card_guid'),'card_guid',1,2147483647)
            if guid not in self.by_guid:raise PlanError('Unknown referenced card')
            if kind=='summon':
                if not self.by_guid[guid]['fighter']:raise PlanError('Summon requires fighter; tricks must be conjured')
                return effect('CreateCard',CardGuid=guid,ForceFaceDown=False)
            subset=self.node('CardGuidQuery',Guid=guid)
            if kind=='conjure':return effect('DrawCardFromSubset',SubsetQuery=subset,DrawAmount=1)
            return effect('TransformIntoCardFromSubset',SubsetQuery=subset)
        if kind=='set_stat':
            stat={'attack':'Attack','health':'Health','cost':'SunCost'}.get(data.get('stat'))
            if not stat:raise PlanError('Unknown stat')
            return effect('SetStat',StatType=stat,Value=number(data.get('value'),'set value',0,100),ModifyOperation='Set',StripNoncontinousModifiers=True)
        if kind=='gain_resource':
            duration=data.get('duration','end_of_turn')
            if duration not in ('permanent','end_of_turn'):raise PlanError('Unsupported resource duration')
            return effect('GainSun',Amount=amount(),Duration='Permanent'if duration=='permanent'else'EndOfTurn',ActivationTime='Immediate')
        raise PlanError('Unimplemented effect')

    def ability(self,data,faction):
        exact(data,{'trigger','target','selection','count','effects'},'ability')
        trigger=data.get('trigger');target=data.get('target');selection=data.get('selection','all')
        if not isinstance(trigger,str)or not isinstance(target,str)or trigger not in TRIGGERS or target not in TARGETS:raise PlanError('Unsupported trigger/target')
        if selection not in ('all','manual','random'):raise PlanError('Unsupported selection')
        count=0 if selection=='all'else number(data.get('count',1),'target count',1,5)
        if selection=='manual'and trigger!='play':raise PlanError('Manual choice currently restricted to play')
        effects=data.get('effects')
        if not isinstance(effects,list)or not 1<=len(effects)<=8:raise PlanError('An ability needs 1..8 effects')
        if any(not isinstance(e,dict)for e in effects):raise PlanError('Effects must be objects')
        native_effects=[self.effect(e)for e in effects]
        if target in ('own_open_lanes','self_lane')and any(e['type']!='summon'for e in effects):raise PlanError('Lane targets currently support summon only')
        if target.endswith('hero'):
            if any(e['type']in ('freeze','destroy','bounce','extra_attack','transform')for e in effects):raise PlanError('This action requires a fighter target')
            if any(e['type']=='buff'and e.get('attack',0)!=0 for e in effects):raise PlanError('Heroes do not have fighter attack')
            if any(e['type']=='set_stat'and e.get('stat')!='health'for e in effects):raise PlanError('Hero SetStat supports health only')
        # A bounce invalidates the old in-play query. Do not claim exact chaining.
        if any(e.get('type')=='bounce'for e in effects)and len(effects)>1:raise PlanError('Bounce plus another action needs a verified native chain')
        if any(e.get('type')in ('draw','conjure','gain_resource')for e in effects)and not target.endswith('hero'):raise PlanError('Player effect requires hero target')
        if any(e.get('type')=='summon'for e in effects)and target not in ('own_open_lanes','self_lane'):raise PlanError('Summon target must be a lane')
        if target=='event_target'and trigger not in ('own_fighter_played','other_own_fighter_played','enemy_fighter_played'):raise PlanError('Event target contract unavailable for this trigger')
        if trigger=='continuous'and any(e.get('type')!='buff'for e in effects):raise PlanError('Continuous v1 supports buff only')
        if trigger=='continuous'and any(e.get('duration','permanent')!='permanent'for e in effects):raise PlanError('Continuous buff must be permanent while its controller applies it')
        S=self.node('SelfQuery');cs=[self.node('EffectEntityGrouping',AbilityGroupId=0),self.node(TRIGGERS[trigger])]
        event_query=None
        if trigger=='play':event_query=S
        if trigger=='self_damaged':event_query=S
        if trigger=='self_deals_damage':cs.append(self.node('TriggerSourceFilter',Query=S))
        if trigger=='self_destroyed':event_query=self.all(S,self.node('WillTriggerOnDeathEffectsQuery'))
        if trigger in ('own_fighter_played','other_own_fighter_played','enemy_fighter_played'):
            fac=faction if trigger!='enemy_fighter_played'else('Zombies'if faction=='Plants'else'Plants')
            event_query=self.all(self.has(fac),self.node('FighterQuery'))
            if trigger=='other_own_fighter_played':event_query=self.all(event_query,self.notq(S))
        if trigger=='own_draw':event_query=self.query('own_hero',faction)
        if trigger in ('lane_combat_start','lane_combat_end'):event_query=self.node('SameLaneQuery')
        if event_query:cs.append(self.node('TriggerTargetFilter',Query=event_query))
        if trigger!='self_destroyed':
            guard=self.all(self.node('FighterQuery'),self.node('CompositeAnyQuery',queries=[self.node('WillTriggerEffectsQuery'),self.node('WillTriggerOnDeathEffectsQuery')]))
            if trigger=='continuous':guard=self.all(self.node('FighterQuery'),self.node('WillTriggerEffectsQuery'),self.node('IsAliveQuery'))
            cs.append(self.node('SelfEntityFilter',Query=guard))
        if trigger=='continuous':cs.append(self.node('ActiveTargets'))
        target_query=self.query(target,faction)
        if target=='own_open_lanes':
            teamup={self.by_guid[e['card_guid']]['fighter']and self.cards[str(e['card_guid'])]['isTeamup']for e in effects}
            if len(teamup)!=1:raise PlanError('Mixed summon placement requirements need separate abilities')
            target_query['$data']['IsForTeamupCard']=teamup.pop()
        ptf=self.node('PrimaryTargetFilter',Query=target_query,SelectionType=selection.title(),NumTargets=count,
            TargetScopeType='All',TargetScopeSortValue='None',TargetScopeSortMethod='None',
            AdditionalTargetType='None',AdditionalTargetQuery=None,OnlyApplyEffectsOnAdditionalTargets=False)
        cs.append(ptf)
        for e,native_effect in zip(effects,native_effects):
            if e.get('type')=='summon'and self.by_guid[e.get('card_guid',-1)]['faction']!=faction:raise PlanError('Cross-faction summon not enabled')
            if e.get('type')=='transform':cs.append(self.node('TransformWithCreationSource',SourceGuid=-1))
            cs.append(native_effect)
        names=[n['$type']for n in cs]
        if len(names)!=len(set(names)):raise PlanError('Duplicate native component type in one ability; no automatic split')
        return {'components':cs}

    def compile(self,plan):
        exact(plan,PLAN_FIELDS,'plan')
        if type(plan.get('schema_version'))is not int or plan['schema_version']!=1:raise PlanError('Unsupported plan schema')
        if plan.get('status')!='ready':raise PlanError('Plan not ready: '+str(plan.get('status'))+' '+str(plan.get('reason','')))
        guid=number(plan.get('base_guid'),'base_guid',1,2147483647)
        if guid not in self.by_guid or not self.by_guid[guid]['fighter']or not self.by_guid[guid]['usable']:raise PlanError('Base must be a usable native fighter')
        card=copy.deepcopy(self.cards[str(guid)]);body=card['entity']['components'];faction=card['faction']
        mode=plan.get('mode');abilities=plan.get('abilities',[])
        if mode not in ('keep','replace','append','copy_native'):raise PlanError('Unknown ability mode')
        if mode!='replace'and ('keywords'in plan or 'armor'in plan):raise PlanError('Keyword edits require replace mode; copy/keep preserve their exact native package')
        if not isinstance(abilities,list)or len(abilities)>8:raise PlanError('Invalid ability list')
        if mode in ('keep','copy_native')and abilities:raise PlanError('This mode does not accept ability edits')
        if mode=='copy_native':
            source=number(plan.get('source_guid'),'source_guid',1,2147483647)
            if source not in self.by_guid or self.by_guid[source]['faction']!=faction or not self.by_guid[source]['fighter']or not self.by_guid[source]['usable']:raise PlanError('Native-copy source must be same-faction usable fighter')
            body[:]=[n for n in body if short(n['$type'])in CORE_BODY]+copy.deepcopy([n for n in self.cards[str(source)]['entity']['components']if short(n['$type'])not in CORE_BODY])
            card['special_abilities']=copy.deepcopy(self.cards[str(source)]['special_abilities'])
            card['isAquatic']=self.cards[str(source)]['isAquatic'];card['isTeamup']=self.cards[str(source)]['isTeamup']
        elif mode in ('replace','append'):
            # Rewriting an exotic passive body requires copying a verified full
            # ability package. Do not silently preserve unknown old mechanics.
            allowed=CORE_BODY|set(KEYWORDS.values())|{'Armor','EffectEntitiesDescriptor','ShowTriggeredIcon'}
            if mode=='replace'and any(short(n['$type'])not in allowed for n in body):raise PlanError('Base has unsupported passive body; use native-copy or keep')
            if mode=='replace':
                body[:]=[n for n in body if short(n['$type'])not in ('EffectEntitiesDescriptor','ShowTriggeredIcon','GrantedTriggeredAbilities')]
                card['special_abilities']=[s for s in card['special_abilities']if s not in ('Unique','Ambush','AttackOverride','Overshoot','Repeater')]
            descriptor=component(card['entity'],'EffectEntitiesDescriptor',True)
            if descriptor is None:
                descriptor=self.node('EffectEntitiesDescriptor',entities=[]);body.append(descriptor)
            descriptor['$data']['entities'].extend(self.ability(a,faction)for a in abilities)
            if abilities:
                if 'Unique'not in card['special_abilities']:card['special_abilities'].append('Unique')
                old=component(card['entity'],'ShowTriggeredIcon',True)
                if old is None:body.append(self.node('ShowTriggeredIcon',abilities=[13]))
                elif 13 not in old['$data']['abilities']:old['$data']['abilities'].append(13)
        if 'source_guid'in plan and mode!='copy_native':raise PlanError('Unused source_guid')
        if 'keywords'in plan:
            words=plan['keywords']
            if not isinstance(words,list)or any(not isinstance(k,str)or k not in KEYWORDS for k in words)or len(words)!=len(set(words)):raise PlanError('Invalid keyword list')
            if mode=='copy_native':raise PlanError('Native-copy keyword package must remain intact')
            body[:]=[n for n in body if short(n['$type'])not in KEYWORDS.values()]
            card['special_abilities']=[s for s in card['special_abilities']if s not in set(KEYWORDS.values())|{'Repeater'}]
            for word in words:
                name=KEYWORDS[word]
                if word=='double_strike':
                    body.append(self.node(name,a=[{'g':562,'vt':0,'va':0}]))
                    card['special_abilities'].append('Repeater')
                    icon=component(card['entity'],'ShowTriggeredIcon',True)
                    if icon is None:body.append(self.node('ShowTriggeredIcon',abilities=[11]))
                    elif 11 not in icon['$data']['abilities']:icon['$data']['abilities'].append(11)
                else:
                    body.append(self.node(name))
                    if word not in ('aquatic','teamup','gravestone'):card['special_abilities'].append(name)
            card['isAquatic']='aquatic'in words;card['isTeamup']='teamup'in words
        if 'armor'in plan:
            armor=number(plan['armor'],'armor',0,20);body[:]=[n for n in body if short(n['$type'])!='Armor']
            card['special_abilities']=[s for s in card['special_abilities']if s!='Armor']
            if armor:body.append(self.node('Armor',ArmorAmount={'BaseValue':armor}));card['special_abilities'].append('Armor')
        stats=plan.get('stats',{});exact(stats,{'cost','attack','health'},'stats')
        for field,typ,native,display in [('cost','SunCost','SunCostValue','displaySunCost'),('attack','Attack','AttackValue','displayAttack'),('health','Health','MaxHealth','displayHealth')]:
            if field in stats:
                value=number(stats[field],field,1 if field=='health'else 0,100)
                component(card['entity'],typ)['$data'][native]['BaseValue']=value;card[display]=value
        self.validate_card(card,guid)
        return card

    def validate_card(self,card,guid):
        if component(card['entity'],'Card')['$data']['Guid']!=guid:raise PlanError('Card identity mismatch')
        for n in walk(card):
            if 'components'in n:
                kinds=[c['$type']for c in n['components']]
                if len(kinds)!=len(set(kinds)):raise PlanError('Duplicate entity component')
            if '$type'not in n:continue
            typ=n['$type'];data=n['$data']
            if typ not in self.fields or not set(data)<=self.fields[typ]:raise PlanError('Unknown native type/fields')
            for key,value in data.items():
                if isinstance(value,str)and self.strings[typ,key]and value not in self.strings[typ,key]:
                    raise PlanError('Unobserved native enum/type '+short(typ)+'.'+key)
            if short(typ)=='CreateCardEffectDescriptor'and str(data['CardGuid'])not in self.cards:raise PlanError('Unknown summon reference')
            if short(typ)=='CardGuidQuery'and str(data['Guid'])not in self.cards:raise PlanError('Unknown query reference')
            if short(typ)=='GrantTriggeredAbilityEffectDescriptor'and str(data['AbilityGuid'])not in self.cards:raise PlanError('Unknown granted ability')
            if short(typ)=='GrantedTriggeredAbilities'and any(str(a['g'])not in self.cards for a in data['a']):raise PlanError('Unknown passive ability')
        for typ,base,display in [('SunCost','SunCostValue','displaySunCost'),('Attack','AttackValue','displayAttack'),('Health','MaxHealth','displayHealth')]:
            if component(card['entity'],typ)['$data'][base]['BaseValue']!=card[display]:raise PlanError('Display/stat mismatch')
        for flag,name in [('isAquatic','Aquatic'),('isTeamup','Teamup')]:
            if bool(component(card['entity'],name,True))!=card[flag]:raise PlanError('Keyword boolean mismatch')

    def describe(self,plan,compiled_card=None):
        if plan['mode']=='keep':return self.cn.get(self.cards[str(plan['base_guid'])]['prefabName']+'_longDesc','')
        if plan['mode']=='copy_native':return self.cn.get(self.cards[str(plan['source_guid'])]['prefabName']+'_longDesc','')
        targets={'self':'这张牌','event_target':'刚打出的单位','own_hero':'你的英雄','enemy_hero':'对方英雄','plant_hero':'植物英雄','zombie_hero':'僵尸英雄','own_fighters':'所有友方单位','enemy_fighters':'所有敌方单位','all_fighters':'所有植物和僵尸','other_own_fighters':'其他所有友方单位','lane_enemy_fighters':'本线的所有敌方单位','adjacent_enemy_fighters':'相邻路线的所有敌方单位','self_and_adjacent_own':'自己及相邻路线的友方单位','own_open_lanes':'可用的友方路线','self_lane':'自己的路线'}
        triggers={'play':'打出','turn_start':'回合开始','self_damaged':'受到伤害时','self_deals_damage':'造成伤害后','self_destroyed':'被消灭时','own_fighter_played':'打出友方单位后','other_own_fighter_played':'打出其他友方单位后','enemy_fighter_played':'对方打出单位后','own_draw':'你抽牌后','lane_combat_start':'本线战斗开始前','lane_combat_end':'本线战斗结束后','continuous':'在场时'}
        words=plan.get('keywords',[]);armor=plan.get('armor',0)
        if plan['mode']=='replace':
            card=compiled_card or self.compile(plan)
            words=[k for k,v in KEYWORDS.items()if component(card['entity'],v,True)]
            armor_component=component(card['entity'],'Armor',True)
            armor=armor_component['$data']['ArmorAmount']['BaseValue']if armor_component else 0
        lines=[KW_TEXT[k]for k in words]
        if armor:lines.append('[armored='+str(armor)+']')
        for ability in plan.get('abilities',[]):
            target=targets[ability['target']];selection=ability.get('selection','all')
            if selection=='manual':target='你选择的'+target.replace('所有','一名')
            if selection=='random':target='随机选择的'+target.replace('所有','一名')
            actions=[]
            for e in ability['effects']:
                kind=e['type'];amount=e.get('amount')
                if kind=='damage':s=f'对{target}造成{amount}点伤害'
                elif kind=='heal':s=f'为{target}恢复{amount}生命'
                elif kind=='draw':s=f'{target}抽{amount}张牌'
                elif kind=='buff':s=f'{target}获得{e.get("attack",0):+d}/{e.get("health",0):+d}'+('，持续到本回合结束'if e.get('duration')=='end_of_turn'else'')
                elif kind in ('freeze','destroy','bounce','extra_attack'):s={'freeze':'冻结','destroy':'消灭','bounce':'弹射','extra_attack':'发动一次额外攻击：'}[kind]+target
                elif kind in ('summon','conjure','transform'):
                    name=self.by_guid[e['card_guid']]['name'];s={'summon':f'在{target}召唤{name}','conjure':f'将{name}加入{target}的手牌','transform':f'将{target}变成{name}'}[kind]
                elif kind=='set_stat':s=f'将{target}的'+{'attack':'力量','health':'生命','cost':'费用'}[e['stat']]+f'设为{e["value"]}'
                else:s=f'{target}获得{amount}点资源'
                actions.append(s)
            lines.append(triggers[ability['trigger']]+'：'+'；'.join(actions)+'。')
        result='\\n'.join(lines)
        if plan['mode']=='append':
            old=self.cn.get(self.cards[str(plan['base_guid'])]['prefabName']+'_longDesc','')
            if old:result=old+('\\n'+result if result else'')
        return result

def patch_csv(source,replacements):
    lines=source.splitlines(keepends=True);out=[];seen=set();previous=0
    reader=csv.reader(io.StringIO(source,newline=''))
    for row in reader:
        end=reader.line_num;key=row[0]if row else''
        if key in replacements:
            if key in seen:raise PlanError('Duplicate localization key')
            buf=io.StringIO(newline='');csv.writer(buf,lineterminator='\n').writerow([key,replacements[key]])
            out.append(buf.getvalue());seen.add(key)
        else:out.extend(lines[previous:end])
        previous=end
    if seen!=set(replacements):raise PlanError('Missing localization key')
    result=''.join(out)
    unchanged=lambda value:[r for r in csv.reader(io.StringIO(value,newline=''))if not r or r[0]not in replacements]
    if unchanged(source)!=unchanged(result):raise PlanError('Unrelated localization changed')
    return result

def pack_bundle(source,target,name,payload):
    import UnityPy
    env=UnityPy.load(source.read_bytes());found=[]
    before={(str(o.assets_file.name),o.path_id):o.get_raw_data()for o in env.objects}
    for obj in env.objects:
        if obj.type.name=='TextAsset':
            tree=obj.read_typetree()
            if tree['m_Name']==name:found.append((obj,tree))
    if len(found)!=1:raise PlanError('Unique TextAsset missing')
    obj,tree=found[0]
    old_value=tree['m_Script'];old_text=old_value.decode('utf-8')if isinstance(old_value,bytes)else old_value
    if old_text==payload:
        target.write_bytes(source.read_bytes())
        if bundle_text(target,name)!=payload:raise PlanError('Unchanged bundle readback mismatch')
        return {'input_sha256':sha(source),'output_sha256':sha(target),'changed_path_id':None,'object_changes':0}
    tree['m_Script']=payload.encode('utf-8')if isinstance(tree['m_Script'],bytes)else payload
    obj.save_typetree(tree);target.write_bytes(env.file.save(packer='lz4'))
    check=UnityPy.load(target.read_bytes());after={(str(o.assets_file.name),o.path_id):o.get_raw_data()for o in check.objects}
    changed=[key for key in before if before[key]!=after.get(key)]
    if before.keys()!=after.keys()or changed!=[(str(obj.assets_file.name),obj.path_id)]:raise PlanError('Unexpected bundle object change')
    if bundle_text(target,name)!=payload:raise PlanError('Bundle readback mismatch')
    return {'input_sha256':sha(source),'output_sha256':sha(target),'changed_path_id':obj.path_id,'object_changes':1}

def write_card(catalog,plan,output,input_dir=None,pack=False):
    output=Path(output)
    if output.exists():raise PlanError('Output already exists; choose a new directory')
    card=catalog.compile(plan);guid=str(plan['base_guid'])
    cards=copy.deepcopy(catalog.cards);cards[guid]=card
    prefab=card['prefabName'];description=catalog.describe(plan,card)
    replacements={prefab+suffix:description for suffix in ('_longDesc','_shortDesc')}
    if 'name'in plan:
        if not isinstance(plan['name'],str)or not 1<=len(plan['name'])<=80:raise PlanError('Invalid display name')
        replacements[prefab+'_name']=plan['name']
    cn=patch_csv(catalog.cn_text,replacements)
    changed=[g for g in cards if cards[g]!=catalog.cards[g]]
    if set(changed)-{guid}:raise PlanError('Unrelated card changed')
    output.mkdir(parents=True)
    save_json(output/'plan.json',plan);save_json(output/'card.patch.json',{guid:card})
    payload=json.dumps(cards,ensure_ascii=False,separators=(',',':'))
    (output/'cards.after.json').write_text(payload,encoding='utf-8')
    (output/'cn.after.csv').write_text(cn,encoding='utf-8',newline='')
    report={'status':'PASS','kind':'native-only-offline-compilation','base_guid':int(guid),
        'changed_guids':list(map(int,changed)),'input_fingerprint':catalog.fingerprint,
        'description':description,'localization_keys':list(replacements),
        'native_component_sources':{name:sorted(catalog.origins[name])[:5]for name in sorted({short(n['$type'])for n in walk(card)if '$type'in n})},
        'private_extensions_used':False,'runtime_verification':'NOT TESTED','bundles':{}}
    if plan['mode']=='copy_native':
        source_guid=plan['source_guid']
        report['native_copy']={'source_guid':source_guid,'reference_policy':'preserve_literal_native_references',
            'matching_source_guid_reference_count':sum(1 for n in walk([c for c in card['entity']['components']if short(c['$type'])not in CORE_BODY])for key,value in n.items()if key in ('Guid','CardGuid','SourceGuid')and value==source_guid),
            'proof_scope':'exact native ability components; implicit same-name behavior and animations require gameplay verification'}
    if pack:
        if input_dir is None:raise PlanError('Packing requires original input directory')
        input_dir=Path(input_dir)
        for bundle,asset,value in [('card_data_1','cards',payload),('cn_8','LocalizedStrings',cn)]:
            if sha(input_dir/bundle)!=catalog.fingerprint[bundle]:raise PlanError('Input changed during build')
            report['bundles'][bundle]=pack_bundle(input_dir/bundle,output/bundle,asset,value)
    save_json(output/'build-report.json',report)
    return report
