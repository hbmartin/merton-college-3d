# Merton College A1 candidates

## Freestanding detailed model — print launched 17 October 2026

Open **[merton-detailed-freestanding-a1.3mf](merton-detailed-freestanding-a1.3mf)** as a project in Bambu Studio. The matching [STL](merton-detailed-freestanding.stl) has the 3 mm site slab removed. Three connected building groups stand directly on Z = 0, with the original scale and relative positions retained and the courtyards open. Overall dimensions are **203.96 × 189.81 × 55.18 mm**.

The saved setup uses an **A1, 0.4 mm nozzle, Generic PLA and Textured PEI Plate**, with:

- **12% gyroid infill and three walls**, as selected by the user, to balance material, rigidity and print time.
- **0.12 mm layers and Arachne walls** for the architectural details.
- **Manual tree supports painted only beneath the four projecting oriel bays**. The 67 selected underside triangles are recorded in `validation/support_refinement/targeted_contacts.json`; mullions, tracery and shallow window trim are left free of support contacts. Supports start on the build plate, with **0.5 mm XY clearance and 0.24 mm top Z clearance**.
- A **removable 3 mm outer brim**, separated by a 0.1 mm gap, and **no raft**. The brim is a first-layer adhesion aid; there is no modeled base plate.

Bambu Studio sliced the project successfully: approximately **12 h 37 min and 109.24 g PLA**, including supports and brim. The support estimate fell from **29.08 g to 0.30 g** after replacing broad automatic support generation with four targeted underside regions. The editable project is saved separately from the **[sliced plate file](merton-detailed-freestanding-a1.gcode.3mf)**. The mesh has 295,512 triangles, three watertight positive-volume components, no boundary/nonmanifold edges, and all three bottoms at bed level. Support refinement does not change the model geometry.

After explicit authorization on **17 October 2026**, the final job was sent to A1 **`3DP-039-180`**, using **PLA from AMS slot A1**, with **auto bed leveling and flow dynamics calibration enabled** and **timelapse disabled**. The transfer completed, and the printer reported **Heatbed preheating, 0%, layer 0/459**; the displayed finish estimate was **22:16 America/Los_Angeles** that day. This records the verified launch, not a live status or completed-print result. See the [README](../README.md#freestanding-print-preparation-and-support-refinement) for the full workflow.

To reproduce from the repository root, run `.venv/bin/python scripts/prepare_freestanding.py`, then `.venv/bin/python scripts/slice_candidates.py detailed-freestanding`, then `.venv/bin/python scripts/refine_window_supports.py`. Open the resulting project in Bambu Studio, re-slice, and export the plate sliced file. The final script is required: the preliminary command-line slice uses the older automatic supports. The base cut includes an additional 0.01 mm clearance to eliminate coincident slab faces.

Geometry checks are in [freestanding_mesh.json](../validation/freestanding_mesh.json); final settings, hashes, support-toolpath checks and the launch observation are in [freestanding_print_project.json](../validation/freestanding_print_project.json). The final slice has no floating-region warning and stays inside the build volume. Its metadata flags traditional timelapse as unsupported. Completed-print quality is not yet verified: shallow trim and short window spans rely on the printer's overhang/bridging performance, trading some possible underside cleanup for avoiding supports attached to delicate detail. Check the first layer's adhesion. Remove the four supports from their bases and undersides after cooling, without pulling on the window mullions. For a future print, confirm the actual loaded filament and plate match the saved setup before sending the job.

## New detailed models

`merton-detailed-a1.3mf` is the new full-college model (220 × 207.52 × 58.19 mm). `merton-detailed-chapel-1-333-a1.3mf` is an enlarged standalone chapel (148.51 × 129.77 × 111.81 mm). Both have matching STLs and passed independent geometry checks.

These two projects use **0.12 mm layers, Arachne walls and automatic tree supports**, with 3 walls, 12% gyroid, Generic PLA and the A1 0.4 mm nozzle. Supports are enabled because the initial slices flagged floating regions. Choose your actual filament and plate before printing. No physical print has been tested. Fine window/tracery geometry is thickened; the model remains an architectural interpretation of the reference photographs. [Detailed source and build notes](../approaches/detailed/README.md).

## Earlier candidates

Open any `*-a1.3mf` in Bambu Studio as a project. Choose your actual filament and plate before printing. The saved profiles use an A1 with a standard 0.4 mm nozzle, Generic PLA, Textured PEI Plate, 0.16 mm layers, 3 walls, 12% gyroid and supports off. No physical print has been tested.

The full models are 220 × 207.52 mm. Architectural and hybrid are 57.39 mm tall; LiDAR is 58.79 mm tall. All are checked, connected watertight solids and have successfully sliced with the A1 profile. The chapel comparison project contains three 54.61 × 62.41 mm samples at the same scale, approximately 5 h 04 min and 84 g PLA for the entire plate.

Architectural has clean interpreted roofs and a modeled tower. Hybrid preserves measured roof variation with a clean ground and modeled tower. LiDAR is the direct measured relief, retaining terrain and survey artifacts. These are historic-core models with estimated architectural details, not complete survey models of the estate.

[Full results, estimates, source limitations and reproduction instructions](../RESULTS.md).

Source attribution: © Environment Agency copyright and/or database right 2022. All rights reserved. LiDAR available under [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Footprints © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Frozen footprint sources and model builders are supplied in the adjacent `approaches/` directory. Retain source attribution with copies.
