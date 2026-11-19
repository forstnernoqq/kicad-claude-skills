"""export_dsn.py in.kicad_pcb out.dsn  -- Specctra DSN via pcbnew (works with bottom-side footprints)."""
import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
print('dsn', pcbnew.ExportSpecctraDSN(b, sys.argv[2]))
