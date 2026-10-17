# Merton College, Oxford — three models for the Bambu Lab A1

This project turns the ideas in the original research into three printable models of Merton College's historic core: an architectural interpretation, a measured LiDAR relief, and a hybrid combining measured roofs with a reconstructed chapel tower. The approaches were developed in parallel so their results could be compared at the same scale.

**All three full models and three chapel samples passed mesh checks. Four Bambu Studio projects were sliced successfully for an A1 with the user's standard 0.4 mm nozzle.** No physical print has been tested or sent to a printer. No API keys, paid downloads, or additional modeling apps were needed.

Work and source checks were completed on **17 October 2026**. The LiDAR itself records an older survey, as explained below.

## Open or print a result

| Candidate | Bambu Studio project | Standalone mesh | What it shows | Estimated print time | Estimated PLA |
|---|---|---|---|---:|---:|
| Architectural | [A1 3MF](deliverables/merton-architectural-a1.3mf) | [STL](deliverables/merton-architectural.stl) | Real mapped building outlines, clean interpreted roofs, detailed chapel tower | 7 h 44 min | 198 g |
| Hybrid | [A1 3MF](deliverables/merton-hybrid-a1.3mf) | [STL](deliverables/merton-hybrid.stl) | Measured roof variation, mapped walls, flat ground, reconstructed tower | 8 h 23 min | 191 g |
| Measured LiDAR | [A1 3MF](deliverables/merton-lidar-a1.3mf) | [STL](deliverables/merton-lidar.stl) | Measured surface, including terrain, vegetation, survey artifacts, and edge fragments | 13 h 02 min | 243 g |
| Chapel comparison plate | [Three-sample A1 3MF](deliverables/merton-chapel-comparison-a1.3mf) | [Individual sample STLs](deliverables/chapel-samples/) | The same chapel-area crop from each candidate, at the full models' scale | 5 h 04 min | 84 g total |

These are estimates from actual local slices, rounded for readability. The exact seconds, grams, and project SHA-256 hashes are in [validation/final_projects.json](validation/final_projects.json).

The **architectural model is the cleanest first print**. Choose the hybrid if retaining the real roof variation matters more than having uniformly clean roof surfaces. Use the LiDAR model as the measured-surface benchmark. The comparison plate lets you judge the tower and nearby roofs before committing to a complete model.

The 3MFs include model geometry, saved project settings, slice output, and thumbnails. The STLs contain the geometry alone, in millimetres, for use with your own settings. Open a 3MF **as a project** in Bambu Studio, select the filament and build plate you actually use, and slice again if you change the saved configuration. Print with the flat base down.

For a shorter reference, see [RESULTS.md](RESULTS.md) or the [print notes](deliverables/PRINT-NOTES.md).

## Site coverage, scale, and coordinates

All three models share the same rectangular crop, horizontal scale, orientation, and minimum base thickness. This makes differences in the buildings easier to judge.

| Property | Value |
|---|---|
| Coordinate system | British National Grid, EPSG:27700 |
| Crop, west / south / east / north | 451665 / 206000 / 451806 / 206133 metres |
| Real-world crop | 141 × 133 m |
| Printed footprint | 220 × 207.51773 mm |
| Scale | 1.56028368794 mm per real metre, approximately 1:640.91 |
| Vertical exaggeration | None; vertical and horizontal scale are equal |
| Axes | X east, Y north, Z up |
| Origin | Southwest crop corner; model bottom at Z = 0 mm |
| Minimum base thickness | 3 mm |
| Architectural / hybrid height | 57.39149 mm |
| LiDAR height | 58.78990 mm |
| A1 build volume used for checks | 256 × 256 × 256 mm |

The selected historic buildings include the **chapel, Front Quad, Mob Quad, Fellows' Quad, St Alban's Quad, and Grove I/II**. This is a model of the historic core, rather than the entire college estate. Most gardens, modern Rose Lane buildings, and remote properties fall outside the selected scope. The LiDAR rectangle also retains whatever neighboring fragments occur within its boundaries; the architectural and hybrid variants select Merton's mapped buildings.

Horizontal coordinates map into the print as follows:

```text
s = 220 / 141 millimetres per metre
x = (E - 451665) × s
y = (N - 206000) × s
```

The variants use different ground references:

