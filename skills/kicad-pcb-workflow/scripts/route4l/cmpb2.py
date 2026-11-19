import pcbnew,sys,json
b=pcbnew.LoadBoard(sys.argv[1]); B={x['reference']:x for x in json.load(open(sys.argv[2]))}
ch=[]
for f in b.GetFootprints():
    r=f.GetReference(); p=f.GetPosition(); x,y=pcbnew.ToMM(p.x),pcbnew.ToMM(p.y); rot=f.GetOrientationDegrees()%360
    t=B[r]
    if abs(x-t['x'])>0.011 or abs(y-t['y'])>0.011 or abs(rot-t['rotation']%360)>0.5: ch.append(t)
print(json.dumps(ch,separators=(',',':')))
