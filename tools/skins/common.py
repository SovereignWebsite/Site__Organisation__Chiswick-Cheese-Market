"""Shared building blocks for the skins: the content model, routes, link and image rewriting,
the block renderer, and the demonstration strip with the "Choose a design" control.

A skin is a class with a folder number, a name and a stylesheet, which can override any of:
home, page, stallholders, stallholder, journal, post, layout. Every skin draws the same routes, so
the design chooser can jump to the same page in another design.
"""
import datetime, html, json, os, re

OFFICIAL = "https://www.chiswickcheesemarket.uk"
HOST_RE = re.compile(r"^https?://(?:www\.)?chiswickcheesemarket\.uk")
DISCLAIMER = "A demonstration by Sovereign Website for Chiswick Cheese Market. Not the official site."

DESIGNS = [  # folder, short name, one line
    ("1", "The current site", "A close copy of chiswickcheesemarket.uk, built from its own data"),
    ("2", "Journal", "An editorial, magazine-style front page"),
    ("3", "Poster", "Bold market-poster typography"),
    ("4", "Cellar", "Dark and warm, like a cheese cave"),
    ("5", "The makers", "Built around the stallholders and their own sites"),
    ("6", "The data", "The open JSON behind every design, with a query tool and charts"),
]

esc = html.escape


SITE = "https://chiswick-cheese-market.organisation.sovereignweb.site/"


def og_tags(abs_path, title, desc):
    """Link-preview tags for every page (the share card is the site's own image)."""
    t, d, u = esc(title), esc((desc or "")[:200]), SITE + abs_path
    return (f'<meta property="og:type" content="website"><meta property="og:site_name" content="Chiswick Cheese Market, a demonstration">'
            f'<meta property="og:locale" content="en_GB"><meta property="og:url" content="{esc(u)}"><meta property="og:title" content="{t}">'
            f'<meta property="og:description" content="{d}"><meta property="og:image" content="{SITE}assets/share/card-1200x630.jpg">'
            f'<meta property="og:image:type" content="image/jpeg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="Chiswick Cheese Market, a demonstration"><meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:title" content="{t}"><meta name="twitter:description" content="{d}"><meta name="twitter:image" content="{SITE}assets/share/card-1200x630.jpg">')


def load(root):
    d = lambda n: json.load(open(os.path.join(root, "data", n)))
    site, pages, posts, ex, cats, media = (d(n) for n in ("site.json", "pages.json", "posts.json", "exhibitors.json", "categories.json", "media.json"))
    c = Content(site, pages, posts, ex, cats, media, d("index.json"))
    dl = os.path.join(root, "data", "dead-links.json")
    c.dead = {x["url"] for x in json.load(open(dl))["items"]} if os.path.exists(dl) else set()
    return c


class Content:
    def __init__(self, site, pages, posts, ex, cats, media, index):
        self.site = site["items"]
        self.snapshot = site["snapshot"]
        self.index = index
        self.pages = {p["slug"]: p for p in pages["items"]}
        self.posts = sorted(posts["items"], key=lambda p: p["date"], reverse=True)
        self.exhibitors = sorted(ex["items"], key=lambda e: e["name"].lower())
        self.ex_cats = sorted(cats["items"]["exhibitor_categories"], key=lambda c: (-c.get("count", 0), c["id"]))
        self.post_cats = {c["id"]: c for c in cats["items"]["post_categories"]}
        self.ex_cat = {c["id"]: c for c in self.ex_cats}
        self.media = {str(m["id"]): m for m in media["items"]}
        self.by_url = {}
        for m in media["items"]:
            self.by_url[m["original_url"]] = m
        self.routes = {}  # official URL path -> route
        for p in pages["items"]:
            self.routes[path_of(p["source_url"])] = page_route(p["slug"])
        for e in ex["items"]:
            self.routes[path_of(e["source_url"])] = f"stallholders/{e['slug']}/"
        for p in posts["items"]:
            self.routes[path_of(p["source_url"])] = f"journal/{p['slug']}/"
        self.routes["/"] = ""
        snap = datetime.datetime.fromisoformat(self.snapshot["snapshot_finished"].replace("Z", "+00:00"))
        self.snap_date = snap.date()
        self.snap_label = snap.strftime("%-d %B %Y, %H:%M UTC")
        self.market_dates = market_dates(self.pages.get("home"))

    def img(self, mid):
        m = self.media.get(str(mid)) if mid else None
        return m if m and (m.get("sizes") or m.get("original_url")) else None

    def listing_posts(self, spec):
        """The posts a page-builder listing shows: its categories, newest first."""
        cats = set(spec.get("categories") or [])
        ps = [p for p in self.posts if not cats or cats & set(p["categories"])]
        return ps

    def ex_in(self, cid):
        return [e for e in self.exhibitors if cid in e["categories"]]

    def next_market(self):
        future = [d for d in self.market_dates if d >= self.snap_date]
        return future[0] if future else None

    def post_cat_names(self, p):
        return [self.post_cats[c]["name"] for c in p.get("categories", []) if c in self.post_cats and self.post_cats[c]["slug"] != "uncategorized"]


