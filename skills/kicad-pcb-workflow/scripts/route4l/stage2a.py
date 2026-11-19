"""rebuild.py base.kicad_pcb batch.json out.kicad_pcb : new outline 65..120 x 54..72 (r=2), new positions, In1 GND plane + keepouts for the router."""
import pcbnew,sys,json,math
b=pcbnew.LoadBoard(sys.argv[1]); 
mm=pcbnew.FromMM; V=pcbnew.VECTOR2I
KEEP=[]
print('STAGE # outline',flush=True)
# outline
for d in list(b.GetDrawings()):
    if d.GetLayer()==pcbnew.Edge_Cuts: b.Remove(d)
import os
X0,Y0,X1,Y1,R=65.0,54.0,115.0+float(os.environ.get('DL','5')),69.0+float(os.environ.get('DH','3')),2.0
def seg(x0,y0,x1,y1):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetStart(V(mm(x0),mm(y0))); s.SetEnd(V(mm(x1),mm(y1))); s.SetWidth(mm(0.05)); b.Add(s); KEEP.append(s)
def arc(cx,cy,a0):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.05))
    p0=V(mm(cx+R*math.cos(math.radians(a0))),mm(cy+R*math.sin(math.radians(a0))))
    pm=V(mm(cx+R*math.cos(math.radians(a0+45))),mm(cy+R*math.sin(math.radians(a0+45))))
    p1=V(mm(cx+R*math.cos(math.radians(a0+90))),mm(cy+R*math.sin(math.radians(a0+90))))
    s.SetArcGeometry(p0,pm,p1); b.Add(s); KEEP.append(s)
print('STAGE seg(X0+R',flush=True)
seg(X0+R,Y0,X1-R,Y0); seg(X1,Y0+R,X1,Y1-R); seg(X1-R,Y1,X0+R,Y1); seg(X0,Y1-R,X0,Y0+R)
arc(X0+R,Y0+R,180); arc(X1-R,Y0+R,270); arc(X1-R,Y1-R,0); arc(X0+R,Y1-R,90)
b.Save(sys.argv[2]); print('outline saved')
