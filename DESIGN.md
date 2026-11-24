# Marvin — Design Decisions

A cinematic, clean, lightweight Kodi skin (`skin.marvin`) for a movies & TV library.
Decisions below were settled in a design interview, informed by reading the code of
[Nimbus](https://github.com/ivarbrandt/skin.nimbus) and
[Arctic Fuse 3](https://github.com/jurialmunkey/skin.arctic.fuse.3).
No code is copied from either (AF3 is CC BY-NC-SA, Nimbus is CC BY-SA/GPLv2) — ideas only.

## 1. Audience & platform
- Personal daily driver first; may be published later.
- Performance floor: **Nvidia Shield TV**. Rich visuals (fanart, crossfades, layered art) are affordable.
- Input: Shield remote (d-pad + back/home + play/pause). Every screen is d-pad-first.
- **Kodi 21 Omega** minimum. **1080i** coordinate space, **16:9 only**.

## 2. Content & dependencies
- Library comes from **Kodi's own scrapers** (TMDb Python scrapers) into the Kodi database.
- **Core has zero dependencies.** Every screen works and looks complete on bare Kodi.
- **Optional integrations**, each gated by a single `$EXP[Has_<addon>]` expression defined in one file:
  - `plugin.video.themoviedb.helper` — ratings, recommendations, similar, people/filmography, trailers, "not in your library" search row.
  - `service.upnext` — styled end-of-episode card.
  - Subtitle addons — download button in the Audio & Subtitles panel.
- Never hardcode per-addon branches across many files (the Nimbus anti-pattern).

## 3. Scope (tiers)
Used: **Movies (heavy), TV shows (heavy).** Not used: music, Live TV/PVR, music videos, add-on browsing, pictures, games, weather.

- **Tier 1 — hero quality:** Home, library views, Info (movie/show/season/episode/collection), person/cast, Next Up, video OSD/seekbar/pause, fullscreen info, search, core dialogs (context menu, select, busy, notification, volume, keyboard), settings.
- **Tier 2 — clean & consistent:** Favourites, file browsing, Kodi settings windows.
- **Tier 3 — minimal:** everything else (music, PVR, games, pictures, weather, add-on browser). Built from ~4–5 generic templates (list, panel, dialog frame, settings frame) so Kodi never breaks.

## 4. Visual identity — cinematic dark
Emphasis: **cleanliness, browseability, immersion, ease of use.**
- Background `#0B0B0F` (OLED-safe near-black). Text/accent warm off-white `#F2EFEA`. Muted text = 60% grey.
- One accent by default + 3–4 alternates in `colors/`.
- Typeface: **Inter**, 4 weights. Icons: **Phosphor** icon font (no bitmap icons).
- Corners 14px. Motion 200ms ease-out. Focus = subtle scale (~1.06) + soft glow, no borders.
- Frosted-glass panels only on overlays (dialogs, info panel, side panel).
- Clearlogos instead of titles wherever available.

## 5. Artwork policy
- Design **for** clearlogo, never **depend** on it: every logo slot has a styled text fallback with matching position/weight.
- Landscape slots: `landscape` → `fanart` cropped with gradient + logo/text overlay. Never letterboxed posters.
- Recommended Kodi setup: Settings → Media → Videos → **Artwork level: Maximum**; enable **fanart.tv** in both TMDb scrapers; refresh existing items.

## 6. Home
- Two layouts selected by `Skin.String(Home.Layout)`: **`appletv` (default)** and `netflix`.
  - Apple TV: minimal top menu, full-bleed fanart, hero that shrinks as you scroll into rows.
  - Netflix: left rail menu, hero top-right, rows below.
- **Only geometry differs.** `Includes_Home_<layout>.xml` owns positions; rows, widget content, focus logic and hero contents are shared includes. A feature needing per-layout code is a design smell.
- Menu: Movies, TV Shows, Search, Favourites (optional), Settings/Power.
- **Editing (native, no skinshortcuts):** menu items toggleable; **8 widget slots per section** (+ custom section slot or two), each chosen from presets (In Progress, Next Up, Recently Added, Unwatched, genres, sets, user `.xsp`) or any path via `Skin.String`/`Skin.SetPath` + custom select dialog.

## 7. Library views (exactly 4, remembered per content type)
1. **Poster Wall** — ~7-across poster grid, fanart behind, slim info strip. Default for movies, collections, shows.
2. **Landscape** — 16:9 thumbs with logos, ~4 across, hero above. One press away.
3. **List + Showcase** — narrow list left; fanart, logo, plot, cast strip, media flags right. One press away.
4. **Episode List** — season strip on top, episodes with stills/plot/progress. Default for seasons & episodes.
- Sort/filter in a slide-out **side panel** (left from first column, or menu key) with one-click presets: Unwatched, Recently Added, By Year, By Rating, Genre, A–Z jump.

## 8. Info screen
- **OK opens Info; Play/Resume is default-focused** (OK-OK plays). **Play key plays directly** from any view.
- Layout: full-bleed fanart + left gradient → clearlogo (text fallback) → meta line (year · runtime · rating · genres) + media flags from the file (4K, HDR/DV, Atmos, codec) → plot (3 lines, More expands) → buttons: Play/Resume · Trailer · Watched · More.
- Scroll down: hero shrinks, rows slide up — Cast → Collection (if in set) → Recommendations/Similar (TMDbHelper only). TV: Seasons → Next Up → Cast → Recommendations.
- Single window; rows by visibility, not hub windows.
- Optional muted trailer autoplay after ~3s (TMDbHelper only, setting).

## 9. Playback
Three tiers:
1. **Seek** (left/right): thin bottom seekbar — elapsed, remaining, "ends at", chapter ticks, seek-preview time. Fades after 2s.
2. **Pause**: video dims; clearlogo, episode title, short plot, seekbar, ends-at fade in.
3. **Full OSD** (OK/menu): seekbar + minimal icon row. **Audio & Subtitles merged panel is first and default-focused** (OK-OK opens it): tracks left; subtitle offset/size/download right. Remaining: chapters, video settings, stop, next.
- Up Next card when `service.upnext` is installed; otherwise nothing.
- Fullscreen info button: resolution, HDR format, audio codec/channels, bitrate.

## 10. Search
- Native live search window: keyboard left, results rows right updating as you type (debounced `Container.Update`): Movies, TV Shows, Episodes, Actors via `videodb://` filters.
- **Autofill:** suggestion strip above the keyboard — library titles via `startswith` smart-playlist filter + matching search history (+ actors with TMDbHelper). Selecting fills field and jumps to results.
- Last 8 searches in skin strings, shown when field is empty.
- TMDbHelper adds "Not in your library" row and person filmography.
- Reachable from Home menu and a global key; Shield mic → Android voice keyboard.

## 11. Skin settings
- Fleshed out but easy: category list left, options right, **live preview panel**, one-line description per option.
- Categories: Home · Look · Library · Info screen · Playback · Search · Integrations (detected addons + install buttons) · Maintenance (reset, clear caches, about).
- Every setting has a good default and maps to one `Skin.String`/`Skin.Bool` documented in a single file.

### Skin setting keys (the single source of truth)
| Key | Type | Meaning | Default |
|---|---|---|---|
| `Home.Layout` | String | `appletv` \| `netflix` (Netflix arrives in v0.4) | empty = appletv |
| `Home.HideMovies` / `Home.HideTV` / `Home.HideFavourites` | Bool | hide a home menu item | off |
| `Widget.<Movies\|TV>.<1-8>.Path` | String | content path of a home row | set by Startup.xml |
| `Widget.<Movies\|TV>.<1-8>.Label` | String | row title | set by Startup.xml |
| `Widget.<Movies\|TV>.<1-8>.Style` | String | `poster` \| `landscape` | set by Startup.xml |
| `Widgets.Initialised` | Bool | defaults written; reset re-seeds them | off |
| `Marvin.SetupDone` | Bool | first-run "recommended settings" prompt answered | off |

## 12. Build, test, deliver
- Repo root **is** the skin (`skin.marvin`): `addon.xml`, `xml/`, `media/`, `fonts/`, `colors/`, `language/`, `extras/`, `scripts/`.
- Checks on every change: XML well-formedness; include/variable/expression reference checker; filename case check; texture existence check.
- Visual verification: Kodi on Linux under a virtual display with a dummy movie/TV library; screenshot each screen before it reaches the Shield.
- Delivery: zip install first → personal GitHub-Pages Kodi repository once stable.
- Maintained mostly through Claude: strict conventions + checks over cleverness.

## 13. Implementation notes (learned while building v0.1)
- **OK → Info needs a Kodi setting.** Kodi ignores a container's `<onclick>` in library windows; OK follows
  *Settings → Media → Videos → Default select action*. Marvin ships `resources/marvin.py` (Kodi's built-in
  Python, no add-on) and asks once on first run to apply: select action = Show information, hide `..` items,
  hide "All seasons". Re-apply from Marvin settings → Maintenance. Home rows open Info natively.
- **Pause screen lives in `DialogSeekBar.xml`**, which Kodi shows/hides from its `<visible>` conditions;
  controls in `VideoFullScreen.xml` are not drawn over paused video.
- **Kodi labels cannot bottom-align**, so the logo text fallback takes explicit `fb_top`/`fb_h` per use.
- **Kodi 20 lists ignore `width="auto"` items**; season tabs use fixed widths.
- **Buttons wrapped in groups lose automatic navigation**; Home rows and Info buttons carry explicit
  up/down/left/right links (Kodi skips hidden targets by following their own links).
- **Kodi colour `00000000` means "no tint" (renders white)**; use the named `clear` colour instead.
- **Default view per content type** works by giving every view `viewtype=list` and a `<visible>`
  condition; Kodi picks the first visible view in `<views>` order.
- **Seek/slider nibs render at texture size**; only small dedicated textures (`common/nib.png`) are used.

## 14. Roadmap
- **v0.1 "Watchable"** (built) — foundation (colors, fonts, includes, checks, screenshot rig), Apple TV home with Movies/TV rows, Poster Wall, Episode List, movie + episode Info, minimal OSD + Audio/Subs panel, pause screen, core dialogs, tier-3 templates for all other windows.
- **v0.2 "Browse"** — Landscape + List/Showcase views, sort/filter side panel, collections, TV show Info with seasons, person/cast.
- **v0.3 "Find"** — search with autofill + history, TMDbHelper layer (ratings, recommendations, trailers).
- **v0.4 "Tune"** — full settings page, Netflix home layout, Up Next styling, GitHub-Pages repository.