def pick_size_url(m, target):
    """Smallest WordPress-made size at least `target` px wide (else the largest), from media.json."""
    sizes = [v for k, v in (m.get("sizes") or {}).items() if v.get("url") and v.get("width") and "woocommerce" not in k]
    big = sorted((v for v in sizes if v["width"] >= target), key=lambda v: v["width"])
    if big:
        return big[0]["url"]
    if sizes:
        return max(sizes, key=lambda v: v["width"])["url"]
    return m.get("download_url") or m.get("original_url")


def path_of(url):
    return HOST_RE.sub("", (url or "").split("#")[0].split("?")[0]) or "/"


def page_route(slug):
    return {"home": "", "meet-the-stallholders": "stallholders/", "journal": "journal/"}.get(slug, slug + "/")


MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}


def market_dates(home):
    """The 'Sunday 18th January 2026' lines on the home page, as dates (from the site, not invented)."""
    out = []
    def walk(bl):
        for b in bl or []:
            if b.get("blocks"):
                walk(b["blocks"])
            for t in re.findall(r"Sunday\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})", re.sub("<[^>]+>", "", b.get("html", "") + " " + b.get("text", ""))):
                if t[1].lower() in MONTHS:
                    out.append(datetime.date(int(t[2]), MONTHS[t[1].lower()], int(t[0])))
    walk((home or {}).get("blocks"))
    return sorted(set(out))


def fmt_date(iso, style="%-d %B %Y"):
    return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime(style)


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


class Ctx:
    """Where a page is (its route) inside a design folder, for relative links."""
    def __init__(self, content, design, route):
        self.c, self.design, self.route = content, design, route
        self.depth = route.count("/")

    def up(self):
        return "../" * (self.depth + 2)  # to the site root (designs/N/<route>)

    def asset(self, p):
        return self.up() + "assets/" + p

    def media_src(self, m, thumb=False):
        """The image on the market's own site, at a size WordPress already made (no copies are kept here)."""
        return pick_size_url(m, 480 if thumb else 1100)

    def link(self, route, design=None):
        d = design or self.design
        base = "../" * self.depth + ("" if d == self.design else f"../{d}/")
        return base + route + "index.html"

    def rewrite_url(self, url):
        if not url:
            return "#"
        if HOST_RE.match(url):
            p = path_of(url)
            frag = ("#" + url.split("#", 1)[1]) if "#" in url else ""
            if p in self.c.routes:
                return self.link(self.c.routes[p]) + frag
            for prefix, r in (("/category/", "journal/"), ("/stallholders/", "stallholders/"), ("/portfolio_category/", "stallholders/")):
                if p.startswith(prefix):
                    return self.link(r)
        return url

    def is_dead(self, u):
        u = (u or "").split("#")[0]
        return bool(u) and (u in self.c.dead or u.rstrip("/") + "/" in self.c.dead)

    def rewrite_html(self, h):
        def dead(m):
            u = html.unescape(m.group(1))
            if self.is_dead(u):
                return f'<span class="dead" title="This link no longer works">{m.group(2)} <small>(link no longer works)</small></span>'
            return m.group(0)
        h = re.sub(r'<a href="([^"]*)">(.*?)</a>', dead, h or "", flags=re.S)
        def a(m):
            return f'<a href="{esc(self.rewrite_url(html.unescape(m.group(1))))}">'
        h = re.sub(r'<a href="([^"]*)">', a, h)
        def img(m):
            tag = m.group(0)
            mid = re.search(r'data-media-id="(\d+)"', tag)
            src = re.search(r'src="([^"]+)"', tag).group(1)
            alt = re.search(r'alt="([^"]*)"', tag)
            rec = self.c.img(mid.group(1)) if mid else self.c.by_url.get(src)
            if not rec:
                return ""
            return f'<img src="{self.media_src(rec)}" alt="{alt.group(1) if alt else ""}" loading="lazy">'
        return re.sub(r"<img [^>]+>", img, h)

    def image(self, mid, cls="", thumb=False, alt=None):
        m = self.c.img(mid)
        if not m:
            return ""
        a = alt if alt is not None else (m.get("alt") or "")
        return f'<img class="{cls}" src="{self.media_src(m, thumb)}" alt="{esc(a)}" loading="lazy">'


