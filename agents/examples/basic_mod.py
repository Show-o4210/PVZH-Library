"""Source-preserving, offline example: one fighter + zombie mission 200 + CN.

Requires UnityPy; does not deploy to a device or depend on mod1/mod2 scripts.
This example is intentionally limited to the exact input revision in agents/README.md.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import UnityPy

HASHES = {
    'card_data_1': 'e2579da5636125f82b86a85fba829459810b4ca41b1980528771b80da9c80201',
    'data_assets_29': '37fd5f5af67dda86664b76e9bfefe1878b281cf8a1af05afec7a4282bf7b3007',
    'cn_8': '950fc91396daf74f0a8e93b78d57662b8580818e8ffa38f5f74838a7ceed2bd7',
}
LEVEL = 'PVE_Soft_Node_Zombie_200'
SUFFIX = ', EngineLib, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null'

def typename(name):
    return 'PvZCards.Engine.Components.' + name + SUFFIX

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def component(entity, name):
    matches = [n for n in entity['components'] if n['$type'] == typename(name)]
    if len(matches) != 1:
        raise ValueError((name, len(matches)))
    return matches[0]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def asset(env, name):
    matches = [(obj, obj.read_typetree()) for obj in env.objects if obj.type.name == 'TextAsset']
    matches = [(obj, tree) for obj, tree in matches if tree['m_Name'] == name]
    if len(matches) != 1:
        raise ValueError(('TextAsset name must match exactly once', name, len(matches)))
    return matches[0]

def text(tree):
    value = tree['m_Script']
    return value.decode('utf-8') if isinstance(value, bytes) else value

def schema_check(before, after):
    schemas = {}
    type_fields = set()
    for n in walk(before):
        if '$type' in n:
            schemas.setdefault(n['$type'], set()).update(n['$data'])
            for key, value in n['$data'].items():
                if isinstance(value, str) and value.startswith('PvZCards.Engine.'):
                    type_fields.add((n['$type'], key))
    for n in walk(after):
        if '$type' in n:
            assert n['$type'] in schemas, n['$type']
            assert set(n['$data']) <= schemas[n['$type']], n
            for key, value in n['$data'].items():
                if (n['$type'], key) in type_fields and value is not None:
                    assert isinstance(value, str) and value.startswith('PvZCards.Engine.') and ', EngineLib,' in value

def edit_cards(before, guid):
    after = copy.deepcopy(before)
    card = after[guid]
    assert guid != '409' and card['isFighter'] and card['prefabName']
    assert card['faction'] in ('Plants', 'Zombies')
    for name, field, display, value in [('SunCost', 'SunCostValue', 'displaySunCost', 2),
                                        ('Attack', 'AttackValue', 'displayAttack', 3),
                                        ('Health', 'MaxHealth', 'displayHealth', 4)]:
        component(card['entity'], name)['$data'][field]['BaseValue'] = value
        card[display] = value
    source = component(before['409']['entity'], 'EffectEntitiesDescriptor')
    added = copy.deepcopy(source['$data']['entities'][0])
    group = max((n['AbilityGroupId'] for n in walk(card) if 'AbilityGroupId' in n), default=-1) + 1
    for n in walk(added):
        if 'AbilityGroupId' in n:
            n['AbilityGroupId'] = group
        if card['faction'] == 'Zombies' and n.get('ComponentType') == typename('Zombies'):
            n['ComponentType'] = typename('Plants')
    matches = [n for n in card['entity']['components'] if n['$type'] == typename('EffectEntitiesDescriptor')]
    assert len(matches) <= 1
    if not matches:
        descriptor = copy.deepcopy(source)
        descriptor['$data']['entities'] = []
        card['entity']['components'].append(descriptor)
    else:
        descriptor = matches[0]
    old_effects = copy.deepcopy(descriptor['$data']['entities'])
    descriptor['$data']['entities'].append(added)
    assert descriptor['$data']['entities'][:-1] == old_effects
    assert {g for g in before if before[g] != after[g]} == {guid}
    assert before.keys() == after.keys()
    schema_check(before, after)
    return after

def edit_level(before, title_key):
    after = copy.deepcopy(before)
    for side in ('OpponentConfig', 'PlayerConfig'):
        after[side]['Parameters']['InitialHealth'] = 30
    lanes = after['BoardConfig']['LaneEntries']
    assert len(lanes) == 5
    for lane, lane_type in zip(lanes, [0, 1, 1, 1, 2], strict=True):
        lane['LaneType'] = lane_type
    event = after['GameEvents'][0]
    assert event['$type'] == 'PvZCards.Core.Data.MessageEventConfig'
    event['Narrator'] = 2
    event['TextKey'] = title_key
    restored = copy.deepcopy(after)
    for side in ('OpponentConfig', 'PlayerConfig'):
        restored[side]['Parameters']['InitialHealth'] = before[side]['Parameters']['InitialHealth']
    for old, lane in zip(before['BoardConfig']['LaneEntries'], restored['BoardConfig']['LaneEntries'], strict=True):
        lane['LaneType'] = old['LaneType']
    restored['GameEvents'][0] = before['GameEvents'][0]
    assert restored == before
    return after

def edit_csv(source, replacements):
    lines = source.splitlines(keepends=True)
    result, seen, previous = [], set(), 0
    for row in (reader := csv.reader(io.StringIO(source, newline=''))):
        end = reader.line_num
        key = row[0] if row else ''
        if key in replacements:
            assert len(row) == 2 and key not in seen
            buffer = io.StringIO(newline='')
            csv.writer(buffer, lineterminator='\n').writerow([key, replacements[key]])
            result.append(buffer.getvalue())
            seen.add(key)
        else:
            result.extend(lines[previous:end])
        previous = end
    for key, value in replacements.items():
        if key not in seen:
            if result and not result[-1].endswith(('\n', '\r')):
                result.append('\n')
            buffer = io.StringIO(newline='')
            csv.writer(buffer, lineterminator='\n').writerow([key, value])
            result.append(buffer.getvalue())
    output = ''.join(result)
    old_rows = list(csv.reader(io.StringIO(source)))
    new_rows = list(csv.reader(io.StringIO(output)))
    assert [r for r in old_rows if not r or r[0] not in replacements] == [r for r in new_rows if not r or r[0] not in replacements]
    counts = Counter(r[0] for r in new_rows if r)
    assert all(counts[key] == 1 for key in replacements)
    assert all(r[1] == replacements[r[0]] for r in new_rows if r and r[0] in replacements)
    return output

def pack(source, target, name, payload):
    env = UnityPy.load(str(source))
    obj, tree = asset(env, name)
    tree['m_Script'] = payload.encode('utf-8') if isinstance(tree['m_Script'], bytes) else payload
    obj.save_typetree(tree)
    target.write_bytes(env.file.save(packer='lz4'))
    output = UnityPy.load(str(target))
    assert text(asset(output, name)[1]) == payload
    original = UnityPy.load(str(source))
    before = {(str(o.assets_file.name), o.path_id): o.get_raw_data() for o in original.objects}
    after = {(str(o.assets_file.name), o.path_id): o.get_raw_data() for o in output.objects}
    assert before.keys() == after.keys()
    changed = [key for key in before if before[key] != after[key]]
    assert changed == [(str(obj.assets_file.name), obj.path_id)], changed
    return {'input_sha256': sha(source), 'output_sha256': sha(target),
            'changed_object': {'serialized_file': changed[0][0], 'path_id': changed[0][1], 'name': name}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='Directory containing the three verified clean inputs.')
    parser.add_argument('--output', required=True, type=Path, help='New output directory; existing directories are never overwritten.')
    parser.add_argument('--guid', default='326', help='Collectible fighter to change; default Weenie Beanie326. 409 is excluded.')
    args = parser.parse_args()
    source, output = args.input.resolve(), args.output.resolve()
    if output.exists() or source == output:
        raise ValueError('Choose a new output directory; existing work will not be overwritten.')
    for name, expected in HASHES.items():
        if sha(source/name) != expected:
            raise ValueError(('Input revision differs: inspect it before adapting this example', name))
    load = lambda bundle, name: text(asset(UnityPy.load(str(source/bundle)), name)[1])
    old_cards = json.loads(load('card_data_1', 'cards'))
    cards = edit_cards(old_cards, args.guid)
    title_key = 'Node_' + LEVEL + ':LibraryExample_Title'
    level = edit_level(json.loads(load('data_assets_29', LEVEL)), title_key)
    cn = load('cn_8', 'LocalizedStrings')
    rows = dict(r for r in csv.reader(io.StringIO(cn)) if len(r) == 2)
    prefab = cards[args.guid]['prefabName']
    enemy = '僵尸' if cards[args.guid]['faction'] == 'Plants' else '植物'
    addition = '打出时：冻结相邻路线上的所有' + enemy + '。'
    replacements = {title_key: '本博士的修改示例！双方30生命，路线为高、平、平、平、水。'}
    for suffix in ('_shortDesc', '_longDesc'):
        key = prefab + suffix
        assert key in rows, key
        replacements[key] = rows[key] + ('\\n' if rows[key] else '') + addition
    payloads = {'card_data_1': ('cards', json.dumps(cards, ensure_ascii=False, separators=(',', ':'))),
                'data_assets_29': (LEVEL, json.dumps(level, ensure_ascii=False, separators=(',', ':'))),
                'cn_8': ('LocalizedStrings', edit_csv(cn, replacements))}
    output.mkdir(parents=True)
    files = {bundle: pack(source/bundle, output/bundle, name, payload) for bundle, (name, payload) in payloads.items()}
    assert all(sha(source/name) == expected for name, expected in HASHES.items())
    report = {'unitypy': UnityPy.__version__, 'changed_card': args.guid, 'faction': cards[args.guid]['faction'],
              'stats': [2, 3, 4], 'level': LEVEL, 'hero_health': 30, 'lane_types': [0, 1, 1, 1, 2],
              'localization_keys': list(replacements), 'files': files, 'static_verification': 'PASS',
              'runtime_verification': 'NOT TESTED; this example never deploys or launches the game.'}
    (output/'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PASS: fighter {args.guid} ({cards[args.guid]["faction"]}), mission 200 and CN; output: {output}')

if __name__ == '__main__':
    main()
