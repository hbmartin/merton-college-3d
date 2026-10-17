#!/usr/bin/env python3
"""Frozen OSM footprints + EA-calibrated roof parameters + interpreted chapel tower.
Run from repository root: .venv/bin/python approaches/architectural/build_architectural.py
All geometry in mm. Geographic frame: EPSG:27700, X east/Y north.
"""
from pathlib import Path
import json, math, argparse, io
import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString, box, mapping, shape
from shapely.ops import split, polygonize
from shapely.affinity import affine_transform
from pyproj import Transformer

HERE=Path(__file__).resolve().parent
BBOX=[451665.,206000.,451806.,206133.]
SCALE=220./141.
BASE=3.
TOWER_CENTER=[451681.6,206079.1]
ANGLE=math.radians(13.88)
C,S=math.cos(ANGLE),math.sin(ANGLE)
SELECT_IDS={39606739,39606975,39607373,95664347,228196820,*range(301498988,301499002),*range(301499006,301499012)}
SOURCE=HERE/'sources'/'osm_features.json'


def to_print(poly):
    return affine_transform(poly,[SCALE,0,0,SCALE,-BBOX[0]*SCALE,-BBOX[1]*SCALE])


def mesh_union(meshes):
    meshes=[m for m in meshes if len(m.faces)]
    if len(meshes)==1:return meshes[0]
    return trimesh.boolean.union(meshes,engine='manifold')


def extrude(poly,z0,z1):
    if poly.is_empty:return None
    if poly.geom_type=='MultiPolygon':return mesh_union([extrude(p,z0,z1) for p in poly.geoms])
    m=trimesh.creation.extrude_polygon(poly,height=z1-z0,engine='earcut');m.apply_translation([0,0,z0]);return m


def taper_prism(poly,z0,zfunc):
    """Closed prism with a planar, sloping top for a ridge-split polygon."""
    v2,faces=trimesh.creation.triangulate_polygon(poly,engine='earcut')
    n=len(v2);vertices=np.vstack([np.column_stack([v2,np.full(n,z0)]),np.column_stack([v2,[zfunc(x) for x in v2]])])
    out=[list(f[::-1]) for f in faces]+[list(f+n) for f in faces]
    # Earcut may reorder outer/inner vertices; find exact index in returned array.
    for ring in [poly.exterior,*poly.interiors]:
        r=list(ring.coords)
        for a,b in zip(r,r[1:]):
            ia=int(np.argmin(np.linalg.norm(v2-a,axis=1)));ib=int(np.argmin(np.linalg.norm(v2-b,axis=1)))
            out.extend([[ia,ib,ib+n],[ia,ib+n,ia+n]])
    m=trimesh.Trimesh(vertices=vertices,faces=out,process=True);m.fix_normals();return m


def gabled(poly,eave,ridge):
    """Gable clipped to the real OSM outline, oriented by minimum rectangle."""
    rect=np.array(poly.minimum_rotated_rectangle.exterior.coords[:4]);edges=np.roll(rect,-1,axis=0)-rect
    lengths=np.linalg.norm(edges,axis=1);u=edges[np.argmax(lengths)]/max(lengths)
    v=np.array([-u[1],u[0]]);coords=np.array(poly.exterior.coords);lo,hi=(coords@v).min(),(coords@v).max();mid=(lo+hi)/2
    center=np.array(poly.centroid.coords[0]);line_origin=center+v*(mid-center@v)
    cuts=split(poly,LineString([line_origin-u*1000,line_origin+u*1000]))
    def zfunc(pt):return eave+(ridge-eave)*max(0,1-abs(np.dot(pt,v)-mid)/((hi-lo)/2))
    return [taper_prism(p,eave-.08,zfunc) for p in cuts.geoms if p.geom_type=='Polygon']


def box_mesh(x,y,z0,w,d,z1):return extrude(box(x-w/2,y-d/2,x+w/2,y+d/2),z0,z1)


