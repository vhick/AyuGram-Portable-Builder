"""Fetch the ORIGINAL upstream Windows portable ZIP and arrange its files.

On GitHub Actions this runs on Windows x64 and uses the release publisher's
existing binaries. The source is NOT rebuilt, patched, or re-signed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import urllib.request
import zipfile

OWNER_REPO = "AyuGram/AyuGramDesktop"
USER_AGENT = "AyuGram-Portable-Builder/1.0"


def request_bytes(url: str) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN", "")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as res:
        return res.read()


def get_release(tag: str) -> dict:
    if tag != "latest" and not re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-.][a-zA-Z0-9.-]+)?", tag):
        raise ValueError("Enter 'latest' or a release tag like v7.2.9")
    url = (f"https://api.github.com/repos/{OWNER_REPO}/releases/latest" if tag == "latest"
           else f"https://api.github.com/repos/{OWNER_REPO}/releases/tags/{tag}")
    release = json.loads(request_bytes(url))
    if release.get("draft") or release.get("prerelease"):
        raise RuntimeError("Only published non-prerelease versions are packaged.")
    if not release.get("tag_name", "").startswith("v"):
        raise RuntimeError("Unexpected upstream release tag")
    return release


def download(url: str, destination: Path) -> str:
    # Release binary, not a GitHub-generated source archive.
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    hasher = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=180) as response, destination.open("wb") as f:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            f.write(chunk)
    return hasher.hexdigest()


def verify_archive_paths(zf: zipfile.ZipFile) -> None:
    """No zip-slip paths or hidden symlink tricks."""
    for member in zf.infolist():
        name = member.filename.replace("\\", "/")
        if (name.startswith("/") or re.match(r"^[A-Za-z]:", name) or
                ".." in name.split("/") or (member.external_attr >> 16) & 0o170000 == 0o120000):
            raise RuntimeError("Unsafe ZIP member: " + name)


def stage_release(zip_path: Path, root: Path) -> None:
    app = root / "App" / "AyuGram"
    with tempfile.TemporaryDirectory(prefix="ayu_extracted_") as tmp:
        temp = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            verify_archive_paths(archive)
            archive.extractall(temp)
        candidates = [p for p in temp.rglob("AyuGram.exe") if p.is_file()]
        if not candidates:
            raise RuntimeError("Official Windows ZIP did not contain AyuGram.exe.")
        if len(candidates) != 1:
            raise RuntimeError(f"Unexpected number of AyuGram.exe files ({len(candidates)}).")
        source = candidates[0].parent
        app.mkdir(parents=True, exist_ok=True)
        ignored = {"tdata", "tupdates", "downloads", "temp_data", "logs"}
        for entry in source.iterdir():
            if entry.name.lower() in ignored or entry.name.lower().startswith("log_start"):
                continue
            if entry.is_dir():
                shutil.copytree(entry, app / entry.name, dirs_exist_ok=True)
            else:
                shutil.copy2(entry, app / entry.name)
        if not (app / "AyuGram.exe").is_file():
            raise RuntimeError("AyuGram.exe wasn't copied to App.")
        if any(p.is_dir() and p.name.lower() == "tdata" for p in app.rglob("*")):
            raise RuntimeError("Unexpected user-data folder was included under App.")


def extract_brand_icon(binary: Path, appinfo: Path) -> None:
    # Extract ORIGINAL embedded multi-resolution icon; no Windows associated-icon shortcut.
    from icoextract import IconExtractor
    from PIL import Image
    extractor = IconExtractor(str(binary))
    icon = appinfo / "appicon.ico"
    extractor.export_icon(str(icon), num=0)
    if not icon.is_file() or icon.stat().st_size < 100:
        raise RuntimeError("Could not extract AyuGram's original icon")
    with Image.open(icon) as im:
        for size in (16, 32, 75, 128):
            im.seek(0)
            rendered = im.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
            rendered.save(appinfo / f"appicon_{size}.png")


def create_metadata(root: Path, tag: str, digest: str, asset: dict) -> None:
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)(?:.*)?", tag)
    if not match:
        raise RuntimeError("Unsupported release version")
    major, minor, patch = match.groups()
    appinfo = root / "App" / "AppInfo"
    appinfo.mkdir(parents=True, exist_ok=True)
    ini = f"""[Format]
