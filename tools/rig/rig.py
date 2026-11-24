#!/usr/bin/env python3
"""Screenshot rig: run Kodi under Xvfb with Marvin and a fake library, drive it over JSON-RPC.

Usage:
  rig.py setup LIBRARY_DIR      create an isolated Kodi profile, sources and settings
  rig.py start                  start Xvfb + Kodi (installs a fresh copy of the skin)
  rig.py stop
  rig.py scan                   scan the fake library and set some watched/resume states
  rig.py rpc METHOD [JSON]      call JSON-RPC
  rig.py shot NAME              save a screenshot to $RIG_OUT/NAME.png
  rig.py run SCRIPT             run a scenario file (one command per line: rpc/action/window/shot/wait)

The installed copy has its xbmc.gui requirement relaxed so it loads on the Kodi
available here (20.x); the repository's addon.xml is never modified.
"""
import base64
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WORK = os.environ.get("RIG_HOME", os.path.join(REPO, ".rig"))
KHOME = os.path.join(WORK, "home")
USERDATA = os.path.join(KHOME, ".kodi", "userdata")
ADDONS = os.path.join(KHOME, ".kodi", "addons")
OUT = os.environ.get("RIG_OUT", os.path.join(WORK, "shots"))
DISPLAY = os.environ.get("RIG_DISPLAY", ":99")
URL = "http://127.0.0.1:8080/jsonrpc"
AUTH = "Basic " + base64.b64encode(b"kodi:kodi").decode()
SKIP = {".git", ".rig", "tools", "scripts", "DESIGN.md", "CLAUDE.md", "README.md"}


def rpc(method, params=None, timeout=30):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "Authorization": AUTH})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        res = json.loads(r.read())
    if "error" in res:
        raise RuntimeError(f"{method}: {res['error']}")
    return res.get("result")


def wait_rpc(seconds=90):
    end = time.time() + seconds
    while time.time() < end:
        try:
            rpc("JSONRPC.Ping", timeout=3)
            return True
        except Exception:
            time.sleep(1)
    raise SystemExit("Kodi did not answer JSON-RPC")


def setup(library):
    library = os.path.abspath(library)
    os.makedirs(USERDATA, exist_ok=True)
    with open(os.path.join(WORK, "library"), "w") as f:
        f.write(library)
    settings = {
        "lookandfeel.skin": "skin.marvin",
        "services.webserver": "true",
        "services.webserverport": "8080",
        "services.webserverauthentication": "true",
        "services.webserverusername": "kodi",
        "services.webserverpassword": "kodi",
        "videolibrary.artworklevel": "0",
        "videolibrary.moviesetsfolder": os.path.join(library, "MovieSets") + "/",
        "videolibrary.showemptytvshows": "true",
        "filelists.showparentdiritems": "false",
        "general.addonupdates": "2",
        "general.addonnotifications": "false",
        "addons.unknownsources": "true",
        "locale.timeformat": "h:mm xx",
        "audiooutput.audiodevice": "NULL",
    }
    with open(os.path.join(USERDATA, "guisettings.xml"), "w") as f:
        f.write('<settings version="2">\n')
        for k, v in settings.items():
            f.write(f'  <setting id="{k}">{v}</setting>\n')
        f.write("</settings>\n")
    with open(os.path.join(USERDATA, "sources.xml"), "w") as f:
        f.write(f"""<sources><video><default pathversion="1"></default>
<source><name>Movies</name><path pathversion="1">{library}/Movies/</path><allowsharing>true</allowsharing></source>
<source><name>TV</name><path pathversion="1">{library}/TV/</path><allowsharing>true</allowsharing></source>
</video></sources>
""")
    with open(os.path.join(USERDATA, "advancedsettings.xml"), "w") as f:
        f.write("<advancedsettings><loglevel>1</loglevel></advancedsettings>\n")
    print("profile ready at", KHOME)


def install_skin():
    dst = os.path.join(ADDONS, "skin.marvin")
    if os.path.islink(dst) or os.path.isfile(dst):
        os.remove(dst)
    elif os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(REPO, dst, ignore=lambda d, names: [n for n in names if d == REPO and n in SKIP])
    path = os.path.join(dst, "addon.xml")
    xml = open(path).read()
    xml = re.sub(r'(addon="xbmc.gui" version=")[0-9.]+', r"\g<1>5.16.0", xml)
    open(path, "w").write(xml)


def enable_skin():
    db = os.path.join(USERDATA, "Database", "Addons33.db")
    if not os.path.exists(db):
        return False
    con = sqlite3.connect(db)
    cur = con.execute("SELECT enabled FROM installed WHERE addonID='skin.marvin'")
    row = cur.fetchone()
    changed = row is None or row[0] != 1
    if row is None:
        con.execute("INSERT INTO installed (addonID, enabled, installDate, origin) VALUES "
                    "('skin.marvin', 1, datetime('now'), '')")
    else:
        con.execute("UPDATE installed SET enabled=1 WHERE addonID='skin.marvin'")
    con.commit()
    con.close()
    return changed