def demo_strip(ctx, skin_routes=None):
    """The line on every page, and the design chooser (links to the same page in each design)."""
    opts = []
    for d, name, _ in DESIGNS:
        route = ctx.route if (d != "6" and ctx.design != "6") else ""
        here = ' aria-current="page"' if d == ctx.design else ""
        opts.append(f'<a href="{ctx.link(route, d)}"{here}><b>{d}</b> {esc(name)}</a>')
    return (f'<div class="demo-strip" role="note"><p class="demo-line">{esc(DISCLAIMER)} '
            f'The official site is <a href="{OFFICIAL}/">chiswickcheesemarket.uk</a>. '
            f'Content snapshot {esc(ctx.c.snap_label)}.</p>'
            f'<div class="demo-actions"><details class="demo-choose"><summary>Choose a design</summary><nav aria-label="Choose a design">{"".join(opts)}</nav></details>'
            f'<a class="demo-admin" href="{ctx.up()}admin/index.html">Admin</a></div></div>')


DEMO_CSS = """
.demo-strip{font:13px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:#111;color:#f3f3f3;display:flex;flex-wrap:wrap;gap:4px 16px;align-items:center;justify-content:space-between;padding:6px 16px;position:relative;z-index:50}
.demo-strip a{color:#ffd65a;text-decoration:underline}
.demo-line{margin:0;flex:1 1 420px}
.demo-choose{position:relative}
.dead{text-decoration:line-through;text-decoration-thickness:1px}.dead small{text-decoration:none;display:inline-block;opacity:.7;font-size:.8em}
.demo-actions{display:flex;gap:10px;align-items:center}
.demo-admin{border:1px solid #ffd65a;border-radius:999px;padding:2px 12px;text-decoration:none;font-weight:600}
.demo-choose summary{cursor:pointer;list-style:none;background:#ffd65a;color:#111;border-radius:999px;padding:3px 12px;font-weight:600;white-space:nowrap}
.demo-choose summary::-webkit-details-marker{display:none}
.demo-choose summary::after{content:" \\25BE"}
.demo-choose nav{position:absolute;right:0;top:calc(100% + 6px);background:#111;border:1px solid #444;border-radius:10px;padding:6px;display:grid;min-width:220px;box-shadow:0 10px 30px rgba(0,0,0,.4)}
.demo-choose nav a{color:#f3f3f3;text-decoration:none;padding:7px 10px;border-radius:6px}
.demo-choose nav a b{display:inline-block;width:1.4em;color:#ffd65a}
.demo-choose nav a:hover,.demo-choose nav a:focus{background:#2a2a2a}
.demo-choose nav a[aria-current]{background:#ffd65a;color:#111}
.demo-choose nav a[aria-current] b{color:#111}
@media (max-width:600px){.demo-choose nav{right:auto;left:0}}
"""


def fonts_css(ctx, faces):
    """@font-face rules for the self-hosted, openly licensed fonts (SIL OFL) in assets/fonts/."""
    out = []
    for fam, file, weight, style in faces:
        out.append(f"@font-face{{font-family:'{fam}';src:url('{ctx.asset('fonts/' + file)}') format('woff2');font-weight:{weight};font-style:{style};font-display:swap}}")
    return "\n".join(out)


