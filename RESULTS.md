# Merton College — three A1 print candidates

## New detailed model from the supplied photographs

The new [full-college A1 project](deliverables/merton-detailed-a1.3mf) and [STL](deliverables/merton-detailed.stl) add actual mullions, transoms, Gothic tracery, stepped buttresses, coped gables, projecting oriels, chimney stacks and pierced parapets. The full model is 220 × 207.52 × 58.19 mm and contains 295,336 triangles. The [enlarged chapel project](deliverables/merton-detailed-chapel-1-333-a1.3mf) makes the window and tower detail easier to inspect.

Both models pass independent mesh checks and were sliced successfully. Their projects use **0.12 mm layers, Arachne walls and automatic tree supports** on the A1 with a 0.4 mm nozzle. The supported slices have no plate warning messages. Estimates: **21 h 05 min / 232 g PLA** for the full college; **15 h 04 min / 205 g PLA** for the chapel. No physical print has been tested. The original models remain available below.

[Photograph observations, modeling assumptions and rebuild instructions](approaches/detailed/README.md) · [Full-model preview](approaches/detailed/preview-southeast.png) · [Mullioned-window close-up](approaches/detailed/preview-fellows-windows.png) · [Chapel close-up](approaches/detailed/preview-chapel.png)

Built 17 October 2026 from the approaches in the original README. All three use the same historic-core crop and horizontal scale, so you can compare their actual shapes. No API keys or additional apps were required; the installed Bambu Studio was used for slicing.

## Open a candidate

| Candidate | Bambu Studio project | What you are comparing | A1 estimate | PLA estimate |
|---|---|---|---:|---:|
| Architectural | [merton-architectural-a1.3mf](deliverables/merton-architectural-a1.3mf) | Clean mapped outlines, interpreted pitched roofs, detailed chapel tower | 7 h 44 min | 198 g |
| Hybrid | [merton-hybrid-a1.3mf](deliverables/merton-hybrid-a1.3mf) | Measured LiDAR roofs, clean flat ground and mapped walls, same modeled tower | 8 h 23 min | 191 g |
| Measured LiDAR | [merton-lidar-a1.3mf](deliverables/merton-lidar-a1.3mf) | Measured roofs and terrain, including survey noise and neighboring fragments | 13 h 02 min | 243 g |

The architectural candidate is the cleanest starting print. The hybrid retains more of the real roof variation. The LiDAR candidate provides the direct measured-surface benchmark. They are prototypes with documented architectural assumptions; none is a detailed survey of every facade.

Each base is **220 × 207.52 mm**, fitting the A1's configured 256 × 256 mm bed. Height is 57.39 mm for architectural/hybrid and 58.79 mm for LiDAR. The minimum base thickness is 3 mm. Scale is approximately 1:641, with no vertical exaggeration. The cropped site includes the chapel and historic quads plus Grove I/II; it omits most gardens, modern Rose Lane buildings and remote college properties.

## Try the smaller comparison plate

[merton-chapel-comparison-a1.3mf](deliverables/merton-chapel-comparison-a1.3mf) contains a **54.61 × 62.41 mm chapel sample from each model**, all at the full models' scale. The whole plate is estimated at **5 h 04 min / 84 g PLA**. Use the named objects in Bambu Studio to identify the candidates or delete two objects if you want to print one sample first. The samples are crops, so their edges deliberately cut through surrounding roofs.

STLs for the full models and samples are in [deliverables](deliverables/). These let you use your own settings without importing a project profile.

## Print profile and verification

The 3MF projects contain A1 / standard 0.4 mm nozzle settings, Generic PLA, Textured PEI Plate, 0.16 mm High Quality layers, 3 wall loops, 12% gyroid infill, 5 top layers, 4 bottom layers, and supports off. The flat base is already on the bed. Open the file as a project and choose the filament and plate you actually use, then slice again if you change the settings. No print has been sent to the printer.

