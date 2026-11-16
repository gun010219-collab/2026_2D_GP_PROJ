"""Immutable golden PNG digests allow redundant captures to remain local.

The digest is never updated by a test or read from the newly rendered image.
Kept pixel-reference PNGs still support all existing per-cell comparisons.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def reference_sha256(path):
    path=Path(path).resolve()
    key=path.relative_to(ROOT).as_posix()
    records=json.loads((ROOT/'assets/arena_art_catalog.json').read_text(encoding='utf-8'))['records']
    matches=[r for r in records if r['path']==key]
    if len(matches)!=1:raise ValueError('Missing or duplicate golden capture: '+key)
    digest=matches[0]['sha256']
    if len(digest)!=64:raise ValueError('Invalid golden digest: '+key)
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise ValueError('Stored capture differs from baseline: '+key)
    return digest