- **LiDAR:** `z = 3 + (elevation_mOD - 56.01050186) × s`. The lowest registered surface sample sets the datum, preserving measured terrain variation.
- **Architectural and hybrid:** use an estimated, flat **59 m above Ordnance Datum** ground reference. A height above that ground maps to `z = 3 + height_AGL × s`. The hybrid clamps measured values below the flat datum to the base top.

The ground-reference difference is approximately **4.66 mm in the print**. Equal scale therefore does not imply identical height above the base for a corresponding roof. The architectural and hybrid ground is a modeling assumption; no bare-earth terrain model was used for those variants. The final tower heights also differ because the LiDAR tower is sampled and interpolated, while the other two use an interpreted reconstruction.

Exact transformations are recorded in [the architectural transform](approaches/architectural/transform.json), [LiDAR metadata](approaches/lidar/metadata.json), and [hybrid metadata](approaches/hybrid/metadata.json).

## How the parallel work was organized

Three investigations ran in parallel: obtaining official LiDAR and making a relief; building from real building footprints and architectural references; and checking existing Oxford models and other acquisition routes. Once the first two produced compatible source artifacts, the existing-model investigation also produced a hybrid using both sets of data.

| Original idea | Work completed | Outcome |
|---|---|---|
| EA LiDAR relief | Downloaded a numerical DSM, identified the survey and correct tile, registered the crop, built and closed the mesh | Completed printable candidate |
| OSM footprints plus architectural modeling | Selected actual Merton polygons, estimated roofs, reconstructed the chapel tower, united everything with a base | Completed printable candidate and reusable tower |
| LiDAR roofs plus reconstructed tower | Clipped measured roof triangles to mapped buildings, removed the old tower's spread locally, inserted the reconstruction | Completed hybrid candidate |
| Crop an existing Oxford city model | Inspected MakerWorld and Thangs listings, previews, account gates, and usage terms | Awaiting an authorized local download; no third-party mesh was obtained |
| Google Photorealistic 3D Tiles through Blosm | Reviewed the technical route and standard Google content restrictions | Not pursued as a printable-mesh source under those terms |
| Other scans or photogrammetry datasets | Checked Sketchfab and Oxford VGG Merton data | No complete downloadable college mesh found in the material checked |

The following sections describe the completed construction and research in detail.

## 1. Measured Environment Agency LiDAR relief

### Acquisition and source checks

The source is the official [Environment Agency LIDAR Composite Digital Surface Model, 1 m](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178). A DSM records the upper surface, including roofs and vegetation, rather than just bare ground.

The public [WCS service](https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-last-return-dsm-1m/wcs) returned a numerical elevation GeoTIFF without an account or key. The request used WCS 2.0.1, `GetCoverage`, TIFF output, and this coverage identifier:

```text
9ba4d5ac-d596-445a-9056-dae3ddec0178__Lidar_Composite_Elevation_LZ_DSM_1m
```

A **500 × 400 m context raster** was requested at BNG bounds `[451450, 205750, 451950, 206150]`. It provides enough surrounding geography to identify the college and contains the final crop. This avoided downloading an entire 5 km tile. The numerical raster, request, dataset page, service capabilities, coverage description, and survey-index responses are retained in [approaches/lidar/raw](approaches/lidar/raw/).

The product is the **2022 composite**, but the coverage catalogue identifies the local underlying survey as **15 March 2020**, National Programme, polygon `P_10719`. Heights are in metres relative to Ordnance Datum Newlyn. The catalogue checked did not establish usable 25 cm or 50 cm coverage here; the delivered models use the verified 1 m product.

The correct 5 km tile is **SP50NE**, covering E450000–455000 and N205000–210000. This corrects the tentative SP50NW suggestion in the starting research. The original statement that the EA data could not be reached was also superseded: direct WCS acquisition worked.

### Registration and mesh construction

[build_lidar.py](approaches/lidar/build_lidar.py) performs these steps:

