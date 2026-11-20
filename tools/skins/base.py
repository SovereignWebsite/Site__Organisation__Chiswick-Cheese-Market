"""The default skin: every page type, plainly. Each design subclasses it and overrides what it draws differently."""
from .common import esc, demo_strip, render_blocks, page_sourced, fmt_date, OFFICIAL, Ctx, og_tags

PER_PAGE = 24


class Skin:
    folder = "0"
    name = "Base"
    css = "base.css"
    body_class = ""
    theme_color = "#ffffff"

    # ------------------------------------------------------------ frame
    def layout(self, ctx, title, body, desc=""):
        c = ctx.c
        full = f"{title} | {c.site['name']}" if title else f"{c.site['name']} | {c.site['tagline']}"
        return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="{self.theme_color}">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc or c.site['tagline'])}">
{og_tags(f"designs/{ctx.design}/{ctx.route}", full, desc or c.site['tagline'])}
<link rel="stylesheet" href="{ctx.asset('css/demo.css')}">
<link rel="stylesheet" href="{ctx.asset('css/' + self.css)}">
</head>
<body class="{self.body_class}">
<a class="skip" href="#main">Skip to content</a>
{demo_strip(ctx)}
{self.header(ctx)}
<main id="main">
{body}
</main>
{self.footer(ctx)}
</body>
</html>
"""

    def nav_items(self, ctx):
        """The site's own main menu, with links rewritten to this design's pages."""
        out = []
        for it in ctx.c.site.get("navigation", []):
            kids = it.get("children") or []
            if kids:
                sub = "".join(f'<li><a href="{esc(ctx.rewrite_url(k["url"]))}">{esc(k["label"])}</a></li>' for k in kids if k.get("url"))
                out.append(f'<li class="has-sub"><details><summary>{esc(it["label"])}</summary><ul>{sub}</ul></details></li>')
            elif it.get("url"):
                out.append(f'<li><a href="{esc(ctx.rewrite_url(it["url"]))}">{esc(it["label"])}</a></li>')
        return "".join(out)

    def header(self, ctx):
        return f'<header class="site-head"><a class="brand" href="{ctx.link("")}">{esc(ctx.c.site["name"])}</a><nav aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></header>'

    def footer(self, ctx):
        c = ctx.c
        return (f'<footer class="site-foot"><p>{esc(c.site.get("copyright") or c.site["name"])}</p>'
                f'<p class="credit">All words and images: Chiswick Cheese Market, from <a href="{OFFICIAL}/">chiswickcheesemarket.uk</a>, '
                f'snapshot {esc(c.snap_label)}. Fonts: SIL Open Font License.</p></footer>')

    # ------------------------------------------------------------ helpers
    def cats_of(self, ctx, e):
        return [ctx.c.ex_cat[i]["name"] for i in e["categories"] if i in ctx.c.ex_cat]

    def post_card(self, ctx, p, thumb=True):
        cats = "".join(f'<span class="pill">{esc(n)}</span>' for n in ctx.c.post_cat_names(p))
        im = ctx.image(p["image"], "card-img", thumb, "")
        return (f'<article class="card"><a href="{ctx.link("journal/" + p["slug"] + "/")}">'
                f'{im or "<span class=card-img-empty></span>"}<div class="pills">{cats}</div><h3>{esc(p["title"])}</h3></a>'
                f'<p class="date">{fmt_date(p["date"])}</p>{f"<p class=excerpt>{esc(p["excerpt"])}</p>" if p["excerpt"] else ""}</article>')

    def ex_card(self, ctx, e):
        im = ctx.image(e["image"], "card-img", True, "")
        cats = ", ".join(self.cats_of(ctx, e))
        return (f'<article class="card ex"><a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{im or "<span class=card-img-empty></span>"}'
                f'<h3>{esc(e["name"])}</h3></a><p class="cat">{esc(cats)}</p></article>')

    def listing(self, ctx, spec):
        if spec.get("post_type") == "portfolio":
            return '<div class="grid">' + "".join(self.ex_card(ctx, e) for e in ctx.c.exhibitors) + "</div>"
        posts = ctx.c.listing_posts(spec)
        posts = posts[:3] if not spec.get("categories") else posts
        return '<div class="grid">' + "".join(self.post_card(ctx, p) for p in posts) + "</div>"

    def link_label(self, url):
        u = url.lower()
        for k, v in (("instagram.com", "Instagram"), ("facebook.com", "Facebook"), ("tiktok.com", "TikTok"), ("x.com", "X"), ("twitter.com", "X")):
            if k in u:
                return v
        return url.split("//", 1)[-1].split("/")[0].replace("www.", "")

    # ------------------------------------------------------------ pages
    def page_hero(self, ctx, p):
        im = ctx.image(p.get("image"), "hero-img", False, "")
        return f'<div class="page-hero">{im}</div>' if im else ""

    def page(self, ctx, p):
        body = self.page_hero(ctx, p) + f'<div class="page-body">{render_blocks(ctx, p["blocks"], self)}</div>' + page_sourced(ctx, p["source_url"])
        return self.layout(ctx, p["title"], body)

    def home(self, ctx):
        return self.page(ctx, ctx.c.pages["home"])

    def stallholders(self, ctx):
        p = ctx.c.pages.get("meet-the-stallholders")
        chips = "".join(f'<a class="chip" href="#{esc(c["slug"])}">{esc(c["name"])}</a>' for c in ctx.c.ex_cats if ctx.c.ex_in(c["id"]))
        groups = "".join(
            f'<section class="ex-group" id="{esc(c["slug"])}"><h2>{esc(c["name"])}</h2><div class="grid">'
            + "".join(self.ex_card(ctx, e) for e in ctx.c.ex_in(c["id"])) + "</div></section>"
            for c in ctx.c.ex_cats if ctx.c.ex_in(c["id"]))
        intro = self.page_hero(ctx, p) if p else ""
        return self.layout(ctx, "Meet the stallholders", f'{intro}<div class="page-body"><h1>Meet the stallholders</h1><nav class="chips" aria-label="Categories">{chips}</nav>{groups}</div>')

    def stallholder(self, ctx, e, prev, nxt):
        im = ctx.image(e["image"], "ex-img", False, e["name"])
        links = "".join(f'<li><a href="{esc(u)}">{esc(self.link_label(u))}</a></li>' for u in e["links"])
        pn = (f'<nav class="prevnext"><a href="{ctx.link("stallholders/" + prev["slug"] + "/")}">Previous: {esc(prev["name"])}</a>'
              f'<a href="{ctx.link("stallholders/")}">All stallholders</a>'
              f'<a href="{ctx.link("stallholders/" + nxt["slug"] + "/")}">Next: {esc(nxt["name"])}</a></nav>')
        body = (f'<article class="ex-page"><div class="ex-text"><p class="cat">{esc(", ".join(self.cats_of(ctx, e)))}</p><h1>{esc(e["name"])}</h1>'
                f'<div class="txt">{ctx.rewrite_html(e["description_html"])}</div><ul class="ex-links">{links}</ul></div>'
                f'<div class="ex-media">{im}</div></article>{pn}{page_sourced(ctx, e["source_url"])}')
        return self.layout(ctx, e["name"], body, e["description_text"][:160])

    def journal_pages(self, ctx):
        posts = ctx.c.posts
        return [posts[i:i + PER_PAGE] for i in range(0, len(posts), PER_PAGE)]

    def pager(self, ctx, n, total):
        if total < 2:
            return ""
        items = []
        for i in range(1, total + 1):
            r = "journal/" if i == 1 else f"journal/page-{i}/"
            items.append(f'<a href="{ctx.link(r)}"{" aria-current=page" if i == n else ""}>{i}</a>')
        return f'<nav class="pager" aria-label="Journal pages">{"".join(items)}</nav>'

    def journal(self, ctx, n, chunk, total, cat=None):
        p = ctx.c.pages.get("journal")
        hero = self.page_hero(ctx, p) if p and n == 1 and not cat else ""
        title = cat["name"] if cat else "Community journal"
        cards = "".join(self.post_card(ctx, x) for x in chunk)
        return self.layout(ctx, title + (f" (page {n})" if n > 1 else ""),
                           f'{hero}<div class="page-body"><h1>{esc(title)}</h1><div class="grid">{cards}</div>{"" if cat else self.pager(ctx, n, total)}</div>')

    def post(self, ctx, p):
        cats = "".join(f'<span class="pill">{esc(n)}</span>' for n in ctx.c.post_cat_names(p))
        im = ctx.image(p["image"], "post-img", False, "")
        body = ctx.rewrite_html(p["body_html"]) if p.get("body_html") is not None else render_blocks(ctx, p.get("blocks"), self)
        return self.layout(ctx, p["title"], f'<article class="post"><header><div class="pills">{cats}</div><h1>{esc(p["title"])}</h1>'
                           f'<p class="date">{fmt_date(p["date"])}</p></header>{im}<div class="txt post-body">{body}</div></article>'
                           f'{page_sourced(ctx, p["source_url"])}', p["excerpt"])
