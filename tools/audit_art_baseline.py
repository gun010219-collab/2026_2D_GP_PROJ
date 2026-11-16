"""Verify the selected baseline and preserve optional local archives by hash."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def audit(root=ROOT,check_index=False):
    data=json.loads((root/'assets/arena_art_catalog.json').read_text(encoding='utf-8'))
    seen=set();counts={'track':0,'local_archive':0};missing_archive=0
    for row in data['records']:
        name=row['path'];path=(root/name).resolve()
        if name in seen or not path.is_relative_to(root.resolve()):raise ValueError('Invalid catalog path: '+name)
        seen.add(name);counts[row['decision']]+=1
        if not path.is_file():
            if row['decision']=='track':raise FileNotFoundError(path)
            missing_archive+=1;continue
        if path.stat().st_size!=row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Art changed: '+name)
    if check_index:
        indexed=set(subprocess.check_output(['git','ls-files','--cached'],cwd=root,text=True).splitlines())
        for row in data['records']:
            if (row['path'] in indexed)!=(row['decision']=='track'):raise ValueError('Index policy differs: '+row['path'])
    print('PASS art catalog:',counts,'optional archives absent:',missing_archive)
    return counts,missing_archive


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',action='store_true',help='also verify selected Git index membership')
    audit(check_index=parser.parse_args().index)
