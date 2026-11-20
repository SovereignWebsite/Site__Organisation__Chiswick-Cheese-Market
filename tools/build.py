#!/usr/bin/env python3
"""
build.py - build every design of the site from the snapshot in data/.

  python3 tools/build.py [--out site]

Output (static files, published as they are):
  index.html            a plain chooser, for ordinary static hosting
  designs/1 .. 6/       each design, with the same routes (so "Choose a design" keeps your place)
  admin/                the WordPress viewer and parser (API map, raw data, parser, charts)
  assets/css, fonts    stylesheets and the openly licensed fonts. Images are NOT copied: every page loads
                        them from the market's own site, at a size WordPress already made.
  data/                 the JSON files, plus designs/6/ccm-data.js and admin/raw-data.js
"""
import argparse, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from skins.common import load, Ctx, DESIGNS, DEMO_CSS, esc, OFFICIAL, DISCLAIMER  # noqa: E402
from skins.d1_copy import Copy  # noqa: E402
from skins.d2_journal import Journal  # noqa: E402
from skins.d3_poster import Poster  # noqa: E402
from skins.d4_cellar import Cellar  # noqa: E402
from skins.d5_makers import Makers  # noqa: E402
from skins.d6_data import DataSkin  # noqa: E402
from skins import admin  # noqa: E402

SKINS = [Copy(), Journal(), Poster(), Cellar(), Makers()]