Type=PortableApps.comFormat
Version=3.8

[Details]
Name=AyuGram Desktop Portable
AppID=AyuGramPortable
Publisher=AyuGram contributors & Portable Builder
Homepage=https://github.com/AyuGram/AyuGramDesktop
Category=Internet
Description=Portable desktop Telegram client with AyuGram customization
Language=Multilingual

[License]
Shareable=true
OpenSource=true
Freeware=true
CommercialUse=true

[Version]
PackageVersion={major}.{minor}.{patch}.0
DisplayVersion={tag}

[Control]
Icons=1
Start=AyuGramPortable.exe
"""
    (appinfo / "appinfo.ini").write_text(ini, encoding="utf-8")
    other = root / "Other"
    other.mkdir(parents=True, exist_ok=True)
    info = {
        "builder_version": "1.0",
        "upstream": f"https://github.com/{OWNER_REPO}",
        "release_tag": tag,
        "download_url": asset["browser_download_url"],
        "download_sha256": digest,
        "asset_declared_digest": asset.get("digest", ""),
        "portable_data_directory": "Data",
    }
    (other / "build-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    (other / "README-PORTABLE.txt").write_text('''AyuGram Desktop Portable — builder 1.0

START: Run AyuGramPortable.exe in the root folder.
DATA: Keep Data/ when updating. Login credentials, settings, caches and
      message history normally live in Data/tdata/.
UPGRADE: Quit AyuGram completely (including notification tray). Back up
         Data/. Extract the new ZIP, and replace App/, Other/ and the root
         AyuGramPortable.exe. Do not replace/delete your existing Data/.
DOWNLOADS: Configure AyuGram Settings > Advanced > Download path to
           the portable Data/Downloads folder. Other chosen download paths
           are outside our control.
INTEGRATION: Do not enable in-app 'Launch at startup' or 'Register as
             handler' if you want to limit host-PC traces. Windows can still
             create system caches and notification state. This is not a sandbox.
SECURITY: Data/tdata includes sensitive Telegram authentication material.
          Never share or publish your populated Data folder on GitHub.
          Use a local passcode and secure the drive.
UPDATE: The portable launcher passes -noupdate; use a fresh GitHub Actions
        build to update the app, rather than the in-app updater.
SOURCE: https://github.com/AyuGram/AyuGramDesktop
''', encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", default="latest")
    parser.add_argument("--out", type=Path, default=Path("dist"))
    args = parser.parse_args()
    release = get_release(args.release)
    tag = release["tag_name"]
    assets = [a for a in release["assets"] if a["name"].casefold() == "ayugram.zip"]
    if len(assets) != 1:
        raise RuntimeError("Cannot find unique official AyuGram.zip release asset")
    asset = assets[0]
    if not asset["browser_download_url"].startswith(f"https://github.com/{OWNER_REPO}/releases/download/"):
        raise RuntimeError("Unexpected asset download domain")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    root = out / "AyuGramPortable"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    with tempfile.TemporaryDirectory(prefix="ayu_asset_") as tmp:
        zip_file = Path(tmp) / "AyuGram.zip"
        digest = download(asset["browser_download_url"], zip_file)
        expected = asset.get("digest") or ""
        if expected and expected.startswith("sha256:") and digest.casefold() != expected[7:].casefold():
            raise RuntimeError("Official GitHub asset SHA-256 checksum mismatch")
        print(f"Selected official upstream release: {tag}")
        print(f"Verified/downloaded SHA-256: {digest}")
        stage_release(zip_file, root)
    create_metadata(root, tag, digest, asset)
    shutil.copy2(Path(__file__).resolve().parent.parent / "launcher" / "AyuGramPortable.cs",
                 root / "Other" / "Launcher-Source.cs")
    extract_brand_icon(root / "App" / "AyuGram" / "AyuGram.exe", root / "App" / "AppInfo")
    (root / "Data" / "tdata").mkdir(parents=True)
    (root / "Data" / "Downloads").mkdir(parents=True)
    print("Release staged at:", root)


if __name__ == "__main__":
    main()
