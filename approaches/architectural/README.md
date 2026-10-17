# Architectural interpretation — Merton historic core

A printable interpretation of the real plan of Merton College, Oxford: Chapel, Front Quad, Mob Quad, Fellows’ Quad, St Alban’s Quad, and Grove I/II. Buildings retain the OpenStreetMap ground plan. The chapel has its real T-shaped plan; the crossing tower is a deliberate small-scale reconstruction with eight pinnacles, paired pointed belfry recesses, string courses, corner/mid-face piers and a simplified crenellated parapet.

`merton_architectural_220mm.stl` is the print. `chapel_tower_component.stl` is an aligned, separate component for the hybrid approach. Both use millimetres. The full model has a 220 × 207.52 mm, 3 mm flat base; north points along +Y. Scale is approximately 1:641 with no vertical exaggeration. The common British National Grid crop is E451665–451806 / N206000–206133. `transform.json` records the exact mapping.

Print base down on the Bambu A1, with its standard 0.4 mm nozzle and PLA. Start at 0.12–0.16 mm layers, 3 wall loops, 10–15% infill and supports off. The 0.83 mm pinnacle caps, stout 1.87 mm piers, solid backed window recesses and shallow ledges are intentional print compromises. Review the slice before printing; a physical print has not been tested. A brim can help the broad base if your plate adhesion needs it.

## Reproduce

From the repository root:

```sh
.venv/bin/python approaches/architectural/build_architectural.py
```

Dependencies: numpy, trimesh, manifold3d, shapely, pyproj, mapbox-earcut, networkx. This normal build uses only the frozen local GeoJSON and does not need a network connection, an API key or the EA raster. `--freeze-parameters` regenerates the GeoJSON roof estimates from the frozen OSM data and the other approach’s EA context raster; it additionally needs rasterio.

## Evidence and assumptions

- Plan: canonical [OSM map API](https://www.openstreetmap.org/api/0.6/map?bbox=-1.2555,51.7494,-1.2495,51.7521), retrieved 17 October 2026. Frozen original XML and converted JSON are in `sources/`. Buildings selected by their actual Merton operator/name tags, not invented rectangles. `building_footprints.geojson` contains selected OSM IDs, complete OSM tags, metric polygons, named ranges and roof parameters. This is the historic main core, not the complete college estate or the modern buildings along Rose Lane.
- Identity/orientation: [official Merton site map and building illustration](https://www.merton.ox.ac.uk/conference-welcome-and-guest-information), reference image from [the college image API](https://www.merton.ox.ac.uk/api/images/file/map.png). The original illustration is © Merton College 2010, Jeremy Bower; retained as private reference. Geometry comes from OSM; the illustration was consulted to identify ranges and the tower’s silhouette.
- Chapel’s T-shaped plan and transept history: [Merton’s chapel history](https://www.merton.ox.ac.uk/history-merton-college-chapel). No unbuilt nave was added.
- Chapel position and history: [Historic England 1199994](https://historicengland.org.uk/listing/the-list/list-entry/1199994), including legacy grid reference SP 51680 06079. The tower is placed at E451681.6 N206079.1 after checking OSM against the DSM tower plateau. This is an interpretation of the crossing, not a measured survey point.
- Eight pinnacles: [Wolfson College’s account of its Merton pinnacle](https://www.wolfson.ox.ac.uk/7-the-merton-pinnacle/), describing one of eight originals. The external proportions, paired pointed belfry openings, buttress piers and parapet are simplified from the [college’s chapel reference photograph](https://www.merton.ox.ac.uk/api/images/file/Chapel.jpg). No fine tracery, crockets, crosses, gargoyles or thin balustrade openings are attempted.
- Roof heights: frozen EA 1 m composite DSM, 2020 acquisition, provided by the LiDAR approach. Each range uses the 90th percentile of samples inside a 0.6 m-inset OSM polygon minus a common 59 mOD ground datum. Inferred eaves use a nominal 34-degree pitched roof; they are not measured eaves. The chapel is treated separately, with 13 m eaves and 19.8 m ridges inferred from the choir/transept DSM, excluding the taller crossing. The gatehouse is interpreted at 17.2 m AGL. The flat base deliberately removes real ground relief.
- Tower: 10.8 m-square main body rotated 13.88° north of east, main parapet 29.35 m AGL, pinnacle tops 34.86 m AGL. Its highest DSM sample is 93.904 mOD, roughly 35 m above the common ground datum. The detailed heights, recesses, pinnacle widths, crenellations and string courses are estimated. Openings are shallow recesses and decorative piers are thickened for printing.
- Roof shapes: gables follow each range’s minimum oriented rectangle and the true footprint. The L-shaped Mob library is split into its two ranges. The chapel has separately oriented choir/transept gables. Roof pitches and intersections remain approximate; dormers, chimneys, doors and most window relief are omitted.
- Courtyards: the footprint gaps are retained and left as open, flat base. Gate passage arches are not cut through, to keep the first print robust. Vegetation, neighboring Corpus Christi buildings, paths and garden furnishings are omitted.

## Licence and provenance

OSM-derived footprints and the resulting model: ©[OpenStreetMap contributors](https://www.openstreetmap.org/copyright), available under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The frozen source and selected derived database are included for attribution and reproducibility. The height parameters also derive from Environment Agency LiDAR under the Open Government Licence v3; see the LiDAR approach’s source notes. The college reference images retain their original copyright and are not licensed as part of the generated model.

`validation.json` records mesh dimensions, watertightness, winding, connected body count, volume and minimum pinnacle width. Geometric validation does not establish architectural survey accuracy or guarantee a successful physical print.
