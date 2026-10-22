"""Regression tests for the Windows csc.exe launcher source path failure."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class WorkflowRegressionTests(unittest.TestCase):
    def test_csharp_source_exists_in_builder(self):
        self.assertTrue((ROOT / 'launcher' / 'AyuGramPortable.cs').is_file())

    def test_compiler_uses_absolute_resolved_source_path(self):
        workflow = (ROOT / '.github' / 'workflows' / 'build-ayugram-portable.yml').read_text(encoding='utf-8')
        self.assertIn("$source = (Resolve-Path -LiteralPath '.\\launcher\\AyuGramPortable.cs'", workflow)
        self.assertIn('if (!(Test-Path -LiteralPath $source -PathType Leaf))', workflow)
        # This regression caused CS1504: CSC ignored the relative folder and
        # tried to open the file from the repository root.
        self.assertNotIn(' /reference:System.Windows.Forms.dll launcher/AyuGramPortable.cs', workflow)
        self.assertIn("'/reference:System.Windows.Forms.dll' $source", workflow)

    def test_build_still_uses_manual_trigger_and_zip_only(self):
        workflow = (ROOT / '.github' / 'workflows' / 'build-ayugram-portable.yml').read_text(encoding='utf-8')
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('retention-days: 1', workflow)
        self.assertIn('path: dist/AyuGramPortable-Win64.zip', workflow)


if __name__ == '__main__':
    unittest.main()