All six STLs were reloaded from disk and checked for a single connected solid, watertightness, consistent winding, positive volume, zero boundary/nonmanifold edges, flat Z=0 placement and A1 bed fit. All four projects were actually sliced using Bambu Studio 02.08.02.61. Every slice returned `Success.` with no plate warning message and all objects inside the bed. Print time/material figures above are slicer estimates; a physical print has not been tested.

The modeled tower has deliberately thickened piers and approximately 0.83 mm pinnacle caps for the standard nozzle. Its recesses are backed by solid walls. Roof and tower details below the source data's resolution are interpretations, not measured geometry.

## What the parallel work established

- **EA LiDAR works without a key.** The official numerical WCS supplied a 1 m DSM GeoTIFF. The local source survey is dated 15 March 2020, included in the 2022 composite. Correct 5 km tile: **SP50NE**, correcting the tentative SP50NW in the original README. At this model scale, 1 m is 1.56 mm, which explains the softened details. [Acquisition, source evidence and builder](approaches/lidar/README.md).
- **Architectural modeling is viable.** The actual OSM plan supplies 27 named polygons; roof heights are calibrated from the DSM. Roof pitch/eaves and the tower details are estimated using the official college map, photographs and heritage references. [Assumptions, sources and builder](approaches/architectural/README.md).
- **The hybrid is also viable.** Roof triangles are clipped to the mapped buildings; outside vegetation and neighboring fragments are removed. A 14.8 m region around the tower is modified to remove the spread of the old DSM tower before inserting the reconstruction. [Exact processing](approaches/hybrid/metadata.json) and [builder](approaches/hybrid/build_hybrid.py).
- **Existing city models remain an optional fourth comparison.** The free [MakerWorld Oxford model](https://makerworld.com/en/models/2574076-dream-university-prestigious-university-map-oxford#profileId-2838133) needs a MakerWorld/Bambu login to download. Its photograph appears to cover Merton, but the actual mesh detail is unverified. Download its **3MF** through the green button's dropdown and save it into this workspace to enable a personal Merton crop. The paid [Micropolitan Oxford](https://thangs.com/m/1254135) requires membership; no purchase was made. [Research and evidence](approaches/existing/RESEARCH.md).
- **A Google API key is not the useful next step.** Standard Google Map Tiles policies/terms restrict the extraction/export needed for a saved printable model. The original README's “gray area” wording should not be treated as permission. Official policy links are in the existing-model report.

The raw relief subtracts its measured minimum elevation (56.0105 mOD). The architectural and hybrid versions use an estimated flat 59 mOD ground datum. This changes apparent building height by approximately **4.66 mm**, even at the same scale. The clean variants intentionally remove local terrain variation. Trees or artifacts over a mapped roof can remain in the hybrid.

## Reproduce locally

The source snapshots and builders are included. From this folder, with `uv` installed:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python approaches/lidar/build_lidar.py
.venv/bin/python approaches/architectural/build_architectural.py
.venv/bin/python approaches/hybrid/build_hybrid.py
.venv/bin/python scripts/package_candidates.py
.venv/bin/python scripts/prepare_profiles.py
.venv/bin/python scripts/slice_candidates.py lidar architectural hybrid samples
.venv/bin/python scripts/inspect_mesh.py deliverables/*.stl deliverables/chapel-samples/*.stl --output validation/final_meshes.json
```

These normal builds use frozen data. The profile/slicing scripts require the installed macOS Bambu Studio path recorded in them. They only export local files; they do not contact a printer. `scripts/build_comparison.py` generates the reduced interactive preview from the actual full-resolution masters; the print meshes themselves are not decimated. Validation JSON, slicer logs and project thumbnails are retained in [validation](validation/).

## Source attribution

Environment Agency DSM: © Environment Agency copyright and/or database right 2022. All rights reserved. Available under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). [Official dataset](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178).

Mapped footprints: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The frozen and derived footprint data are included in the architectural approach directory. Preserve attribution with derived copies. College reference images and commercial-listing previews retain their original copyrights and are kept separately as research evidence, outside the print bundle.
