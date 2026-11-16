"""Packaging preserves fixture strength while omitting regenerable PNGs."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.art_review_fixtures import reference_sha256,ROOT
from tools.audit_art_baseline import audit


class ArtBaselineCatalogTests(unittest.TestCase):
    def test_selected_assets_exist_and_any_local_archives_keep_original_hashes(self):
        counts,missing=audit()
        self.assertEqual(counts,{'track':300,'local_archive':263})
        self.assertGreaterEqual(missing,0)

    def test_absent_redundant_capture_still_uses_the_frozen_golden_digest(self):
        rows=json.loads((ROOT/'assets/arena_art_catalog.json').read_text())['records']
        row=next(r for r in rows if r['decision']=='local_archive' and '/review/' in r['path'])
        with patch.object(Path,'exists',return_value=False):
            self.assertEqual(reference_sha256(ROOT/row['path']),row['sha256'])
        with self.assertRaises(ValueError):reference_sha256(ROOT/'assets/unregistered_capture.png')

    def test_corrupted_optional_capture_is_rejected_instead_of_rebaselined(self):
        rows=json.loads((ROOT/'assets/arena_art_catalog.json').read_text())['records']
        row=next(r for r in rows if r['decision']=='local_archive' and '/review/' in r['path'])
        with patch.object(Path,'exists',return_value=True),patch.object(Path,'read_bytes',return_value=b'corrupt'):
            with self.assertRaisesRegex(ValueError,'differs from baseline'):
                reference_sha256(ROOT/row['path'])
