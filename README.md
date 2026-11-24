# Marvin

A cinematic, clean and lightweight Kodi skin for a movies & TV library (`skin.marvin`, Kodi 21+).
No required add-ons; the whole skin is ~1.3 MB.

- **Home:** Apple TV-style. Full-bleed artwork, a hero for the focused title, rows that compact the hero as you browse.
- **Library:** Poster Wall for movies, shows and collections; Episode List (season tabs + episode cards) for TV.
- **Info:** one screen. OK opens it with Play focused, so OK-OK plays; the Play key plays from anywhere.
- **Playback:** seek bar → pause screen → minimal OSD with an Audio & Subtitles panel first.

Design decisions live in [DESIGN.md](DESIGN.md).

## Install (v0.1)

1. `python3 scripts/build_zip.py` → `dist/skin.marvin-<version>.zip`
2. Copy the zip to the Shield (network share or USB).
3. Kodi → Settings → System → Add-ons → enable **Unknown sources**.
4. Add-ons → Install from zip file → pick the zip → switch skin when prompted.
5. On first start, choose **Apply** in the "recommended Kodi settings" prompt (OK opens Info, hides `..` and "All seasons").

For the best artwork: Settings → Media → Videos → **Artwork level: Maximum**, enable **fanart.tv** in both TMDb
scrapers, then refresh existing items.

## Develop

```sh
python3 scripts/check.py           # XML, references, fonts, colors, textures (case), strings, window coverage
python3 scripts/gen_textures.py    # regenerate media/ textures
python3 tools/rig/make_library.py LIBDIR   # fake movies/TV library with generated art
python3 tools/rig/rig.py setup LIBDIR && python3 tools/rig/rig.py start && python3 tools/rig/rig.py scan
python3 tools/rig/rig.py run scenario.txt  # drive Kodi over JSON-RPC and take screenshots
```

The rig runs Kodi under Xvfb. It relaxes the `xbmc.gui` requirement in its private copy so the skin also loads on
Kodi 20, which is what the cloud environment provides; the shipped `addon.xml` still targets Kodi 21.

Fonts: Inter (OFL-1.1), Phosphor Icons (MIT). Licenses are in `fonts/`.
