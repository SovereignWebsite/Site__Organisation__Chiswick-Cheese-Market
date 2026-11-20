"""Design 3: Poster. Bold market-poster typography: huge condensed type, a calendar of the year's
market days, stallholders as a big type index. Bebas Neue and Work Sans (SIL OFL)."""
from .base import Skin
from .common import esc, home_facts, fmt_date, ordinal, render_blocks, page_sourced


class Poster(Skin):
    folder, name, css, body_class, theme_color = "3", "Poster", "d3.css", "d3", "#111111"

    def header(self, ctx):
        return (f'<header class="bar"><a class="mark" href="{ctx.link("")}">Chiswick<br>Cheese<br>Market</a>'
                f'<nav aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></header>')

    def footer(self, ctx):
        c = ctx.c
        return (f'<footer class="foot"><p class="huge">#Cheesewick</p><p>{esc(c.site.get("copyright") or "")}</p>'
                f'<p class="small">All words and images: Chiswick Cheese Market, chiswickcheesemarket.uk, snapshot {esc(c.snap_label)}. '
                f'Type: Bebas Neue and Work Sans (SIL Open Font License).</p></footer>')

    def home(self, ctx):
        c = ctx.c
        f = home_facts(c)
        nm = c.next_market()
        hero_img = ctx.image(f.get("hero_side") or (c.posts[0]["image"]), "poster-img", False, "")
        big_date = (f'<p class="next"><span>Next market</span><b>{nm:%d}</b><i>{nm:%b}</i><span>Sunday {ordinal(nm.day)} {nm:%B %Y}</span></p>' if nm else "")
        intro = "".join(f'<div class="txt">{ctx.rewrite_html(h)}</div>' for h in f["intro"])
        cal = "".join(f'<li class="{"past" if d < c.snap_date else ("next" if d == nm else "")}"><b>{d:%d}</b><span>{d:%b}</span></li>' for d in c.market_dates)
        cats = "".join(f'<li><a href="{ctx.link("stallholders/")}#{esc(x["slug"])}"><b>{len(c.ex_in(x["id"]))}</b>{esc(x["name"])}</a></li>'
                       for x in c.ex_cats if c.ex_in(x["id"]))
        names = " ".join(f'<a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{esc(e["name"])}</a><span aria-hidden="true">/</span>' for e in c.exhibitors)
        feats = "".join(f'<section class="band"><h2>{esc(g["title"])}</h2><ol class="feats">' + "".join(
            f'<li>{ctx.image(i["image"], "", True, "")}<b>{esc(i["title"])}</b></li>' for i in g["items"]) + "</ol></section>" for g in f["features"])
        news = "".join(f'<li><a href="{ctx.link("journal/" + p["slug"] + "/")}"><span>{fmt_date(p["date"], "%d.%m.%y")}</span>{esc(p["title"])}</a></li>' for p in c.posts[:8])
        words = "".join(f'<span class="hl">{esc(w)}</span> ' if w.lower() == "cheese" else f"<span>{esc(w)}</span> " for w in c.site["tagline"].split())
        body = (f'<section class="hero"><h1>{words}</h1>'
                f'<div class="hero-side">{hero_img}{big_date}</div></section>'
                f'<section class="band yellow"><div class="two"><h2>{esc(f["tagline"] or "")}</h2><div>{intro}'
                f'<p><a class="btn" href="{ctx.link("visit-us/")}">{esc(f["button"]["text"]) if f.get("button") else "Visit us"}</a></p></div></div></section>'
                f'<section class="band"><h2>{c.market_dates[0].year if c.market_dates else ""} market days</h2><ol class="cal">{cal}</ol></section>'
                f'<section class="band black"><h2>Stalls by kind</h2><ol class="cats">{cats}</ol><p class="names">{names}</p></section>'
                f'{feats}<section class="band"><h2>Journal</h2><ol class="news">{news}</ol><p><a class="btn" href="{ctx.link("journal/")}">Read the journal</a></p></section>')
        return self.layout(ctx, "", body)

    def stallholders(self, ctx):
        c = ctx.c
        out = []
        for x in c.ex_cats:
            es = c.ex_in(x["id"])
            if not es:
                continue
            rows = "".join(f'<li><a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<b>{esc(e["name"])}</b></a></li>' for e in es)
            out.append(f'<section class="band" id="{esc(x["slug"])}"><h2><small>{len(es):02d}</small> {esc(x["name"])}</h2><ol class="biglist">{rows}</ol></section>')
        return self.layout(ctx, "Meet the stallholders", f'<section class="hero short"><h1>Meet the <span class="hl">stallholders</span></h1></section>{"".join(out)}')

    def stallholder(self, ctx, e, prev, nxt):
        links = "".join(f'<a class="btn" href="{esc(u)}">{esc(self.link_label(u))}</a>' for u in e["links"])
        body = (f'<article class="exp"><div class="exp-img">{ctx.image(e["image"], "", False, e["name"])}</div><div class="exp-txt">'
                f'<p class="tag">{esc(" + ".join(self.cats_of(ctx, e)))}</p><h1>{esc(e["name"])}</h1><div class="txt">{ctx.rewrite_html(e["description_html"])}</div>{links}</div></article>'
                f'<nav class="pn"><a href="{ctx.link("stallholders/" + prev["slug"] + "/")}">← {esc(prev["name"])}</a><a href="{ctx.link("stallholders/" + nxt["slug"] + "/")}">{esc(nxt["name"])} →</a></nav>'
                f'{page_sourced(ctx, e["source_url"])}')
        return self.layout(ctx, e["name"], body, e["description_text"][:160])

    def journal(self, ctx, n, chunk, total, cat=None):
        c = ctx.c
        title = cat["name"] if cat else "Journal"
        cats = [x for x in sorted(c.post_cats.values(), key=lambda x: -x.get("count", 0)) if x.get("count") and x["slug"] != "uncategorized"]
        toc = f'<a href="{ctx.link("journal/")}">All</a>' + "".join(f'<a href="{ctx.link("journal/category/" + x["slug"] + "/")}">{esc(x["name"])}</a>' for x in cats)
        items = "".join(f'<li><a href="{ctx.link("journal/" + p["slug"] + "/")}">{ctx.image(p["image"], "", True, "")}<span class="d">{fmt_date(p["date"], "%d.%m.%y")}</span>'
                        f'<b>{esc(p["title"])}</b></a></li>' for p in chunk)
        return self.layout(ctx, title, f'<section class="hero short"><h1>{esc(title)}</h1></section><nav class="toc">{toc}</nav>'
                           f'<section class="band"><ol class="jlist">{items}</ol>{self.pager(ctx, n, total) if not cat else ""}</section>')

    def post(self, ctx, p):
        body = ctx.rewrite_html(p["body_html"]) if p.get("body_html") is not None else render_blocks(ctx, p.get("blocks"), self)
        return self.layout(ctx, p["title"], f'<article class="art"><p class="tag">{esc(" + ".join(ctx.c.post_cat_names(p)))} / {fmt_date(p["date"])}</p><h1>{esc(p["title"])}</h1>'
                           f'{ctx.image(p["image"], "art-img", False, "")}<div class="txt">{body}</div></article>{page_sourced(ctx, p["source_url"])}', p["excerpt"])

    def page(self, ctx, p):
        return self.layout(ctx, p["title"], f'<section class="hero short"><h1>{esc(p["title"])}</h1></section>'
                           f'<div class="generic">{render_blocks(ctx, p["blocks"], self)}</div>{page_sourced(ctx, p["source_url"])}')
