# AyuGram Desktop Portable Builder v1.0

A **manual, Windows x64 GitHub Actions builder** that repackages the **official, already-compiled** [AyuGram Desktop](https://github.com/AyuGram/AyuGramDesktop) Windows release into the user's PortableApps-style structure. It does not compile AyuGram's giant C++ codebase or replace its original program files.

## Build in your browser

1. Create a **new, empty** repository named `AyuGram-Portable-Builder` on GitHub.
2. Upload **the contents of this builder ZIP**, including the hidden `.github/workflows/build-ayugram-portable.yml` file. Do not upload the enclosing builder directory as an extra level.
3. Open the repository **Actions** tab. Allow workflows if GitHub asks.
4. Click **Build AyuGram Portable (Manual) → Run workflow**. Leave `upstream_ref` as `latest` for the current stable release, or provide a tag such as `v7.2.9`.
5. Open the completed build's **Artifacts** section, download `AyuGram-Portable-Windows-x64`, and extract the `AyuGramPortable-Win64.zip` inside it.
6. Extract that ZIP to the location of your choice and run `AyuGramPortable.exe`.

Only the **final application ZIP** is published as an artifact. Retention is **1 day**. The builder kit itself is not the application.

## What your final ZIP contains

```text
AyuGramPortable/
├── AyuGramPortable.exe       # Native Windows .NET launcher, official icon
├── App/
│   ├── AyuGram/
│   │   ├── AyuGram.exe       # Untouched upstream Windows binary
│   │   └── ...              # Upstream libraries and resources
│   └── AppInfo/
│       ├── appinfo.ini       # PortableApps.com Menu metadata
│       ├── appicon.ico      # Original AyuGram icon extracted from binary
│       ├── appicon_16.png
│       ├── appicon_32.png
│       ├── appicon_75.png
│       └── appicon_128.png
├── Data/
│   ├── tdata/                # Private account, settings, cache, history
│   └── Downloads/            # Optional target for app's download setting
└── Other/
    ├── build-info.json      # Version, source URL and SHA-256
    ├── Launcher-Source.cs   # Source for the small portable launcher
    └── README-PORTABLE.txt
```

## Upgrading without losing your login

1. **Quit AyuGram fully**, including from the Windows notification area.
2. **Back up the entire `Data` folder**. It contains login/session credentials and cached chat content; keep it private.
3. Build the new version and extract the resulting ZIP to a **separate** temporary location.
4. Replace your existing **`App` folder**, **root `AyuGramPortable.exe`** and **`Other` folder** with the new ones.
5. Keep the **old `Data` folder entirely untouched**. Launch normally.

Do **not** overwrite the root folder with a freshly extracted archive and assume an unzip tool will preserve your `Data` folder: some extraction/merge operations can destroy it.

## Portability and privacy boundaries

- `AyuGramPortable.exe` launches `App/AyuGram/AyuGram.exe` with `-workdir <portable root>/Data` and `-noupdate`, so normal profile files land in `Data/tdata` rather than the replaceable `App` directory.
- No initial configuration, terminal command, or user cleanup is required before first launch. This builder avoids modifying the application's source, and does not automatically create registry entries or start-menu shortcuts.
- To keep downloaded files portable, **inside AyuGram change its Download path to the bundled `Data/Downloads` folder**. Other paths set in-app will not be redirected.
- Avoid AyuGram's optional **autostart**, **register URL handler**, **Explorer integration** and **custom host icon** settings. The Windows system and AyuGram features can create traces outside the portable directory; this isn't a sandbox and absolute zero traces cannot be guaranteed.
- Telegram/AyuGram profile material is security-sensitive. Keep your `Data` folder encrypted or protected as appropriate. **Never commit `Data` to GitHub or send it to anyone.**
- Updates are applied using **new manually triggered ZIP builds**. The launcher passes `-noupdate` to avoid applying in-app updates.
- GitHub Actions fetches upstream binaries from **the official GitHub Releases URL**, not from mirrors, checks the publisher-provided SHA-256 digest when present, and always records its computed SHA-256 in `Other/build-info.json`.

## Scope and limitations

- **Windows 10/11 x64**, and standard .NET Framework 4.x launcher runtime.
- The GitHub Action does layout, launcher compilation, integrity and format checks. It cannot fully verify QR sign-in, actual profile persistence, voice/video calls or cleanup of every Windows integration without an interactive application test on your computer.
- The packaged binaries come from AyuGram's own release. Build issues in the upstream client cannot be solved by this repackager.
- Do not assume Telegram server-side authorization and live sessions remain valid after a Windows reinstall or transfer. Re-login may be required.

## Credits and licensing

AyuGram Desktop is an independent Telegram client from [AyuGram contributors](https://github.com/AyuGram/AyuGramDesktop), licensed under the upstream project's GPL-3.0 terms. No affiliation with Telegram FZ-LLC. This portable launcher is a small independent packaging tool and uses the publisher's original icon.