def write(out, rel, s):
    if rel.endswith(".html"):  # house style: no em dashes in visible text (the market's own dashes show as en dashes; data/ keeps them)
        s = s.replace("\u2014", "\u2013")
    p = os.path.join(out, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(s)


def build_skin(skin, c, out):
    n = 0
    def emit(route, html):
        nonlocal n
        write(out, f"designs/{skin.folder}/{route}index.html", html); n += 1
    emit("", skin.home(Ctx(c, skin.folder, "")))
    emit("stallholders/", skin.stallholders(Ctx(c, skin.folder, "stallholders/")))
    ex = c.exhibitors
    for i, e in enumerate(ex):
        r = f"stallholders/{e['slug']}/"
        emit(r, skin.stallholder(Ctx(c, skin.folder, r), e, ex[i - 1], ex[(i + 1) % len(ex)]))
    chunks = skin.journal_pages(Ctx(c, skin.folder, "journal/"))
    for k, chunk in enumerate(chunks, 1):
        r = "journal/" if k == 1 else f"journal/page-{k}/"
        emit(r, skin.journal(Ctx(c, skin.folder, r), k, chunk, len(chunks)))
    for cat in c.post_cats.values():
        posts = [p for p in c.posts if cat["id"] in p["categories"]]
        if posts and cat["slug"] != "uncategorized":
            r = f"journal/category/{cat['slug']}/"
            emit(r, skin.journal(Ctx(c, skin.folder, r), 1, posts, 1, cat=cat))
    for p in c.posts:
        r = f"journal/{p['slug']}/"
        emit(r, skin.post(Ctx(c, skin.folder, r), p))
    for slug, p in c.pages.items():
        if slug in ("home", "meet-the-stallholders", "journal"):
            continue
        r = slug + "/"
        emit(r, skin.page(Ctx(c, skin.folder, r), p))
    return n


def chooser(c):
    """The front door: what this is, and the six designs plus Admin, each with a picture from the market's site."""
    from skins.common import home_facts, pick_size_url
    f = home_facts(c)
    pics = [g["items"][k]["image"] for g in f["features"] for k in range(len(g["items"]))]
    def pic(i):
        m = c.img(pics[i % len(pics)]) if pics else None
        return f'<img src="{esc(pick_size_url(m, 480))}" alt="" loading="lazy">' if m else ""
    items = "".join(f'<li><a href="designs/{d}/index.html">{pic(k)}<span class="n">{d}</span><b>{esc(n)}</b><span class="t">{esc(t)}</span></a></li>'
                    for k, (d, n, t) in enumerate(DESIGNS))
    url = "https://chiswick-cheese-market.organisation.sovereignweb.site/"
    title = "Chiswick Cheese Market, six ways: a demonstration"
    desc = "A demonstration by Sovereign Website: the market's own content, read from its WordPress site, drawn six ways. Not the official site."
    hh = (c.site.get("home_header") or {}).get("image_url") or ""
    nm = c.next_market()
    import re as _re
    import html as _html
    where = _html.unescape(_re.sub(r"<[^>]+>", "", (f["intro"] or [""])[0])).strip()
    nm_html = (f'<p class="nextm"><b>Next market: Sunday {nm.day} {nm:%B %Y}</b><span>{esc(where)}</span></p>' if nm else "")
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="noindex, nofollow">
<meta property="og:type" content="website"><meta property="og:site_name" content="Chiswick Cheese Market, a demonstration"><meta property="og:locale" content="en_GB">
<meta property="og:url" content="{url}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{url}assets/share/card-1200x630.jpg"><meta property="og:image:type" content="image/jpeg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{url}assets/share/card-1200x630.jpg">
<link rel="stylesheet" href="assets/css/demo.css"><link rel="stylesheet" href="assets/css/home.css"></head>
<body><aside class="demo-strip" aria-label="About this demonstration"><p class="demo-line">{esc(DISCLAIMER)} The official site is <a href="{OFFICIAL}/">chiswickcheesemarket.uk</a>. Pictures load from the market's own site.</p></aside>
<header class="door" style="background-image:url('{esc(hh)}')"><div class="veil">{nm_html}<p class="k">A demonstration for the organisers</p>
<h1>Chiswick Cheese Market, six ways</h1><p>The market's own words and pictures, read from its WordPress site ({esc(c.snap_label)}) and drawn six ways.
WordPress stays exactly as it is; these are new front ends on the same content.</p></div></header>
<main><ul class="designs">{items}<li><a href="buttercup/index.html" class="adm"><span class="n">&#128004;</span><b>Buttercup</b><span class="t">The market's cow in its own pictures and journal: every outfit we could find</span></a></li><li><a href="admin/index.html" class="adm"><span class="n">&#9881;</span><b>Admin</b><span class="t">The WordPress viewer and parser: everything the API gives, raw and parsed</span></a></li></ul>
<p class="foot">Pictures load from chiswickcheesemarket.uk; nothing is copied. Data: <a href="data/index.json">data/index.json</a>.</p></main></body></html>"""


def buttercup(c):
    """Buttercup the cow: her pictures and outfits, from data/buttercup.json (every image loads from the market's site)."""
    from skins.common import og_tags
    d = json.load(open(os.path.join(ROOT, "data", "buttercup.json")))
    imgs = "".join(f'<figure><a href="{esc(i["image_url"])}"><img src="{esc(i["image_url"])}" alt="{esc(re.sub(r"[-_]", " ", i["title"].split(" (")[0]))}" loading="lazy"></a>'
                   f'<figcaption>{esc(i["title"].split(" (caption: ")[-1].rstrip(")") if "caption:" in i["title"] else re.sub(r"[-_]", " ", i["title"].split(" (")[0]))}'
                   f'<small>{esc(i["date"].split(" (")[0])}</small></figcaption></figure>' for i in d["images"])
    outfits = "".join(f'<li><time>{esc(o["date"])}</time><blockquote>{esc(o["quote"])}</blockquote><a href="{esc(o["post_url"])}">The journal post</a></li>' for o in d["outfits"])
    gifs = "".join(f'<li><a href="{esc(g["url"])}">{esc(g["url"].rsplit("/", 1)[-1])}</a> <small>{g["bytes"] / 1e6:.1f} MB{" (shows Buttercup)" if g["verified_shows_buttercup"] else ""}</small></li>' for g in d["animated_banners"])
    dec = next((g["url"] for g in d["animated_banners"] if g["verified_shows_buttercup"]), None)
    snaps = "".join(f'<li><a href="{esc(x["url"])}">{x["timestamp"][:4]}-{x["timestamp"][4:6]}-{x["timestamp"][6:8]}</a></li>' for x in d["wayback"]["snapshots"])
    title = "Buttercup, the Cheesewick cow"
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | Chiswick Cheese Market, a demonstration</title><meta name="description" content="Buttercup the cow in the market's own pictures and journal."><meta name="robots" content="noindex, nofollow">
{og_tags("buttercup/", title, "Buttercup the cow in the market's own pictures and journal.")}
<link rel="stylesheet" href="../assets/css/demo.css"><link rel="stylesheet" href="../assets/css/home.css"><link rel="stylesheet" href="../assets/css/buttercup.css"></head>
<body><aside class="demo-strip" aria-label="About this demonstration"><p class="demo-line">{esc(DISCLAIMER)} The official site is <a href="{OFFICIAL}/">chiswickcheesemarket.uk</a>. <a href="../index.html">All six designs</a>.</p></aside>
<main class="cow"><p class="k">From the market's own media library and journal</p><h1>{esc(title)}</h1>
<p class="lede">{esc(d["about"])}</p>
{f'<figure class="anim"><img src="{esc(dec)}" alt="The December 2026 market banner: Buttercup in Christmas tinsel, with cheeses sliding in beside her" loading="lazy"><figcaption>The animated banner on the home page now (December 2026 market).</figcaption></figure>' if dec else ""}
<h2>{len(d["images"])} pictures of Buttercup</h2><div class="cowgrid">{imgs}</div>
<h2>What she wore</h2><ol class="outfits">{outfits}</ol>
<h2>The monthly animated banners</h2><p>{len(d["animated_banners"])} animated GIFs announce each market, January 2025 to December 2026. Only the December one has been checked frame by frame; some are large (up to 20 MB), so they are linked, not shown.</p><ul class="gifs">{gifs}</ul>
<h2>Earlier versions of the site</h2><p>{esc(d["wayback"]["note"])}</p><ul class="gifs">{snaps}</ul>
</main></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "site"))
    a = ap.parse_args()
    out = a.out
    c = load(ROOT)
    os.makedirs(out, exist_ok=True)
    # assets
    for d in ("designs", "admin", "data", "assets/css", "assets/fonts"):  # rebuilt each time; CNAME, robots.txt and the share card stay
        shutil.rmtree(os.path.join(out, d), ignore_errors=True)
    shutil.copytree(os.path.join(HERE, "skins", "fonts"), os.path.join(out, "assets", "fonts"), dirs_exist_ok=True)
    os.makedirs(os.path.join(out, "assets", "css"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "skins", "css")):
        shutil.copy(os.path.join(HERE, "skins", "css", f), os.path.join(out, "assets", "css", f))
    write(out, "assets/css/demo.css", DEMO_CSS)
    # data
    os.makedirs(os.path.join(out, "data"), exist_ok=True)
    for f in os.listdir(os.path.join(ROOT, "data")):
        if f.endswith(".json"):
            shutil.copy(os.path.join(ROOT, "data", f), os.path.join(out, "data", f))
    total = 0
    for s in SKINS:
        k = build_skin(s, c, out); total += k
        print(f"design {s.folder} {s.name}: {k} pages")
    k = DataSkin().build(c, out, write); total += k
    print(f"design 6 data: {k} pages")
    k = admin.build(c, ROOT, out, write); total += k
    print(f"admin: {k} pages")
    write(out, "index.html", chooser(c))
    if os.path.exists(os.path.join(ROOT, "data", "buttercup.json")):
        write(out, "buttercup/index.html", buttercup(c)); total += 1
    print("total pages", total + 1, "->", out)


if __name__ == "__main__":
    main()
