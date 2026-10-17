"""Copy print masters and make optional, full-scale chapel comparison samples."""
import json
import shutil
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'lidar': ROOT/'approaches/lidar/merton_lidar_220mm.stl',
    'architectural': ROOT/'approaches/architectural/merton_architectural_220mm.stl',
    'hybrid': ROOT/'approaches/hybrid/merton_hybrid_220mm.stl',
}


def main():
    out=ROOT/'deliverables'
    out.mkdir(exist_ok=True)
    sample_dir=out/'chapel-samples'
    sample_dir.mkdir(exist_ok=True)
    # Same 35 x 40 m region for each, without reducing its 1:640.91 scale.
    scale=220/141
    west,south,east,north=[451668,206060,451703,206100]
    lower=np.array([(west-451665)*scale,(south-206000)*scale,-1])
    upper=np.array([(east-451665)*scale,(north-206000)*scale,100])
    clipper=trimesh.creation.box(upper-lower)
    clipper.apply_translation((upper+lower)/2)
    reports=[]
    for key,source in SOURCES.items():
        target=out/f'merton-{key}.stl'
        shutil.copy2(source,target)
        mesh=trimesh.load_mesh(target,process=True)
        sample=trimesh.boolean.intersection([mesh,clipper],engine='manifold')
        sample.apply_translation([-lower[0],-lower[1],0])
        assert sample.is_volume and len(sample.split())==1
        path=sample_dir/f'{key}-chapel.stl'
        sample.export(path)
        reports.append({'model':key,'file':str(path.relative_to(ROOT)),
            'bbox_bng_m':[west,south,east,north],
            'dimensions_mm':sample.extents.tolist(),'watertight':bool(sample.is_watertight),
            'scale_denominator':1000/scale,'scale_change':1.0})
    (sample_dir/'samples.json').write_text(json.dumps(reports,indent=2)+'\n')


if __name__=='__main__':main()
