"""Design 4: Cellar. Dark and warm, like a cheese cave: full-bleed photographs, gold rules, a serif
in italics. A light 'parchment' version follows the visitor's light mode. Playfair Display and Inter (SIL OFL)."""
from .base import Skin
from .common import esc, home_facts, fmt_date, ordinal, render_blocks, page_sourced


class Cellar(Skin):
    folder, name, css, body_class, theme_color = "4", "Cellar", "d4.css", "d4", "#15110e"

    def header(self, ctx):
        return (f'<header class="cave-head"><a class="wordmark" href="{ctx.link("")}"><i>the</i> Chiswick <span>Cheese Market</span></a>'
                f'<details class="drawer"><summary>Menu</summary><nav aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></details></header>')

    def footer(self, ctx):
        c = ctx.c
        nm = c.next_market()
        return (f'<footer class="cave-foot"><p class="wordmark"><i>the</i> Chiswick <span>Cheese Market</span></p>'
                f'{f"<p>Next market: Sunday {ordinal(nm.day)} {nm:%B %Y}</p>" if nm else ""}<p>{esc(c.site.get("copyright") or "")}</p>'
                f'<p class="small">Words and photographs: Chiswick Cheese Market, chiswickcheesemarket.uk, snapshot {esc(c.snap_label)}. '
                f'Type: Playfair Display and Inter (SIL Open Font License).</p></footer>')

    def home(self, ctx):
        c = ctx.c
        f = home_facts(c)
        hh = c.site.get("home_header") or {}
        hero_src = hh.get("image_url") or ""
        nm = c.next_market()
        intro = "".join(f'<div class="txt">{ctx.rewrite_html(h)}</div>' for h in f["intro"])
        chapters = []
        for gi, g in enumerate(f["features"]):
            items = "".join(f'<figure class="{"wide" if i == 0 else ""}">{ctx.image(it["image"], "", False, "")}<figcaption>{esc(it["title"])}</figcaption></figure>'
                            for i, it in enumerate(g["items"]))
            chapters.append(f'<section class="chapter"><p class="num">{["I", "II", "III", "IV"][gi % 4]}</p><h2>{esc(g["title"])}</h2><div class="mosaic">{items}</div></section>')
        dates = "".join(f'<li class="{"past" if d < c.snap_date else ""}{" next" if d == nm else ""}">Sunday {ordinal(d.day)} {d:%B}</li>' for d in c.market_dates)
        maker = [e for e in c.exhibitors if e["image"]]
        makers = "".join(f'<a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<span>{esc(e["name"])}</span></a>' for e in maker[:12])
        posts = "".join(f'<article><a href="{ctx.link("journal/" + p["slug"] + "/")}">{ctx.image(p["image"], "", True, "")}<p class="small">{fmt_date(p["date"])}</p>'
                        f'<h3>{esc(p["title"])}</h3></a></article>' for p in c.posts[:3])
        body = (f'<section class="cave-hero" style="background-image:url(\'{hero_src}\')"><div class="veil"><p class="eyebrow">{esc(c.site["tagline"])}</p>'
                f'<h1>{esc(f["tagline"] or c.site["name"])}</h1>'
                f'{f"<p class=when>Next market <em>Sunday {ordinal(nm.day)} {nm:%B}</em></p>" if nm else ""}</div></section>'
                f'<section class="prose">{intro}<p><a class="gold" href="{ctx.link("visit-us/")}">{esc(f["button"]["text"]) if f.get("button") else "Visit us"}</a></p></section>'
                f'{"".join(chapters)}'
                f'<section class="chapter"><p class="num">&#10022;</p><h2>The makers</h2><div class="makers">{makers}</div>'
                f'<p class="centre"><a class="gold" href="{ctx.link("stallholders/")}">All {len(c.exhibitors)} stallholders</a></p></section>'
                f'<section class="chapter dates"><p class="num">&#10022;</p><h2>Market days</h2><ol>{dates}</ol></section>'
                f'<section class="chapter"><p class="num">&#10022;</p><h2>From the journal</h2><div class="posts">{posts}</div>'
                f'<p class="centre"><a class="gold" href="{ctx.link("journal/")}">Read the journal</a></p></section>')
        return self.layout(ctx, "", body)

    def stallholders(self, ctx):
        c = ctx.c
        secs = "".join(f'<section class="chapter" id="{esc(x["slug"])}"><h2>{esc(x["name"])}</h2><div class="makers">' + "".join(
            f'<a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<span>{esc(e["name"])}</span></a>' for e in c.ex_in(x["id"]))
            + "</div></section>" for x in c.ex_cats if c.ex_in(x["id"]))
        toc = "".join(f'<a href="#{esc(x["slug"])}">{esc(x["name"])}</a>' for x in c.ex_cats if c.ex_in(x["id"]))
        return self.layout(ctx, "Meet the stallholders", f'<section class="title"><p class="eyebrow">Stallholders</p><h1>Meet the makers</h1><nav class="toc">{toc}</nav></section>{secs}')

    def stallholder(self, ctx, e, prev, nxt):
        links = "".join(f'<a class="gold" href="{esc(u)}">{esc(self.link_label(u))}</a>' for u in e["links"])
        body = (f'<article class="portrait"><div class="p-img">{ctx.image(e["image"], "", False, e["name"])}</div><div class="p-txt">'
                f'<p class="eyebrow">{esc(" & ".join(self.cats_of(ctx, e)))}</p><h1>{esc(e["name"])}</h1><div class="txt">{ctx.rewrite_html(e["description_html"])}</div>{links}'
                f'<nav class="pn"><a href="{ctx.link("stallholders/" + prev["slug"] + "/")}">&larr; {esc(prev["name"])}</a><a href="{ctx.link("stallholders/" + nxt["slug"] + "/")}">{esc(nxt["name"])} &rarr;</a></nav>'
                f'</div></article>{page_sourced(ctx, e["source_url"])}')
        return self.layout(ctx, e["name"], body, e["description_text"][:160])

    def journal(self, ctx, n, chunk, total, cat=None):
        c = ctx.c
        title = cat["name"] if cat else "The journal"
        cats = [x for x in sorted(c.post_cats.values(), key=lambda x: -x.get("count", 0)) if x.get("count") and x["slug"] != "uncategorized"]
        toc = f'<a href="{ctx.link("journal/")}">All</a>' + "".join(f'<a href="{ctx.link("journal/category/" + x["slug"] + "/")}">{esc(x["name"])}</a>' for x in cats)
        posts = "".join(f'<article><a href="{ctx.link("journal/" + p["slug"] + "/")}">{ctx.image(p["image"], "", True, "")}<p class="small">{fmt_date(p["date"])}</p>'
                        f'<h3>{esc(p["title"])}</h3></a>{f"<p class=ex>{esc(p["excerpt"])}</p>" if p["excerpt"] else ""}</article>' for p in chunk)
        return self.layout(ctx, title, f'<section class="title"><p class="eyebrow">Journal</p><h1>{esc(title)}</h1><nav class="toc">{toc}</nav></section>'
                           f'<section class="chapter"><div class="posts">{posts}</div>{self.pager(ctx, n, total) if not cat else ""}</section>')

    def post(self, ctx, p):
        body = ctx.rewrite_html(p["body_html"]) if p.get("body_html") is not None else render_blocks(ctx, p.get("blocks"), self)
        return self.layout(ctx, p["title"], f'<article class="reading"><p class="eyebrow">{esc(" & ".join(ctx.c.post_cat_names(p)))}</p><h1>{esc(p["title"])}</h1>'
                           f'<p class="small">{fmt_date(p["date"])}</p>{ctx.image(p["image"], "lead", False, "")}<div class="txt">{body}</div></article>{page_sourced(ctx, p["source_url"])}', p["excerpt"])

    def page(self, ctx, p):
        return self.layout(ctx, p["title"], f'<section class="title"><h1>{esc(p["title"])}</h1></section>{ctx.image(p.get("image"), "band-img", False, "")}'
                           f'<div class="generic">{render_blocks(ctx, p["blocks"], self)}</div>{page_sourced(ctx, p["source_url"])}')
