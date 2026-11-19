import pcbnew,sys
b=pcbnew.LoadBoard(sys.argv[1]); print('import',pcbnew.ImportSpecctraSES(b,sys.argv[2]))
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[3])
print('tracks',len([t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK']),'vias',len([t for t in b.GetTracks() if t.GetClass()=='PCB_VIA']))
