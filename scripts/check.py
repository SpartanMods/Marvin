#!/usr/bin/env python3
"""Static checks for the Marvin skin. Run before every commit:  python3 scripts/check.py

Checks:
  xml        every XML file is well-formed
  refs       every <include>, $VAR[...], $EXP[...] reference is defined
  fonts      every <font> exists in Font.xml and every font file exists
  colors     every named color exists in colors/defaults.xml
  textures   every media path exists with exactly that case (Android/Linux are case-sensitive)
  strings    every skin string ($LOCALIZE[31xxx]) exists in strings.po
  windows    every window Kodi may open has a file
Exit code is non-zero when any check fails. Unused definitions are reported as warnings.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
XML_DIR = os.path.join(ROOT, "xml")
MEDIA = os.path.join(ROOT, "media")

# Windows Kodi 21 can open (from the Kodi skinning contract). Missing ones fail to open.
REQUIRED_WINDOWS = """AddonBrowser DialogAddonInfo DialogAddonSettings DialogBusy DialogButtonMenu DialogColorPicker
DialogConfirm DialogContextMenu DialogExtendedProgressBar DialogFavourites DialogFullScreenInfo DialogGameControllers
DialogKeyboard DialogMediaSource DialogMusicInfo DialogNotification DialogNumeric DialogPVRChannelGuide
DialogPVRChannelManager DialogPVRChannelsOSD DialogPVRGroupManager DialogPVRGuideControls DialogPVRGuideSearch
DialogPVRInfo DialogPVRRadioRDSInfo DialogPictureInfo DialogPlayerProcessInfo DialogSeekBar DialogSelect
DialogSettings DialogSlider DialogSubtitles DialogTextViewer DialogVideoInfo DialogVideoManager DialogVolumeBar
EventLog FileBrowser FileManager Font GameOSD Home LoginScreen MusicOSD MusicVisualisation MyFavourites MyGames
MyMusicNav MyMusicPlaylistEditor MyPVRChannels MyPVRGuide MyPVRRecordings MyPVRSearch MyPVRTimers MyPics MyPlaylist
MyPrograms MyVideoNav MyWeather PlayerControls Pointer Settings SettingsCategory SettingsProfile
SettingsScreenCalibration SettingsSystemInfo SkinSettings SlideShow SmartPlaylistEditor SmartPlaylistRule Startup
VideoFullScreen VideoOSD VideoOSDBookmarks""".split()

# Defined now, used by upcoming versions (v0.3 TMDb Helper layer, v0.4 Up Next + Netflix layout)
RESERVED = {"Has_TMDbHelper", "Has_UpNext", "Layout_AppleTV", "Layout_Netflix"}

TEXTURE_TAGS = {"texture", "texturefocus", "texturenofocus", "texturebg", "midtexture", "lefttexture",
                "righttexture", "texturesliderbar", "textureslidernib", "textureslidernibfocus",
                "texturesliderbackground", "texturesliderbarfocus", "textureradioonfocus",
                "textureradioonnofocus", "textureradiooffocus", "textureradiooffnofocus", "textureup",
                "textureupfocus", "texturedown", "texturedownfocus", "textureupdisabled", "texturedowndisabled",
                "bordertexture", "progresstexture", "texturecolormask", "texturecolordisabledmask"}
COLOR_TAGS = {"textcolor", "focusedcolor", "disabledcolor", "selectedcolor", "shadowcolor", "spincolor",
              "invalidcolor", "backgroundcolor"}

errors, warnings = [], []


def err(kind, msg):
    errors.append(f"[{kind}] {msg}")


def xml_files():
    for d, _, files in os.walk(ROOT):
        if any(p in d for p in (".git", ".rig", os.sep + "tools")):
            continue
        for f in files:
            if f.endswith((".xml", ".xsp")):
                yield os.path.join(d, f)


def check_xml():
    parsed = {}
    for path in xml_files():
        try:
            parsed[path] = ET.parse(path)
        except ET.ParseError as e:
            err("xml", f"{os.path.relpath(path, ROOT)}: {e}")
    return parsed


def is_dynamic(name):
    return "$PARAM[" in name or "$INFO[" in name


def check_refs(trees):
    defs = {"include": set(), "variable": set(), "expression": set(), "constant": set()}
    used = {"include": set(), "variable": set(), "expression": set()}
    skin_trees = {p: t for p, t in trees.items() if p.startswith(XML_DIR)}
    for path, tree in skin_trees.items():
        for el in tree.iter():
            name = el.get("name")
            if el.tag in defs and name and (el.tag != "include" or el.find("definition") is not None
                                             or len(el) or (el.text or "").strip() or el.get("file") is None):
                if el.tag == "include" and name is None:
                    continue
                defs[el.tag].add(name)
    raw = {p: re.sub(r"<!--.*?-->", "", open(p, encoding="utf-8").read(), flags=re.S) for p in skin_trees}
    for path, tree in skin_trees.items():
        rel = os.path.relpath(path, ROOT)
        for el in tree.iter("include"):
            if el.get("file"):
                if not os.path.exists(os.path.join(XML_DIR, el.get("file"))):
                    err("refs", f"{rel}: included file {el.get('file')} missing (case-sensitive)")
                continue
            if el.get("name"):
                continue
            target = el.get("content") or (el.text or "").strip()
            if target and not is_dynamic(target):
                used["include"].add(target)
                if target not in defs["include"]:
                    err("refs", f"{rel}: include '{target}' is not defined")
        text = raw[path]
        for kind, pat in (("variable", r"\$(?:ESC)?VAR\[([^\]\[]+(?:\[[^\]]*\])?[^\]]*)\]"),
                          ("expression", r"\$EXP\[([^\]]+)\]")):
            for m in re.finditer(pat, text):
                name = m.group(1)
                if is_dynamic(name):
                    continue
                used[kind].add(name)
                if name not in defs[kind]:
                    err("refs", f"{rel}: {kind} '{name}' is not defined")
    for kind in ("include", "variable", "expression"):
        for name in sorted(defs[kind] - used[kind]):
            if kind == "variable" and re.search(r"_(movies|tvshows|none|true|false|\d+)$", name):
                continue  # selected dynamically via $PARAM
            if kind == "include" and name.startswith(("Home_Geometry_",)):
                continue
            if name.startswith("Icon_") or name in RESERVED:
                continue  # icon library / reserved for upcoming versions
            warnings.append(f"[unused] {kind} '{name}'")
    return skin_trees


def check_fonts(skin_trees):
    font_xml = ET.parse(os.path.join(XML_DIR, "Font.xml"))
    names = set()
    for f in font_xml.iter("font"):
        names.add(f.findtext("name"))
        fn = f.findtext("filename")
        if not os.path.exists(os.path.join(ROOT, "fonts", fn)):
            err("fonts", f"font file fonts/{fn} missing")
    if "font13" not in names:
        err("fonts", "Kodi requires a 'font13' fallback font")
    for path, tree in skin_trees.items():
        for el in tree.iter("font"):
            v = (el.text or "").strip()
            if v and not is_dynamic(v) and v not in names and not path.endswith("Font.xml"):
                err("fonts", f"{os.path.relpath(path, ROOT)}: unknown font '{v}'")


def color_ok(v, colors):
    v = v.strip()
    return (not v or is_dynamic(v) or v.startswith("$VAR[") or v in colors
            or re.fullmatch(r"(0x)?[0-9A-Fa-f]{8}", v) is not None)


def check_colors(skin_trees):
    colors = {c.get("name") for c in ET.parse(os.path.join(ROOT, "colors", "defaults.xml")).iter("color")}
    for path, tree in skin_trees.items():
        rel = os.path.relpath(path, ROOT)
        for el in tree.iter():
            if el.tag in COLOR_TAGS and not color_ok(el.text or "", colors):
                err("colors", f"{rel}: unknown color '{el.text.strip()}' in <{el.tag}>")
            cd = el.get("colordiffuse")
            if cd is not None and not color_ok(cd, colors):
                err("colors", f"{rel}: unknown colordiffuse '{cd}'")
        # variables used as colors may return names
        for var in tree.iter("variable"):
            if var.get("name", "").startswith(("Home_Menu", "Dialog_RowText", "Template_RowText", "View_TabColor",
                                               "Settings_Tile")):
                for val in var.iter("value"):
                    if not color_ok(val.text or "", colors):
                        err("colors", f"{rel}: variable {var.get('name')} returns unknown color '{val.text}'")


def media_files():
    found = set()
    for d, _, files in os.walk(MEDIA):
        for f in files:
            found.add(os.path.relpath(os.path.join(d, f), MEDIA).replace(os.sep, "/"))
    return found


def check_textures(skin_trees):
    available = media_files()
    for path, tree in skin_trees.items():
        rel = os.path.relpath(path, ROOT)
        for el in tree.iter():
            vals = []
            if el.tag in TEXTURE_TAGS:
                vals.append((el.text or "").strip())
            if el.get("diffuse"):
                vals.append(el.get("diffuse"))
            for v in vals:
                if not v or "$" in v or v.startswith(("special://", "/", "http")) or "://" in v:
                    continue
                if v not in available:
                    hint = [a for a in available if a.lower() == v.lower()]
                    err("textures", f"{rel}: '{v}' not in media/" + (f" (case differs: {hint[0]})" if hint else ""))


def check_strings(skin_trees):
    po = open(os.path.join(ROOT, "language", "resource.language.en_gb", "strings.po"), encoding="utf-8").read()
    defined = set(int(x) for x in re.findall(r'msgctxt "#(\d+)"', po))
    for path in skin_trees:
        for m in re.finditer(r"\$LOCALIZE\[(\d+)\]", open(path, encoding="utf-8").read()):
            n = int(m.group(1))
            if 31000 <= n <= 31999 and n not in defined:
                err("strings", f"{os.path.relpath(path, ROOT)}: skin string {n} missing from strings.po")


def check_windows():
    have = {f[:-4] for f in os.listdir(XML_DIR) if f.endswith(".xml")}
    for w in REQUIRED_WINDOWS:
        if w not in have:
            err("windows", f"xml/{w}.xml missing")


def main():
    trees = check_xml()
    skin = check_refs(trees)
    check_fonts(skin)
    check_colors(skin)
    check_textures(skin)
    check_strings(skin)
    check_windows()
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:  ", e)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s) across {len(trees)} XML files")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
