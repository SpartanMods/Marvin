#!/usr/bin/env python3
"""Package the skin for "Install from zip file":  python3 scripts/build_zip.py
Writes dist/skin.marvin-<version>.zip containing only what Kodi needs."""
import os
import re
import zipfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INCLUDE = ["addon.xml", "xml", "media", "fonts", "colors", "language", "extras", "resources"]


def main():
    version = re.search(r'<addon[^>]*version="([^"]+)"', open(os.path.join(ROOT, "addon.xml")).read()).group(1)
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", f"skin.marvin-{version}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in INCLUDE:
            path = os.path.join(ROOT, item)
            if os.path.isfile(path):
                z.write(path, f"skin.marvin/{item}")
                continue
            for d, _, files in os.walk(path):
                for f in sorted(files):
                    if f.endswith((".pyc", ".pyo")) or f.startswith("."):
                        continue
                    full = os.path.join(d, f)
                    z.write(full, "skin.marvin/" + os.path.relpath(full, ROOT).replace(os.sep, "/"))
    print(out, f"{os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
