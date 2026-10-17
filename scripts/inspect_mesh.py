"""Inspect delivered meshes without repairing away evidence of defects."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh


def inspect(path):
    mesh = trimesh.load_mesh(path, process=True)
    edge_incidence = np.bincount(mesh.edges_unique_inverse)
    pieces = mesh.split(only_watertight=False)
    result = {
        'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'vertices': len(mesh.vertices), 'triangles': len(mesh.faces),
        'bounds_mm': mesh.bounds.round(6).tolist(),
        'dimensions_mm': mesh.extents.round(4).tolist(),
        'volume_mm3': round(float(mesh.volume), 3),
        'watertight': bool(mesh.is_watertight),
        'winding_consistent': bool(mesh.is_winding_consistent),
        'positive_volume': bool(mesh.volume > 0),
        'boundary_edges': int(np.sum(edge_incidence == 1)),
        'nonmanifold_edges': int(np.sum(edge_incidence > 2)),
        'connected_components': len(pieces),
        'sits_flat_at_z0': bool(abs(mesh.bounds[0, 2]) < 1e-4),
        'fits_a1_256_cube': bool(np.all(mesh.extents <= 256)),
        'finite_vertices': bool(np.isfinite(mesh.vertices).all()),
    }
    result['geometry_pass'] = bool(
        result['watertight'] and result['winding_consistent']
        and result['positive_volume'] and result['boundary_edges'] == 0
        and result['nonmanifold_edges'] == 0
        and result['connected_components'] == 1
        and result['sits_flat_at_z0'] and result['fits_a1_256_cube']
        and result['finite_vertices']
    )
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    results = [inspect(path.resolve()) for path in args.paths]
    output = json.dumps(results, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    print(output)
    raise SystemExit(0 if all(item['geometry_pass'] for item in results) else 1)