def local_mesh_to_print(m):
    """Tower input coordinates local metres (u choir axis, v north, z AGL)."""
    mat=np.array([[C*SCALE,-S*SCALE,0,(TOWER_CENTER[0]-BBOX[0])*SCALE],[S*SCALE,C*SCALE,0,(TOWER_CENTER[1]-BBOX[1])*SCALE],[0,0,SCALE,BASE],[0,0,0,1]])
    m.apply_transform(mat);return m


def arch_polygon(cx,z0,width,height):
    # Gothic-inspired pointed recess; deliberately simplified for a 0.4mm nozzle.
    spring=z0+height*.66
    pts=[(cx-width/2,z0),(cx+width/2,z0),(cx+width/2,spring),(cx+width*.35,z0+height*.85),(cx,z0+height),(cx-width*.35,z0+height*.85),(cx-width/2,spring)]
    return Polygon(pts)


def arch_cutter(cx,z0,width,height,face,depth=.45):
    # polygon XY currently horizontal/height; extrude then orient around tower.
    p=arch_polygon(cx,z0,width,height);m=trimesh.creation.extrude_polygon(p,height=depth+.15,engine='earcut')
    # x -> horizontal; old y -> height; old z -> depth, face plane local v=5.4
    mat=np.array([[1,0,0,0],[0,0,1,5.4-depth],[0,1,0,0],[0,0,0,1]])
    m.apply_transform(mat);m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(face),[0,0,1]));return m


def tower_mesh():
    """Printable interpreted 15th-century tower, exported separately for hybrid."""
    parts=[box_mesh(0,0,-.1,10.8,10.8,28.0)]
    # Continuous string courses and upper parapet belt: projections under 0.5mm in print.
    for z in [17.6,27.8]:parts.append(box_mesh(0,0,z,11.35,11.35,z+.45))
    parts.append(box_mesh(0,0,28.0,11.1,11.1,29.35))
    # Corner and mid-face piers carry all eight pinnacles down into tower body.
    positions=[(-5.05,-5.05),(-5.05,5.05),(5.05,-5.05),(5.05,5.05),(-5.05,0),(5.05,0),(0,-5.05),(0,5.05)]
    for x,y in positions:
        parts.append(box_mesh(x,y,16,1.2,1.2,30.8))
        parts.append(box_mesh(x,y,29.9,1.55,1.55,30.3))
        # Stepped pinnacle finishes with a flat 0.8mm square cap, avoiding fragile tips.
        stages=[(30.8,1.35),(31.8,1.15),(32.7,.95),(33.55,.75),(34.2,.53),(34.85,.53)]
        for (z,w),(zt,_) in zip(stages,stages[1:]):
            parts.append(box_mesh(x,y,z-.04,w,w,zt+.01))
    tower=mesh_union(parts)
    cutters=[]
    for angle in [0,90,180,270]:
        for x in [-2.55,2.55]:cutters.append(arch_cutter(x,20.4,2.05,6.4,angle))
        # Shallow lower-stage panel adds the blind-arch silhouette below the belfry.
        for x in [-2.55,2.55]:cutters.append(arch_cutter(x,15.4,1.9,3.9,angle,.3))
    tower=trimesh.boolean.difference([tower,*cutters],engine='manifold')
    # Crenellations between the pinnacles; openings are top-open and support-free.
    merlons=[]
    for angle in [0,90,180,270]:
        for x in [-3.6,-1.45,1.45,3.6]:
            m=box_mesh(x,5.2,29.3,.95,.72,30.15);m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle),[0,0,1]));merlons.append(m)
    return local_mesh_to_print(mesh_union([tower,*merlons]))


def get_source_footprints():
    es=json.loads(SOURCE.read_text())['elements'];ways={str(e['id']):e for e in es if e['type']=='way'}
    pr=Transformer.from_crs(4326,27700,always_xy=True)
    out=[]
    def coords(e):return [pr.transform(n['lon'],n['lat']) for n in e['geometry']]
    for e in es:
        if e['type']=='way' and int(e.get('id',0)) in SELECT_IDS:
            out.append({'type':'Feature','properties':{'osm_type':'way','osm_id':int(e['id']),'name':e['tags'].get('name'), 'osm_tags':e['tags']},'geometry':mapping(Polygon(coords(e)).buffer(0))})
        elif e['type']=='relation' and e['tags'].get('name') in ['Grove I','Grove II']:
            polys=list(polygonize([LineString(coords(ways[m['ref']])) for m in e['members'] if m['type']=='way']))
            for po in polys:out.append({'type':'Feature','properties':{'osm_type':'relation','osm_id':int(e['id']),'name':e['tags']['name'],'osm_tags':e['tags']},'geometry':mapping(po)})
    return out


