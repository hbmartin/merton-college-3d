"""Embed reduced, quantized copies of actual STL geometry in the comparison.

Full-resolution print files are never reduced or modified by this script.
"""
import base64
import json
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
VIZ = Path('/Users/haroldmartin/.codex/visualizations/2026/10/17/01a14a44-aa91-7021-9dc1-1c327945b1b1')
MODELS = [
    ('lidar', 'Measured LiDAR', 'merton-lidar.stl', 'Measured 1 m surface; survey noise retained'),
    ('architectural', 'Architectural', 'merton-architectural.stl', 'Mapped footprints; simplified roofs and tower'),
    ('hybrid', 'Hybrid', 'merton-hybrid.stl', 'Measured roofs; clean ground and modeled tower'),
]


def main():
    data=[]
    for key, name, filename, detail in MODELS:
        mesh=trimesh.load_mesh(ROOT/'deliverables'/filename, process=True)
        dimensions=mesh.extents.round(3).tolist()
        if len(mesh.faces)>15000:
            mesh=mesh.simplify_quadric_decimation(face_count=15000)
        # All 220 mm models fit signed int16 at 0.01 mm preview precision.
        vertices=np.rint(mesh.vertices*100).astype('<i2')
        if len(vertices)>65535: raise ValueError('Preview index overflow')
        faces=np.asarray(mesh.faces,dtype='<u2')
        data.append(dict(id=key,name=name,detail=detail,dimensions=dimensions,
            vertices=base64.b64encode(vertices.tobytes()).decode(),
            faces=base64.b64encode(faces.tobytes()).decode()))
    fragment=(ROOT/'scripts'/'comparison-template.html').read_text().replace('__MERTON_DATA__',json.dumps(data,separators=(',',':')))
    if len(fragment.encode())>=1_000_000: raise ValueError('Inline preview exceeds 1 MB')
    path=VIZ/'merton-models.html'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(fragment)
    print(f'{path} ({len(fragment.encode()):,} bytes)')


if __name__=='__main__': main()
