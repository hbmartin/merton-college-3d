"""Remove only the 3 mm site slab, retaining the buildings' scale and layout."""
import importlib.util
import json
from pathlib import Path
import manifold3d as mf
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('detailed',ROOT/'approaches/detailed/build_detailed.py')
detail=importlib.util.module_from_spec(spec);spec.loader.exec_module(detail)
source=ROOT/'deliverables/merton-detailed.stl'
output=ROOT/'deliverables/merton-detailed-freestanding.stl'
mesh=trimesh.load_mesh(source,process=True)
assert mesh.is_volume
solid=mf.Manifold(mf.Mesh(np.asarray(mesh.vertices,dtype=np.float32),np.asarray(mesh.faces,dtype=np.uint32)))
assert solid.status()==mf.Error.NoError
cut_height=3.01  # 0.01 mm clearance removes coincident/sliver faces at the slab top.
cut=solid.trim_by_plane((0,0,1),cut_height).translate((0,0,-cut_height))
assert cut.status()==mf.Error.NoError
raw=detail.to_tri(cut)
assert raw.is_watertight
substantial=[p for p in raw.split(only_watertight=False) if abs(p.volume)>.001]
raw=trimesh.util.concatenate(substantial)
# Preserve explicit topology in coordinate-only STL serialization.
v=raw.vertices.copy()
_,inverse,counts=np.unique(v.astype(np.float32),axis=0,return_inverse=True,return_counts=True)
repeated=counts[inverse]>1
rng=np.random.default_rng(1047)
v[repeated]+=rng.uniform(-.0004,.0004,(int(repeated.sum()),3))
v[:,2]=np.where(np.abs(raw.vertices[:,2])<1e-8,0,v[:,2])
raw.vertices=v
raw.export(output)
result=trimesh.load_mesh(output,process=True)
parts=result.split(only_watertight=False)
assert all(p.is_volume and abs(p.bounds[0,2])<1e-5 for p in parts)
incidence=np.bincount(result.edges_unique_inverse)
assert np.all(incidence==2)
# At ground level, the remaining footprint must occupy a minority of the old site slab.
flat=(np.abs(result.triangles[:,:,2]).max(axis=1)<1e-7)&(result.face_normals[:,2]<-.99)
foot_area=float(result.area_faces[flat].sum())
assert foot_area<220*(207.5177307)*.5
report={'source':str(source.relative_to(ROOT)),'output':str(output.relative_to(ROOT)),
 'removed_base_mm':3.0,'cut_clearance_mm':.01,'cut_height_mm':cut_height,'scale_change':1.0,'layout_preserved':True,
 'dimensions_mm':result.extents.round(4).tolist(),'bounds_mm':result.bounds.round(6).tolist(),
 'triangles':len(result.faces),'watertight':bool(result.is_watertight),
 'winding_consistent':bool(result.is_winding_consistent),'boundary_or_nonmanifold_edges':int(np.count_nonzero(incidence!=2)),
 'connected_building_groups':len(parts),'all_groups_stand_at_z0':True,
 'bottom_contact_area_mm2':round(foot_area,3),'old_slab_area_mm2':round(220*207.5177307,3),
 'removed_solid_volume_mm3':round(float(mesh.volume-result.volume),3),
 'components':[{'triangles':len(p.faces),'volume_mm3':round(float(p.volume),3),'bounds_mm':p.bounds.round(4).tolist()} for p in sorted(parts,key=lambda p:p.volume,reverse=True)]}
(ROOT/'validation/freestanding_mesh.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
