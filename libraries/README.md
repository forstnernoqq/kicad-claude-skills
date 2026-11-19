# KiCad libraries

| File | Contents |
|---|---|
| `RCL.kicad_sym` | Generic passives that show their spec on the schematic. **R_Spec_V / R_Spec_H** display value, package (`Size`) and tolerance; **C_Spec_V / C_Spec_H** display value, package and dielectric. `_V` is vertical and `_H` horizontal. |

**Use:** in KiCad, Preferences → Manage Symbol Libraries → Global (or Project) → add `RCL.kicad_sym` with the nickname `RCL`.

**Fields:** set `Size` (0402, 0603, …), `Tolerance` and `Dielectric`, plus the footprint, per instance. For JLC assembly, also add an `LCSC` field with the part number (see `skills/kicad-pcb-workflow/reference_jlcpcb.md`).

The file format is KiCad 10, version 20251024. Keep that version when editing the file as text: newer version numbers fail to load in KiCad 10.
