> Archived starting research, preserved before the README rewrite on 17 October 2026. Some claims below were tentative or subsequently corrected. See the [current project README](../README.md) for the completed work, verified outputs, and current conclusions.

# 3D model for Merton College, Oxford

There's no ready-made printable model of Merton College. I checked the main repositories and aggregators, and nothing dedicated to it exists. You can still get a Merton print two ways: from a city-scale Oxford model that includes it, or by building one yourself, which is where you'll get the best result.

**What I checked**
- An aggregator search for "merton college" covered Thingiverse, MakerWorld, Cults3D, GrabCAD, Sketchfab and others. It returned 29 results, and none of them are the college; they're unrelated name matches like scalpel tools and board-game inserts.
- On Sketchfab, the only Merton-related model is the tomb of Bishop Walter de Merton in Rochester Cathedral, and it isn't downloadable.
- Other colleges have scans, such as SIAD Studio's Jesus, Univ and St Peter's, but they're premium Sketchfab models and not print-ready. The Radcliffe Camera has several printable models. Merton doesn't have any.

**Off-the-shelf models that include Merton**
1. **Micropolitan, "Oxford, UK – S, M, L, & XL" (Thangs).** This is the best-quality option. The maker says they use LiDAR and refine the architecture, block by block, using digital sculpting tools and satellite imagery. It's tagged with Christ Church, the Rad Cam and the Bodleian, and Merton sits between those, so it's almost certainly in frame. At city scale, though, Merton will be a small patch, a couple of centimetres across by my estimate. It requires a Thangs membership, and the maker says to scale to at least 150x150mm to preserve details.
2. **MakerWorld, "[Dream University] Oxford University" map.** It's free, multi-colour, and takes about 15.7 hours over 3 plates. The listing has no description, so I can't confirm what area it covers. Its license is a Standard Digital File License, which means personal use only.

**Building your own (the realistic route to a Merton-specific piece)**
- **Environment Agency LiDAR, for a clean relief.** The 1m composite DSM covers ~99% of England and is available as GeoTiff rasters in 5km tiles aligned to the OS National grid. There's also a 25cm composite covering areas of England. The license is clean and the pipeline is simple: crop, convert the heightmap to a mesh, add a base. The limit is that a DSM is 2.5D, so it captures massing and roof lines but no overhangs or tower tracery.
- **Google Photorealistic 3D Tiles in Blender via Blosm.** You import, crop to the Merton block, voxel-remesh, solidify, and export STL. This gives true 3D, but photogrammetry turns mushy up close, and the trees in Fellows' Garden will fuse into the buildings. Note that by using Google 3D Tiles you are bound by Map Tiles API Policies, which restrict exporting the data. A one-off personal print is a gray area.
- **Hand-modelling.** At desk scale the chapel tower is the only element that really needs detail. Mob Quad and Front Quad are essentially rectangles with pitched roofs. OSM footprints plus LiDAR heights would give you accurate massing in an afternoon.

**My recommendation:** use a LiDAR DSM relief for the site and hand-model a chapel tower to drop in. That gets you accurate geometry, clean licensing, and the one feature people actually recognise.

If you want to go that way, download the DSM tile covering Merton and attach it here; I think it's SP50NW, but confirm against the EA index. I can't reach the EA site from my workspace. Once I have the tile, I'll crop it to the college and produce a print-ready STL.

Sources:
- [STLFinder – "merton college"](https://www.stlfinder.com/3dmodels/merton-college/)
- [Micropolitan Oxford on Thangs](https://thangs.com/m/1254135)
- [MakerWorld – Dream University: Oxford](https://makerworld.com/en/models/2574076-dream-university-prestigious-university-map-oxford)
- [EA LIDAR Composite DSM 1m](https://ckan.publishing.service.gov.uk/dataset/cf3f1137-c12b-44a1-a835-e80fe4a60b92)
- [Blosm – Import of Google 3D Cities](https://github.com/vvoovv/blosm/wiki/Import-of-Google-3D-Cities)
