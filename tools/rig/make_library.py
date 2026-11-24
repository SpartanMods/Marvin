#!/usr/bin/env python3
"""Build a fake movies & TV library (files, .nfo, artwork) for screenshot testing.

Usage: make_library.py OUT_DIR

Titles are fictional. Artwork is procedurally generated so screenshots look
like a real library without shipping copyrighted images. A few items lack a
clearlogo on purpose, to exercise the text fallback.
"""
import colorsys
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.normpath(os.path.join(HERE, "..", "..", "fonts"))
BOLD = os.path.join(FONTS, "Inter-Bold.ttf")
SEMI = os.path.join(FONTS, "Inter-SemiBold.ttf")

MOVIES = [
    # title, year, genres, rating, runtime(min), mpaa, has_logo, set, video, audio
    ("Neon Harbor", 2023, ["Thriller", "Crime"], 7.8, 128, "R", True, None, "4k_dv", "atmos"),
    ("The Quiet Orbit", 2024, ["Science Fiction", "Drama"], 8.2, 141, "PG-13", True, None, "4k_hdr", "atmos"),
    ("Ashfall", 2022, ["Action", "Adventure"], 6.9, 117, "PG-13", True, None, "4k_hdr", "dts"),
    ("Paper Lanterns", 2021, ["Romance", "Drama"], 7.3, 109, "PG", False, None, "1080", "ac3"),
    ("Midnight Cartography", 2024, ["Mystery", "Thriller"], 7.6, 133, "R", True, None, "4k_dv", "atmos"),
    ("Ironwood", 2019, ["Western", "Drama"], 7.9, 125, "R", True, "Ironwood Collection", "1080", "dts"),
    ("Ironwood II: Embers", 2022, ["Western", "Action"], 7.1, 131, "R", True, "Ironwood Collection", "4k_hdr", "atmos"),
    ("Saltwater Requiem", 2020, ["Drama"], 8.4, 147, "R", True, None, "4k_hdr", "truehd"),
    ("The Last Lighthouse", 2023, ["Horror", "Mystery"], 6.6, 98, "R", True, None, "1080", "ac3"),
    ("Glasshouse", 2024, ["Comedy", "Drama"], 7.0, 104, "PG-13", False, None, "1080", "aac"),
    ("Northern Static", 2021, ["Science Fiction", "Thriller"], 7.4, 119, "PG-13", True, None, "4k_dv", "atmos"),
    ("Velvet Circuit", 2025, ["Animation", "Family"], 8.0, 96, "PG", True, None, "4k_hdr", "atmos"),
]

SHOWS = [
    # title, year, genres, rating, has_logo, seasons{n: episodes}
    ("Long Division", 2022, ["Drama", "Mystery"], 8.6, True, {1: 6, 2: 5}),
    ("The Orchard", 2023, ["Comedy"], 7.9, True, {1: 6}),
    ("Signal Lost", 2021, ["Science Fiction", "Thriller"], 8.1, False, {1: 4, 2: 4, 3: 3}),
]

PLOT = ("When a routine assignment unravels, {who} is pulled into a quiet conspiracy that stretches "
        "across three cities and twenty years. Every answer costs something, and the people who know "
        "the truth are running out of reasons to stay silent.")
WHO = ["a disgraced cartographer", "a night-shift pilot", "two estranged sisters", "a retired detective",
       "a young archivist", "the last keeper of a coastal light"]

VIDEO = {
    "4k_dv": dict(codec="hevc", width=3840, height=1600, aspect="2.40", hdr="dolbyvision"),
    "4k_hdr": dict(codec="hevc", width=3840, height=2160, aspect="1.78", hdr="hdr10"),
    "1080": dict(codec="h264", width=1920, height=800, aspect="2.40", hdr=""),
}
AUDIO = {
    "atmos": ("truehd", 8), "truehd": ("truehd", 8), "dts": ("dtshd_ma", 6), "ac3": ("ac3", 6), "aac": ("aac", 2)}


