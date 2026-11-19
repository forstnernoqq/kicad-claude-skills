#!/bin/bash
# chain.sh IN_PCB TAG PRO DRU : post-processing chain (cwd = route_job)
S="$(cd "$(dirname "$0")" && pwd)"
K="$S/../kcli"
IN=$1; T=$2; PRO=$3; DRU=$4
drc(){ $K pcb drc --severity-all --format json -o $2 $1 >/dev/null 2>&1; }
setup(){ cp $PRO ${1%.kicad_pcb}.kicad_pro; cp $DRU ${1%.kicad_pcb}.kicad_dru; }
$S/py.sh $S/post13.py $IN ${T}_a.kicad_pcb | tail -1; setup ${T}_a.kicad_pcb; drc ${T}_a.kicad_pcb drc_${T}_a.json
$S/py.sh $S/post13.py $IN ${T}_b.kicad_pcb drc_${T}_a.json | tail -1; setup ${T}_b.kicad_pcb
for i in 1 2 3; do drc ${T}_b.kicad_pcb drc_${T}_b.json; $S/py.sh $S/prune.py ${T}_b.kicad_pcb ${T}_b.kicad_pcb drc_${T}_b.json | tail -1; done
$S/py.sh $S/frag2.py ${T}_b.kicad_pcb ${T}_c.kicad_pcb | tail -1; setup ${T}_c.kicad_pcb
for i in 1 2; do drc ${T}_c.kicad_pcb drc_${T}_c.json; $S/py.sh $S/prune.py ${T}_c.kicad_pcb ${T}_c.kicad_pcb drc_${T}_c.json | tail -1; done
$S/py.sh $S/heat2.py ${T}_c.kicad_pcb ${T}_d.kicad_pcb 3.0 | tail -1; setup ${T}_d.kicad_pcb
for i in 1 2 3; do drc ${T}_d.kicad_pcb drc_${T}_d.json; $S/py.sh $S/gndfix2.py ${T}_d.kicad_pcb ${T}_d.kicad_pcb drc_${T}_d.json | tail -2; done
for i in 1 2; do drc ${T}_d.kicad_pcb drc_${T}_d.json; $S/py.sh $S/prune.py ${T}_d.kicad_pcb ${T}_d.kicad_pcb drc_${T}_d.json | tail -1; done
$S/py.sh $S/frag2.py ${T}_d.kicad_pcb ${T}_e.kicad_pcb | tail -1; setup ${T}_e.kicad_pcb
for i in 1 2; do drc ${T}_e.kicad_pcb drc_${T}_e.json; $S/py.sh $S/prune.py ${T}_e.kicad_pcb ${T}_e.kicad_pcb drc_${T}_e.json | tail -1; done
drc ${T}_e.kicad_pcb drc_${T}_e.json
python3 - $T <<'PY'
import json,collections,sys
j=json.load(open('drc_%s_e.json'%sys.argv[1])); print(dict(collections.Counter((v['type'],v['severity']) for v in j['violations'])),'unconnected',len(j['unconnected_items']))
for u in j['unconnected_items']: print([i['description'][:42] for i in u['items']])
for v in j['violations']:
    if v['severity']=='error' and v['type']!='npth_inside_courtyard': print(v['type'],v['description'][:60],[i['description'][:42] for i in v['items']][:2])
PY
