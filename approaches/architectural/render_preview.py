"""Small orthographic triangle z-buffer renderer; no GPU/runtime needed."""
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont
P=Path(__file__).resolve().parent

def render(mesh_path,output,az=125,elev=38,size=1800):
    mesh=trimesh.load_mesh(mesh_path);v=mesh.vertices.copy();v-=mesh.bounds.mean(axis=0)
    az,el=np.deg2rad([az,elev]);depth=np.array([np.cos(az)*np.cos(el),np.sin(az)*np.cos(el),np.sin(el)])
    right=np.array([-np.sin(az),np.cos(az),0.]);up=np.cross(depth,right)
    vv=v@np.array([right,up,depth]).T
    screen=vv[:,:2];mi,ma=screen.min(axis=0),screen.max(axis=0);scale=(size-180)/max(ma-mi)
    screen=(screen-(ma+mi)/2)*scale+size/2;screen[:,1]=size-screen[:,1]
    out=np.full((size,size,3),[245.,243.,237.]);zbuf=np.full((size,size),-np.inf)
    light=np.array([-.6,-.6,1.]);light/=np.linalg.norm(light)
    shade=.5+.5*np.maximum(mesh.face_normals@light,0)
    color=np.array([205.,185.,149.])[None,:]*shade[:,None]
    for fi,f in enumerate(mesh.faces):
        xy=screen[f];z=vv[f,2];x0,y0=np.maximum(np.floor(xy.min(axis=0)).astype(int),0);x1,y1=np.minimum(np.ceil(xy.max(axis=0)).astype(int),size-1)
        if x1<x0 or y1<y0:continue
        den=(xy[1,1]-xy[2,1])*(xy[0,0]-xy[2,0])+(xy[2,0]-xy[1,0])*(xy[0,1]-xy[2,1])
        if abs(den)<1e-9:continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        a=((xy[1,1]-xy[2,1])*(xx-xy[2,0])+(xy[2,0]-xy[1,0])*(yy-xy[2,1]))/den
        b=((xy[2,1]-xy[0,1])*(xx-xy[2,0])+(xy[0,0]-xy[2,0])*(yy-xy[2,1]))/den;c=1-a-b
        zz=a*z[0]+b*z[1]+c*z[2];sub=zbuf[y0:y1+1,x0:x1+1];mask=(a>=-1e-8)&(b>=-1e-8)&(c>=-1e-8)&(zz>sub)
        sub[mask]=zz[mask];out[y0:y1+1,x0:x1+1][mask]=color[fi]
    im=Image.fromarray(out.clip(0,255).astype('uint8')).resize((size//2,size//2),Image.Resampling.LANCZOS);im.save(output)

if __name__=='__main__':
    for az,name in [(125,'northwest'),(-55,'southeast')]:render(P/'merton_architectural_220mm.stl',P/f'preview_{name}.png',az=az)