1. Read the frozen source TIFF, or download it when requested or missing.
2. Check that the requested crop lies inside the source and that the source crop has no missing or nonfinite heights.
3. Save the unmodified raster cells covering the crop as [merton_dsm_crop.tif](approaches/lidar/merton_dsm_crop.tif).
4. Register heights to whole-metre vertices on the exact shared crop boundaries. Native raster cell centres lie at half-metre coordinates, so this uses bilinear interpolation at the original 1 m spacing.
5. Triangulate the registered surface, add vertical perimeter walls, and close the underside at Z = 0. The lowest measured sample has 3 mm of material beneath it.
6. Export the STL, reload it, check its integrity again, and save metadata and previews.

The shared registered grid has **142 east–west vertices × 134 south–north vertices**. [raw_dsm_grid.npz](approaches/lidar/raw_dsm_grid.npz) stores the BNG axes, elevation and model-height arrays, scale, origin, minimum base, and datum. Rows run south to north. The hybrid consumes this same grid, so its roof triangles begin with the same registered surface.

There is **no further smoothing, vegetation removal, invented roof detail, or height exaggeration** in this candidate. Registration interpolation does soften peaks: the raw tower sample used to inform the reconstruction reaches 93.904 mOD, while the registered relief peaks at 91.76675 mOD. One real metre occupies 1.56 mm on the print, which limits the detail available from this source regardless of mesh density.

### Result and limitations

The final relief has **39,150 triangles** and is one closed, consistently wound solid. It preserves measured roof massing, terrain variation, vegetation, and survey artifacts. It is a heightfield, often called **2.5D**: each plan position has one height. It cannot recover vertical facade windows, undercuts, overhangs, or tower tracery.

The [crop hillshade](approaches/lidar/crop_hillshade.png) and [wider context hillshade](approaches/lidar/context_hillshade.png) support site identification. The [approach README](approaches/lidar/README.md) and [metadata](approaches/lidar/metadata.json) contain the detailed source and mesh records.

## 2. Architectural model from mapped footprints

### Ground plan and references

