# Marvin (skin.marvin)

Kodi 21+ skin for a movies & TV library. **Read `DESIGN.md` before changing anything** — it holds every settled design decision.

## Rules
- Core must work with zero addon dependencies. Optional addons are gated by one `$EXP[Has_<addon>]` each, defined in a single file.
- Home layouts (`appletv` default, `netflix`) differ only in geometry; shared includes own content and logic.
- Every clearlogo slot needs a styled text fallback.
- Every skin setting maps to one `Skin.String`/`Skin.Bool` and is documented in one place.
- Run the checks in `scripts/` (XML validity, reference checker, case check, texture check) before committing.
- Verify visual changes with screenshots from Kodi under a virtual display before shipping.
- Do not copy code from Nimbus or Arctic Fuse 3 (licensing); ideas only.
- Read DESIGN.md §13 (implementation notes) before touching navigation, the logo fallback, views or playback overlays.

## Workflow
- `python3 scripts/check.py` must report 0 errors.
- Screenshot rig: `tools/rig/` (see README "Develop"). Set `RIG_HOME` to a scratch dir; `RIG_RESET_SKIN=1`
  clears skin settings, `RIG_RESET_VIEWS=1` clears saved view modes. The cloud rig runs Kodi 20 with a relaxed
  gui version; Kodi 21-only windows (DialogVideoManager) are unverified there.
- Package with `python3 scripts/build_zip.py` (output in `dist/`, not committed).
