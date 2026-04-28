"""
Wikidata Knowledge Ingester
Pulls structured entity facts from Wikidata and stores in knowledge_graph.json
"""
import json, urllib.request, urllib.parse, os, re, time, time
DATA_DIR = os.path.expanduser('~/.quantum-mcagi')
KG_PATH = os.path.join(DATA_DIR, 'knowledge_graph.json')
# Wikidata property labels we care about
PROP_LABELS = {
'P31': 'is_a',
# instance of
'P17': 'country',
# country
'P30': 'continent',
# continent
'P36': 'capital',
# capital
'P18': 'image',
# skip
'P856': 'website',
# skip
'P625': 'coordinates', # skip
'P571': 'founded',
# inception
'P576': 'dissolved',
# dissolution
'P101': 'field',
# field of work
'P361': 'part_of',
# part of
'P527': 'has_part',
# has part
'P1566': 'geonames',
# skip
'P18': 'image',
# skip
'P856': 'website',
# skip
'P19': 'birth_place',
# place of birth
'P20': 'death_place',
# place of death
'P569': 'born',
# date of birth
'P570': 'died',
# date of death
'P21': 'gender',
# sex or gender
'P106': 'occupation',
# occupation
'P27': 'nationality',
# country of citizenship
'P131': 'located_in',
# located in admin entity
'P276': 'location',
# location
'P571': 'created',
# inception
'P582': 'ended',
# end time
'P2044': 'elevation',
# elevation
'P1082': 'population', # population
'P2046': 'area',
# area
'P421': 'timezone',
# timezone
'P37': 'language',
# official language
'P38': 'currency',
# currency
'P35': 'head_of_state', # head of state
'P6': 'head_of_gov',
# head of government
'P122': 'gov_type',
# basic form of government
'P41': 'flag',
# skip
'P94': 'coat_of_arms', # skip
}
SKIP_PROPS = {'P18', 'P856', 'P41', 'P94', 'P1566', 'P625', 'P242', 'P158', 'P948'}
def get_entity_id(title):
"""Get Wikidata entity ID from Wikipedia title."""
url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={urllib.parse.quote(title)}&props=ids&format=json"
for attempt in range(3):
try:
req = urllib.request.Request(url, headers={'User-Agent': 'QuantumMCAGI/1.0 (educational project)'})
with urllib.request.urlopen(req, timeout=15) as r:
data = json.load(r)
entities = data.get('entities', {})
for eid, edata in entities.items():
if eid != '-1':
return eid
return None
except Exception as e:
if '429' in str(e):
print(f" Rate limited, waiting 10s...")
time.sleep(30)
else:
print(f" Error getting entity ID: {e}")
return None
return None
def get_label(entity_id, lang='en'):
"""Get human-readable label for a Wikidata entity."""
url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=labels&languages=en&format=json"
try:
req = urllib.request.Request(url, headers={'User-Agent': 'QuantumMCAGI/1.0 (educational project)'})
with urllib.request.urlopen(req, timeout=10) as r:
data = json.load(r)
return data['entities'][entity_id]['labels'].get(lang, {}).get('value', entity_id)
except:
return entity_id
def get_entity_facts(entity_id):
"""Pull structured facts for an entity."""
url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=claims|labels|descriptions&languages=en&format=json"
try:
req = urllib.request.Request(url, headers={'User-Agent': 'QuantumMCAGI/1.0 (educational project)'})
with urllib.request.urlopen(req, timeout=15) as r:
data = json.load(r)
except Exception as e:
print(f" Error fetching entity: {e}")

return {}
entity = data['entities'].get(entity_id, {})
label = entity.get('labels', {}).get('en', {}).get('value', entity_id)
description = entity.get('descriptions', {}).get('en', {}).get('value', '')
claims = entity.get('claims', {})
facts = {
'_id': entity_id,
'_label': label,
'_description': description,
'_relations': {}
}
for prop, claim_list in claims.items():
if prop in SKIP_PROPS:
continue
prop_name = PROP_LABELS.get(prop, prop)
values = []
for claim in claim_list[:3]: # Max 3 values per property
try:
snak = claim['mainsnak']
if snak['snaktype'] != 'value':
continue
val = snak['datavalue']['value']
vtype = snak['datavalue']['type']
if vtype == 'string':
values.append(val)
elif vtype == 'monolingualtext':
if val.get('language') == 'en':
values.append(val['text'])
elif vtype == 'wikibase-entityid':
# Resolve entity ID to label
eid = val['id']
elabel = get_label(eid)
values.append(elabel)
elif vtype == 'quantity':
amount = val['amount'].lstrip('+')
unit = val.get('unit', '')
if 'Q' in unit:
unit_id = unit.split('/')[-1]
unit_label = get_label(unit_id)
values.append(f"{amount} {unit_label}")
else:
values.append(amount)
elif vtype == 'time':
values.append(val['time'][:11]) # Just the date part
elif vtype == 'globecoordinate':
values.append(f"lat:{val['latitude']:.2f} lon:{val['longitude']:.2f}")
except Exception:
continue
if values:
facts['_relations'][prop_name] = values
return facts
def load_kg():
try:
with open(KG_PATH) as f:
return json.load(f)
except:
return {}
def save_kg(kg):
with open(KG_PATH, 'w') as f:
json.dump(kg, f, indent=2)
def ingest_entity(title):
"""Ingest a Wikipedia article title as structured knowledge."""
print(f" Fetching: {title}...")
eid = get_entity_id(title)
if not eid:
print(f" Not found: {title}")
return False
facts = get_entity_facts(eid)
if not facts:
print(f" No facts: {title}")
return False
kg = load_kg()
key = title.lower().replace('_', ' ')
kg[key] = facts
save_kg(kg)
rel_count = len(facts.get('_relations', {}))
print(f" ✓ {facts['_label']}: {facts['_description'][:60]}...")
print(f"
{rel_count} structured relations stored")
return True
def query_kg(entity_name):
"""Query knowledge graph for an entity."""
kg = load_kg()
key = entity_name.lower().strip()
if key in kg:
return kg[key]
# Fuzzy match
for k in kg:
if key in k or k in key:

return kg[k]
return None
def kg_to_facts(entity_name):
"""Convert KG entry to readable fact strings for response injection."""
entry = query_kg(entity_name)
if not entry:
return []
facts = []
label = entry.get('_label', entity_name)
desc = entry.get('_description', '')
if desc:
facts.append(f"{label} is {desc}")
for rel, values in entry.get('_relations', {}).items():
if rel.startswith('_'):
continue
facts.append(f"{label} {rel.replace('_', ' ')} {', '.join(str(v) for v in values[:2])}")
return facts[:8] # Max 8 facts per entity
if __name__ == '__main__':
import sys
if len(sys.argv) < 2:
print("Usage: python3 wikidata_ingester.py <Wikipedia_Title> [Title2] ...")
print("Example: python3 wikidata_ingester.py Europe England London")
sys.exit(1)
for title in sys.argv[1:]:
ingest_entity(title)
kg = load_kg()
print(f"
Knowledge graph: {len(kg)} entities")