def start():
    stop(quiet=True)
    install_skin()
    if os.environ.get("RIG_RESET_SKIN"):
        p = os.path.join(USERDATA, "addon_data", "skin.marvin", "settings.xml")
        if os.path.exists(p):
            os.remove(p)
    if os.environ.get("RIG_RESET_VIEWS"):
        for f in os.listdir(os.path.join(USERDATA, "Database")):
            if f.startswith("ViewModes"):
                os.remove(os.path.join(USERDATA, "Database", f))
    if subprocess.run(["pgrep", "-f", f"Xvfb {DISPLAY}"], capture_output=True).returncode != 0:
        subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1920x1080x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    first = enable_skin() is False and not os.path.exists(os.path.join(USERDATA, "Database", "Addons33.db"))
    launch()
    if first or enable_skin():
        # first boot registers the add-on disabled; enable it and restart
        stop(quiet=True)
        enable_skin()
        launch()
    # dismiss "enable optional add-on?" prompts from the distro packages
    for _ in range(3):
        try:
            if rpc("GUI.GetProperties", {"properties": ["currentwindow"]})["currentwindow"]["id"] == 10100 and \
                    rpc("XBMC.GetInfoLabels", {"labels": ["Control.GetLabel(1)"]})["Control.GetLabel(1)"] != "Marvin":
                rpc("Input.Back")
                time.sleep(1)
        except Exception:
            pass
    for k, v in (("filelists.showparentdiritems", False), ("videolibrary.showallitems", False)):
        rpc("Settings.SetSettingValue", {"setting": k, "value": v})
    skin = rpc("Settings.GetSettingValue", {"setting": "lookandfeel.skin"})["value"]
    print("kodi up, skin =", skin)


def launch():
    env = dict(os.environ, HOME=KHOME, DISPLAY=DISPLAY, LIBGL_ALWAYS_SOFTWARE="1")
    log = open(os.path.join(WORK, "kodi.out"), "w")
    subprocess.Popen(["kodi", "--standalone", "--windowing=x11"], env=env, cwd=WORK,
                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    wait_rpc()
    time.sleep(4)


def stop(quiet=False):
    try:
        rpc("Application.Quit", timeout=3)
        time.sleep(3)
    except Exception:
        pass
    subprocess.run(["pkill", "-f", "kodi.bin"], capture_output=True)
    time.sleep(1)
    if not quiet:
        print("stopped")


def scan():
    library = open(os.path.join(WORK, "library")).read().strip()
    db = sorted(f for f in os.listdir(os.path.join(USERDATA, "Database")) if f.startswith("MyVideos"))[-1]
    con = sqlite3.connect(os.path.join(USERDATA, "Database", db))
    for sub, content, recursive in (("Movies", "movies", 2147483647), ("TV", "tvshows", 0)):
        p = f"{library}/{sub}/"
        con.execute("DELETE FROM path WHERE strPath=?", (p,))
        con.execute("INSERT INTO path (strPath, strContent, strScraper, scanRecursive, useFolderNames, "
                    "strSettings, noUpdate, exclude, allAudio) VALUES (?,?,?,?,?,?,?,?,?)",
                    (p, content, "metadata.local", recursive, 0, "", 0, 0, 0))
    con.commit()
    con.close()
    rpc("VideoLibrary.Scan", {"showdialogs": False})
    time.sleep(5)
    for _ in range(120):
        if not rpc("XBMC.GetInfoBooleans", {"booleans": ["Library.IsScanningVideo"]})["Library.IsScanningVideo"]:
            break
        time.sleep(1)
    movies = rpc("VideoLibrary.GetMovies", {"properties": ["title"]}).get("movies", [])
    eps = rpc("VideoLibrary.GetEpisodes", {"properties": ["title", "season", "episode", "tvshowid"]}).get("episodes", [])
    # Library state that exercises badges, progress bars and "continue watching"
    for m in movies:
        t = m["title"]
        if t in ("Ashfall", "Ironwood"):
            rpc("VideoLibrary.SetMovieDetails", {"movieid": m["movieid"], "playcount": 1})
        if t in ("Neon Harbor", "Saltwater Requiem", "Northern Static"):
            rpc("VideoLibrary.SetMovieDetails", {"movieid": m["movieid"],
                                                 "resume": {"position": 2400 + len(t) * 60, "total": 7200}})
    for e in eps:
        if e["season"] == 1 and e["episode"] <= 2:
            rpc("VideoLibrary.SetEpisodeDetails", {"episodeid": e["episodeid"], "playcount": 1})
        if e["season"] == 1 and e["episode"] == 3:
            rpc("VideoLibrary.SetEpisodeDetails", {"episodeid": e["episodeid"],
                                                   "resume": {"position": 1200, "total": 2900}})
    print(f"scanned: {len(movies)} movies, {len(eps)} episodes")


def shot(name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".png")
    xwd = subprocess.run(["xwd", "-root", "-silent", "-display", DISPLAY], capture_output=True, check=True)
    subprocess.run(["convert", "xwd:-", path], input=xwd.stdout, check=True)
    print(path)


def run(script):
    for raw in open(script):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cmd, _, arg = line.partition(" ")
        if cmd == "wait":
            time.sleep(float(arg))
        elif cmd == "shot":
            shot(arg)
        elif cmd == "action":
            for a in arg.split():
                rpc("Input.ExecuteAction", {"action": a})
                time.sleep(0.35)
        elif cmd == "window":
            w, _, p = arg.partition(" ")
            params = {"window": w}
            if p:
                params["parameters"] = [p]
            rpc("GUI.ActivateWindow", params)
        elif cmd == "rpc":
            m, _, p = arg.partition(" ")
            print(json.dumps(rpc(m, json.loads(p) if p else {}))[:400])
        else:
            raise SystemExit(f"unknown command: {line}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "setup":
        setup(args[0])
    elif cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "scan":
        scan()
    elif cmd == "rpc":
        print(json.dumps(rpc(args[0], json.loads(args[1]) if len(args) > 1 else {}), indent=1)[:4000])
    elif cmd == "shot":
        shot(args[0])
    elif cmd == "run":
        run(args[0])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
