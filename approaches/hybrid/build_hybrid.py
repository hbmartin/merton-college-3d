#!/usr/bin/env python3
"""Clip measured EA LiDAR roofs to selected OSM footprints and add the modeled tower.

Run from the project root: .venv/bin/python approaches/hybrid/build_hybrid.py
Inputs are frozen sister-approach artifacts; no network or API key is required.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Polygon, box, mapping, shape
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
LIDAR = PROJECT / 'approaches/lidar'
ARCH = PROJECT / 'approaches/architectural'
WEST, SOUTH, EAST, NORTH = 451665.0, 206000.0, 451806.0, 206133.0
SCALE = 220.0 / (EAST - WEST)
BASE_MM = 3.0
GROUND_OD_M = 59.0  # Estimated common flat datum, not a measured terrain model.
TOWER_CENTER_BNG = [451681.6, 206079.1]
TOWER_BODY_M = 10.8
TOWER_ANGLE_DEG = 13.88
TOWER_TRANSITION_WIDTH_M = 14.8
CHAPEL_RIDGE_OD_M = GROUND_OD_M + 19.8


def checks(mesh):
    return dict(watertight=bool(mesh.is_watertight),
                winding_consistent=bool(mesh.is_winding_consistent),
                is_volume=bool(mesh.is_volume),
                connected_components=len(mesh.split(only_watertight=False)),
                euler_number=int(mesh.euler_number),
                vertices=len(mesh.vertices), triangles=len(mesh.faces),
                degenerate_triangles=int(np.count_nonzero(mesh.area_faces < 1e-10)),
                dimensions_mm=mesh.extents.tolist(), bounds_mm=mesh.bounds.tolist(),
                volume_mm3=float(mesh.volume))


def polygon_parts(geometry):
    if geometry.geom_type == 'Polygon':
        yield geometry
    elif hasattr(geometry, 'geoms'):
        for part in geometry.geoms:
            yield from polygon_parts(part)


def top_surface(mask, elevations):
    """Intersect the original 1m triangular roof surface with exact vector outlines.

    Each clipped triangle stays on its original source plane. Geometry is in local
    metres during clipping to avoid precision loss from six-digit BNG coordinates.
    """
    vertices, faces = [], []
    prepared = prep(mask)
    rows, cols = elevations.shape
    for row in range(rows - 1):
        for col in range(cols - 1):
            cell = box(col, row, col + 1, row + 1)
            if not prepared.intersects(cell):
                continue
            sw, se = elevations[row, col], elevations[row, col + 1]
            nw, ne = elevations[row + 1, col], elevations[row + 1, col + 1]
            triangles = [
                ([(col, row), (col + 1, row), (col, row + 1)],
                 lambda xy: sw + (xy[:, 0] - col) * (se - sw)
                 + (xy[:, 1] - row) * (nw - sw)),
                ([(col + 1, row), (col + 1, row + 1), (col, row + 1)],
                 lambda xy: ne + (col + 1 - xy[:, 0]) * (nw - ne)
                 + (row + 1 - xy[:, 1]) * (se - ne)),
            ]
            for points, interpolate in triangles:
                clipped = Polygon(points).intersection(mask)
                for polygon in polygon_parts(clipped):
                    if polygon.area < 1e-11:
                        continue
                    xy, face = trimesh.creation.triangulate_polygon(polygon, engine='earcut')
                    if not len(face):
                        continue
                    z = BASE_MM + np.maximum(0, interpolate(xy) - GROUND_OD_M) * SCALE
                    offset = len(vertices)
                    vertices.extend(np.column_stack([xy * SCALE, z]))
                    faces.extend(face + offset)
    roof = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    roof.merge_vertices(digits_vertex=6)
    roof.update_faces(roof.nondegenerate_faces())
    roof.update_faces(roof.unique_faces())
    roof.remove_unreferenced_vertices()
    # Earcut preserves input winding, which can differ after intersections.
    down = roof.face_normals[:, 2] < 0
    roof.faces[down] = roof.faces[down, ::-1]
    return roof


def solid_from_roof(roof):
    """Close roof boundaries with vertical walls and a flat underside in the base."""
    count = len(roof.vertices)
    bottom = roof.vertices.copy()
    bottom[:, 2] = BASE_MM - 0.5
    occurrences = np.bincount(roof.edges_unique_inverse)
    boundary_indices = np.flatnonzero(occurrences[roof.edges_unique_inverse] == 1)
    boundary = roof.edges[boundary_indices]
    a, b = boundary[:, 0], boundary[:, 1]
    sides = np.vstack([np.column_stack([a, a + count, b]),
                       np.column_stack([b, a + count, b + count])])
    faces = np.vstack([roof.faces, roof.faces[:, ::-1] + count, sides])
    solid = trimesh.Trimesh(vertices=np.vstack([roof.vertices, bottom]), faces=faces, process=True)
    solid.merge_vertices(digits_vertex=6)
    solid.remove_unreferenced_vertices()
    return solid


def preview(mesh, mask, elevations):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(13, 9), facecolor='#f6f3ec')
    ax = fig.add_subplot(111, projection='3d', facecolor='#f6f3ec')
    # Subdivide only for painter-style preview visibility, without changing STL.
    pv, pf = trimesh.remesh.subdivide_to_size(mesh.vertices, mesh.faces, max_edge=6.0, max_iter=8)
    render_mesh = trimesh.Trimesh(vertices=pv, faces=pf, process=False)
    elev, azim = np.radians(42), np.radians(-120)
    camera = np.array([np.cos(azim) * np.cos(elev), np.sin(azim) * np.cos(elev), np.sin(elev)])
    visible = render_mesh.face_normals @ camera > 1e-5
    light = np.array([-0.5, -0.4, 1.0]); light /= np.linalg.norm(light)
    shade = 0.42 + 0.58 * np.maximum(0, render_mesh.face_normals[visible] @ light)
    colors = np.column_stack([0.79 * shade, 0.72 * shade, 0.58 * shade, np.ones(len(shade))])
    ax.add_collection3d(Poly3DCollection(render_mesh.triangles[visible], facecolors=colors,
                                       edgecolors='none', linewidths=0, antialiaseds=False, rasterized=True))
    dims = mesh.extents.copy()
    ax.set_xlim(0, dims[0]); ax.set_ylim(0, dims[1]); ax.set_zlim(0, dims[2])
    ax.set_box_aspect(dims.copy()); ax.view_init(elev=42, azim=-120); ax.set_axis_off()
    fig.suptitle('Merton College · measured roofs + architectural tower', fontsize=20, y=0.94)
    fig.text(0.5, 0.08, f'{dims[0]:.0f} × {dims[1]:.1f} × {dims[2]:.1f} mm · mapped buildings · flat 3 mm base',
             ha='center', fontsize=12)
    fig.savefig(HERE / 'preview_hybrid.png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 9))
    im = ax.imshow(elevations[::-1], extent=[WEST, EAST, SOUTH, NORTH], cmap='terrain')
    for polygon in polygon_parts(mask):
        coords = np.asarray(polygon.exterior.coords) + [WEST, SOUTH]
        ax.plot(coords[:, 0], coords[:, 1], color='#cc3434', lw=0.7)
        for ring in polygon.interiors:
            coords = np.asarray(ring.coords) + [WEST, SOUTH]
            ax.plot(coords[:, 0], coords[:, 1], color='#cc3434', lw=0.7)
    ax.set(title='Roof selection mask on measured EA DSM; north up', xlabel='BNG Easting (m)', ylabel='BNG Northing (m)')
    ax.ticklabel_format(useOffset=False)
    fig.colorbar(im, ax=ax, label='Measured elevation (m OD)')
    fig.savefig(HERE / 'footprint_mask.png', dpi=150, bbox_inches='tight'); plt.close(fig)


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    source = np.load(LIDAR / 'raw_dsm_grid.npz')
    raw_elevations = source['z_elevation_m']
    elevations = raw_elevations.copy()
    assert np.allclose(source['x_bng_m'], np.arange(WEST, EAST + 1))
    assert np.allclose(source['y_bng_m'], np.arange(SOUTH, NORTH + 1))
    # The1m scan spreads the tower return beyond its modeled footprint. Remove
    # that ghost rim in a narrowly documented reconstruction transition region.
    gx, gy = np.meshgrid(source['x_bng_m'] - TOWER_CENTER_BNG[0],
                         source['y_bng_m'] - TOWER_CENTER_BNG[1])
    angle = np.radians(TOWER_ANGLE_DEG)
    u = gx * np.cos(angle) + gy * np.sin(angle)
    v = -gx * np.sin(angle) + gy * np.cos(angle)
    transition = ((np.abs(u) <= TOWER_TRANSITION_WIDTH_M / 2)
                  & (np.abs(v) <= TOWER_TRANSITION_WIDTH_M / 2))
    adjusted = transition & (elevations > CHAPEL_RIDGE_OD_M)
    elevations[adjusted] = CHAPEL_RIDGE_OD_M
    np.savez_compressed(HERE / 'processed_roof_grid.npz',
                        x_bng_m=source['x_bng_m'], y_bng_m=source['y_bng_m'],
                        raw_z_elevation_m=raw_elevations, roof_z_elevation_m=elevations,
                        tower_transition_adjusted_vertices=adjusted)
    footprint_file = ARCH / 'building_footprints.geojson'
    features = json.loads(footprint_file.read_text())['features']
    geometries = [affinity.translate(shape(f['geometry']), -WEST, -SOUTH) for f in features]
    # A1-scale 0.016mm plan expansion resolves OSM point-touch junctions which
    # otherwise become non-manifold vertical edges. It is far below source accuracy.
    mask = unary_union(geometries).buffer(0.01, join_style=2).intersection(box(0, 0, EAST - WEST, NORTH - SOUTH))
    mask = mask.simplify(1e-7, preserve_topology=True)
    cx, cy = np.array(TOWER_CENTER_BNG) - [WEST, SOUTH]
    # Roofs overlap the modeled body by 0.05m, avoiding a visible moat/seam.
    half = TOWER_BODY_M / 2 - 0.05
    tower_mask = affinity.rotate(box(cx - half, cy - half, cx + half, cy + half),
                                 TOWER_ANGLE_DEG, origin=(cx, cy))
    roof_mask = mask.difference(tower_mask)
    (HERE / 'roof_mask.geojson').write_text(json.dumps({
        'type': 'FeatureCollection',
        'crs': {'type': 'name', 'properties': {'name': 'EPSG:27700'}},
        'features': [{'type': 'Feature', 'properties': {'name': 'Selected roofs excluding tower'},
                      'geometry': mapping(affinity.translate(roof_mask, WEST, SOUTH))}]
    }, indent=2) + '\n')
    roof = top_surface(roof_mask, elevations)
    building_solid = solid_from_roof(roof)
    building_checks = checks(building_solid)
    if not building_checks['watertight'] or not building_checks['is_volume']:
        raise RuntimeError('Roof solids failed checks: ' + str(building_checks))
    base = trimesh.creation.box(extents=[(EAST - WEST) * SCALE, (NORTH - SOUTH) * SCALE, BASE_MM])
    base.apply_translation([(EAST - WEST) * SCALE / 2, (NORTH - SOUTH) * SCALE / 2, BASE_MM / 2])
    tower_file = ARCH / 'chapel_tower_component.stl'
    if not tower_file.exists():
        raise FileNotFoundError(f'Awaiting reusable architectural tower: {tower_file}')
    tower = trimesh.load_mesh(tower_file, process=True)
    mesh = trimesh.boolean.union([base, building_solid, tower], engine='manifold', check_volume=True)
    mesh.remove_unreferenced_vertices()
    # Any enclosed cavities sealed by the tower/roof junction are unprintable
    # internal details. Retain the exterior shell only, without altering surfaces.
    shells = mesh.split(only_watertight=False)
    negative_shells = [part for part in shells if part.volume < 0]
    exterior_shells = [part for part in shells if part.volume > 0]
    if negative_shells and len(exterior_shells) == 1:
        mesh = exterior_shells[0]
    integrity = checks(mesh)
    if not integrity['watertight'] or not integrity['is_volume'] or integrity['connected_components'] != 1:
        raise RuntimeError('Final hybrid failed checks: ' + str(integrity))
    output = HERE / 'merton_hybrid_220mm.stl'
    mesh.export(output)
    reload_checks = checks(trimesh.load_mesh(output, process=True))
    if not reload_checks['watertight'] or not reload_checks['is_volume'] or reload_checks['connected_components'] != 1:
        raise RuntimeError('Exported STL failed checks: ' + str(reload_checks))
    lidar_metadata = json.loads((LIDAR / 'metadata.json').read_text())
    metadata = {
        'approach': 'EA measured 1m roof surface clipped continuously to selected OSM building footprints; modeled chapel tower; flat base',
        'crop_bbox_bng_m': [WEST, SOUTH, EAST, NORTH], 'crs': 'EPSG:27700',
        'axes': 'X=east, Y=north, Z=up; origin=SW crop; bottom Z=0 mm',
        'scale_mm_per_m': SCALE, 'nominal_scale_denominator': 1000 / SCALE,
        'base_mm': BASE_MM, 'height_exaggeration': 1,
        'estimated_flat_ground_elevation_m_od': GROUND_OD_M,
        'ground_datum_method': 'Common estimated 59 m OD flat-ground datum agreed with architectural approach; no DTM or local terrain variation modeled',
        'raw_lidar_crop_min_elevation_m_od': float(elevations.min()),
        'datum_difference_from_raw_relief_mm': (GROUND_OD_M - float(elevations.min())) * SCALE,
        'source_survey_date': lidar_metadata['source_survey_date'], 'source_resolution_m': 1,
        'selected_osm_building_count': len(features),
        'selected_building_area_m2': float(mask.area), 'roof_mask_area_m2': float(roof_mask.area),
        'footprint_precision_expansion_m': 0.01,
        'tower': {'source_file': str(tower_file.relative_to(PROJECT)),
                  'center_bng_m': TOWER_CENTER_BNG, 'body_width_m': TOWER_BODY_M,
                  'rotation_deg': TOWER_ANGLE_DEG, 'method': 'Same reusable architectural tower as the architectural candidate; see its metadata for reconstructed details'},
        'tower_transition': {'width_m': TOWER_TRANSITION_WIDTH_M, 'orientation_deg': TOWER_ANGLE_DEG,
                             'cap_elevation_m_od': CHAPEL_RIDGE_OD_M,
                             'adjusted_grid_vertices': int(adjusted.sum()),
                             'method': 'Cap only measured samples above the adjacent chapel ridge within the 14.8 m tower transition square to remove scan spread beyond the replacement tower'},
        'filled_sealed_internal_cavities': len(negative_shells),
        'filled_internal_cavity_volume_mm3': float(-sum(part.volume for part in negative_shells)),
        'processing': ['Use the same 1 m-spaced source roof triangles as the measured LiDAR candidate.',
                       f'Expand the union of {len(features)} selected mapped building polygons by 0.01 m to resolve point-touch junctions, then clip each roof triangle to that boundary.',
                       'Within the documented 14.8 m tower transition square, cap source samples at 78.8 m OD to remove tower scan spread; all other source roof triangle planes are preserved.',
                       'Subtract the modeled tower body footprint with 0.05 m overlap; union reusable architectural tower.',
                       'Subtract common estimated 59 m OD ground and add 3 mm base; clamp measured values below the flat datum to the base top.',
                       'Extrude exact footprint boundary walls vertically into the base; union solids with manifold3d.',
                       'Fill any enclosed internal cavities sealed at the roof/tower union; exterior surfaces remain unchanged.',
                       'Merge clipping vertices to 0.000001 mm precision to remove numerical seams.'],
        'inputs': {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [LIDAR / 'raw_dsm_grid.npz', footprint_file, tower_file]},
        'licenses': [
            {'dataset': 'Environment Agency DSM', 'license': 'Open Government Licence v3.0',
             'url': 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
             'attribution': lidar_metadata['attribution'], 'source_url': lidar_metadata['dataset_url']},
            {'dataset': 'Selected OpenStreetMap building footprints', 'license': 'ODbL 1.0',
             'url': 'https://www.openstreetmap.org/copyright', 'attribution': '© OpenStreetMap contributors'}],
        'limitations': ['DSM is 2.5D: roofs are measured, but façade detail and overhangs are absent.',
                        'Mask removes vegetation and neighbors outside selected footprints; canopy or sensor artifacts over a roof remain.',
                        'Roof edge falloff and 1 m sampling artifacts remain inside footprints; no general roof smoothing. The tower transition locally caps heights as documented.',
                        'Tower is a simplified architectural reconstruction, not a survey mesh.',
                        'Estimated flat 59 m OD ground differs from the raw-relief minimum datum; this changes apparent building heights.',
                        'Selected historic-core buildings omit unmodeled site walls, gardens, trees and remote college properties.'],
        'roof_solid_checks': building_checks, 'mesh_checks': integrity,
        'exported_stl_reload_checks': reload_checks,
        'stl_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    (HERE / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    preview(mesh, roof_mask, elevations)
    print(json.dumps(integrity, indent=2))


if __name__ == '__main__':
    main()
