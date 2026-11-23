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
