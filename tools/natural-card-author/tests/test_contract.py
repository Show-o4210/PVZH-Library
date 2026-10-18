"""Run with PVZH_NATIVE_INPUT pointing to the supported user's original bundles."""
import copy
import json
import os
import sys
import uuid
import shutil
from contextlib import contextmanager
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import NativeCatalog,PlanError,component,write_card,pack_bundle,bundle_text
from provider import DeepSeek,ProviderError
from planner import generate,validate_envelope

@unittest.skipUnless(os.environ.get('PVZH_NATIVE_INPUT'),'Set PVZH_NATIVE_INPUT to original bundle directory')
class NativeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(os.environ['PVZH_NATIVE_INPUT'])
        cls.catalog=NativeCatalog.from_directory(cls.source)
        cls.temp_root=Path(__file__).resolve().parents[1]/'runs'
        cls.temp_root.mkdir(exist_ok=True)
    @contextmanager
    def temporary(self):
        # Python 3.14's Windows 0700 tempfile ACL can deny restricted tokens.
        # These non-secret fixtures use ordinary project-directory inheritance.
        root=self.temp_root.resolve();folder=root/('test-'+uuid.uuid4().hex)
        folder.mkdir()
        try:yield folder
        finally:
            resolved=folder.resolve()
            if not resolved.is_relative_to(root)or resolved==root:raise RuntimeError('Unsafe test cleanup path')
            shutil.rmtree(resolved)
    def base(self):return {'schema_version':1,'status':'ready','base_guid':326,'mode':'replace','abilities':[]}
    def rejects(self,plan):
        with self.assertRaises(PlanError):self.catalog.compile(plan)
    def ability(self,**kw):
        return {'trigger':'play','target':'enemy_fighters','effects':[{'type':'damage','amount':2}]}|kw
    def test_no_private_input_rules(self):
        cards=copy.deepcopy(self.catalog.cards)
        cards['326']['entity']['components'].append(self.catalog.node('GrantAbilityEffectDescriptor',GrantableAbilityType='1015'))
        with self.assertRaises(PlanError):NativeCatalog(cards,self.catalog.cn_text)
    def test_unknown_code_field_rejected(self):self.rejects(self.base()|{'python_code':'print(1)'})
    def test_unknown_trigger_rejected(self):self.rejects(self.base()|{'abilities':[self.ability(trigger='after_attack')]})
    def test_manual_observer_rejected(self):self.rejects(self.base()|{'abilities':[self.ability(trigger='self_damaged',selection='manual')]})
    def test_duplicate_components_rejected(self):
        self.rejects(self.base()|{'abilities':[self.ability(effects=[{'type':'set_stat','stat':'attack','value':0},{'type':'set_stat','stat':'health','value':0}])]})
    def test_bounce_chain_rejected(self):self.rejects(self.base()|{'abilities':[self.ability(effects=[{'type':'bounce'},{'type':'damage','amount':2}])]})
    def test_unknown_keyword_rejected(self):self.rejects(self.base()|{'keywords':['god_mode']})
    def test_cross_faction_copy_rejected(self):self.rejects(self.base()|{'mode':'copy_native','source_guid':491})
    def test_noncollectible_copy_source_rejected(self):
        original=self.catalog.by_guid[597]
        self.catalog.by_guid[597]=original|{'usable':False}
        try:self.rejects(self.base()|{'mode':'copy_native','source_guid':597})
        finally:self.catalog.by_guid[597]=original
    def test_cross_faction_summon_rejected(self):self.rejects(self.base()|{'abilities':[self.ability(target='own_open_lanes',effects=[{'type':'summon','card_guid':350}])]})
    def test_player_effect_cannot_target_fighter(self):self.rejects(self.base()|{'abilities':[self.ability(target='self',effects=[{'type':'draw','amount':1}])]})
    def test_continuous_damage_rejected(self):self.rejects(self.base()|{'abilities':[self.ability(trigger='continuous')]})
    def test_event_target_contract(self):self.rejects(self.base()|{'abilities':[self.ability(trigger='turn_start',target='event_target')]})
    def test_bool_stat_is_not_integer(self):self.rejects(self.base()|{'stats':{'attack':True}})
    def test_copy_skill_package_without_source_mutation(self):
        before=copy.deepcopy(self.catalog.cards['597'])
        card=self.catalog.compile(self.base()|{'mode':'copy_native','source_guid':597})
        self.assertEqual(component(card['entity'],'EffectEntitiesDescriptor'),component(before['entity'],'EffectEntitiesDescriptor'))
        self.assertEqual(before,self.catalog.cards['597'])
        self.assertEqual(card['displayAttack'],1)
    def test_keyword_display_and_internal_flags(self):
        card=self.catalog.compile(self.base()|{'keywords':['aquatic','teamup','double_strike'],'armor':2})
        self.assertTrue(card['isAquatic']and card['isTeamup'])
        self.assertEqual(component(card['entity'],'Armor')['$data']['ArmorAmount']['BaseValue'],2)
        self.assertIn('Repeater',card['special_abilities'])
        self.assertIn(11,component(card['entity'],'ShowTriggeredIcon')['$data']['abilities'])
    def test_malformed_json_shapes_are_validation_errors(self):
        for edit in ({'schema_version':True},{'keywords':[{}]},{'abilities':[self.ability(trigger={})]},
                     {'abilities':[self.ability(effects=[3])]}, {'abilities':[self.ability(effects=[{'type':{}}])]}):
            self.rejects(self.base()|edit)
    def test_summoned_teamup_uses_teamup_open_lanes(self):
        card=self.catalog.compile(self.base()|{'abilities':[self.ability(target='own_open_lanes',effects=[{'type':'summon','card_guid':77}])]})
        entity=component(card['entity'],'EffectEntitiesDescriptor')['$data']['entities'][0]
        self.assertTrue(component(entity,'PrimaryTargetFilter')['$data']['Query']['$data']['IsForTeamupCard'])
    def test_hero_cannot_be_bounced(self):self.rejects(self.base()|{'abilities':[self.ability(target='enemy_hero',effects=[{'type':'bounce'}])]})
    def test_planner_repairs_only_after_real_compiler_feedback(self):
        good=self.base()|{'case_id':'test'};bad=good|{'python_code':'not allowed'}
        class Client:
            calls=0
            def complete(self,system,user,max_tokens):
                self.calls+=1
                if self.calls==2:self.saw_feedback='unknown fields'in user
                return {'plans':[bad if self.calls==1 else good]},{'usage':{}}
        client=Client();result,attempts=generate(self.catalog,client,{'case_id':'test','request':'小豆丁替换旧技能，不增加新技能。'})
        self.assertEqual(result,good);self.assertEqual(len(attempts),2);self.assertTrue(client.saw_feedback)
    def test_planner_rejects_after_two_invalid_attempts(self):
        class Client:
            calls=0
            def complete(self,*args):self.calls+=1;return {'plans':[]},{}
        client=Client()
        with self.assertRaises(PlanError):generate(self.catalog,client,{'case_id':'test','request':'小豆丁改属性'})
        self.assertEqual(client.calls,2)
    def test_envelope_rejects_non_object_plans(self):
        with self.assertRaises(ValueError):validate_envelope({'plans':[None]},[{'case_id':'test'}])
    def test_output_no_overwrite(self):
        with self.temporary()as folder:
            with self.assertRaises(PlanError):write_card(self.catalog,self.base(),Path(folder))
    def test_nonready_writes_nothing(self):
        with self.temporary()as folder:
            out=Path(folder)/'rejected'
            with self.assertRaises(PlanError):write_card(self.catalog,self.base()|{'status':'unsupported'},out)
            self.assertFalse(out.exists())
    def test_unchanged_textasset_keeps_exact_bundle(self):
        with self.temporary()as folder:
            original=self.source/'cn_8';target=Path(folder)/'cn_8'
            report=pack_bundle(original,target,'LocalizedStrings',bundle_text(original,'LocalizedStrings'))
            self.assertEqual(report['object_changes'],0)
            self.assertEqual(original.read_bytes(),target.read_bytes())
    def test_unknown_baseline_is_not_silently_trusted(self):
        with self.temporary()as folder:
            changed=copy.deepcopy(self.catalog.cards)
            changed['326']['displayAttack']=7
            component(changed['326']['entity'],'Attack')['$data']['AttackValue']['BaseValue']=7
            pack_bundle(self.source/'card_data_1',folder/'card_data_1','cards',json.dumps(changed,ensure_ascii=False))
            (folder/'cn_8').write_bytes((self.source/'cn_8').read_bytes())
            with self.assertRaisesRegex(PlanError,'Unknown native baseline'):NativeCatalog.from_directory(folder)

class ProviderContract(unittest.TestCase):
    def test_http_failure_cannot_echo_server_body_or_credential(self):
        client=DeepSeek('test-credential-never-write')
        error=urllib.error.HTTPError('https://api.deepseek.com/models',401,'bad',{},None)
        with patch('urllib.request.urlopen',side_effect=error):
            with self.assertRaises(ProviderError)as caught:client.probe()
        self.assertEqual(str(caught.exception),'DeepSeek HTTP 401')

if __name__=='__main__':unittest.main()
