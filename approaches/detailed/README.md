# Detailed Merton College model

A new architectural model built after inspecting all five photographs in `images/`. The existing footprint, orientation and 220 mm site width are retained. Facade details are solid geometry, including the mullions and tracery; no textures or displacement maps are required.

## Files

- [`../../deliverables/merton-detailed.stl`](../../deliverables/merton-detailed.stl): full college, 220 × 207.52 × 58.19 mm, approximately 1:641.
- [`../../deliverables/merton-detailed-a1.3mf`](../../deliverables/merton-detailed-a1.3mf): full college with Bambu A1 / 0.4 mm / PLA settings.
- [`../../deliverables/merton-detailed-chapel-1-333.stl`](../../deliverables/merton-detailed-chapel-1-333.stl): enlarged standalone chapel, 148.51 × 129.77 × 111.81 mm, approximately 1:333.
- [`../../deliverables/merton-detailed-chapel-1-333-a1.3mf`](../../deliverables/merton-detailed-chapel-1-333-a1.3mf): enlarged chapel A1 project.

Both projects use 0.12 mm layers, Arachne walls, 3 wall loops, 12% gyroid, Generic PLA and a textured PEI plate. Automatic tree supports are enabled because the initial supports-off slices flagged floating regions. Choose your actual filament and plate before printing. No physical print has been performed.

## What the photographs contributed

| Reference | Visible evidence used |
|---|---|
| `Merton_College,_Oxford_from_Merton_Field.jpg` | Repeated triangular coped gables, alternating broad chimney stacks, stack collars and vertical flue divisions, three facade levels, projecting multi-light oriels with transoms, tall tower belfry openings. |
| `fit.webp` | Oblique confirmation of the long outer ranges, gable/chimney rhythm, oriel depth, horizontal stone courses and eight-pinacled tower silhouette. |
| `images.jpeg` | Lower-resolution exterior overview used to cross-check the silhouette; not treated as an additional dimensional survey. |
| `Mob20Quad.webp` | Two-storey court facades, varied two/three/four-light windows, dropped hood molds, pointed doorways, roof dormers, library oriel, octagonal stair turret, chapel gable and tower tracery. |
| `Merton20College20Buildings_Fisher20Studios20Ltd_Aug202025.webp` | Close tower view: nested pointed arch surrounds, fine belfry subdivisions, banded piers, carved parapet frieze, pierced upper balustrade and crocketed pinnacles. Also confirms the court's window surrounds and dormer profiles. |

The builder authors 35 stepped buttresses, 15 coped facade gables, 65 dormers, 31 chimney stacks with 41 shallow flue mouths, four projecting oriels, eight tower pinnacles and four pierced parapet faces. It also generates hundreds of window assemblies with actual stone mullions, transoms, Gothic heads and recessed panes. These are counts of authored features, **not surveyed counts of the real building**; adjoining solids can obscure individual features. `feature-register.json` and `validation.json` record the construction details.

The tower's paired windows have four lights with transoms, subsidiary pointed heads and circular tracery. The chapel has larger three- and five-light windows. Its buttresses have three setbacks and sloping weathering caps. The parapet includes a quatrefoil frieze, open upper slots and merlons. The small pinnacles use simplified crockets and thickened tips. The full-scale mullions are nominally 0.50 mm wide; the enlarged chapel makes the same details easier to inspect.

## Interpretation and limits

This is a photograph-informed reconstruction, not photogrammetry or a measured facade survey. The reference images establish characteristic forms but do not show every elevation or give dimensions. The builder retains the earlier OSM footprints and EA-derived roof estimates. Window spacing, chimney positions, hidden facades, chapel buttress dimensions and tracery patterns are interpreted. Fine carving is simplified, and stonework is thickened to survive the chosen scale. Door and window openings are predominantly backed recesses. The tower parapet has genuine open slots. The footprint crop still omits the larger gardens and modern Rose Lane ranges.

No artificial brick or tile texture was added: effort is concentrated on the requested structural details. The preview images render the actual delivered meshes with directional light and screen-space ambient occlusion.

## Geometry checks

The full model contains 295,336 triangles, versus 4,352 in the original architectural model. The chapel sample contains 79,838 triangles. Both delivered STLs were reloaded independently and pass single-component, watertightness, consistent winding, positive-volume, finite-coordinate, flat-base and A1 bed-fit checks. Both have zero boundary and nonmanifold edges. See [`../../validation/detailed_meshes.json`](../../validation/detailed_meshes.json).

Inaccessible voids sealed between adjoining buildings are filled. The solid kernel's vertex-merge mapping is preserved explicitly, and coincident vertices are separated by less than 0.0007 mm for reliable STL serialization. Two numerical shells below 0.001 mm³ are discarded in the full model. Surface simplification is bounded by 0.01 mm. These measures preserve the modeled details and are recorded in the validation files.

Slicing reports, actual plate thumbnails and the original supports-off warning reports are retained under `validation/detailed_slice/` and `validation/detailed-chapel-1-333_slice/`.

## Rebuild

From the repository root, using the existing environment and requirements:

```sh
.venv/bin/python approaches/detailed/build_detailed.py
.venv/bin/python scripts/inspect_mesh.py deliverables/merton-detailed.stl deliverables/merton-detailed-chapel-1-333.stl --output validation/detailed_meshes.json
.venv/bin/python scripts/slice_candidates.py detailed detailed-chapel-1-333
.venv/bin/python approaches/detailed/render_details.py full
.venv/bin/python approaches/detailed/render_details.py chapel
.venv/bin/python approaches/detailed/render_details.py facade
```

The builder uses frozen local data and does not need network access. Slicing requires the existing Bambu Studio installation. The script exports local projects and does not submit a print. `facade-preview-only.ply` is an open crop solely for rendering, not a printable deliverable.

Footprints © OpenStreetMap contributors, ODbL 1.0. Roof-height source © Environment Agency, OGL v3.0. See the existing architectural and LiDAR source records for full attribution. The supplied photographs retain their own copyrights and are not embedded in the deliverables.