def freeze_parameters():
    """One-time creation of numeric roof parameters; normal builds never need a raster."""
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.windows import from_bounds
    fp=get_source_footprints()
    p=HERE.parent/'lidar'/'raw'/'ea_dsm_1m_merton_context.tif'
    with rasterio.open(p) as r:
        for f in fp:
            poly=shape(f['geometry']);w=from_bounds(*poly.bounds,r.transform).round_offsets().round_lengths();a=r.read(1,window=w);t=r.window_transform(w)
            mask=geometry_mask([mapping(poly.buffer(-.6))],a.shape,t,invert=True);vals=a[mask]
            ground=59.0 # Common flat datum; terrain intentionally excluded from this approach.
            ridge=float(np.quantile(vals,.90)-ground)
            if f['properties']['name']=='Merton College Chapel':ridge=19.8
            ridge=max(6.5,min(ridge,22.))
            rect=np.array(poly.minimum_rotated_rectangle.exterior.coords[:4]);width=float(min(np.linalg.norm(np.roll(rect,-1,axis=0)-rect,axis=1)))
            rise=min(5.,max(2.5,width*.34))
            if f['properties']['name']=='Lodge':ridge=17.2;rise=0
            f['properties'].update(ridge_agl_m=round(ridge,2),eave_agl_m=round(ridge-rise,2),height_method='90th percentile EA 2020 DSM minus common59m datum; eaves inferred from 34-degree nominal pitch',roof_width_m=round(width,2))
            if f['properties']['name']=='Merton College Chapel':f['properties']['height_method']='Choir/transept ridge estimated19.8mAGL from DSM excluding crossing tower; eaves13.0mAGL'
            if f['properties']['name']=='Lodge':f['properties']['height_method']='Gate tower17.2mAGL interpreted from official site isometric; no pitched roof'
    doc={'type':'FeatureCollection','name':'Merton historic core OSM footprints','crs':{'type':'name','properties':{'name':'EPSG:27700'}},'source':'© OpenStreetMap contributors, ODbL1.0','features':fp}
    (HERE/'building_footprints.geojson').write_text(json.dumps(doc,indent=2))


