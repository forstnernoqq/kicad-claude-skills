import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1])
for ref,num in (('U3','4'),):
    f=b.FindFootprintByReference(ref)
    for p in f.Pads():
        if p.GetNumber()==num: p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.ZONE_FILLER(b).Fill([z for z in b.Zones() if not z.GetIsRuleArea()]); b.Save(sys.argv[2])
