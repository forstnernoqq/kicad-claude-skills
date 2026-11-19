"""widen.py in.kicad_pcb out.kicad_pcb state.json mode target [drc.json]
mode 'apply': widen heater-net tracks (below target) to target, remembering the old width per uuid.
mode 'revert': revert tracks (widened this round) that appear in DRC errors (clearance/shorting/hole)."""
import pcbnew,sys,json
b=pcbnew.LoadBoard(sys.argv[1]); out=sys.argv[2]; sp=sys.argv[3]; mode=sys.argv[4]; target=float(sys.argv[5]); mm=pcbnew.FromMM; T=pcbnew.ToMM
try: st=json.load(open(sp))
except Exception: st={'old':{},'failed':{}}
HEAT=('VBUS','/VH','/OUT_CH1')
tr={t.m_Uuid.AsString():t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK'}
if mode=='apply':
    n=0
    for u,t in tr.items():
        if t.GetNetname() in HEAT and T(t.GetWidth())<target-0.01 and st['failed'].get(u,99)>target:
            st['old'][u]=st['old'].get(u,T(t.GetWidth())); st.setdefault('round',{})[u]=target; t.SetWidth(mm(target)); n+=1
    print('widened',n)
else:
    d=json.load(open(sys.argv[6])); n=0
    for v in d['violations']:
        if v['severity']!='error': continue
        for it in v['items']:
            u=it.get('uuid')
            if u in tr and st.get('round',{}).get(u)==target:
                tr[u].SetWidth(mm(st['old'][u])); st['failed'][u]=target; st['round'].pop(u); n+=1
    print('reverted',n)
json.dump(st,open(sp,'w')); b.Save(out)
