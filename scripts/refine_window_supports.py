"""Paint support contacts only beneath the four projecting oriel bays.

Edits Bambu Studio's project settings and support-paint attributes. Model
vertices, triangles, arrangement, infill and wall settings are preserved.
Run after prepare_freestanding.py and slice_candidates.py detailed-freestanding.
Re-slice the resulting project in Bambu Studio; no printer is contacted.
"""
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'deliverables/merton-detailed-freestanding-a1.3mf'
EVIDENCE = ROOT / 'validation/support_refinement'
EVIDENCE.mkdir(exist_ok=True)

with ZipFile(PROJECT) as archive:
    entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
contents = {info.filename: data for info, data in entries}
mesh_path = '3D/Objects/object_1.model'
xml = contents[mesh_path].decode()
ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
tree = ET.fromstring(xml)
vertices = np.array([[float(e.attrib[k]) for k in ('x', 'y', 'z')]
                     for e in tree.findall('.//m:vertex', ns)])
faces = np.array([[int(e.attrib[k]) for k in ('v1', 'v2', 'v3')]
                  for e in tree.findall('.//m:triangle', ns)])
mesh = trimesh.Trimesh(vertices, faces, process=False)

# These are the two apron/base levels in build_detailed.py, transformed to
# the freestanding model. Area and normal checks exclude unrelated trim.
scale = 220 / 141
base_levels = np.array([2.9, 5.0]) * scale - .01
selected = set()
contacts = []
for facet in mesh.facets:
    height = mesh.triangles_center[facet[0], 2] - mesh.bounds[0, 2]
    area = float(mesh.area_faces[facet].sum())
    if (mesh.face_normals[facet[0], 2] < -.999 and area > 2.5
            and np.min(np.abs(base_levels - height)) < .002):
        selected.update(map(int, facet))
        contacts.append({'height_mm': float(height), 'area_mm2': area,
                         'triangle_indices': list(map(int, facet)),
                         'center_in_mesh_coordinates': mesh.triangles_center[facet].mean(axis=0).tolist()})
assert len(contacts) == 4, f'Expected the four modeled oriels, found {len(contacts)}'

# Bambu's TriangleSelector encodes an unsplit ENFORCER (state 1) as hex 4:
# https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/TriangleSelector.cpp
# This is the same per-triangle attribute written by its support-paint tool.
counter = 0
def paint(match):
    global counter
    triangle = re.sub(r'\s+paint_supports="[^"]*"', '', match.group())
    if counter in selected:
        triangle = triangle.replace('/>', ' paint_supports="4"/>')
    counter += 1
    return triangle
updated_xml = re.sub(r'<triangle\s+[^>]+/>', paint, xml)
assert counter == len(faces)
assert re.sub(r'\s+paint_supports="[^"]*"', '', updated_xml) == re.sub(r'\s+paint_supports="[^"]*"', '', xml)

settings = json.loads(contents['Metadata/project_settings.config'])
changes = {
    'enable_support': '1', 'support_type': 'tree(manual)',
    'support_on_build_plate_only': '1', 'support_critical_regions_only': '0',
    'support_remove_small_overhang': '1', 'support_object_xy_distance': '0.5',
    'support_top_z_distance': '0.24', 'support_bottom_z_distance': '0.24',
    'support_threshold_angle': '15', 'max_bridge_length': '3',
}
settings.update(changes)
for key, value in {'sparse_infill_density': '12%', 'sparse_infill_pattern': 'gyroid',
                   'wall_loops': '3', 'layer_height': '0.12', 'raft_layers': '0'}.items():
    assert settings[key] == value
replacements = {mesh_path: updated_xml.encode(),
                'Metadata/project_settings.config': json.dumps(settings, indent=2).encode()}
temp = PROJECT.with_suffix('.refined.3mf')
with ZipFile(temp, 'w') as archive:
    for info, data in entries:
        # Never carry stale machine instructions into the edited project.
        if info.filename.endswith(('.gcode', '.gcode.md5')):
            continue
        archive.writestr(info, replacements.get(info.filename, data))
backup = EVIDENCE / 'automatic-reduced-project.3mf'
if not backup.exists():
    shutil.copy2(PROJECT, backup)
temp.replace(PROJECT)
report = {'contacts': contacts, 'contact_regions': len(contacts),
          'painted_triangles': len(selected), 'geometry_unchanged': True,
          'mesh_vertex_face_sha256': hashlib.sha256(vertices.tobytes() + faces.tobytes()).hexdigest(),
          'settings': changes,
          'rationale': 'Support the four oriel undersides while leaving mullions, tracery, sills and shallow coping free of support contacts.'}
(EVIDENCE / 'targeted_contacts.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'contact_regions': len(contacts), 'painted_triangles': len(selected),
                  'geometry_unchanged': True, 'project': str(PROJECT)}, indent=2))
