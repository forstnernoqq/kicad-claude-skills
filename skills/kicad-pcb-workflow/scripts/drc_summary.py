"""drc_summary.py drc.json  -- counts per type, details for anything except lib_footprint_mismatch."""
import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
for k in ('violations', 'unconnected_items', 'schematic_parity'):
    print(k, dict(Counter(x['type'] for x in d.get(k, []))))
for x in d.get('violations', []):
    if x['type'] != 'lib_footprint_mismatch':
        print(x['severity'], x['type'], x['description'][:90], [(i['description'][:45], i['pos']) for i in x['items']][:2])
