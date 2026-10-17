#!/usr/bin/env python3
"""Photo-informed, solid architectural model. All construction is in local metres.
The final transform retains the original 220 mm footprint, north orientation and scale.
No network calls; the five user images and frozen footprints are the source evidence.
"""
from pathlib import Path
import collections
import importlib.util
import json
import math
import time

import manifold3d as mf
import numpy as np
import trimesh
from shapely.affinity import affine_transform, translate
from shapely.geometry import Point, Polygon, LineString, box, shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('original', ROOT/'approaches/architectural/build_architectural.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
SCALE, BASE = original.SCALE, original.BASE
C, S = original.C, original.S
E, N = original.TOWER_CENTER
COUNTS = collections.Counter()
FEATURES = []


def union(parts):
    return mf.Manifold.batch_boolean([p for p in parts if not p.is_empty()], mf.OpType.Add)


def subtract(solid, cuts):
    return mf.Manifold.batch_boolean([solid, *[p for p in cuts if not p.is_empty()]], mf.OpType.Subtract)


def extrude(poly, z0, z1):
    if poly.is_empty:
        return mf.Manifold()
    if poly.geom_type != 'Polygon':
        return union([extrude(p, z0, z1) for p in poly.geoms if p.geom_type in ('Polygon', 'MultiPolygon')])
    poly = orient(poly)
    contours = [np.asarray(poly.exterior.coords[:-1]), *[np.asarray(r.coords[:-1]) for r in poly.interiors]]
    return mf.CrossSection(contours).extrude(z1-z0).translate((0, 0, z0))


def block(x, y, z, w, d, h):
    return mf.Manifold.cube((w, d, h)).translate((x-w/2, y-d/2, z))


def from_tri(mesh):
    return mf.Manifold(mf.Mesh(np.asarray(mesh.vertices, dtype=np.float32), np.asarray(mesh.faces, dtype=np.uint32)))


def to_tri(solid):
    result = solid.to_mesh64()
    vertices=np.array(result.vert_properties[:, :3])
    parents=np.arange(len(vertices))
    for a,b in zip(result.merge_from_vert,result.merge_to_vert):
        parents[int(a)]=int(b)
    while not np.array_equal(parents,parents[parents]):parents=parents[parents]
    mesh=trimesh.Trimesh(vertices,parents[np.array(result.tri_verts)],process=False)
    mesh.remove_unreferenced_vertices()
    return mesh


def facade(poly, center, tangent, normal, d0, d1):
    """Extrude a horizontal/height polygon out of a facade, preserving its solid back."""
    return extrude(poly, d0, d1).transform(np.array([
        [tangent[0], 0, normal[0], center[0]],
        [tangent[1], 0, normal[1], center[1]],
        [0, 1, 0, 0],
    ]))


def gothic(x, z, w, h):
    # Two circular arcs meet at a Gothic point, rather than a polygonal pentagon.
    r = w
    spring = z+h-math.sqrt(3)*w/2
    spring = max(z+h*.40, spring)
    pts = [(x-w/2, z), (x+w/2, z)]
    for t in np.linspace(0, math.pi/3, 13)[:-1]:
        pts.append((x-w/2+r*math.cos(t), spring+(z+h-spring)*math.sin(t)/math.sin(math.pi/3)))
    pts.append((x, z+h))
    for t in np.linspace(2*math.pi/3, math.pi, 13)[1:]:
        pts.append((x+w/2+r*math.cos(t), spring+(z+h-spring)*math.sin(t)/math.sin(math.pi/3)))
    return Polygon(pts)


def window(parts, cuts, center, tangent, normal, z, w, h, lights=2,
           pointed=False, transom=False, depth=.48, frame=.23, label='mullioned_windows'):
    """Deep pane recesses leave real stone mullions and tracery, plus a raised surround."""
    inner = gothic(0, z, w, h) if pointed else box(-w/2, z, w/2, z+h)
    bars = []
    bar = .32  # 0.50 mm in the full model; supported through the depth of the wall.
    cell = w/lights
    for i in range(1, lights):
        x = -w/2+i*cell
        bars.append(box(x-bar/2, z-.05, x+bar/2, z+h+.05))
    if transom:
        level = z+h*(.48 if not pointed else .49)
        bars.append(box(-w, level-bar/2, w, level+bar/2))
    # Each light has a small pointed head, with a stone spandrel above it.
    head_top = z+h*(.72 if pointed else 1.0)
    if pointed:
        for i in range(lights):
            x = -w/2+(i+.5)*cell
            arch = gothic(x, z+.05, cell, head_top-z-.05)
            bars.append(arch.boundary.buffer(bar/2, cap_style=2, join_style=2))
        # Small circles in the tracery are holes between the curved ribs.
        for i in range(lights-1):
            x = -w/2+(i+1)*cell
            ring = Point(x, z+h*.81).buffer(cell*.34, quad_segs=10)
            bars.append(ring.difference(ring.buffer(-.22)))
    else:
        # Three-center-like heads in the rectangular stone frame.
        for i in range(lights):
            x = -w/2+(i+.5)*cell
            cap = gothic(x, z+h-.65, cell-.08, .65)
            spandrel = box(x-cell/2, z+h-.65, x+cell/2, z+h).difference(cap)
            bars.append(spandrel)
    stone = unary_union(bars).intersection(inner) if bars else Polygon()
    panes = inner.difference(stone).buffer(-.006, join_style=2)
    cuts.append(facade(panes, center, tangent, normal, -depth, .55))
    # Mullions slightly stand forward of the recessed glazing.
    if not stone.is_empty:
        parts.append(facade(stone, center, tangent, normal, -depth-.05, .10))
    surround = inner.buffer(frame, join_style=2).difference(inner)
    parts.append(facade(surround, center, tangent, normal, -.10, .22))
    parts.append(facade(box(-w/2-frame-.12, z-.26, w/2+frame+.12, z+.03), center, tangent, normal, -.12, .34))
    if not pointed:
        # Hood mold with dropped stops, visible in the Mob Quad photographs.
        hood = unary_union([box(-w/2-.42, z+h+.20, w/2+.42, z+h+.43),
            box(-w/2-.42, z+h-.15, -w/2-.18, z+h+.30),
            box(w/2+.18, z+h-.15, w/2+.42, z+h+.30)])
        parts.append(facade(hood, center, tangent, normal, -.09, .29))
    COUNTS[label] += 1
    COUNTS['stone_mullions'] += lights-1
    COUNTS['transoms'] += bool(transom)


def doorway(parts, cuts, center, tangent, normal, height=2.5, width=1.55):
    p = gothic(0, .08, width, height)
    cuts.append(facade(p, center, tangent, normal, -.55, .5))
    rim = p.buffer(.27, join_style=2).difference(p)
    parts.append(facade(rim, center, tangent, normal, -.08, .24))
    COUNTS['pointed_doorways'] += 1


def roof(poly, eave, ridge):
    return union([from_tri(m) for m in original.gabled(poly, eave, ridge)])


def beam(a, b, width):
    """Square beam between 3D points: coping/ridge strip."""
    a, b = np.asarray(a), np.asarray(b)
    axis = b-a
    length = np.linalg.norm(axis)
    direction = axis/length
    trial = np.array([0., 0., 1.]) if abs(direction[2]) < .9 else np.array([0., 1., 0.])
    u = np.cross(direction, trial); u /= np.linalg.norm(u)
    v = np.cross(direction, u)
    return mf.Manifold.cube((width, width, length)).translate((-width/2, -width/2, 0)).transform(np.column_stack([u, v, direction, a]))


def gable(parts, cuts, center, tangent, normal, eave, ridge, width, inward,
          dormer=False):
    z = eave+.18 if dormer else eave-.35
    wall_top = z+1.50 if dormer else eave+.25
    apex = max(wall_top+1.0, ridge+.12)
    p = Polygon([(-width/2, z-.25), (width/2, z-.25), (width/2, wall_top), (0, apex), (-width/2, wall_top)])
    parts.append(facade(p, center, tangent, normal, -inward, .18))
    # Deep triangular shoulders tie the gable into the main roof.
    outline = LineString([(-width/2-.10, wall_top), (0, apex+.16), (width/2+.10, wall_top)]).buffer(.16, cap_style=2, join_style=2)
    parts.append(facade(outline, center, tangent, normal, -.18, .39))
    if dormer:
        window(parts, cuts, center+normal*.18, tangent, normal, z+.05, width*.65, 1.25, lights=2, depth=.35, frame=.17, label='dormer_windows')
    else:
        wh = min(1.5, (apex-z)*.51)
        window(parts, cuts, center+normal*.18, tangent, normal, z+.10, width*.40, wh, lights=3, depth=.4, frame=.18, label='gable_windows')
        # Stout apex finial and collar; deliberately not a sub-nozzle needle.
        xy = center+normal*.05
        parts += [block(*xy, apex-.1, .40, .40, .65), block(*xy, apex+.24, .54, .54, .23)]
    COUNTS['roof_dormers' if dormer else 'coped_gables'] += 1


def chimney(parts, cuts, xy, tangent, normal, roof_z, height=3.2, broad=True):
    w = 1.6 if broad else .95
    d = 1.0
    bottom = roof_z-3.0
    top = roof_z+height
    center = np.asarray(xy)
    # The flue mass extends deeply into the roof so every stack is connected.
    parts.append(facade(box(-w/2, bottom, w/2, top), center, tangent, normal, -d/2, d/2))
    for level, extra, thick in [(roof_z-.55,.18,.32),(top-.28,.18,.25),(top-.08,.24,.27)]:
        parts.append(facade(box(-w/2-extra,level,w/2+extra,level+thick), center,tangent,normal,-d/2-extra,d/2+extra))
    flues = 2 if broad else 1
    for i in range(flues):
        x = (i-(flues-1)/2)*.70
        # Thick shallow flue mouth gives an actual open top.
        hole_center = center+tangent*x
        cuts.append(block(*hole_center,top-.23,.40,.40,.8))
    for x in ([-.48,.48] if broad else [0.]):
        for sign in [-1,1]:
            parts.append(facade(box(x-.10,roof_z-.2,x+.10,top-.3),center,tangent,normal,sign*d/2-.12,sign*d/2+.12))
    COUNTS['chimney_stacks'] += 1
    COUNTS['flue_mouths'] += flues


def buttress(parts, center, tangent, normal, height=12.8):
    # Three setbacks, each with a sloping weathering stone.
    for z0,z1,depth,width in [(0,3.2,1.75,1.05),(3.15,7.7,1.30,.88),(7.65,height,.83,.72)]:
        parts.append(facade(box(-width/2,z0-.03,width/2,z1),center,tangent,normal,-.30,depth))
        # Side profile (outward depth, height) rotated into the wall-normal plane.
        cap = Polygon([(-.30,z1-.03),(depth+.12,z1-.03),(depth+.12,z1+.10),(.05,z1+.48),(-.30,z1+.48)])
        parts.append(facade(cap,center,normal,tangent,-width/2-.09,width/2+.09))
    COUNTS['stepped_buttresses'] += 1


def ridge_and_gable_ends(parts, poly, eave, ridge, others=None):
    rect = np.array(poly.minimum_rotated_rectangle.exterior.coords[:4])
    edges = np.roll(rect,-1,axis=0)-rect
    u = edges[np.argmax(np.linalg.norm(edges,axis=1))]
    u /= np.linalg.norm(u); v=np.array([-u[1],u[0]])
    points=np.array(poly.exterior.coords); along=points@u; across=points@v
    lo,hi=along.min(),along.max(); middle=(across.min()+across.max())/2
    ridge_line=LineString([u*lo+v*middle,u*hi+v*middle]).intersection(poly)
    for line in ([ridge_line] if ridge_line.geom_type=='LineString' else getattr(ridge_line,'geoms',[])):
        if line.length > 1:
            a,b=np.array(line.coords)[[0,-1]]
            parts.append(beam([*a,ridge+.04],[*b,ridge+.04],.30))
    for value,sign in [(lo,-1),(hi,1)]:
        c=u*value+v*middle
        if others is not None and others.covers(Point(*(c+u*sign*.5))):continue
        # Only add stone copings on genuine short end walls, not internal seams.
        cross=LineString([c-v*100,c+v*100]).intersection(poly.buffer(.02))
        if cross.geom_type!='LineString' or cross.length<2:continue
        a,b=np.array(cross.coords)[[0,-1]]
        if np.linalg.norm(a-b) > 18:continue
        parts.extend([beam([*a,eave+.08],[*c,ridge+.16],.32),beam([*c,ridge+.16],[*b,eave+.08],.32)])


def tower():
    parts=[block(0,0,-.04,10.8,10.8,28.2)]
    cuts=[]
    for z,width,h in [(14.9,11.18,.36),(15.45,11.55,.35),(20.0,11.12,.28),(26.8,11.42,.32),(27.25,11.7,.35)]:
        parts.append(block(0,0,z,width,width,h))
    # Upper parapet: hollow center, blind pierced frieze and open balustrade slots.
    ring=box(-5.65,-5.65,5.65,5.65).difference(box(-4.94,-4.94,4.94,4.94))
    parts.append(extrude(ring,27.4,30.15))
    cuts.append(block(0,0,28.0,9.86,9.86,5.0))
    for angle in [0,90,180,270]:
        a=math.radians(angle);t=np.array([math.cos(a),math.sin(a)]);n=np.array([-math.sin(a),math.cos(a)]);c=n*5.4
        for x in [-2.65,2.65]:
            window(parts,cuts,c+t*x,t,n,16.2,3.50,10.0,lights=4,pointed=True,transom=True,depth=.65,frame=.26,label='tower_traceried_windows')
            # Nested arch molding outside each main opening.
            p=gothic(0,16.2,3.5,10.)
            mold=p.buffer(.49,join_style=2).difference(p.buffer(.35,join_style=2))
            parts.append(facade(mold,c+t*x,t,n,-.07,.28))
        for x in np.linspace(-4.35,4.35,13):
            # Quatrefoil blind panels in the lower parapet frieze.
            flowers=unary_union([Point(x+dx,27.86+dz).buffer(.21,quad_segs=7) for dx,dz in [(-.15,0),(.15,0),(0,-.15),(0,.15)]])
            cuts.append(facade(flowers,c,t,n,-.25,.55))
        for x in np.linspace(-4.35,4.35,15):
            if abs(x)<.58:continue
            # True slots pass through the narrow upper parapet, leaving stout balusters.
            slot=gothic(x,28.53,.36,1.12)
            cuts.append(facade(slot,c,t,n,-.75,.65))
        for x in [-4.1,-2.7,-1.3,1.3,2.7,4.1]:
            parts.append(facade(box(x-.38,30.05,x+.38,30.65),c,t,n,-.46,.29))
            COUNTS['parapet_merlons']+=1
        COUNTS['pierced_parapet_faces']+=1
    # Eight pinacled piers with stepped weatherings, shaft panels and tapered crockets.
    for x,y in [(-5.08,-5.08),(-5.08,5.08),(5.08,-5.08),(5.08,5.08),(-5.18,0),(5.18,0),(0,-5.18),(0,5.18)]:
        parts.append(block(x,y,14.7,1.12,1.12,16.8))
        for z in [16.0,20.0,26.9,29.9,31.5]:parts.append(block(x,y,z,1.46,1.46,.29))
        parts.append(block(x,y,30.25,.94,.94,2.15))
        spire=mf.CrossSection([np.array([[-.65,-.65],[.65,-.65],[.65,.65],[-.65,.65]])]).extrude(3.0,scale_top=(.33,.33)).translate((x,y,32.15))
        parts.append(spire)
        for i,z in enumerate([32.35,32.85,33.35,33.85,34.35]):
            width=1.25-(z-32.15)*.29
            parts.append(block(x,y,z,width+.28,width+.28,.24))
            COUNTS['pinnacle_crocket_collars']+=1
        parts.append(block(x,y,35.02,.46,.46,.35))
        COUNTS['tower_pinnacles']+=1
    result=subtract(union(parts),cuts)
    FEATURES.append({'building':'Chapel tower','triangles':result.num_tri(),'detail':'Paired four-light Gothic belfry windows, tracery, transoms, nested archivolts, quatrefoil frieze, pierced parapet, eight crocketed pinnacles'})
    return result


def chapel(poly):
    parts=[extrude(poly,-.05,13.0)];cuts=[]
    for p in [poly.intersection(box(-20,-25,8.05,25)),poly.intersection(box(7,-5.6,45,7.2))]:
        parts.append(roof(p,13.,19.8));ridge_and_gable_ends(parts,p,13,19.8)
    # Six choir window bays, seven buttress stations on each long face.
    for side,y in [(-1,-5.45),(1,7.05)]:
        tangent=np.array([1.,0.]);normal=np.array([0.,float(side)])
        for x in np.linspace(10.2,35.8,7):buttress(parts,np.array([x,y]),tangent,normal)
        for x in np.linspace(12.33,33.67,6):window(parts,cuts,np.array([x,y]),tangent,normal,3.3,2.9,8.7,lights=3,pointed=True,transom=True,depth=.62,label='chapel_traceried_windows')
        parts.append(facade(box(8.2,12.75,37.9,13.65),np.array([0.,y]),tangent,normal,-.22,.28))
        parts.append(facade(box(8.2,13.5,37.9,13.82),np.array([0.,y]),tangent,normal,-.30,.39))
    window(parts,cuts,np.array([37.85,.8]),np.array([0.,1.]),np.array([1.,0.]),2.7,7.2,10.0,lights=5,pointed=True,transom=True,depth=.70,label='great_gothic_windows')
    for y in [-4.7,6.3]:buttress(parts,np.array([37.85,y]),np.array([0.,1.]),np.array([1.,0.]))
    for y,n,center_x in [(-18.03,-1,1.95),(19.0,1,.3)]:
        window(parts,cuts,np.array([center_x,y]),np.array([1.,0.]),np.array([0.,float(n)]),3.1,6.4,9.2,lights=5,pointed=True,transom=True,depth=.65,label='great_gothic_windows')
        window(parts,cuts,np.array([center_x,y]),np.array([1.,0.]),np.array([0.,float(n)]),15.0,1.2,1.9,lights=2,pointed=True,label='gable_lancets')
        for x in [center_x-4.6,center_x+4.6]:buttress(parts,np.array([x,y]),np.array([1.,0.]),np.array([0.,float(n)]))
    # West transept facade is oblique in the mapped outline.
    t=np.array([-.054, .9985]);normal=np.array([-.9985,-.054])
    for y in [-13.,-6.0,7.5,14.0]:
        x=-5.0-.054*y
        window(parts,cuts,np.array([x,y]),t,normal,3.0,3.3,8.8,lights=3,pointed=True,transom=True,depth=.65,label='chapel_traceried_windows')
    for y in [-17.,-9.5,10.7,18.0]:buttress(parts,np.array([-5.0-.054*y,y]),t,normal)
    # Octagonal stair turret visible at the chapel/Mob Quad junction.
    xy=np.array([7.1,-16.7]);parts.append(mf.Manifold.cylinder(15.2,1.72,circular_segments=8).translate((*xy,-.05)))
    parts.append(mf.Manifold.cylinder(.35,1.9,circular_segments=8).translate((*xy,14.8)))
    parts.append(mf.Manifold.cylinder(3.0,1.90,.24,circular_segments=8).translate((*xy,15.15)))
    window(parts,cuts,xy+np.array([0.,-1.59]),np.array([1.,0.]),np.array([0.,-1.]),10.5,.48,1.8,lights=1,depth=.35,label='turret_slits')
    COUNTS['octagonal_stair_turrets']+=1
    return subtract(union(parts),cuts)


def exposed_edges(poly, others):
    points=np.array(orient(poly).simplify(.16,preserve_topology=True).exterior.coords)
    for a,b in zip(points,points[1:]):
        length=np.linalg.norm(b-a)
        if length<3.3:continue
        tangent=(b-a)/length;normal=np.array([tangent[1],-tangent[0]])
        # Shared party walls receive no facade details.
        exposed=[not others.covers(Point(*(a+(b-a)*fraction+normal*.45))) for fraction in [.2,.5,.8]]
        if sum(exposed)<2:continue
        yield a,b,tangent,normal,length


def building(prop, poly, others):
    name=prop['name'];eave=prop['eave_agl_m'];ridge=prop['ridge_agl_m']
    parts=[extrude(poly,-.05,eave)];cuts=[]
    fellows=name.startswith("Fellows'")
    mob=name.startswith('Mob') or name=='Upper and Lower Libraries'
    if name=='Lodge':
        parts.append(extrude(poly.buffer(.25,join_style=2).difference(poly.buffer(-.6,join_style=2)),eave-.2,eave+1.0))
        # Recess the roof inside the gatehouse parapet.
        cuts.append(extrude(poly.buffer(-.65,join_style=2),eave-.55,eave+2))
    elif name=='Upper and Lower Libraries':
        for p in [poly.intersection(box(-5,-50,7.4,0)),poly.intersection(box(7.25,-50,40,-30))]:
            parts.append(roof(p,eave,ridge));ridge_and_gable_ends(parts,p,eave,ridge,others)
    else:
        parts.append(roof(poly,eave,ridge));ridge_and_gable_ends(parts,poly,eave,ridge,others)
    # Foundation plinth and eaves use the actual mapped polygon, not its rectangle.
    parts.append(extrude(poly.buffer(.15,join_style=2),.05,.40))
    parts.append(extrude(poly.buffer(.16,join_style=2),eave-.26,eave+.03))
    edges=list(exposed_edges(poly,others))
    stacks=[]
    for edge_index,(a,b,t,n,length) in enumerate(edges):
        count=max(1,int(round((length-1.0)/(4.1 if mob else 4.5))))
        bays=[a+(b-a)*(i+.5)/count for i in range(count)]
        major_fellows = fellows and (n[1]<-.65 or n[0]>.65) and length>8 and length>prop['roof_width_m']*1.1
        oriel_center = None
        if major_fellows and length>17:
            desired=a+(b-a)*(.20 if n[1]<-.65 else .72)
            oriel_center=min(bays,key=lambda c: np.linalg.norm(c-desired))
        if name=='Mob 6' and n[1]<-.65:
            oriel_center=np.array([12.8,-14.2])
        if name=='Hall':
            for c in bays:
                window(parts,cuts,c,t,n,3.4,2.25,6.15,lights=3,pointed=True,transom=True,label='hall_windows')
            for c in [a+(b-a)*j/count for j in range(1,count)]:buttress(parts,c,t,n,height=eave-.8)
        elif name=='Lodge':
            for c in bays:
                for z in [5.2,9.2,13.0]:window(parts,cuts,c,t,n,z,2.0,2.4,lights=2,transom=True)
            if length>6:
                doorway(parts,cuts,(a+b)/2,t,n,height=3.6,width=2.7)
                for i in range(int(length/1.1)):
                    c=a+(b-a)*(i+.5)/int(length/1.1)
                    parts.append(facade(box(-.34,eave+.85,.34,eave+1.65),c,t,n,-.52,.22))
                    COUNTS['parapet_merlons']+=1
        else:
            levels=3 if fellows or name.startswith("St Alban") else 2
            for i,c in enumerate(bays):
                for floor in range(levels):
                    z=.85+floor*((eave-1.25)/levels)
                    h=min(2.35,(eave-1.25)/levels-.65)
                    if floor>0 and oriel_center is not None and np.linalg.norm(c-oriel_center)<3.2:
                        continue
                    is_door=floor==0 and i==len(bays)//2 and length>8
                    if is_door:doorway(parts,cuts,c,t,n,height=min(2.7,h+.35))
                    else:window(parts,cuts,c,t,n,z,min(2.5,length/count*.53),h,lights=3 if i%3==0 else 2,transom=bool(fellows and floor==1))
            # Horizontal stone courses at floor transitions.
            if fellows:
                for z in [3.3,6.45]:parts.append(facade(box(-length/2,z,length/2,z+.22),(a+b)/2,t,n,-.12,.21))
        long_edge=length>8 and length>prop['roof_width_m']*1.1
        if long_edge and name not in ('Lodge','Hall'):
            major_fellows=fellows and (n[1]<-.65 or n[0]>.65)
            gcount=max(1,round(length/(6.8 if major_fellows else 5.8)))
            if major_fellows:
                for i in range(gcount):
                    c=a+(b-a)*(i+.5)/gcount
                    gable(parts,cuts,c,t,n,eave,ridge,min(5.0,length/gcount-.7),3.4)
                for i in range(1,gcount):
                    c=a+(b-a)*i/gcount-n*.45
                    stacks.append((c,t,n,ridge,3.3,True))
                # Projecting oriel, with real five-light mullions and transoms.
                if length>17:
                    c=oriel_center
                    oriel=box(-2.1,3.5,2.1,8.85)
                    parts.append(facade(oriel,c,t,n,-.2,.95))
                    apron=Polygon([(-1.45,2.9),(1.45,2.9),(2.1,3.55),(-2.1,3.55)])
                    parts.append(facade(apron,c,t,n,-.1,.95))
                    window(parts,cuts,c+n*.95,t,n,4.15,3.6,4.15,lights=5,transom=True,depth=.50,label='projecting_oriel_windows')
                    for z in [3.5,8.85]:parts.append(facade(box(-2.22,z,2.22,z+.28),c,t,n,-.1,1.05))
                    COUNTS['projecting_oriel_bays']+=1
            elif mob or name.startswith('Front') or fellows:
                for i in range(gcount):
                    # Inset dormer face stands on the roof rather than hanging above its edge.
                    c=a+(b-a)*(i+.5)/gcount-n*.85
                    gable(parts,cuts,c,t,n,eave,ridge-.1,2.35,2.3,dormer=True)
            if not major_fellows and not mob:
                c=(a+b)/2-n*(prop['roof_width_m']*.43)
                if not others.covers(Point(*c)) and poly.buffer(.1).covers(Point(*c)):
                    stacks.append((c,t,n,ridge,2.3,False))
    if mob and name!='Upper and Lower Libraries':
        c=np.array(poly.centroid.coords[0]);stacks.append((c,np.array([1.,0.]),np.array([0.,1.]),ridge,1.9,False))
    accepted=[]
    for c,t,n,r,h,broad in stacks:
        if any(np.linalg.norm(c-old)<2.5 for old in accepted):continue
        accepted.append(c);chimney(parts,cuts,c,t,n,r,h,broad)
    # Library oriel rising into the roof, as seen on the left of both Mob Quad photographs.
    if name=='Mob 6':
        c=np.array([12.8,-14.2]);t=np.array([1.,0.]);n=np.array([0.,-1.])
        parts.append(facade(box(-1.65,5.0,1.65,11.0),c,t,n,-.3,.70))
        window(parts,cuts,c+n*.70,t,n,6.1,2.8,4.3,lights=4,transom=True,depth=.45,label='projecting_oriel_windows')
        parts.append(facade(box(-1.85,10.9,1.85,11.35),c,t,n,-.3,.88))
        for x in [-1.5,-.5,.5,1.5]:parts.append(facade(Point(x,11.4).buffer(.25,quad_segs=8),c,t,n,-.2,.9))
        COUNTS['projecting_oriel_bays']+=1
    result=subtract(union(parts),cuts)
    FEATURES.append({'building':name,'triangles':result.num_tri(),'exposed_facades':len(edges),'eaves_agl_m':eave,'ridge_agl_m':ridge})
    return result


def print_frame(solid):
    return solid.transform(np.array([[C*SCALE,-S*SCALE,0,(E-original.BBOX[0])*SCALE],[S*SCALE,C*SCALE,0,(N-original.BBOX[1])*SCALE],[0,0,SCALE,BASE]]))


def save(solid,path):
    assert solid.status()==mf.Error.NoError, str(solid.status())
    # Adjacent ranges can seal blind window recesses inside party walls. Fill
    # those inaccessible cavities; retain all positive-volume exterior geometry.
    components=solid.decompose()
    positive=[p for p in components if p.volume()>.001]
    print('Kernel shells:',len(components),'positive volumes:',sorted([round(p.volume(),6) for p in positive],reverse=True)[:20],flush=True)
    solid=union(positive).set_tolerance(.01).simplify(.01)
    mesh=to_tri(solid)
    print('Before STL serialization:',mesh.is_watertight,flush=True)
    topology_parts=mesh.split(only_watertight=False)
    numerical_shells=[p for p in topology_parts if abs(p.volume)<.001]
    substantial=[p for p in topology_parts if abs(p.volume)>=.001]
    assert len(substantial)==1,[(len(p.faces),p.volume) for p in substantial]
    mesh=substantial[0]
    # Preserve the kernel's explicit topology through STL's coordinate-only storage.
    # Split coincident vertices by <0.001 mm, far below the print resolution.
    v=mesh.vertices.copy()
    _,inverse,count=np.unique(v.astype(np.float32),axis=0,return_inverse=True,return_counts=True)
    repeated=count[inverse]>1
    rng=np.random.default_rng(1047)
    shift=rng.uniform(-.0004,.0004,(int(repeated.sum()),3))
    v[repeated]+=shift
    v[:,2]=np.where(mesh.vertices[:,2]==0,0,v[:,2])
    mesh.vertices=v
    mesh.export(path)
    # Reload the actual delivered STL; never rely just on the construction kernel.
    mesh=trimesh.load_mesh(path,process=True)
    edge_incidence=np.bincount(mesh.edges_unique_inverse)
    pieces=mesh.split(only_watertight=False)
    report={'file':str(path.relative_to(ROOT)),'dimensions_mm':mesh.extents.round(4).tolist(),'triangles':len(mesh.faces),'vertices':len(mesh.vertices),'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'connected_components':len(pieces),'nonmanifold_or_boundary_edges':int(np.count_nonzero(edge_incidence!=2)),'volume_mm3':float(mesh.volume),'minimum_z':float(mesh.bounds[0,2]),'filled_inaccessible_cavities':sum(p.volume()<0 for p in components),'pruned_numerical_shells':len(numerical_shells),'separated_coincident_vertices':int(repeated.sum()),'maximum_vertex_separation_mm':.0004*math.sqrt(3),'surface_simplification_tolerance_mm':.01}
    assert report['watertight'] and report['winding_consistent'] and len(pieces)==1 and report['nonmanifold_or_boundary_edges']==0,report
    return report


def main():
    start=time.time()
    data=json.loads((ROOT/'approaches/architectural/building_footprints.geojson').read_text())
    buildings=[]
    for f in data['features']:
        p=affine_transform(shape(f['geometry']),[C,S,-S,C,-C*E-S*N,S*E-C*N]).simplify(.06,preserve_topology=True)
        buildings.append((f['properties'],orient(p)))
    pieces=[]
    for index,(prop,p) in enumerate(buildings):
        others=unary_union([q for j,(_,q) in enumerate(buildings) if j!=index])
        print(f"Building {index+1}/{len(buildings)}: {prop['name']}",flush=True)
        detail=chapel(p) if prop['name']=='Merton College Chapel' else building(prop,p,others)
        pieces.append(detail)
    print('Building traceried tower and pierced parapet',flush=True)
    tower_part=tower();pieces.append(tower_part)
    width=220;depth=(original.BBOX[3]-original.BBOX[1])*SCALE
    base=block(width/2,depth/2,0,width,depth,BASE)
    print('Unioning the complete college',flush=True)
    college=union([base,*[print_frame(s) for s in pieces]])
    out=ROOT/'deliverables';out.mkdir(exist_ok=True)
    report=save(college,out/'merton-detailed.stl')
    # Enlarged chapel detail sample is useful for seeing/testing the fine tracery.
    cp=buildings[0][1]
    chapel_solid=union([pieces[0],tower_part])
    bounds=cp.buffer(2.8).bounds
    sample_base=extrude(box(*bounds),-1.9,0)
    chapel_solid=union([sample_base,chapel_solid])
    chapel_solid=chapel_solid.translate((-bounds[0],-bounds[1],1.9)).scale((3.0,3.0,3.0))
    sample_report=save(chapel_solid,out/'merton-detailed-chapel-1-333.stl')
    report.update(scale_denominator=1000/SCALE,base_thickness_mm=BASE,minimum_mullion_mm=.32*SCALE,minimum_spire_tip_mm=.429*SCALE,feature_counts=dict(COUNTS),build_seconds=round(time.time()-start,2),source_images=[p.name for p in sorted((ROOT/'images').iterdir()) if p.is_file()],interpretation='Photograph-informed architectural reconstruction; unseen facade rhythms and dimensions are estimated. Details thickened for printing. No physical print tested.')
    (HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'chapel-validation.json').write_text(json.dumps(sample_report,indent=2)+'\n')
    (HERE/'feature-register.json').write_text(json.dumps(FEATURES,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
