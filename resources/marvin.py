# Marvin helper: applies Kodi settings the skin is designed around.
# Uses only Kodi's built-in Python modules (no add-on dependency).
# Called from the skin:  RunScript(special://skin/resources/marvin.py,setup|apply)
import json
import sys

import xbmc
import xbmcgui

RECOMMENDED = (
    # (setting id, value, why)
    ("myvideos.selectaction", 3, "OK opens the Info screen (Play is one more press)"),
    ("filelists.showparentdiritems", False, "Hide '..' parent items in lists"),
    ("videolibrary.showallitems", False, "Hide the 'All seasons' item"),
)


def set_setting(key, value):
    xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "Settings.SetSettingValue",
        "params": {"setting": key, "value": value}}))


def apply():
    for key, value, _ in RECOMMENDED:
        set_setting(key, value)
    xbmc.executebuiltin("Skin.SetBool(Marvin.SetupDone)")


def setup():
    lines = "\n".join("•  " + why for _, _, why in RECOMMENDED)
    if xbmcgui.Dialog().yesno("Marvin", "Apply the recommended Kodi settings?\n\n" + lines,
                              nolabel="Not now", yeslabel="Apply"):
        apply()
        xbmcgui.Dialog().notification("Marvin", "Recommended settings applied", sound=False)
    else:
        xbmc.executebuiltin("Skin.SetBool(Marvin.SetupDone)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "setup"
    apply() if mode == "apply" else setup()
