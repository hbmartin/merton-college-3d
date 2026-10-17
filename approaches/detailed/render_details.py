"""Orthographic previews of the actual full-resolution print meshes."""
from pathlib import Path
import importlib.util
import numpy as np
import trimesh
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('renderer',HERE/'mesh_renderer.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('view',choices=['full','chapel','facade']);a=p.parse_args()
    source=ROOT/'deliverables/merton-detailed.stl'
    if a.view=='full':r.render(source,HERE/'preview-southeast.png',az=-55,elev=32,size=2600)
    elif a.view=='chapel':r.render(ROOT/'deliverables/merton-detailed-chapel-1-333.stl',HERE/'preview-chapel.png',az=-55,elev=22,size=2400)
    else:
        # Fellows' south front as a tight source-geometry crop.
        m=trimesh.load_mesh(source)
        c,s=np.cos(np.deg2rad(13.88)),np.sin(np.deg2rad(13.88))
        v=m.vertices.copy();v[:,:2]-=np.array([16.6,79.1])*(220/141)
        xy=v[:,:2]@np.array([[c,-s],[s,c]])/(220/141)
        selected=np.all((xy[m.faces,0]>43)&(xy[m.faces,0]<92)&(xy[m.faces,1]<-49)&(xy[m.faces,1]>-64),axis=1)
        crop=m.submesh([selected],append=True);crop.export(HERE/'facade-preview-only.ply')
        r.render(HERE/'facade-preview-only.ply',HERE/'preview-fellows-windows.png',az=-76.12,elev=10,size=2600)