# ------------------------------------------------------------------ blocks
def render_blocks(ctx, blocks, skin, depth=0):
    out = []
    for b in blocks or []:
        t = b["type"]
        if t == "section":
            bg = b.get("background") or ""
            style = ""
            if b.get("background_image") and ctx.c.img(b["background_image"]):
                style = f' style="background-image:url(\'{ctx.media_src(ctx.c.img(b["background_image"]))}\')"'
            inner = render_blocks(ctx, b["blocks"], skin, depth + 1)
            if inner.strip() or style:
                out.append(f'<section class="sec bg-{esc(bg)}{" has-bg" if style else ""}"{style}><div class="sec-in">{inner}</div></section>')
        elif t == "column":
            w = b.get("width", "1/1").replace("/", "-")
            style = ""
            if b.get("background_image") and ctx.c.img(b["background_image"]):
                style = f' style="background-image:url(\'{ctx.media_src(ctx.c.img(b["background_image"]))}\')"'
            inner = render_blocks(ctx, b["blocks"], skin, depth + 1)
            if inner.strip() or style:
                out.append(f'<div class="col w-{w}{" has-bg" if style else ""}"{style}>{inner}</div>')
        elif t == "heading":
            if b.get("style") == "marquee":
                txt = esc(b["text"])
                icon = "".join(ctx.image(i, "mq-ic", True, "") for i in b.get("inline_images", [])[:1])
                if txt:
                    unit = f"<span>{txt} {icon}</span>"
                    out.append(f'<div class="marquee" role="marquee" aria-label="{txt}"><div class="mq-track" aria-hidden="true">{unit * 8}</div></div>')
                continue
            lvl = b.get("level", "h2")
            lvl = lvl if lvl in ("h1", "h2", "h3", "h4", "h5", "h6") else "h2"
            if lvl == "h6":
                lvl = "h3"
            cls = ' class="vertical"' if b.get("style") == "vertical" else ""
            out.append(f"<{lvl}{cls}>{esc(b['text'])}</{lvl}>")
        elif t in ("text", "html"):
            out.append(f'<div class="txt">{ctx.rewrite_html(b["html"])}</div>')
        elif t == "button":
            if ctx.is_dead(b.get("url")):
                out.append(f'<p class="btn-wrap"><span class="btn dead" title="This link no longer works">{esc(b["text"])}</span> <small>(link no longer works)</small></p>')
            else:
                out.append(f'<p class="btn-wrap"><a class="btn" href="{esc(ctx.rewrite_url(b["url"]))}">{esc(b["text"])}</a></p>')
        elif t == "image":
            im = ctx.image(b["media"], "blk-img")
            if im:
                url = b.get("url")
                out.append(f'<figure class="fig">{f"<a href=\"{esc(ctx.rewrite_url(url))}\">{im}</a>" if url and url.startswith("http") else im}</figure>')
        elif t == "gallery":
            imgs = "".join(ctx.image(i, "", True) for i in b["media"])
            out.append(f'<div class="gallery">{imgs}</div>')
        elif t == "listing":
            out.append(skin.listing(ctx, b))
        elif t == "form":
            out.append(f'<p class="note">The form is on the official site.</p>')
        elif t == "embed":
            out.append('<p class="note">An embedded feed or sign-up form on the official site is not copied here.</p>')
    return "".join(out)


def page_sourced(ctx, url):
    return f'<p class="source">From the official page: <a href="{esc(url)}">{esc(url.replace("https://", ""))}</a></p>'


def leaves(blocks):
    for b in blocks or []:
        if b.get("blocks") is not None and b["type"] in ("section", "column"):
            yield from leaves(b["blocks"])
        else:
            yield b


def home_facts(c):
    """What the home page says, pulled out of its blocks so each design can lay it out its own way."""
    home = c.pages.get("home") or {"blocks": []}
    f = {"marquee": None, "tagline": None, "intro": [], "button": None, "features": [], "hero": home.get("image")}
    for sec in home["blocks"]:
        ls = list(leaves([sec]))
        heads = [b for b in ls if b["type"] == "heading" and b.get("style") not in ("marquee", "vertical")]
        if any(b["type"] == "heading" and b.get("style") == "marquee" and b.get("text") for b in ls):
            f["marquee"] = next(b["text"] for b in ls if b.get("style") == "marquee" and b.get("text"))
        imgs = [b for b in ls if b["type"] == "image"]
        if heads and not f["tagline"] and any(b["type"] == "text" for b in ls):
            f["tagline"] = heads[0]["text"]
            f["intro"] = [b["html"] for b in ls if b["type"] == "text"]
            f["button"] = next((b for b in ls if b["type"] == "button"), None)
            if imgs:
                f["hero_side"] = imgs[0]["media"]
            continue
        if len(imgs) >= 3 and len(heads) >= len(imgs):
            # a group: its title, then image + heading pairs
            pairs = []
            it = iter(ls)
            pend = None
            for b in ls:
                if b["type"] == "image":
                    pend = b["media"]
                elif b["type"] == "heading" and pend:
                    pairs.append({"image": pend, "title": b["text"]}); pend = None
            f["features"].append({"title": heads[0]["text"], "items": pairs})
    return f


def intro_text(c):
    import re as _re
    return [_re.sub(r"<[^>]+>", "", h) for h in home_facts(c)["intro"]]
