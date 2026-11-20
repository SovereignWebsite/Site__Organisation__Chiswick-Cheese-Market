"""Design 1: as close a copy of the current chiswickcheesemarket.uk as static HTML and CSS allow.

Layout, colours (the theme's own palette), navigation and page structure follow the live site. The
heading face on the live site (Kapra Neue) is a commercial font, so Barlow Condensed (SIL OFL) stands
in; the body face, Roboto Slab, is the same (SIL OFL), self-hosted.
"""
from .base import Skin
from .common import esc, render_blocks, page_sourced, fmt_date, OFFICIAL

SOCIAL_ICON = {  # simple monograms, not brand logos
    "instagram": "IG", "facebook": "f", "x.com": "X", "twitter": "X", "tiktok": "TT", "threads": "@"}


def social_label(u):
    for k, v in (("instagram", "Instagram"), ("facebook", "Facebook"), ("x.com", "X"), ("twitter", "X"), ("tiktok", "TikTok"), ("threads", "Threads")):
        if k in u:
            return v
    return u


class Copy(Skin):
    folder, name, css, body_class, theme_color = "1", "The current site", "d1.css", "d1", "#fab600"

    def social(self, ctx, cls="social"):
        items = []
        for u in ctx.c.site.get("social", []):
            lab = social_label(u)
            mono = next((v for k, v in SOCIAL_ICON.items() if k in u), "?")
            items.append(f'<li><a href="{esc(u)}" title="{esc(lab)}"><span aria-hidden="true">{esc(mono)}</span><span class="sr">{esc(lab)}</span></a></li>')
        return f'<ul class="{cls}">{"".join(items)}</ul>'

    def header(self, ctx):
        c = ctx.c
        top = "".join(f'<li><a href="{esc(ctx.rewrite_url(i["url"]) if i.get("url") else ctx.link("newsletter/"))}">{esc(i["label"])}</a></li>'
                      for i in c.site.get("topbar", []))
        logo = f'<img src="{esc(c.site["logo_url"])}" alt="{esc(c.site["name"])}" width="120" height="120">' if c.site.get("logo_url") else esc(c.site["name"])
        return (f'<nav class="topbar" aria-label="Top menu"><ul class="top-menu">{top}</ul>{self.social(ctx)}</nav>'
                f'<header class="site-head"><a class="logo" href="{ctx.link("")}">{logo}</a>'
                f'<details class="menu-toggle"><summary aria-label="Menu"><span></span></summary></details>'
                f'<nav class="main-nav" aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></header>')

    def footer(self, ctx):
        c = ctx.c
        def menu(key):
            return "".join(f'<li><a href="{esc(ctx.rewrite_url(i["url"]))}">{esc(i["label"])}</a></li>' for i in c.site.get(key, []) if i.get("url"))
        bottom = "".join(f'<li><a href="{esc(ctx.rewrite_url(i["url"]))}">{esc(i["label"])}</a></li>' for i in c.site.get("bottom_bar", []) if i.get("url"))
        return (f'<footer class="site-foot"><div class="foot-cols"><div class="foot-spacer"></div><ul>{menu("footer_1")}</ul><ul>{menu("footer_2")}</ul>'
                f'<div class="keep"><p>Keep in touch</p>{self.social(ctx, "social dark")}<p><a href="{ctx.link("newsletter/")}">Sign up for newsletter</a></p></div></div>'
                f'<div class="foot-bottom"><p>{esc(c.site.get("copyright") or "")}</p><ul>{bottom}</ul></div>'
                f'<p class="credit">Copy for demonstration. Words and images: Chiswick Cheese Market, from <a href="{OFFICIAL}/">chiswickcheesemarket.uk</a>, '
                f'snapshot {esc(c.snap_label)}. Headings in Barlow Condensed, a free stand-in for the site\'s licensed font.</p></footer>')

    # The journal cards on the live site: picture, category pills, condensed title, date, excerpt.
    def listing(self, ctx, spec):
        if spec.get("post_type") == "portfolio":
            return self.ex_grid(ctx)
        posts = ctx.c.listing_posts(spec)
        posts = posts[:3] if not spec.get("categories") else posts
        return '<div class="grid g3">' + "".join(self.post_card(ctx, p) for p in posts) + "</div>"

    def ex_grid(self, ctx):
        chips = "".join(f'<a class="chip" href="#{esc(c["slug"])}">{esc(c["name"])}</a>' for c in ctx.c.ex_cats if ctx.c.ex_in(c["id"]))
        groups = "".join(
            f'<section class="ex-group" id="{esc(c["slug"])}"><h2>{esc(c["name"])}</h2><div class="grid g4">'
            + "".join(self.ex_card(ctx, e) for e in ctx.c.ex_in(c["id"])) + "</div></section>"
            for c in ctx.c.ex_cats if ctx.c.ex_in(c["id"]))
        return f'<div class="ex-list"><p class="chips-label">Categories</p><nav class="chips" aria-label="Categories">{chips}</nav>{groups}</div>'

    def page(self, ctx, p, listing_override=None):
        ctx.need_h1 = True
        hero = self.page_hero(ctx, p)
        body = render_blocks(ctx, p["blocks"], self)
        return self.layout(ctx, p["title"] if p["slug"] != "home" else "", f'{hero}<div class="blocks">{body}</div>{page_sourced(ctx, p["source_url"])}')

    def home(self, ctx):
        p = ctx.c.pages["home"]
        hh = ctx.c.site.get("home_header") or {}
        hero = ""
        if hh.get("image_url"):
            poster = hh["image_url"]
            video = (f'<video autoplay muted loop playsinline preload="none" poster="{esc(poster)}" src="{esc(hh["video_url"])}" aria-hidden="true"></video>'
                     if hh.get("video_url") else "")
            hero = f'<div class="home-hero" style="background-image:url(\'{poster}\')">{video}</div>'
        ctx.need_h1 = True
        body = render_blocks(ctx, p["blocks"], self)
        return self.layout(ctx, "", f'{hero}<div class="blocks home">{body}</div>{page_sourced(ctx, p["source_url"])}')

    def stallholders(self, ctx):
        p = ctx.c.pages.get("meet-the-stallholders")
        return self.page(ctx, p)

    def stallholder(self, ctx, e, prev, nxt):
        im = ctx.image(e["image"], "ex-img", False, e["name"])
        links = "".join(f'<li><a href="{esc(u)}">{esc(self.link_label(u))}</a></li>' for u in e["links"])
        def pn(x, label, cls):
            return (f'<a class="pn {cls}" href="{ctx.link("stallholders/" + x["slug"] + "/")}">{ctx.image(x["image"], "pn-img", True, "")}'
                    f'<span><small>{label}</small><b>{esc(x["name"])}</b></span></a>')
        body = (f'<article class="ex-page"><div class="ex-text"><p class="cat">{esc(", ".join(self.cats_of(ctx, e)))}</p><h1>{esc(e["name"])}</h1>'
                f'<div class="txt">{ctx.rewrite_html(e["description_html"])}</div><ul class="ex-links">{links}</ul></div>'
                f'<div class="ex-media">{im}</div></article>'
                f'<nav class="prevnext" aria-label="More stallholders">{pn(prev, "Previous", "prev")}'
                f'<a class="all" href="{ctx.link("stallholders/")}" aria-label="All stallholders">&#9638;</a>{pn(nxt, "Next", "next")}</nav>'
                f'{page_sourced(ctx, e["source_url"])}')
        return self.layout(ctx, e["name"], body, e["description_text"][:160])

    def journal(self, ctx, n, chunk, total, cat=None):
        p = ctx.c.pages.get("journal")
        hero = self.page_hero(ctx, p) if p else ""
        cats = [c for c in sorted(ctx.c.post_cats.values(), key=lambda c: -c.get("count", 0)) if c.get("count") and c["slug"] != "uncategorized"]
        filt = f'<a href="{ctx.link("journal/")}"{" aria-current=page" if not cat else ""}>Show all</a>' + "".join(
            f'<a href="{ctx.link("journal/category/" + c["slug"] + "/")}"{" aria-current=page" if cat and cat["id"] == c["id"] else ""}>{esc(c["name"])}</a>' for c in cats)
        title = cat["name"] if cat else "Community journal"
        intro = ""
        if p and not cat:
            intro = "".join(f'<div class="txt lead">{ctx.rewrite_html(b["html"])}</div>' for b in walk(p["blocks"]) if b["type"] == "text")[:2000]
        cards = "".join(self.post_card(ctx, x) for x in chunk)
        return self.layout(ctx, title + (f" (page {n})" if n > 1 else ""),
                           f'{hero}<div class="journal"><h1>{esc(title)}</h1>{intro}<nav class="filter" aria-label="Journal categories">{filt}</nav>'
                           f'<div class="grid g3">{cards}</div>{self.pager(ctx, n, total) if not cat else ""}</div>')

    def post(self, ctx, p):
        cats = "".join(f'<span class="pill">{esc(n)}</span>' for n in ctx.c.post_cat_names(p))
        im = ctx.image(p["image"], "post-img", False, "")
        body = ctx.rewrite_html(p["body_html"]) if p.get("body_html") is not None else render_blocks(ctx, p.get("blocks"), self)
        return self.layout(ctx, p["title"], f'<article class="post"><header class="post-head"><div class="pills">{cats}</div><h1>{esc(p["title"])}</h1>'
                           f'<p class="date">{fmt_date(p["date"])}</p></header>{f"<div class=post-hero>{im}</div>" if im else ""}<div class="txt post-body">{body}</div>'
                           f'<p class="back"><a href="{ctx.link("journal/")}">Back to the journal</a></p></article>{page_sourced(ctx, p["source_url"])}', p["excerpt"])


def walk(blocks):
    for b in blocks or []:
        if b.get("blocks"):
            yield from walk(b["blocks"])
        else:
            yield b