The plan comes from OpenStreetMap, rather than a set of invented courtyard rectangles. The canonical [OSM map API request](https://www.openstreetmap.org/api/0.6/map?bbox=-1.2555,51.7494,-1.2495,51.7521) worked after the Overpass route failed. The original XML and converted feature records are frozen in [the source directory](approaches/architectural/sources/).

**27 selected building polygons** are stored in [building_footprints.geojson](approaches/architectural/building_footprints.geojson), with OSM identifiers, tags, metric geometry, names, and roof parameters. Selection used Merton names and operator tags. The footprint gaps become open courtyards on a flat base.

Identification and interpretation used these references:

- [Merton's official site map](https://www.merton.ox.ac.uk/conference-welcome-and-guest-information), including the [map image](https://www.merton.ox.ac.uk/api/images/file/map.png), to identify building ranges and compare the overall arrangement.
- [The college's chapel history](https://www.merton.ox.ac.uk/history-merton-college-chapel), to preserve the chapel's actual T-shaped plan. No unbuilt nave was added.
- [Historic England entry 1199994](https://historicengland.org.uk/listing/the-list/list-entry/1199994), including the legacy chapel grid reference SP 51680 06079.
- [The college's chapel photograph](https://www.merton.ox.ac.uk/api/images/file/Chapel.jpg), for tower proportions and the placement of broad architectural features.
- [Wolfson College's account of the Merton pinnacle](https://www.wolfson.ox.ac.uk/7-the-merton-pinnacle/), which identifies the set of eight original pinnacles.

The photographs and illustration are reference material, not geometry extracted into the mesh. Frozen images, a named footprint plan, and the chapel-to-DSM alignment image are included in the source directory.

### Walls and roofs

[build_architectural.py](approaches/architectural/build_architectural.py) extrudes the mapped polygons and constructs simple roofs aligned to each range. Ordinary ridge estimates use the **90th percentile of DSM samples inside a 0.6 m-inset footprint**, less the estimated 59 mOD flat ground. Eaves are inferred using a nominal **34-degree pitch**. These are working roof estimates, not surveyed ridge and eave measurements.

The chapel uses separately oriented choir and transept gables, with interpreted eaves at **13 m above ground** and ridges at **19.8 m**. The L-shaped Mob library is split into its two ranges. The lodge/gatehouse has an interpreted **17.2 m** height and a flat top. Ordinary gables follow the range's minimum oriented rectangle while retaining the mapped outline.

The finished base is flat and 3 mm thick. Dormers, chimneys, most windows, doors, paths, trees, furnishings, and detailed garden walls are omitted. Gate passages remain closed for a robust initial print. Roof intersections and small overlaps were adjusted during construction, followed by a final rebuild and slice.

### Chapel crossing tower

The tower is a deliberate small-scale reconstruction and is shared with the hybrid. Its main parameters are:

| Parameter | Value |
|---|---:|
| Centre | E451681.6, N206079.1 |
| Rotation | 13.88° north of east |
| Main body width | 10.8 m square |
| Main parapet height above estimated ground | 29.35 m |
| Pinnacle top height above estimated ground | 34.86 m |
| Number of pinnacles | 8 |
| Smallest modeled pinnacle cap in the print | Approximately 0.83 mm |
| Thickened decorative piers in the print | Approximately 1.87 mm |

Its centre was checked against the OSM plan and the DSM tower plateau. The body has paired pointed belfry recesses, projecting string courses, corner and mid-face piers, a simplified crenellated parapet, and stepped pinnacles. The recesses have solid backing. Fine tracery, crockets, crosses, gargoyles, and thin open balustrades were omitted. Widths and ledges were adjusted for the 0.4 mm nozzle.

The tower's silhouette and details are interpretations informed by the photographs and height data. They are not a measured reconstruction of every architectural feature. The reusable [chapel_tower_component.stl](approaches/architectural/chapel_tower_component.stl) is already in the full shared model coordinate frame, with a small overlap into the base for Boolean union; it is an assembly input rather than a separately arranged print.

The completed architectural mesh has **4,352 triangles**. The Boolean cleanup removed tiny numerical shells totaling approximately **0.000182 mm³**, as recorded in [validation.json](approaches/architectural/validation.json). The exported model is one connected solid. The [approach README](approaches/architectural/README.md) records the architectural assumptions in full.

## 3. Hybrid: measured roofs, mapped boundaries, reconstructed tower

The hybrid tests the recommendation in the initial research: keep useful measured roof geometry and replace the chapel tower with something more recognizable and printable. It also removes terrain and objects outside the selected building outlines.

[build_hybrid.py](approaches/hybrid/build_hybrid.py) combines three frozen inputs:

- The registered LiDAR grid from the relief approach.
- The 27 selected OSM footprint polygons from the architectural approach.
- The aligned architectural tower component.

The processing is deliberately local and documented:

1. Union the selected building polygons and expand the boundary by **0.01 m** to resolve point-touch junctions.
2. Clip each measured 1 m roof triangle continuously against that boundary. New clipped vertices lie on the source triangle's plane, retaining measured slopes rather than substituting general gables.
3. Remove the old DSM tower's spread around the replacement. Inside a **14.8 m square**, rotated with the tower, source values above **78.8 mOD** are capped at that chapel-ridge elevation. This modifies **137 grid vertices** and prevents a rounded scan rim from remaining around the reconstructed tower.
4. Cut out the replacement tower footprint with a **0.05 m overlap** allowance and insert the reusable tower.
5. Use the common 59 mOD flat-ground reference, close the footprint boundaries with vertical walls extending into the base, and union the solids with `manifold3d`.
6. Merge numerical seams at **0.000001 mm** precision. Fill two sealed internal cavities at the union, totaling **12.30 mm³**, without changing the exterior.
7. Export and reload the STL, verify it, and save the processing record and previews.

The final hybrid has **16,042 triangles** and is one connected watertight solid. The [processed roof grid](approaches/hybrid/processed_roof_grid.npz), [roof mask](approaches/hybrid/roof_mask.geojson), [mask image](approaches/hybrid/footprint_mask.png), and [metadata](approaches/hybrid/metadata.json) make the intervention inspectable. Metadata also records hashes of its three inputs.

Outside the tower transition, the method retains source roof planes, subject to clipping and the flat-ground clamp. It does not smooth all roofs or recover facade detail. Vegetation and neighboring structures outside mapped footprints disappear; canopy or artifacts above a mapped roof can remain. Roof-edge falloff and coarse sampling can still look rougher than the architectural version.

## 4. Existing-model and alternative-source research

The detailed report, saved listing text, account-gate screenshots, preview sources, and search results are in [approaches/existing/RESEARCH.md](approaches/existing/RESEARCH.md). No third-party mesh was downloaded, no membership was purchased, and no external model was incorporated into the completed outputs.

### Free MakerWorld Oxford model

The strongest available next comparison is the [Dream University Oxford city model, model 2574076 / profile 2838133](https://makerworld.com/en/models/2574076-dream-university-prestigious-university-map-oxford#profileId-2838133). Direct HTTP retrieval returned 403, but inspection in an ordinary browser worked and confirmed that downloading requires a login.

The public photograph appears to include the Merton block east of Christ Church, above the meadow. This is an inference from visible geography; the actual file's Merton coverage and architectural detail remain unverified. Enlarging a city-scale crop would not add details absent from its mesh.

The listing advertises approximately 15.7 hours over three plates, with a 0.4 mm nozzle, 0.2 mm layers, two walls, and 15% infill. Those are listing settings for other printer profiles, **not a verified A1 estimate for a Merton crop**.

To enable this comparison, sign in with a MakerWorld/Bambu account, use the green button's dropdown to select **Download 3MF**, and put the file in this workspace. That would allow inspection, geographic registration, a personal Merton crop, and a separate A1 slice. The displayed Standard Digital File License restricts redistribution and commercial use, including derivatives; retain the downloaded file and any personal crop separately from these open-data outputs.

### Paid Micropolitan Oxford model

[Micropolitan's Oxford, UK — S, M, L, & XL](https://thangs.com/m/1254135) requires a Thangs membership. Its public preview covers central Oxford and geographically appears to include Merton's area. The creator describes a LiDAR-based process with architectural refinement, but the mesh itself was unavailable for inspection. The initial claim that this is definitely the best-quality option was therefore not established.

A future comparison would require an authorized download of the relevant STL files and sizing PDF under appropriate membership terms. No current price or exact per-file extent was confirmed during this work.

### Google Photorealistic 3D Tiles and Blosm

The research reviewed [Blosm's import setup](https://github.com/vvoovv/blosm/wiki/Import-of-Google-3D-Cities), which uses Blender, the add-on, a Google Cloud project with billing, the Map Tiles API, and a key. It also reviewed the [Map Tiles API policies](https://developers.google.com/maps/documentation/tile/policies) and [Google Maps Platform terms, section 3.2.3](https://cloud.google.com/maps-platform/terms).

The standard restrictions on extraction, storage, offline use, and derived content make this unsuitable for the saved printable-mesh route considered here without separate permission covering that use. The starting README's description of a personal print as a “gray area” was not treated as permission. No Google key was requested and no Google mesh was extracted. A key would enable API access, but would not resolve the content-use restriction identified in the research.

### Sketchfab and Oxford VGG

The saved Sketchfab search contained Walter de Merton's tomb and unrelated Merton-named objects, but no complete downloadable model of the Oxford college was found. This is a result of the material checked, not proof that no private or institutional scan exists.

[Oxford VGG's multiview dataset](https://www.robots.ox.ac.uk/~vgg/data/mview/) includes Merton College I, II, and III. The sets contain three ground-level photographs, sparse reconstructed points or lines, and camera information. They are not a complete textured college mesh or closed printable solid, so they were not used as the main reconstruction source. A new survey or an all-around photography campaign remains a separate acquisition route.

## Chapel comparison samples

[package_candidates.py](scripts/package_candidates.py) copies the final full-resolution masters into `deliverables/` and intersects each with the same **35 × 40 m** chapel-area box: BNG `[451668, 206060, 451703, 206100]`. It closes the cut through a solid intersection and translates each sample to a local origin.

Each sample is **54.60993 × 62.41135 mm** and retains the full model's approximately 1:641 scale and tower height. These are smaller geographic crops, not scaled-down models. Their edges intentionally cut through surrounding roofs.

The [comparison 3MF](deliverables/merton-chapel-comparison-a1.3mf) arranges all three samples on one A1 plate. Objects are named for their source model; delete two in Bambu Studio to print just one. [samples.json](deliverables/chapel-samples/samples.json) records the crop, dimensions, and unchanged scale.

## A1 profiles, slicing, and validation

### Saved print configuration

The installed **Bambu Studio 02.08.02.61** supplied the A1 presets. [prepare_profiles.py](scripts/prepare_profiles.py) resolves inherited presets and included G-code settings into standalone JSON files under [settings](settings/). It starts with `Bambu Lab A1 0.4 nozzle`, `0.16mm High Quality @BBL A1`, and `Generic PLA @BBL A1`.

| Setting | Saved value |
|---|---|
| Printer / nozzle | Bambu Lab A1 / 0.4 mm |
| Filament | Generic PLA |
| Build plate | Textured PEI Plate |
| Process preset / nominal layer height | 0.16 mm High Quality / 0.16 mm |
| Wall loops | 3 |
| Infill | 12% gyroid |
| Top / bottom shell layers | 5 / 4; inherited shell-thickness constraints also remain in the preset |
| Supports | Off |
| Brim | No brim |
| Orientation | Flat base down; automatic reorientation disabled |

The plate selection was explicitly corrected to Textured PEI before the final slices. Choose a different plate or filament in Bambu Studio if appropriate to your setup; the saved profile is a reproducible starting point. The broad base and thickened details were designed around this nozzle, but only a physical print can establish adhesion and fine-detail quality.

### Geometry checks

[inspect_mesh.py](scripts/inspect_mesh.py) reloads the exported STLs and checks finite coordinates, watertightness, consistent winding, positive signed volume, boundary and nonmanifold edge counts, connected components, Z = 0 placement, and fit within the configured A1 volume. It records a SHA-256 hash for each file. This inspection does not perform Boolean repairs or fill holes to hide a failure.

All **six delivered STLs** passed: each has one connected component, zero boundary edges, zero nonmanifold edges, a flat bottom, and dimensions within the A1 limits. The LiDAR and hybrid builders additionally check degenerate triangles. The full-resolution model statistics are:

| Model | Vertices | Triangles | Height | Enclosed mesh volume |
|---|---:|---:|---:|---:|
| Architectural | 2,166 | 4,352 | 57.39149 mm | 334,762.726 mm³ |
| Hybrid | 8,013 | 16,042 | 57.39149 mm | 312,368.230 mm³ |
| LiDAR | 19,577 | 39,150 | 58.78990 mm | 575,641.491 mm³ |

These enclosed volumes describe the mesh solids, not the quantity of plastic after infill. The definitive delivered-mesh record is [validation/final_meshes.json](validation/final_meshes.json).

### Actual slicer checks

[slice_candidates.py](scripts/slice_candidates.py) invokes the installed Bambu Studio command-line interface for all three full models and the sample plate. It loads the frozen machine, process, and filament settings; arranges objects; preserves their orientation; slices; and exports the 3MFs locally.

For each project, validation checked successful completion, the A1 printer identity, the 0.4 mm nozzle, Textured PEI selection, supports disabled, embedded plate G-code, and arranged object bounds inside the 256 mm bed. Final project inspection also checked ZIP integrity, empty plate warning messages, and that the packaged mesh corresponded to the current final STL rather than an earlier iteration.

All four final slices returned **`Success.`**, with no plate warning message. Bambu Studio emitted some nonfatal internal Voronoi messages while processing the raw relief; these did not prevent a successful final slice. The logs and result JSON remain available for inspection. Slicer success is evidence that the projects can be processed with these settings, rather than a guarantee of physical print quality.

Two command-line details were resolved during setup: presets needed their inheritance and includes expanded, and `--export-3mf` needed a filename alone with a separate absolute `--outputdir`. The final slicing script incorporates both fixes. After the last architectural refinements, the dependent outputs were repackaged and sliced again so the final projects and hashes match the delivered meshes.

Each `validation/<candidate>_slice/` directory contains the result JSON, exported project, and an actual slicer thumbnail. Logs are `validation/<candidate>_slice.log`. [final_projects.json](validation/final_projects.json) is the aggregate final audit snapshot. Earlier candidate/probe records are retained for development history; use the files named `final_*` for the delivered state.

## Interactive comparison and visual inspection

An interactive Three.js viewer was built from the **actual STL meshes**. It supports switching between the three candidates, dragging to rotate, wheel zoom, a three-quarter view, and a north-up overhead view. The common crop and scale make surface and tower differences directly comparable. It uses a common neutral material and lighting, theme-aware styling, and saves the selected model/view through the host's widget-state interface.

[build_comparison.py](scripts/build_comparison.py) embeds the geometry in [comparison-template.html](scripts/comparison-template.html). For the preview only, meshes above 15,000 triangles are reduced, positions are quantized to 0.01 mm, and the arrays are embedded as base64. The resulting fragment is approximately **422 KB**, below the 1 MB limit, and does not fetch model data. The Three.js runtime is loaded from a CDN. **The printable STLs and 3MF geometry are not decimated by this preview process.**

The interactive fragment is saved outside this repository in the local Codex visualization workspace:

```text
/Users/haroldmartin/.codex/visualizations/2026/10/17/01a14a44-aa91-7021-9dc1-1c327945b1b1/merton-models.html
```

A browser wrapper is retained at [validation/comparison-preview.html](validation/comparison-preview.html), with a [browser screenshot](validation/comparison-browser.png). The viewer was opened and exercised in the browser: candidate switching, rotation, zoom, and overhead framing were checked, and an overhead clipping issue was corrected. The temporary local preview server and browser tab were closed after verification. The viewer was not published as a website.

The architectural approach also has depth-buffered [northwest](approaches/architectural/preview_northwest.png) and [southeast](approaches/architectural/preview_southeast.png) renders. The LiDAR and hybrid folders retain static plotting previews and inspection images. Use the interactive mesh viewer or Bambu Studio when judging occlusion and geometry; static plotting previews can have rendering limitations.

## Repository guide

```text
README.md                       Detailed project record and usage
RESULTS.md                      Shorter results and reproduction summary
docs/initial-research.md        Archived starting README, with superseded claims
requirements.txt                Pinned Python dependency versions
approaches/
  lidar/                        Official raster, shared grid, relief builder and master
  architectural/                OSM data, roof parameters, tower, builder and master
  hybrid/                       Clipped roofs, mask, processing record, builder and master
  existing/                     External-model research and public listing evidence
deliverables/
  merton-*.stl                  Three full-resolution printable meshes
  merton-*-a1.3mf               Three sliced A1 projects and the sample project
  chapel-samples/               Three full-scale chapel crops and their metadata
  PRINT-NOTES.md                Brief opening and printing instructions
scripts/
  package_candidates.py         Copy masters and construct sample crops
  prepare_profiles.py           Flatten installed A1 presets into settings JSON
  slice_candidates.py           Slice and export local A1 projects
  inspect_mesh.py               Inspect delivered geometry and record hashes
  build_comparison.py           Embed reduced preview geometry
  comparison-template.html      Interactive comparison interface
settings/                       Frozen machine, process, and filament presets
validation/                     Final audits, slice results, thumbnails, preview evidence
```

The local `.venv` contains the installed modeling environment. `.gitignore` excludes it, Python caches, generated standalone plate G-code, and temporary profile probes. Reference photographs and commercial-listing previews are kept with their research sources, outside the printable deliverables.

## Reproduce the work

### Environment

The work used Python 3.13 in a project-local virtual environment managed with `uv`. [requirements.txt](requirements.txt) pins the installed versions. The principal tools are NumPy/SciPy for sampled data, Rasterio/PyProj for geospatial data, Shapely for footprints and clipping, Trimesh/Manifold3D/Earcut for meshes and solid operations, and Matplotlib/Pillow for inspection images. `fast-simplification` supports the reduced preview. The frozen environment also includes `lib3mf` and supporting libraries.

From the project root, create the environment if it does not already exist:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

### Rebuild models, samples, and geometry checks

Run these in order. The hybrid depends on outputs from the first two builders.

```sh
.venv/bin/python approaches/lidar/build_lidar.py
.venv/bin/python approaches/architectural/build_architectural.py
.venv/bin/python approaches/hybrid/build_hybrid.py
.venv/bin/python scripts/package_candidates.py
.venv/bin/python scripts/inspect_mesh.py deliverables/*.stl deliverables/chapel-samples/*.stl --output validation/final_meshes.json
```

With the supplied frozen inputs present, these normal model builds do not require accounts, keys, or a network connection. The architectural build uses the saved GeoJSON roof parameters, rather than recomputing heights every time. Rebuilding overwrites generated artifacts; preserve any manually edited variants separately. The workflow is reproducible from its inputs, although byte-identical mesh output can depend on library and platform behavior.

### Rebuild A1 projects

The scripts currently use these macOS paths:

```text
Bambu Studio executable:
/Applications/BambuStudio.app/Contents/MacOS/BambuStudio

Bundled BBL presets:
/Applications/BambuStudio.app/Contents/Resources/profiles/BBL
```

To slice with the supplied frozen `settings/` files:

```sh
.venv/bin/python scripts/slice_candidates.py lidar architectural hybrid samples
```

To regenerate those settings from the installed Bambu Studio first:

```sh
.venv/bin/python scripts/prepare_profiles.py
.venv/bin/python scripts/slice_candidates.py lidar architectural hybrid samples
```

Regenerating settings uses the presets in the installed version, so a different Bambu Studio release can change the profile and estimates. On another OS or installation, update the executable/preset paths in the scripts. These commands only create local output files and do not submit a print.

`slice_candidates.py` updates per-candidate slice results and deliverable projects. The aggregate `validation/final_projects.json` is a final audit snapshot, not automatically regenerated by that script; refresh its hashes and figures if delivering a new revision.

### Refresh source data or estimates

To re-request the official numerical raster:

```sh
.venv/bin/python approaches/lidar/build_lidar.py --download
```

This replaces the frozen source TIFF and records a new request. It may change the output if the public composite changes. Rebuild the dependent models and validation afterward.

To recompute architectural roof parameters from the frozen OSM features and EA context raster:

```sh
.venv/bin/python approaches/architectural/build_architectural.py --freeze-parameters
```

This updates the derived GeoJSON parameters and rebuilds the architectural mesh. Rebuild the hybrid, samples, and projects afterward. OSM re-acquisition itself was an investigation step; the builder is not an automatic live OSM updater.

The LiDAR builder also exposes `--bbox`, `--long-edge-mm`, and `--base-mm`. The other builders and sample packager currently contain the agreed crop and scale as constants, so changing only the LiDAR arguments would break the shared comparison. Update all dependent transforms together for a different site extent or size.

### Rebuild the interactive preview

```sh
.venv/bin/python scripts/build_comparison.py
```

The visualization output directory is currently an absolute local path in that script. Change it when moving the project. The generated file is a host visualization fragment; `validation/comparison-preview.html` is the retained standalone browser wrapper from visual QA. The normal model/slicing workflow does not need the visualization runtime.

## Remaining decisions and possible follow-up work

The completed comparison is ready for a first physical test. The smallest useful next step is to print one chapel sample, or all three, and judge pinnacle strength, roof texture, and layer visibility using the actual filament and plate. A successful slice does not establish those results.

Further work could include refining the preferred candidate from better architectural measurements; adding selected windows, chimneys, dormers, or passages where they remain printable at this scale; obtaining a higher-resolution authorized survey; or expanding the site through a coordinated change to every builder's crop. A different scale or nozzle would require another detail and slice review.

The optional fourth comparison remains the authorized MakerWorld city-model crop. It requires the actual downloaded 3MF before coverage, geometry quality, and an A1 estimate can be established. No app or API-key setup is pending for the three completed models.

## Attribution, rights, and research history

**Environment Agency:** © Environment Agency copyright and/or database right 2022. All rights reserved. The [official DSM](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178) is available under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Its numerical data inform all three candidates. Preserve the attribution with derived copies.

**OpenStreetMap:** © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), with source and derived footprint data under [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The original XML, converted source records, and selected derived polygons are included for provenance and reproducibility. Preserve attribution when sharing the footprint-derived work and retain the accompanying source/licence information.

**Reference material:** the Merton illustration, college photographs, and third-party listing previews retain their original copyrights. The official map identifies © Merton College 2010, Jeremy Bower. These materials were retained as research evidence and are not granted the open-data licences of the geometry sources. Commercial model licences are separate; no such mesh is part of these deliverables. This README does not assign a new blanket licence to every file in the repository.

The [starting README is archived](docs/initial-research.md) to preserve the original ideas. This project corrected or qualified several of its claims: EA access worked, the tile is SP50NE, no complete-model search can establish universal absence, Micropolitan's relative quality remains unverified, MakerWorld's Merton detail awaits a real file, and a Google API key does not by itself authorize the proposed extraction. The completed outputs, final validation records, and source-specific reports above are the record of what was actually built and checked.
