"""Build final single-parent-folder, ZIP-only artifact."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def package(root: Path, output: Path) -> None:
    root = root.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if root.name != 'AyuGramPortable':
        raise ValueError('Expected root directory AyuGramPortable')
    if not (root / 'AyuGramPortable.exe').exists():
        raise RuntimeError('Launcher was not compiled')
    with ZipFile(output, 'w', compression=ZIP_DEFLATED, compresslevel=8,
                 allowZip64=True) as archive:
        for folder in sorted(p for p in root.rglob('*') if p.is_dir()):
            if not any(folder.iterdir()):
                archive.writestr(folder.relative_to(root.parent).as_posix() + '/', '')
        for file in sorted(p for p in root.rglob('*') if p.is_file()):
            archive.write(file, file.relative_to(root.parent).as_posix())
    print('Created:', output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    package(args.root, args.out)


if __name__ == '__main__':
    main()
