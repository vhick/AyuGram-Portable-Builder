"""Statically check output before publishing user-facing ZIP."""
import argparse
import json
from pathlib import Path
import re
import struct


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument('--root', type=Path, required=True)
    args = arg.parse_args()
    root = args.root
    required = [
        'AyuGramPortable.exe', 'App/AyuGram/AyuGram.exe',
        'App/AppInfo/appinfo.ini', 'App/AppInfo/appicon.ico',
        'App/AppInfo/appicon_16.png', 'App/AppInfo/appicon_32.png',
        'Data/tdata', 'Data/Downloads', 'Other/build-info.json',
        'Other/README-PORTABLE.txt', 'Other/Launcher-Source.cs',
    ]
    for item in required:
        if not (root / item).exists():
            raise AssertionError('Missing required path: ' + item)
    exe = (root / 'AyuGramPortable.exe').read_bytes()
    if exe[:2] != b'MZ':
        raise AssertionError('Launcher is not a Windows EXE')
    pe_offset = struct.unpack_from('<I', exe, 0x3c)[0]
    if exe[pe_offset:pe_offset + 4] != b'PE\0\0':
        raise AssertionError('Launcher has no PE header')
    if struct.unpack_from('<H', exe, pe_offset + 4)[0] != 0x8664:
        raise AssertionError('Launcher must be x64 Windows executable')
    icon = (root / 'App/AppInfo/appicon.ico').read_bytes()
    if len(icon) < 100 or icon[:4] != b'\x00\x00\x01\x00':
        raise AssertionError('Launcher icon is not a valid ICO')
    ini = (root / 'App/AppInfo/appinfo.ini').read_text(encoding='utf-8')
    if 'Start=AyuGramPortable.exe' not in ini or 'AppID=AyuGramPortable' not in ini:
        raise AssertionError('PortableApps menu metadata is invalid')
    info = json.loads((root / 'Other/build-info.json').read_text(encoding='utf-8'))
    if not re.fullmatch('[0-9a-f]{64}', info['download_sha256']):
        raise AssertionError('Release digest is not a SHA-256')
    if (root / 'App/AyuGram/tdata').exists():
        raise AssertionError('User data must never be inside replaceable App')
    print('PASS: x64 launcher, original icon, AppInfo, source, Data/Other isolation.')


if __name__ == '__main__':
    main()
