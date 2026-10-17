# Measured LiDAR relief prototype

`merton_lidar_220mm.stl` is a printable, closed relief of Merton College's historic core made from the Environment Agency's actual 1 m last-return DSM. It uses the same crop, coordinate frame, 220 mm long edge and 3 mm base as the architectural comparison.

The STL is **220 × 207.518 × 58.790 mm**, at about **1:641** without vertical exaggeration. X points east, Y north and Z up. The rectangular crop is EPSG:27700 **[451665, 206000, 451806, 206133]**. A 1 m source pixel spans **1.56 mm** on the print, so the roof massing is real but tower pinnacles, tracery, vertical windows and sharp building walls are not resolved. Small pieces of neighbouring buildings at the crop edges, ground irregularities and vegetation remain visible.

Mesh verification passed both before export and after reloading the STL: one connected component, watertight, consistent winding, positive volume, Euler characteristic 2 and no degenerate triangles. There are 39,150 triangles. The minimum thickness below the lowest measured height is 3 mm. The heightfield creates no overhangs; base-down printing is the intended orientation. Root-level slicer outputs provide the Bambu A1 validation and print settings.

## Files

- `merton_lidar_220mm.stl` — millimetres, printable relief.
- `preview_lidar.png` — rendered view of the actual mesh.
- `crop_hillshade.png` — measured crop viewed from above, north up.
- `context_hillshade.png` — wider context used to identify the correct site.
- `merton_dsm_crop.tif` — unchanged raster cells within the final crop, for GIS inspection.
- `raw_dsm_grid.npz` — grid registered to the exact shared crop boundaries, used by the hybrid model.
- `metadata.json` — provenance, crop, units, scale, limitations, hashes and mesh checks.
- `build_lidar.py` — reproducible acquisition, crop, registration, meshing and preview generation.
- `raw/` — original official GeoTIFF, request details, metadata page, WCS capability/coverage descriptions and coverage-index responses.

## Reproduce

From the repository root, with the prepared Python environment:

```sh
.venv/bin/python approaches/lidar/build_lidar.py
```

The checked-in source file is sufficient; no account or API key is needed. To download the numerical GeoTIFF again from the official public WCS, add `--download`. Dependencies are `numpy`, `rasterio`, `scipy`, `requests`, `trimesh`, `pyproj` and `matplotlib`.

The raw raster samples heights at half-metre grid centres. The shared model boundaries lie at whole metres. The script therefore samples bilinearly at whole-metre vertices, using the original 1 m spacing, then closes that surface with vertical sides and a planar bottom. This introduces the stated half-cell registration interpolation, with no further smoothing, roof editing, height exaggeration or vegetation removal. No elevations are invented to fill gaps; the build stops if the source contains missing values.

`raw_dsm_grid.npz` contains `x_bng_m` (142 values), `y_bng_m` (134 values), `z_elevation_m` and `z_height_mm` (134 rows south to north × 142 columns west to east), plus `origin_bng_m`, `scale_mm_per_m`, `minimum_base_mm` and `datum_min_elevation_m`. Model coordinates are `(BNG - southwest crop corner) × scale_mm_per_m`. Height is `(elevation - datum_min_elevation_m) × scale_mm_per_m + 3`.

## Sources and rights

The source is the [Environment Agency LIDAR Composite Digital Surface Model (DSM) — 1 m](https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178), a 2022 composite. The [official WCS](https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-last-return-dsm-1m/wcs?request=GetCapabilities&service=WCS&version=2.0.1) supplied an actual numerical elevation TIFF, rather than a coloured map image. Retrieved 17 October 2026.

The [official coverage catalogue](https://environment.data.gov.uk/spatialdata/survey-index-files/ogc/features/v1/collections/LIDAR_Composite_1m_Last_Return_DSM_2022_extents/items?f=json&bbox=-1.256,51.748,-1.249,51.752&limit=100) identifies the underlying local survey as **15 March 2020**, National Programme 1 m DSM, polygon P_10719. The time-stamped DSM catalogue returned 1 m surveys from 2005 and 2014 here; it did not return 25 cm or 50 cm coverage. The product page describes heights in metres relative to Ordnance Datum Newlyn and the OSTN15 transformation.

The correct 5 km OS tile is **SP50NE** (E450000–455000, N205000–210000), established from the BNG location. The source was requested as a smaller 500 × 400 m WCS crop, avoiding an unnecessary full-tile download. The chapel tower is approximately E451681.6 N206079.1 within that tile; its location was independently cross-checked with the architectural model.

Use is under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Retain this source attribution with redistributed derivatives:

> © Environment Agency copyright and/or database right 2022. All rights reserved.
