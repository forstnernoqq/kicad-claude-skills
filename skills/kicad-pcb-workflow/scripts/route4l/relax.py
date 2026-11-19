import json,sys
p=json.load(open(sys.argv[1])); ns=p['net_settings']
for c in ns['classes']:
    n=c['name']
    c['via_diameter']=0.45; c['via_drill']=0.2
    if n=='Default': c.update(clearance=0.127,track_width=0.127)
    if n=='Power_heater': c.update(clearance=0.15,track_width=0.5,via_diameter=0.5,via_drill=0.2)
    if n=='Buck_SW': c.update(clearance=0.15,track_width=0.3)
    if n=='PWM_gate': c.update(clearance=0.15,track_width=0.2)
    if n=='Analog_sensitive': c.update(clearance=0.15,track_width=0.127)
    if n=='USB_FS': c.update(clearance=0.127,track_width=0.2,diff_pair_width=0.2,diff_pair_gap=0.15)
    if n=='Supply_3V3': c.update(clearance=0.127,track_width=0.25)
d=p['board']['design_settings']
d['rules'].update(min_track_width=0.1,min_clearance=0.1)
json.dump(p,open(sys.argv[2],'w'),indent=2)