def palette(seed):
    rnd = random.Random(seed)
    h = rnd.random()
    base = colorsys.hsv_to_rgb(h, 0.55 + rnd.random() * 0.3, 0.35 + rnd.random() * 0.2)
    hi = colorsys.hsv_to_rgb((h + 0.08 + rnd.random() * 0.1) % 1, 0.5, 0.95)
    return rnd, tuple(int(c * 255) for c in base), tuple(int(c * 255) for c in hi)


def scene(w, h, seed):
    """Abstract, filmic backdrop: dark base, glowing horizon, blurred shapes, grain."""
    rnd, base, hi = palette(seed)
    img = Image.new("RGB", (w, h), tuple(int(c * 0.25) for c in base))
    glow = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(glow)
    cx, cy = rnd.uniform(0.45, 0.85) * w, rnd.uniform(0.25, 0.6) * h
    d.ellipse((cx - w * 0.45, cy - h * 0.5, cx + w * 0.45, cy + h * 0.5), fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(w // 8))
    img.paste(base, mask=glow)
    core = Image.new("L", (w, h), 0)
    ImageDraw.Draw(core).ellipse((cx - w * 0.12, cy - h * 0.12, cx + w * 0.12, cy + h * 0.12), fill=170)
    core = core.filter(ImageFilter.GaussianBlur(w // 18))
    img.paste(hi, mask=core)
    # silhouettes along the bottom for a sense of place
    sil = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(sil)
    x = 0
    while x < w:
        bw = rnd.randint(w // 30, w // 8)
        bh = rnd.randint(h // 10, h // 3)
        sd.rectangle((x, h - bh, x + bw, h), fill=235)
        x += bw + rnd.randint(0, w // 40)
    sil = sil.filter(ImageFilter.GaussianBlur(2))
    img.paste((6, 6, 9), mask=sil)
    noise = Image.effect_noise((w, h), 18).convert("L")
    img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.05)
    return img


def fit_font(path, text, max_w, start):
    size = start
    while size > 12:
        f = ImageFont.truetype(path, size)
        if f.getlength(text) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(path, size)


def logo(text, path):
    w, h = 800, 310
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    words = text.upper()
    f = fit_font(BOLD, words, w - 20, 150)
    d.text((w / 2, h / 2), words, font=f, fill=(245, 242, 236, 255), anchor="mm")
    img = img.crop(img.getbbox())
    img.save(path)


def poster(text, seed, path, sub=None):
    w, h = 1000, 1500
    img = scene(w, h, seed)
    shade = Image.new("L", (w, h), 0)
    ImageDraw.Draw(shade).rectangle((0, int(h * 0.62), w, h), fill=200)
    shade = shade.filter(ImageFilter.GaussianBlur(120))
    img.paste((0, 0, 0), mask=shade)
    d = ImageDraw.Draw(img)
    f = fit_font(BOLD, text.upper(), w - 120, 120)
    d.text((w / 2, h * 0.82), text.upper(), font=f, fill=(245, 242, 236), anchor="mm")
    if sub:
        d.text((w / 2, h * 0.9), sub, font=ImageFont.truetype(SEMI, 44), fill=(210, 205, 198), anchor="mm")
    img.save(path, quality=88)


def landscape(text, seed, path):
    img = scene(1280, 720, seed)
    d = ImageDraw.Draw(img)
    f = fit_font(BOLD, text.upper(), 900, 96)
    d.text((80, 600), text.upper(), font=f, fill=(245, 242, 236), anchor="ls")
    img.save(path, quality=88)


def streamdetails(vkey, akey, runtime):
    v = VIDEO[vkey]
    a = AUDIO[akey]
    return (f"<fileinfo><streamdetails><video><codec>{v['codec']}</codec><aspect>{v['aspect']}</aspect>"
            f"<width>{v['width']}</width><height>{v['height']}</height>"
            f"<durationinseconds>{runtime * 60}</durationinseconds><hdrtype>{v['hdr']}</hdrtype></video>"
            f"<audio><codec>{a[0]}</codec><language>eng</language><channels>{a[1]}</channels></audio>"
            f"<audio><codec>ac3</codec><language>fre</language><channels>6</channels></audio>"
            f"<subtitle><language>eng</language></subtitle><subtitle><language>spa</language></subtitle>"
            f"</streamdetails></fileinfo>")


def cast_xml(seed, n=8):
    rnd = random.Random(seed)
    first = ["Ada", "Theo", "Mara", "Jonah", "Ines", "Felix", "Noor", "Hugo", "Lena", "Omar", "Ruth", "Kai"]
    last = ["Calder", "Voss", "Okafor", "Lindqvist", "Moreau", "Sato", "Reyes", "Hale", "Brandt", "Novak"]
    roles = ["The Pilot", "Detective Ward", "Eli", "June", "The Archivist", "Captain Rowe", "Sam", "Mother"]
    return "".join(f"<actor><name>{rnd.choice(first)} {rnd.choice(last)}</name><role>{roles[i % len(roles)]}"
                   f"</role><order>{i}</order></actor>" for i in range(n))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def main(out):
    vid = os.path.join(out, "_sample.mkv")
    movies = os.path.join(out, "Movies")
    shows = os.path.join(out, "TV")
    os.makedirs(movies, exist_ok=True)
    os.makedirs(shows, exist_ok=True)
    make_sample(vid, out)

    for i, (title, year, genres, rating, runtime, mpaa, has_logo, mset, vkey, akey) in enumerate(MOVIES):
        folder = os.path.join(movies, f"{title} ({year})")
        os.makedirs(folder, exist_ok=True)
        base = os.path.join(folder, f"{title} ({year})")
        link(vid, base + ".mkv")
        seed = title
        poster(title, seed, base + "-poster.jpg")
        scene(1920, 1080, seed).save(base + "-fanart.jpg", quality=88)
        landscape(title, seed, base + "-landscape.jpg")
        if has_logo:
            logo(title, base + "-clearlogo.png")
        plot = PLOT.format(who=WHO[i % len(WHO)])
        setxml = f"<set><name>{esc(mset)}</name><overview>Two films.</overview></set>" if mset else ""
        with open(base + ".nfo", "w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<movie><title>{esc(title)}</title><year>{year}</year><premiered>{year}-0{1 + i % 9}-15</premiered>
<plot>{plot}</plot><outline>{plot[:120]}</outline><tagline>Some maps lead home.</tagline>
<runtime>{runtime}</runtime><mpaa>{mpaa}</mpaa>
<ratings><rating name="themoviedb" max="10" default="true"><value>{rating}</value><votes>{1000 + i * 77}</votes></rating></ratings>
{''.join(f'<genre>{g}</genre>' for g in genres)}<studio>Northlight Pictures</studio>
<director>Rhea Castellan</director><credits>Milo Arden</credits>{setxml}
{cast_xml(seed)}{streamdetails(vkey, akey, runtime)}</movie>
""")
        if mset:
            sfolder = os.path.join(out, "MovieSets", mset)
            os.makedirs(sfolder, exist_ok=True)
            poster(mset.replace(" Collection", ""), mset, os.path.join(sfolder, "poster.jpg"), "COLLECTION")
            scene(1920, 1080, mset).save(os.path.join(sfolder, "fanart.jpg"), quality=88)

    for si, (title, year, genres, rating, has_logo, seasons) in enumerate(SHOWS):
        folder = os.path.join(shows, title)
        os.makedirs(folder, exist_ok=True)
        seed = title
        poster(title, seed, os.path.join(folder, "poster.jpg"))
        scene(1920, 1080, seed).save(os.path.join(folder, "fanart.jpg"), quality=88)
        landscape(title, seed, os.path.join(folder, "landscape.jpg"))
        if has_logo:
            logo(title, os.path.join(folder, "clearlogo.png"))
        with open(os.path.join(folder, "tvshow.nfo"), "w") as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<tvshow><title>{esc(title)}</title><year>{year}</year><premiered>{year}-03-01</premiered>
<plot>{PLOT.format(who=WHO[(si + 2) % len(WHO)])}</plot><mpaa>TV-MA</mpaa><status>Continuing</status>
<ratings><rating name="themoviedb" max="10" default="true"><value>{rating}</value><votes>900</votes></rating></ratings>
{''.join(f'<genre>{g}</genre>' for g in genres)}<studio>Harbor Television</studio>{cast_xml(seed)}</tvshow>
""")
        for sn, count in seasons.items():
            poster(title, f"{seed}-s{sn}", os.path.join(folder, f"season{sn:02d}-poster.jpg"), f"SEASON {sn}")
            sdir = os.path.join(folder, f"Season {sn:02d}")
            os.makedirs(sdir, exist_ok=True)
            for en in range(1, count + 1):
                base = os.path.join(sdir, f"{title} S{sn:02d}E{en:02d}")
                link(vid, base + ".mkv")
                scene(1280, 720, f"{seed}-{sn}-{en}").save(base + "-thumb.jpg", quality=85)
                ep_title = random.Random(f"{seed}{sn}{en}").choice(
                    ["The Long Way Round", "Undertow", "Cold Open", "What the River Keeps", "Static",
                     "A Room With No Doors", "Margins", "Low Tide", "The Second Signal", "Homecoming"])
                with open(base + ".nfo", "w") as f:
                    f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<episodedetails><title>{esc(ep_title)}</title><season>{sn}</season><episode>{en}</episode>
<aired>{year + sn - 1}-0{1 + en % 9}-1{en % 9}</aired><runtime>{48 + en}</runtime>
<plot>Pressure builds as an old promise resurfaces and the team splits over who to trust.</plot>
<ratings><rating name="themoviedb" max="10" default="true"><value>{7 + (en % 3) * 0.4:.1f}</value><votes>80</votes></rating></ratings>
{streamdetails('4k_hdr' if si != 1 else '1080', 'atmos' if si == 0 else 'ac3', 48)}</episodedetails>
""")
    print("library written to", out)


def link(src, dst):
    if os.path.lexists(dst):
        os.remove(dst)
    os.symlink(src, dst)


def make_sample(path, out):
    """A 3-minute playable clip: cinematic still, 2 audio tracks, 2 subtitle tracks, chapters."""
    if os.path.exists(path):
        return
    frame = os.path.join(out, "_frame.jpg")
    scene(1920, 1080, "sample-frame").save(frame, quality=90)
    srt_en = os.path.join(out, "_en.srt")
    srt_es = os.path.join(out, "_es.srt")
    with open(srt_en, "w") as f:
        f.write("1\n00:00:01,000 --> 00:02:59,000\nWe were never supposed to find this place.\n")
    with open(srt_es, "w") as f:
        f.write("1\n00:00:01,000 --> 00:02:59,000\nNunca debimos encontrar este lugar.\n")
    chapters = os.path.join(out, "_chapters.txt")
    with open(chapters, "w") as f:
        f.write(";FFMETADATA1\n")
        for i, (s, e) in enumerate([(0, 40), (40, 95), (95, 140), (140, 180)]):
            f.write(f"[CHAPTER]\nTIMEBASE=1/1\nSTART={s}\nEND={e}\ntitle=Chapter {i + 1}\n")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", "2", "-i", frame,
        "-f", "lavfi", "-i", "sine=frequency=220:duration=180",
        "-f", "lavfi", "-i", "sine=frequency=330:duration=180",
        "-i", srt_en, "-i", srt_es, "-i", chapters,
        "-map", "0:v", "-map", "1:a", "-map", "2:a", "-map", "3:s", "-map", "4:s", "-map_metadata", "5",
        "-t", "180", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "48k", "-c:s", "srt",
        "-metadata:s:a:0", "language=eng", "-metadata:s:a:1", "language=fre",
        "-metadata:s:s:0", "language=eng", "-metadata:s:s:1", "language=spa",
        path], check=True)


if __name__ == "__main__":
    main(os.path.abspath(sys.argv[1]))
