"""Reproducible mechanical alpha crop/pad; source art is never repainted."""
import json
import io
from contextlib import redirect_stdout
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import prepare_stage5_art as preparation


if __name__ == '__main__':
    output = ROOT / 'assets/chapter2_units'
    preparation.NAMES = {kind: kind + '.png' for kind in ('pawn', 'rook')}
    with redirect_stdout(io.StringIO()):
        preparation.prepare(output / 'source', output)
    manifest = json.loads((output / 'asset_manifest.json').read_text(encoding='utf-8'))
    print('Actual prepared assets:', len(manifest['assets']))
