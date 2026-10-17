"""Validate supplied STLs in the installed Bambu Studio and save A1 projects.

Slicing only: this script does not contact a printer or submit a print.
"""
import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BAMBU='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'


def run(key):
    output=ROOT/'validation'/f'{key}_slice'
    output.mkdir(exist_ok=True)
    if key=='samples':
        inputs=[ROOT/'deliverables/chapel-samples'/f'{name}-chapel.stl' for name in ['lidar','architectural','hybrid']]
        filename='merton-chapel-comparison-a1.3mf'
    else:
        inputs=[ROOT/'deliverables'/f'merton-{key}.stl']
        filename=f'merton-{key}-a1.3mf'
    command=[BAMBU,'--debug','2','--load-settings',
        ';'.join(str(ROOT/'settings'/f'a1_04_{kind}.json') for kind in ['machine','process']),
        '--load-filaments',str(ROOT/'settings/a1_04_filament.json'),
        '--arrange','1','--orient','0','--slice','0',
        '--export-3mf',filename,'--outputdir',str(output),*map(str,inputs)]
    with (ROOT/'validation'/f'{key}_slice.log').open('w') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Bambu Studio failed for {key}; see validation/{key}_slice.log')
    report=json.loads((output/'result.json').read_text())
    assert report['return_code']==0 and report['error_string']=='Success.'
    source=output/filename
    with zipfile.ZipFile(source) as archive:
        settings=json.loads(archive.read('Metadata/project_settings.config'))
        assert settings['printer_model']=='Bambu Lab A1'
        assert settings['nozzle_diameter']==['0.4']
        assert settings['curr_bed_type']=='Textured PEI Plate'
        assert settings['enable_support']=='0'
        assert 'Metadata/plate_1.gcode' in archive.namelist()
        # Export a small actual slicer thumbnail for the build evidence.
        (output/'slicer-thumbnail.png').write_bytes(archive.read('Metadata/plate_1.png'))
    for plate in report['sliced_plates']:
        for item in plate['objects']:
            bounds=item['bbox']
            assert bounds['x']>=0 and bounds['y']>=0 and bounds['z']>=0
            assert bounds['x']+bounds['width']<=256.01
            assert bounds['y']+bounds['depth']<=256.01
            assert bounds['height']<=256
    shutil.copy2(source,ROOT/'deliverables'/filename)
    print(json.dumps({'model':key,'3mf':filename,
        'seconds':sum(p['total_predication'] for p in report['sliced_plates']),
        'pla_grams':sum(f['total_used_g'] for p in report['sliced_plates'] for f in p['filaments']),
        'warnings':[p['warning_message'] for p in report['sliced_plates'] if p.get('warning_message')]}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('models',nargs='+',choices=['lidar','architectural','hybrid','samples'])
    for model in parser.parse_args().models:run(model)
