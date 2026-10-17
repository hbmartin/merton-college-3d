#!/usr/bin/env python3
"""Reproduce a closed, millimetre-scale Merton relief from official EA DSM.

Run from the repository root:
  .venv/bin/python approaches/lidar/build_lidar.py
Use --download to refresh the 500 x 400 m source GeoTIFF from the official WCS.
The STL has no invented roofs, façade features, vegetation removal or height exaggeration.
Bilinear sampling registers raster pixels to 1 m-spaced shared crop-boundary vertices.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
import requests
import trimesh
from scipy.ndimage import map_coordinates
from pyproj import Transformer

HERE = Path(__file__).resolve().parent
RAW = HERE / 'raw'
SOURCE = RAW / 'ea_dsm_1m_merton_context.tif'
WCS_URL = 'https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-last-return-dsm-1m/wcs'
COVERAGE = '9ba4d5ac-d596-445a-9056-dae3ddec0178__Lidar_Composite_Elevation_LZ_DSM_1m'
PARAMS = [('service','WCS'),('version','2.0.1'),('request','GetCoverage'),('coverageId',COVERAGE),('format','image/tiff'),('subset','E(451450,451950)'),('subset','N(205750,206150)')]
ATTRIBUTION = '© Environment Agency copyright and/or database right 2022. All rights reserved.'

def download():
    RAW.mkdir(exist_ok=True)
    r = requests.get(WCS_URL, params=PARAMS, timeout=90)
    r.raise_for_status()
    if not r.content.startswith((b'II',b'MM')):
        raise RuntimeError('WCS did not return a TIFF: ' + r.text[:200])
    SOURCE.write_bytes(r.content)
    (RAW/'request.json').write_text(json.dumps({'url':WCS_URL,'params':PARAMS,'resolved_url':r.url,'status':r.status_code,'content_type':r.headers.get('Content-Type'),'retrieved_at':datetime.now(timezone.utc).isoformat()},indent=2))

def heightfield_mesh(z: np.ndarray, spacing_mm: float, base_mm: float):
    # z row order south to north. Grid triangles use counterclockwise winding.
    rows, cols = z.shape
    xx, yy = np.meshgrid(np.arange(cols)*spacing_mm,np.arange(rows)*spacing_mm)
    zz = (z-z.min())*spacing_mm + base_mm
    top = np.stack([xx,yy,zz],axis=-1).reshape(-1,3)
    aa = np.arange((rows-1)*cols).reshape(rows-1,cols)[:,:-1].ravel()
    bb,cc,dd=aa+1,aa+cols,aa+cols+1
    faces = np.vstack([np.column_stack([aa,bb,cc]),np.column_stack([bb,dd,cc])])
    # Unique perimeter indices, traversed counterclockwise from SW.
    ring = np.r_[np.arange(cols),np.arange(2*cols-1,rows*cols,cols),np.arange(rows*cols-2,(rows-1)*cols-1,-1),np.arange((rows-2)*cols,0,-cols)]
    lower = top[ring].copy(); lower[:,2]=0
    lower_indices = np.arange(len(top),len(top)+len(ring))
    center_index=len(top)+len(ring)
    vertices=np.vstack([top,lower,[[xx.max()/2,yy.max()/2,0]]])
    nxt=np.roll(ring,-1); bnxt=np.roll(lower_indices,-1)
    sides=np.vstack([np.column_stack([ring,lower_indices,nxt]),np.column_stack([nxt,lower_indices,bnxt])])
    bottom=np.column_stack([bnxt,lower_indices,np.full(len(ring),center_index)])
    mesh=trimesh.Trimesh(vertices=vertices,faces=np.vstack([faces,sides,bottom]),process=True)
    return mesh

def mesh_checks(mesh):
    return {'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'is_volume':bool(mesh.is_volume),'connected_components':len(mesh.split(only_watertight=False)),'euler_number':int(mesh.euler_number),'vertices':len(mesh.vertices),'triangles':len(mesh.faces),'degenerate_triangles':int(np.sum(mesh.area_faces<1e-10)),'bounds_mm':mesh.bounds.tolist(),'dimensions_mm':mesh.extents.tolist(),'volume_mm3':float(mesh.volume)}

def preview(mesh, z, bounds):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    # The preview displays the same registered measured surface as the STL.
    fig=plt.figure(figsize=(13,9),facecolor='#f6f3ec')
    ax=fig.add_subplot(111,projection='3d',facecolor='#f6f3ec')
    tri=mesh.vertices[mesh.faces]
    normals=mesh.face_normals
    light=np.array([-0.5,-0.4,1]);light/=np.linalg.norm(light)
    shade=.42+.58*np.maximum(0,normals@light)
    colors=np.column_stack([.79*shade,.72*shade,.58*shade,np.ones(len(shade))])
    polys=Poly3DCollection(tri,facecolors=colors,edgecolors='none',linewidths=0,rasterized=True)
    ax.add_collection3d(polys)
    dims=mesh.extents.copy(); ax.set_xlim(0,dims[0]);ax.set_ylim(0,dims[1]);ax.set_zlim(0,dims[2]);ax.set_box_aspect(dims.copy())
    ax.view_init(elev=42,azim=-120);ax.set_axis_off()
    fig.suptitle('Merton College · measured LiDAR relief',fontsize=20,y=.94)
    fig.text(.5,.08,f'{dims[0]:.0f} × {dims[1]:.1f} × {dims[2]:.1f} mm · 1 m source · 3 mm minimum base · north to the rear',ha='center',fontsize=12)
    fig.savefig(HERE/'preview_lidar.png',dpi=150,bbox_inches='tight',facecolor=fig.get_facecolor());plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,8))
    north_up=z[::-1]
    rgb=LightSource(azdeg=315,altdeg=45).shade(north_up,cmap=plt.get_cmap('terrain'),vert_exag=1,blend_mode='soft')
    ax.imshow(rgb,extent=bounds);ax.set(xlabel='BNG Easting (m)',ylabel='BNG Northing (m)',title='Merton DSM crop — north up, registered measured heights')
    ax.ticklabel_format(useOffset=False);fig.savefig(HERE/'crop_hillshade.png',dpi=150,bbox_inches='tight');plt.close(fig)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--download',action='store_true')
    p.add_argument('--bbox',nargs=4,type=float,default=[451665,206000,451806,206133],metavar=('WEST','SOUTH','EAST','NORTH'))
    p.add_argument('--long-edge-mm',type=float,default=220)
    p.add_argument('--base-mm',type=float,default=3)
    args=p.parse_args()
    if args.download or not SOURCE.exists(): download()
    west,south,east,north=args.bbox
    with rasterio.open(SOURCE) as src:
        if not (src.bounds.left<=west<east<=src.bounds.right and src.bounds.bottom<=south<north<=src.bounds.top):
            raise ValueError('Requested crop falls outside downloaded source; download a larger official WCS crop first.')
        win=from_bounds(west,south,east,north,src.transform).round_offsets().round_lengths()
        z=src.read(1,window=win,masked=True)
        if np.ma.getmaskarray(z).any() or not np.isfinite(z).all(): raise ValueError('Source contains missing heights; no invented fill is allowed.')
        transform=src.window_transform(win)
        profile=src.profile.copy();profile.update(width=z.shape[1],height=z.shape[0],transform=transform,tiled=False);profile.pop('blockxsize',None);profile.pop('blockysize',None)
        with rasterio.open(HERE/'merton_dsm_crop.tif','w',**profile) as out: out.write(np.array(z),1)
        # Mesh vertices sit on the exact shared crop boundaries rather than pixel
        # centres. Bilinear sampling at 1 m spacing registers with the architectural
        # model; the raw GeoTIFF remains unchanged for evidence.
        context=src.read(1,masked=True)
        xs=np.arange(west,east+0.001,1.0)
        ys=np.arange(south,north+0.001,1.0)
        gx,gy=np.meshgrid(xs,ys)
        row=(src.transform.f-gy)/abs(src.transform.e)-.5
        col=(gx-src.transform.c)/src.transform.a-.5
        z=map_coordinates(np.asarray(context),[row,col],order=1,mode='nearest')
        sw=(west,south);ne=(east,north)
    spacing=args.long_edge_mm/max(east-west,north-south)
    np.savez_compressed(HERE/'raw_dsm_grid.npz',x_bng_m=xs,y_bng_m=ys,z_elevation_m=z,z_height_mm=(z-z.min())*spacing+args.base_mm,origin_bng_m=[west,south],scale_mm_per_m=spacing,minimum_base_mm=args.base_mm,datum_min_elevation_m=z.min())
    mesh=heightfield_mesh(z,spacing,args.base_mm)
    checks=mesh_checks(mesh)
    if not all(checks[k] for k in ['watertight','winding_consistent','is_volume']) or checks['connected_components']!=1 or checks['degenerate_triangles']:
        raise RuntimeError('Generated mesh failed integrity checks: '+str(checks))
    output=HERE/'merton_lidar_220mm.stl';mesh.export(output)
    # Validate exported triangle soup after reloading, not only the in-memory indexed mesh.
    reload_checks=mesh_checks(trimesh.load_mesh(output,process=True))
    if not reload_checks['watertight'] or not reload_checks['is_volume']: raise RuntimeError('STL reload failed')
    to_wgs=Transformer.from_crs(27700,4326,always_xy=True)
    metadata={
      'approach':'EA 1m last-return LiDAR DSM heightfield, bilinearly registered to shared crop bounds',
      'source_dataset':'LIDAR Composite Digital Surface Model (DSM) - 1m (2022 composite)',
      'dataset_url':'https://environment.data.gov.uk/dataset/9ba4d5ac-d596-445a-9056-dae3ddec0178',
      'numeric_service':WCS_URL,'coverage_id':COVERAGE,
      'source_survey_date':'2020-03-15','source_survey_evidence':'raw/coverage-index.geojson',
      'source_resolution_m':1,'mesh_vertex_spacing_m':1,'grid_export':'raw_dsm_grid.npz','crs':'EPSG:27700','vertical_datum':'Ordnance Datum Newlyn (source dataset OSTN15/OSGM15)',
      'os_5km_tile':'SP50NE','context_bbox_bng_m':[451450,205750,451950,206150],
      'requested_crop_bbox_bng_m':args.bbox,'mesh_sample_bbox_bng_m':[sw[0],sw[1],ne[0],ne[1]],
      'crop_bbox_wgs84_lonlat':[list(to_wgs.transform(west,south)),list(to_wgs.transform(east,north))],
      'source_height_range_m':[float(z.min()),float(z.max())],
      'horizontal_and_vertical_scale_mm_per_m':spacing,'nominal_scale_denominator':1000/spacing,
      'height_exaggeration':1,'minimum_base_mm':args.base_mm,
      'axes':'X=east, Y=north, Z=up; origin=SW shared crop boundary vertex; bottom Z=0 mm',
      'processing':'Sample official raster bilinearly at 1m-spaced BNG vertices on exact shared crop bounds; triangulate those heights; no further smoothing, roof invention, or vegetation removal; subtract sampled crop minimum elevation and add 3mm minimum base; close vertical sides and planar bottom.',
      'license':'Open Government Licence v3.0','license_url':'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
      'attribution':ATTRIBUTION,'retrieved_date':'2026-10-17',
      'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'stl_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
      'mesh_checks':checks,'exported_stl_reload_checks':reload_checks,
      'limitations':['DSM is 2.5D: no vertical façade windows, undercuts or overhangs.',f'Source 1m cells map to {spacing:.2f}mm on this print; fine tower tracery is absent.','Vegetation, vehicles and survey artifacts remain in the surface.','Some adjacent buildings may fall within the rectangular crop.','Source reflects the 2020 survey, not a current survey.']
    }
    (HERE/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    preview(mesh,z,[sw[0],ne[0],sw[1],ne[1]])
    print(json.dumps(metadata['mesh_checks'],indent=2))

if __name__=='__main__':main()
