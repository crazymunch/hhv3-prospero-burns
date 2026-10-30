"""Apply the Prospero Burns campaign additions to the HH3 data files.

Idempotent: every object this script adds carries the comment TAG, and is
removed before being re-added, so it can be re-run safely after syncing the
fork with upstream (BSData/horus-heresy-3rd-edition).

Run from the repo root:  python3 tools/prospero_burns.py
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nrjson  # noqa: E402

TAG = 'Prospero Burns campaign'
random.seed(1729)  # stable IDs between runs


def nid():
    return '-'.join(''.join(random.choice('0123456789abcdef') for _ in range(4)) for _ in range(4))


# ---- shared IDs from the game system / catalogues ---------------------------
PTS = '9893-c379-920b-8982'
COSTS0 = [
    {'name': 'Point(s)', 'typeId': PTS, 'value': 0},
    {'name': 'Reaction Point(s)', 'typeId': 'c9ba-097e-c47f-ecc2', 'value': 0},
]
CAT_ARMY_CONFIG = 'abfa-86ab-1726-077a'
CAT_ARMOUR = '643a-1012-bd51-6537'
CAT_FORTIFICATION = '7e2f-62cf-4e42-9e13'
CAT_ELITES = '5d5e-958f-e388-50b5'
SPIREGUARD_DESIGNATION = '2d16-3107-80e2-93c6'
WARHOUND_UNIT = 'de13-dda8-5d1a-89d0'


def load(f):
    return json.load(open(f, encoding='utf-8'))


def save(f, data):
    nrjson.dump_file(f, data)


def strip_tagged(lst):
    return [x for x in lst if x.get('comment') != TAG]


def rule(name, text):
    return {'name': name, 'id': nid(), 'hidden': False, 'description': text}


def maxc(v, scope='parent', **kw):
    c = {'id': nid(), 'field': 'selections', 'scope': scope, 'shared': True, 'type': 'max', 'value': v}
    c.update(kw)
    return c


def cat_count_error(cat_id, op, value, msg):
    return {
        'field': 'error', 'type': 'add', 'value': msg,
        'conditions': [{
            'childId': cat_id, 'field': 'selections', 'scope': 'force',
            'includeChildForces': True, 'includeChildSelections': True,
            'shared': True, 'type': op, 'value': value,
        }],
    }


# ---- Campaign Doctrines -----------------------------------------------------
DOCTRINES = {
    'Thousand Sons.json': dict(
        name='Campaign Doctrine: The Axis of Dissolution',
        fluff='Named for an alchemical formula, the Axis was a battle-configuration that let the enemy impale itself on the Legion\'s lines, then bled it white as it tried to withdraw.',
        effects=[
            ('The Alembic of Adamant', 'Models with the Thousand Sons Trait that are within 6" of an Objective Marker automatically pass Cool Checks made due to the Pinning (X) Special Rule and Leadership Checks made due to Panic.'),
            ('The Caustic of Grace', 'When a Unit with the Thousand Sons Trait makes an Overwatch Reaction, add +1 to its Hit Tests for that Reaction.'),
            ('The Transition of Vitriol', 'Models with the Thousand Sons Trait may re-roll failed Hit Tests and Wound Tests against enemy Units with the Routed Status.'),
        ],
        limits='Every Unit with the Troops Battlefield Role in the Primary Detachment must include the maximum number of Models its profile allows. The Primary Detachment may not include more Units with the Armour Battlefield Role than Units with the Infantry Type. (Not checked automatically - check by hand.)',
        errors=[],
    ),
    'Space Wolves.json': dict(
        name='Campaign Doctrine: The Pale Hunters',
        fluff='The Wolves hunt as their namesakes do: circling, harrying and wearing the prey down until it can no longer run.',
        effects=[
            ('The Circling Wolves', 'Add +1 to Reserves Tests made for Units in the Primary Detachment.'),
            ('Bleed and Harry', 'In the Resolution Sub-Phase, a Unit with the Space Wolves Trait and the Infantry Type, but without the Heavy Sub-Type, may choose to Disengage whatever the result of the Combat.'),
            ('The Fury of the Pack', 'When a Unit with the Space Wolves Trait makes a successful Charge against an enemy Unit that is already Locked in Combat, its Models gain +1 Attacks until the end of that Assault Phase.'),
        ],
        limits='The Primary Detachment may not include Fortifications, or any Model or Unit that may only enter play by Deep Strike from a drop pod or Dreadclaw. The Primary Detachment may include no more than one Unit with the Armour Battlefield Role. (Fortifications and Armour are checked automatically; drop pods/Dreadclaws by hand.)',
        errors=[
            (CAT_FORTIFICATION, 'atLeast', 1, 'The Pale Hunters: no Fortifications allowed'),
            (CAT_ARMOUR, 'greaterThan', 1, 'The Pale Hunters: no more than one Armour Unit allowed'),
        ],
    ),
}


def doctrine_entry(d):
    rules = [rule('Campaign Doctrine', d['fluff'] + ' A player may choose one Campaign Doctrine for their army in addition to its Rite of War (Prospero Burns campaign games only).')]
    rules += [rule(n, t) for n, t in d['effects']]
    rules.append(rule('Limitations', d['limits']))
    return {
        'name': d['name'], 'id': nid(), 'comment': TAG, 'hidden': False, 'import': True, 'type': 'upgrade',
        'constraints': [maxc(1, 'roster', includeChildSelections=True, includeChildForces=True)],
        'costs': COSTS0,
        'rules': rules,
        'modifiers': [cat_count_error(*e) for e in d['errors']],
    }


def apply_doctrine(fname, d):
    data = load(fname)
    c = data['catalogue']
    c['sharedSelectionEntries'] = strip_tagged(c['sharedSelectionEntries'])
    c['entryLinks'] = strip_tagged(c['entryLinks'])
    e = doctrine_entry(d)
    c['sharedSelectionEntries'].append(e)
    c['entryLinks'].append({
        'name': d['name'], 'id': nid(), 'comment': TAG, 'hidden': False, 'import': True,
        'targetId': e['id'], 'type': 'selectionEntry',
        'categoryLinks': [{'name': 'Army Configuration', 'id': nid(), 'primary': True, 'targetId': CAT_ARMY_CONFIG}],
    })
    save(fname, data)


# ---- Venator Ignitum (Warhound upgrade) ------------------------------------
def apply_venator():
    fname = 'Legio Titanicus.json'
    data = load(fname)
    c = data['catalogue']
    unit = next(s for s in c['sharedSelectionEntries'] if s['id'] == WARHOUND_UNIT)
    unit['selectionEntries'] = strip_tagged(unit.get('selectionEntries', []))
    unit['selectionEntries'].append({
        'name': 'Venator Ignitum (Prospero Burns)', 'id': nid(), 'comment': TAG, 'hidden': False,
        'import': True, 'type': 'upgrade',
        'constraints': [maxc(1), maxc(1, 'roster', includeChildSelections=True, includeChildForces=True)],
        'costs': COSTS0,
        'rules': [
            rule('Venator Ignitum, the Canis Vertex', 'The Legio Ignatum Warhound Venator Ignitum (Princeps Jarik Volkov) stands with the Ocularis Ignis. In any Prospero Burns campaign game it counts as a Hero. It is the only Titan the Persecuted may field before Phase Three.'),
            rule('The Dying Engine (Canis Vertex only)', 'In the Canis Vertex Legendary mission Venator Ignitum is free (it does not count toward the Points Limit or Lord of War cap) and is modified as follows. Crippled: it has the Minoris Crew Trait and may pivot but may not otherwise move. Failing Shields: its Titan Void Shield Array (2) is reduced to (1), and that void shield can never be restored during the battle. Heretical Reactor: at the start of each Persecuted Player Turn, every enemy Unit within 12" must make a Willpower Check; a Unit that fails gains the Suppressed Status. Persecuted Models with the Psyker Trait within 12" add +1 to the Target Number of Manifestation Checks.'),
        ],
    })
    save(fname, data)


# ---- Spireguard Templar Section (Solar Auxilia) ----------------------------
CH = {  # Profile characteristic type IDs
    'Type': '50fc-9241-d4a2-045b', 'M': 'a106-a779-d272-5e93', 'WS': '253c-d694-4695-c89e', 'BS': '0cd5-b269-e3bc-028b',
    'S': '498f-dce1-59fd-d8d7', 'T': '3120-8275-e537-ecd2', 'W': 'f5cc-79a3-d302-cc1d', 'I': 'af9d-7db8-dc95-71c1',
    'A': '024e-bdb1-7982-25a0', 'LD': '02ad-ebe6-86e7-9fd6', 'CL': '9cd1-0e7c-2cd6-5f2f', 'WP': 'f714-1726-37d3-44df',
    'IN': '29c5-925d-5b1d-1e77', 'SAV': '03bd-4ecb-351d-143b', 'INV': 'a951-a772-7ce0-0b64',
}
MW = {'IM': '6eec-4093-f946-1014', 'AM': '03d0-6094-84f0-e27e', 'SM': '4505-de6f-d4ae-6280', 'AP': 'a014-126b-3b7b-27e8',
      'D': '6a9d-4feb-065a-33e7', 'Special Rules': 'ebe0-7b28-b40c-694e', 'Traits': '76e3-c188-bc65-3467'}


def profile(name, vals):
    return {'name': name, 'id': nid(), 'hidden': False, 'typeId': 'a76f-8e23-8c3e-166d', 'typeName': 'Profile',
            'characteristics': [{'name': k, '$text': v, 'typeId': CH[k]} for k, v in vals.items()]}


def sickle_axe():
    return {
        'name': 'Spireguard sickle-axe', 'id': nid(), 'hidden': False, 'import': True, 'type': 'upgrade',
        'constraints': [{'id': nid(), 'field': 'selections', 'scope': 'parent', 'shared': True, 'type': 'min', 'value': 1}, maxc(1)],
        'profiles': [{'name': 'Spireguard sickle-axe', 'id': nid(), 'hidden': False, 'typeId': '3587-6dcd-005c-c263',
                      'typeName': 'Melee Weapon',
                      'characteristics': [{'name': k, '$text': v, 'typeId': MW[k]} for k, v in
                                          {'IM': '-1', 'AM': 'A', 'SM': '+1', 'AP': '3', 'D': '1',
                                           'Special Rules': 'Breaching (5+), Force (AP)', 'Traits': 'Power'}.items()]}],
        'infoLinks': [
            {'name': 'Breaching (X)', 'id': nid(), 'hidden': False, 'targetId': 'b094-0b64-eb57-aed6', 'type': 'rule'},
            {'name': 'Force (X)', 'id': nid(), 'hidden': False, 'targetId': '25cd-60d0-a0a4-6b18', 'type': 'rule'},
        ],
    }


def apply_templars():
    fname = 'Solar Auxilia.json'
    data = load(fname)
    c = data['catalogue']
    tmpl = next(s for s in c['sharedSelectionEntries'] if s['name'] == 'Veletaris Storm Section')
    c['sharedSelectionEntries'] = strip_tagged(c['sharedSelectionEntries'])
    c['entryLinks'] = strip_tagged(c['entryLinks'])

    # Unit-level links reused from the Veletaris template: grenades, Prime Unit, Allegiance,
    # and the Cohort Doctrine rule links (so Fateweaver Cohort etc. still show).
    unit_links = [dict(l, id=nid()) for l in json.loads(json.dumps(tmpl['entryLinks'])) if l['name'] in ('Frag grenades', 'Prime Unit')]
    for l in unit_links:
        for k in ('constraints',):
            for x in l.get(k, []):
                x['id'] = nid()
        for sub in l.get('entryLinks', []):
            sub['id'] = nid()
    info = json.loads(json.dumps([l for l in tmpl['infoLinks'] if l['name'] != 'Vanguard (X)']))
    for l in info:
        l['id'] = nid()

    vet_groups = next(p for p in next(m for m in tmpl['selectionEntries'] if m['name'] == 'Veletarii')['profiles'])['modifierGroups']
    prime_groups = next(m for m in tmpl['selectionEntries'] if m['name'] == 'Veletarii Prime')['profiles'][0]['modifierGroups']
    prime_cats = next(m for m in tmpl['selectionEntries'] if m['name'] == 'Veletarii Prime')['categoryLinks']
    prime_mods = next(m for m in tmpl['selectionEntries'] if m['name'] == 'Veletarii Prime')['modifiers']
    inf_cat = next(m for m in tmpl['selectionEntries'] if m['name'] == 'Veletarii')['categoryLinks']

    def fresh(x):
        x = json.loads(json.dumps(x))
        def walk(o):
            if isinstance(o, dict):
                if 'id' in o and isinstance(o['id'], str) and len(o['id']) == 19:
                    o['id'] = nid()
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(x)
        return x

    base = {'M': '6', 'WS': '4', 'BS': '4', 'S': '3', 'T': '3', 'W': '1', 'I': '3', 'A': '2', 'LD': '7', 'CL': '8',
            'WP': '7', 'IN': '6', 'SAV': '4+', 'INV': '6+'}
    prime_p = profile('Templar Prime', {'Type': 'Infantry (Sergeant)', **base, 'A': '3', 'LD': '8', 'WP': '8'})
    prime_p['modifierGroups'] = fresh(prime_groups)
    trooper_p = profile('Templar', {'Type': 'Infantry', **base})
    trooper_p['modifierGroups'] = fresh(vet_groups)

    pistol_group = {
        'name': 'Pistol', 'id': nid(), 'hidden': False,
        'constraints': [{'id': nid(), 'field': 'selections', 'scope': 'parent', 'shared': True, 'type': 'min', 'value': 1}, maxc(1)],
        'entryLinks': [
            {'name': 'Laspistol', 'id': nid(), 'hidden': False, 'import': True, 'targetId': '70e6-52c9-86b9-604c', 'type': 'selectionEntry'},
            {'name': 'Auxilia Pistols', 'id': nid(), 'hidden': False, 'import': True, 'targetId': '22a3-5b09-13b0-2624', 'type': 'selectionEntryGroup'},
        ],
    }
    pistol_group['defaultSelectionEntryId'] = pistol_group['entryLinks'][0]['id']

    prime = {
        'name': 'Templar Prime', 'id': nid(), 'hidden': False, 'import': True, 'sortIndex': 1, 'type': 'model',
        'categoryLinks': fresh(prime_cats),
        'constraints': [{'id': nid(), 'field': 'selections', 'scope': 'parent', 'shared': True, 'type': 'min', 'value': 1}, maxc(1)],
        'modifiers': fresh(prime_mods),
        'profiles': [prime_p],
        'selectionEntries': [sickle_axe()],
        'selectionEntryGroups': [pistol_group],
    }
    trooper = {
        'name': 'Templar', 'id': nid(), 'hidden': False, 'import': True, 'sortIndex': 2, 'type': 'model',
        'categoryLinks': fresh(inf_cat),
        'constraints': [maxc(19), {'id': nid(), 'field': 'selections', 'scope': 'parent', 'shared': True, 'type': 'min', 'value': 9}],
        'costs': [dict(COSTS0[0], value=10)] + COSTS0[1:],
        'profiles': [trooper_p],
        'selectionEntries': [sickle_axe()],
        'entryLinks': [
            {'name': 'Laspistol', 'id': nid(), 'hidden': False, 'import': True, 'targetId': '70e6-52c9-86b9-604c', 'type': 'selectionEntry',
             'constraints': [{'id': nid(), 'field': 'selections', 'scope': 'parent', 'shared': True, 'type': 'min', 'value': 1}, maxc(1)]},
        ],
        'selectionEntryGroups': [{
            'name': 'Options', 'id': nid(), 'hidden': False,
            'entryLinks': [{'name': 'Auxilia vexilla', 'id': nid(), 'hidden': False, 'import': True,
                            'targetId': 'abc6-851f-ab12-1ddd', 'type': 'selectionEntry',
                            'constraints': [maxc(1), maxc(1, 'unit', includeChildSelections=True)],
                            'modifiers': [{'field': PTS, 'type': 'set', 'value': 5}]}],
        }],
    }
    unit = {
        'name': 'Spireguard Templar Section', 'id': nid(), 'comment': TAG, 'hidden': False, 'import': True, 'type': 'unit',
        'costs': [dict(COSTS0[0], value=20)] + COSTS0[1:] + [
            {'name': 'Auxiliary Detachment(s)', 'typeId': '3e8e-05ee-be52-12d6', 'value': 0},
            {'name': 'Apex Detachment(s)', 'typeId': '159d-855c-533d-f592', 'value': 0}],
        'entryLinks': unit_links,
        'infoLinks': [{'name': 'Vanguard (X)', 'id': nid(), 'hidden': False, 'targetId': '530f-b733-993c-ec84', 'type': 'rule',
                       'modifiers': [{'comment': '2', 'field': 'name', 'type': 'set', 'value': 'Vanguard (2)'}]}] + info,
        'profiles': fresh([p for p in tmpl['profiles']]),
        'rules': [
            rule('Psy-warded', "The Templars' Invulnerable Save improves to 5+ against wounds from Psychic Weapons."),
            rule('Prospero Burns campaign unit', 'Campaign games only; playtest points. Only in an army with the Prosperine Spireguard Legiones Auxilia Designation.'),
        ],
        'selectionEntries': [prime, trooper],
    }
    c['sharedSelectionEntries'].append(unit)
    c['entryLinks'].append({
        'name': 'Spireguard Templar Section', 'id': nid(), 'comment': TAG, 'hidden': True, 'import': True,
        'targetId': unit['id'], 'type': 'selectionEntry',
        'categoryLinks': [{'name': 'Elites', 'id': nid(), 'primary': True, 'targetId': CAT_ELITES}],
        'modifiers': [{'field': 'hidden', 'type': 'set', 'value': False, 'conditions': [{
            'childId': SPIREGUARD_DESIGNATION, 'field': 'selections', 'scope': 'roster', 'shared': True,
            'includeChildForces': True, 'includeChildSelections': True, 'type': 'atLeast', 'value': 1}]}],
    })
    save(fname, data)


# ---- House ruling: Dreadnought Talon (Mortificator) takes any Contemptor- or
# Castra Ferrum-chassis Dreadnought, including Legion-specific variants ------
TALON_FORCE = '9ffc-1414-bcb2-ca4b'
TALON_SLOT = 'f817-34d5-598c-d196'  # "War Engine - Contemptor Dreadnoughts Only"
TALON_LINKS = {  # file: root entry links (standard War-engine links only)
    'Legiones Astartes.json': ['0365-190b-7181-ec24'],   # Castra Ferrum Dreadnought
    'Thousand Sons.json': ['1ee2-34ab-cb0e-3b25'],       # Contemptor-Osiron Dreadnought
    'Blood Angels.json': ['5dc8-3fde-9013-ef36'],        # Contemptor-Incaendius Dreadnought
}


def apply_talon():
    mod = {'comment': TAG, 'field': 'category', 'type': 'set-primary', 'value': TALON_SLOT,
           'conditions': [{'childId': TALON_FORCE, 'field': 'selections', 'includeChildSelections': True,
                           'scope': 'parent', 'shared': True, 'type': 'instanceOf', 'value': 1}]}
    for fname, ids in TALON_LINKS.items():
        data = load(fname)
        for link in data['catalogue']['entryLinks']:
            if link['id'] in ids:
                link['modifiers'] = strip_tagged(link.get('modifiers', [])) + [dict(mod)]
        save(fname, data)


# ---- Game system name -------------------------------------------------------
def apply_name():
    fname = 'Horus Heresy 3rd Edition.json'
    data = load(fname)
    data['gameSystem']['name'] = 'Horus Heresy 3rd Edition - Prospero Burns'
    save(fname, data)


if __name__ == '__main__':
    for f, d in DOCTRINES.items():
        apply_doctrine(f, d)
    apply_venator()
    apply_templars()
    apply_talon()
    apply_name()
    print('Prospero Burns additions applied.')
