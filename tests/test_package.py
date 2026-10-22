import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools.package import package
from tools.build import verify_archive_paths, stage_release, create_metadata


class ZipSafetyTests(unittest.TestCase):
    def test_rejects_zip_slip(self):
        with tempfile.TemporaryDirectory() as temp:
            zip_file = Path(temp) / 'bad.zip'
            with ZipFile(zip_file, 'w') as z:
                z.writestr('../bad.txt', 'BAD')
            with ZipFile(zip_file) as z:
                with self.assertRaisesRegex(RuntimeError, 'Unsafe ZIP'):
                    verify_archive_paths(z)

    def test_stages_binary_and_modules_without_user_data(self):
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp)
            zip_file = test_dir / 'upstream.zip'
            with ZipFile(zip_file, 'w') as z:
                z.writestr('AyuGramDesktop/AyuGram.exe', b'MZ fake upstream exe')
                z.writestr('AyuGramDesktop/modules/x64/sample.dll', b'dll')
                z.writestr('AyuGramDesktop/tdata/secret', b'private')
                z.writestr('AyuGramDesktop/log_start0.txt', b'old')
            root = test_dir / 'AyuGramPortable'
            root.mkdir()
            stage_release(zip_file, root)
            self.assertTrue((root / 'App/AyuGram/AyuGram.exe').exists())
            self.assertTrue((root / 'App/AyuGram/modules/x64/sample.dll').exists())
            self.assertFalse((root / 'App/AyuGram/tdata').exists())
            self.assertFalse((root / 'App/AyuGram/log_start0.txt').exists())

    def test_creates_release_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'AyuGramPortable'
            create_metadata(root, 'v7.2.9', 'a' * 64,
                            {'browser_download_url': 'https://github.com/AyuGram/AyuGramDesktop/releases/download/v7.2.9/AyuGram.zip'})
            self.assertIn('PackageVersion=7.2.9.0',
                          (root / 'App/AppInfo/appinfo.ini').read_text())
            self.assertEqual(__import__('json').loads((root / 'Other/build-info.json').read_text())['release_tag'], 'v7.2.9')

    def test_single_top_level_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'AyuGramPortable'
            root.mkdir()
            (root / 'AyuGramPortable.exe').write_bytes(b'MZ')
            (root / 'Data/tdata').mkdir(parents=True)
            result = Path(temp) / 'output.zip'
            package(root, result)
            with ZipFile(result) as z:
                self.assertIn('AyuGramPortable/AyuGramPortable.exe', z.namelist())
                self.assertIn('AyuGramPortable/Data/tdata/', z.namelist())
                self.assertTrue(all(p.startswith('AyuGramPortable/') for p in z.namelist()))


if __name__ == '__main__':
    unittest.main()
