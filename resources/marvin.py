# Marvin helper: applies Kodi settings the skin is designed around.
# Uses only Kodi's built-in Python modules (no add-on dependency).
# Called from the skin:
#   RunScript(special://skin/resources/marvin.py,setup|apply)
#   RunScript(special://skin/resources/marvin.py,togglewatched,type=..,dbid=..,show=..,season=..,watched=0|1)
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


def rpc(method, params):
    res = json.loads(xbmc.executeJSONRPC(json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})))
    return res.get("result") or {}


def set_setting(key, value):
    rpc("Settings.SetSettingValue", {"setting": key, "value": value})


def toggle_watched(args):
    """Mark a movie, episode, season or show watched/unwatched in the Kodi library.
    Trakt users: the Trakt add-on syncs this to Trakt by itself."""
    kind, dbid, watched = args.get("type"), args.get("dbid"), args.get("watched") == "1"
    if not dbid or not dbid.isdigit():
        return
    dbid, count = int(dbid), (1 if watched else 0)
    extra = {"playcount": count, "resume": {"position": 0, "total": 0}} if watched else {"playcount": count}
    if kind == "movie":
        rpc("VideoLibrary.SetMovieDetails", dict(movieid=dbid, **extra))
    elif kind == "episode":
        rpc("VideoLibrary.SetEpisodeDetails", dict(episodeid=dbid, **extra))
    elif kind in ("tvshow", "season"):
        show = dbid if kind == "tvshow" else int(args.get("show") or 0)
        params = {"tvshowid": show}
        if kind == "season" and (args.get("season") or "").isdigit():
            params["season"] = int(args["season"])
        for ep in rpc("VideoLibrary.GetEpisodes", params).get("episodes", []):
            rpc("VideoLibrary.SetEpisodeDetails", dict(episodeid=ep["episodeid"], **extra))
    else:
        return
    # The open info dialog keeps its old item; tell the skin the new state.
    xbmc.executebuiltin("SetProperty(Marvin.WatchedOverride,%d,home)" % count)


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
    kwargs = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    if mode == "apply":
        apply()
    elif mode == "togglewatched":
        toggle_watched(kwargs)
    else:
        setup()
