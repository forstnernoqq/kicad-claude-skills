import pcbnew,sys,json
b=pcbnew.LoadBoard(sys.argv[1]); B={x['reference']:x for x in json.load(open(sys.argv[2]))}
mm=pcbnew.FromMM
n=0
for f in b.GetFootprints():
    r=f.GetReference(); t=B[r]
    f.SetPosition(pcbnew.VECTOR2I(mm(t['x']),mm(t['y'])))
    f.SetOrientationDegrees(float(t['rotation'])); n+=1
    print(r,flush=True) if n%20==0 else None
b.Save(sys.argv[3]); print('saved',n)
