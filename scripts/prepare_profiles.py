"""Freeze installed Bambu Studio presets, including inheritance and G-code includes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESETS = Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')


def resolve(kind, name, chain=()):
    if name in chain:
        raise ValueError(f'Preset cycle: {chain}, {name}')
    source = json.loads((PRESETS / kind / f'{name}.json').read_text())
    result = resolve(kind, source['inherits'], (*chain, name)) if source.get('inherits') else {}
    for included in source.get('include', []):
        result.update(resolve(kind, included, (*chain, name)))
    result.update(source)
    result.pop('inherits', None)
    result.pop('include', None)
    return result


def main():
    configs = {
        'machine': resolve('machine', 'Bambu Lab A1 0.4 nozzle'),
        'process': resolve('process', '0.16mm High Quality @BBL A1'),
        'filament': resolve('filament', 'Generic PLA @BBL A1'),
    }
    configs['process'].update({
        'wall_loops': '3', 'sparse_infill_density': '12%',
        'enable_support': '0', 'brim_type': 'no_brim',
        'top_shell_layers': '5', 'bottom_shell_layers': '4',
    })
    configs['machine']['curr_bed_type'] = 'Textured PEI Plate'
    for kind, config in configs.items():
        path = ROOT / 'settings' / f'a1_04_{kind}.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(config, indent=2) + '\n')
        print(path)


if __name__ == '__main__':
    main()
