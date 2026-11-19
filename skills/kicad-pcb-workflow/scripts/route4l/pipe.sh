#!/bin/sh
# pipe.sh PLACEMENT.json TAG   (run in route_job)
S="$(cd "$(dirname "$0")" && pwd)"
K="$S/.."
P=$1; T=$2
python3 - "$P" "$S/batch_$T.json" <<'PY'
import json,sys
P=json.load(open(sys.argv[1]))['place']
open(sys.argv[2],'w').write(json.dumps([{"reference":r,"x":round(p['x'],2),"y":round(p['y'],2),"rotation":p['rot']} for r,p in sorted(P.items())],separators=(',',':')))
PY
$S/py.sh $S/t1.py base.kicad_pcb $S/batch_$T.json t1_$T.kicad_pcb | tail -1
$S/py.sh $S/stage2a.py t1_$T.kicad_pcb t2_$T.kicad_pcb | tail -1
$S/py.sh $S/stage2b.py t2_$T.kicad_pcb in_$T.kicad_pcb | tail -1
python3 $S/relax.py in.kicad_pro in_$T.kicad_pro
grep -v "^$" in.kicad_dru | sed -n '1,8p' > in_$T.kicad_dru   # JLC rules only (no analog-separation rules)
$S/py.sh $K/export_dsn.py in_$T.kicad_pcb adapter_$T.dsn
python3 - $T <<'PY'
import re,sys
t=sys.argv[1]; s=open('adapter_%s.dsn'%t).read(); s2=re.sub(r'(\(net GND\s*\n\s*\(pins )[^)]*(\))',r'\1\2',s,count=1); assert s2!=s; open('adapter_%s.dsn'%t,'w').write(s2); print('dsn ok')
PY
. "$S/../kenv.sh"; JAR="$FR_JAR"
nohup timeout 1500 java -Djava.awt.headless=true -jar "$JAR" --gui.enabled=false -de adapter_$T.dsn -do out_$T.ses -mp 80 > fr_$T.log 2>&1 &
echo started
