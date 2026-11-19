"""jlc_assembly.py raw_bom.csv pos.csv outdir name  -- plain python (no pcbnew).
raw_bom.csv: one row per symbol (Ref, Value, Footprint, LCSC, DNP) from `kicad-cli sch export bom --group-by ''`.
pos.csv: `kicad-cli pcb export pos --format csv --units mm --side both`.
Writes <name>_BOM_JLC.csv (Comment, Designator, Footprint, LCSC Part #, Quantity) and <name>_CPL_JLC.csv
(Designator, Mid X, Mid Y, Layer, Rotation) for the fitted parts only (no DNP, no 'exclude from BOM').
Rotations are KiCad's: check JLC's placement preview for QFN pin 1, SOT-23, diodes and LEDs."""
import csv, collections, re, sys
bom_in, pos_in, out, name = sys.argv[1:5]
nat = lambda s: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]
rows = [r for r in csv.DictReader(open(bom_in)) if not r.get('DNP')]
pos = {r['Ref']: r for r in csv.DictReader(open(pos_in))}
groups = collections.OrderedDict()
for r in rows: groups.setdefault((r['Value'], r['Footprint'].split(':')[-1], r['LCSC']), []).append(r['Ref'])
with open(f'{out}/{name}_BOM_JLC.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Quantity'])
    for (v, fp, l), refs in groups.items(): w.writerow([v, ','.join(sorted(refs, key=nat)), fp, l, len(refs)])
missing_pos = [r['Ref'] for r in rows if r['Ref'] not in pos]
with open(f'{out}/{name}_CPL_JLC.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in sorted(rows, key=lambda r: nat(r['Ref'])):
        p = pos.get(r['Ref'])
        if p: w.writerow([r['Ref'], p['PosX'] + 'mm', p['PosY'] + 'mm', p['Side'].capitalize(), p['Rot']])
fitted = {r['Ref'] for r in rows}
print(f'BOM: {len(groups)} lines, {len(rows)} parts; sides',
      dict(collections.Counter(pos[r]['Side'] for r in fitted if r in pos)))
print('no LCSC number:', [r['Ref'] for r in rows if not r['LCSC']] or 'none')
print('fitted but not on the board:', missing_pos or 'none')
print('on the board but not assembled:', ' '.join(sorted((k for k in pos if k not in fitted), key=nat)))