def build():
    data=json.loads((HERE/'building_footprints.geojson').read_text());parts=[]
    width=(BBOX[2]-BBOX[0])*SCALE;depth=(BBOX[3]-BBOX[1])*SCALE
    parts.append(extrude(box(0,0,width,depth),0,BASE))
    for f in data['features']:
        prop=f['properties'];po=shape(f['geometry']);poly=to_print(po);name=prop['name']
        # Simplification removes sub-nozzle outline notches without closing the quads.
        poly=poly.simplify(.16,preserve_topology=True).buffer(.04,join_style=2)
        if name=='Merton College Chapel':
            parts.append(extrude(poly,BASE-.1,BASE+13.0*SCALE))
            # Intersect two appropriately aligned roof prisms with true T-shaped outline.
            inv=[C,S,-S,C,-C*TOWER_CENTER[0]-S*TOWER_CENTER[1],S*TOWER_CENTER[0]-C*TOWER_CENTER[1]]
            lp=affine_transform(po,inv)
            for p in [lp.intersection(box(-20,-25,8.05,25)),lp.intersection(box(7.0,-5.6,45,7.2))]:
                if p.is_empty:continue
                pp=affine_transform(p,[C,-S,S,C,TOWER_CENTER[0],TOWER_CENTER[1]])
                parts.extend(gabled(to_print(pp).buffer(.02,join_style=2),BASE+13*SCALE,BASE+19.8*SCALE))
            # Choir buttresses inferred from the seven bays; robust0.9mm minimum.
            for u in [11,15,19,23,27,31,35]:
                for v in [-5.8,7.4]:
                    m=box_mesh(u,v,-.05,.65,1.2,12.2);parts.append(local_mesh_to_print(m))
            continue
        eave=BASE+prop['eave_agl_m']*SCALE;ridge=BASE+prop['ridge_agl_m']*SCALE
        if name=='Lodge':
            parts.append(extrude(poly,BASE-.1,ridge));continue
        parts.append(extrude(poly,BASE-.1,eave))
        if name=='Upper and Lower Libraries':
            # L-shaped library is two real ranges; clip them, keeping the OSM ground plan.
            inv=[C,S,-S,C,-C*BBOX[0]-S*BBOX[1],S*BBOX[0]-C*BBOX[1]]
            lp=affine_transform(po,inv)
            for p in [lp.intersection(box(0,0,42.4,60)),lp.intersection(box(42.2,0,90,60))]:
                if p.is_empty:continue
                pp=affine_transform(p,[C,-S,S,C,BBOX[0],BBOX[1]]);parts.extend(gabled(to_print(pp).buffer(.02,join_style=2),eave,ridge))
        else:parts.extend(gabled(poly,eave,ridge))
    tower=tower_mesh();tower.export(HERE/'chapel_tower_component.stl')
    parts.append(tower)
    model=mesh_union(parts);model.remove_unreferenced_vertices();model.fix_normals()
    # Manifold float output can retain coincident zero-volume boundary shells.
    # Prune only components below0.01mm3, not any printable geometry.
    model=trimesh.load_mesh(io.BytesIO(model.export(file_type='stl')),file_type='stl')
    components=model.split(only_watertight=False)
    slivers=[p for p in components if abs(p.volume)<.01]
    substantial=[p for p in components if abs(p.volume)>=.01]
    model=trimesh.util.concatenate(substantial)
    model.merge_vertices();model.remove_unreferenced_vertices();model.fix_normals()
    model.export(HERE/'merton_architectural_220mm.stl')
    # Helpful geography for callers inserting a replacement tower into another model.
    transform={'crs':'EPSG:27700','bbox_bng':BBOX,'scale_mm_per_m':SCALE,'z_base_mm':BASE,'ground_reference_mOD':59.0,'x_mm':'(E-451665)*220/141','y_mm':'(N-206000)*220/141','z_mm':'3 + AGL_m*220/141','tower_center_bng':TOWER_CENTER,'tower_center_mm':[(TOWER_CENTER[0]-BBOX[0])*SCALE,(TOWER_CENTER[1]-BBOX[1])*SCALE], 'tower_body_width_m':10.8,'tower_rotation_deg':13.88,'tower_top_agl_m':34.86,'tower_body_top_agl_m':29.35,'tower_component_coordinates':'Full shared model mm frame; bottom2.844mm to overlap3mm base'}
    (HERE/'transform.json').write_text(json.dumps(transform,indent=2))
    report={'dimensions_mm':model.extents.tolist(),'bounds_mm':model.bounds.tolist(),'watertight':bool(model.is_watertight),'winding_consistent':bool(model.is_winding_consistent),'signed_volume_mm3':float(model.volume),'body_count':len(model.split()),'vertices':len(model.vertices),'triangles':len(model.faces),'minimum_pinnacle_cap_mm':.53*SCALE,'footprints':len(data['features']),'scale_ratio':1000/SCALE,'pruned_numerical_shells':len(slivers),'pruned_shell_volume_mm3':sum(abs(p.volume) for p in slivers),'print_note':'Flat base down, standard0.4mm nozzle, 0.12–0.16mm layers. Review in BambuStudio. No physical print performed.'}
    assert report['watertight'] and report['body_count']==1 and report['signed_volume_mm3']>0
    (HERE/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    return model


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--freeze-parameters',action='store_true');args=ap.parse_args()
    if args.freeze_parameters:freeze_parameters()
    build()
