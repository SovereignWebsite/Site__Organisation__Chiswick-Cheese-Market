"""Design 2: Journal. An editorial, magazine-style site: a masthead, a lead story, the market's
words set like a newspaper, the stallholders as an index. Fraunces and Inter (SIL OFL)."""
from .base import Skin
from .common import esc, home_facts, fmt_date, ordinal, render_blocks, page_sourced, market_facts, home_ticker


class Journal(Skin):
    folder, name, css, body_class, theme_color = "2", "Journal", "d2.css", "d2", "#f5efe3"

    def header(self, ctx):
        c = ctx.c
        nm = c.next_market()
        when = f"Sunday {ordinal(nm.day)} {nm:%B %Y}: the next market" if nm else ""
        title = f'<a class="title" href="{ctx.link("")}">{esc(c.site["name"])}</a>'
        if ctx.route == "":
            title = f'<h1 class="title-h">{title}</h1>'
        return (f'<header class="mast"><p class="dateline"><span>{esc(c.site["tagline"])}</span><span>{esc(when)}</span></p>{title}'
                f'<nav class="sections" aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></header>')

    def footer(self, ctx):
        c = ctx.c
        return (f'<footer class="colophon"><p class="title">{esc(c.site["name"])}</p><p>Design 2, the Market Paper: the market\'s news, set as a broadsheet.</p><p>{esc(c.site.get("copyright") or "")}</p>'
                f'<p class="credit">Every word and picture: Chiswick Cheese Market, from chiswickcheesemarket.uk, snapshot {esc(c.snap_label)}. '
                f'Set in Fraunces and Inter (SIL Open Font License).</p></footer>')

    def home(self, ctx):
        c = ctx.c
        f = home_facts(c)
        mf = market_facts(c)
        nm = c.next_market()
        lead, rest = c.posts[0], c.posts[1:7]
        lead_html = (f'<article class="lead"><a href="{ctx.link("journal/" + lead["slug"] + "/")}">{ctx.image(lead["image"], "lead-img", False, "")}'
                     f'<p class="kicker">{esc(" / ".join(c.post_cat_names(lead)))}</p><h2>{esc(lead["title"])}</h2></a>'
                     f'<p class="standfirst">{esc(lead["excerpt"])}</p><p class="byline">{fmt_date(lead["date"])}</p></article>')
        side = "".join(f'<article class="brief"><a href="{ctx.link("journal/" + p["slug"] + "/")}"><p class="kicker">{esc(" / ".join(c.post_cat_names(p)[:2]))}</p>'
                       f'<h3>{esc(p["title"])}</h3></a><p class="byline">{fmt_date(p["date"])}</p></article>' for p in rest)
        hours_html = f"<p><b>{esc(mf['hours'])}</b></p>" if mf.get("hours") else ""
        place_html = f"<p>{esc(mf['place'])}</p>" if mf.get("place") else ""
        sunday = (f'<aside class="sunday" aria-label="This Sunday"><p class="rule">{"This Sunday" if nm and (nm - c.snap_date).days < 7 else "The next market"}</p>'
                  f'<p class="big-date">{nm.day}<span>{nm:%B}</span></p><p class="day">Sunday {nm.year}</p>'
                  f'{hours_html}{place_html}'
                  f'<p><a class="more" href="{ctx.link("visit-us/")}">Getting here &rarr;</a></p></aside>') if nm else ""
        intro = "".join(f'<div class="txt">{ctx.rewrite_html(h)}</div>' for h in f["intro"])
        dates = "".join(f'<li class="{"past" if d < c.snap_date else ""}{" next" if d == nm else ""}"><span>Sunday</span> <b>{ordinal(d.day)} {d:%B}</b>{"<span class=sr> (past)</span>" if d < c.snap_date else ""}</li>' for d in c.market_dates)
        feats = "".join(f'<section class="feature"><h2 class="rule">{esc(g["title"])}</h2><div class="feat-grid">' + "".join(
            f'<figure>{ctx.image(i["image"], "", True, "")}<figcaption>{esc(i["title"])}</figcaption></figure>' for i in g["items"]) + "</div></section>"
            for g in f["features"])
        classifieds = "".join(f'<section class="cl"><h3>{esc(x["name"])}</h3><ul>' + "".join(
            f'<li><a href="{ctx.link("stallholders/" + e["slug"] + "/")}"><b>{esc(e["name"])}</b></a> {esc(e["description_text"][:90].rsplit(" ", 1)[0])}&hellip;</li>'
            for e in c.ex_in(x["id"])) + "</ul></section>" for x in c.ex_cats if c.ex_in(x["id"]))
        body = (f'{home_ticker(c)}<div class="front">{sunday}<div class="col-main">{lead_html}</div><aside class="col-side" aria-label="Latest"><h2 class="rule">Latest</h2>{side}'
                f'<p><a class="more" href="{ctx.link("journal/")}">The whole journal &rarr;</a></p></aside></div>'
                f'<section class="about-market"><h2 class="big">{esc(f["tagline"] or "")}</h2><div class="cols dropcap">{intro}</div></section>'
                f'<section class="listings"><h2 class="rule">Listings: market days {c.market_dates[0].year if c.market_dates else ""}</h2><ol class="list-box">{dates}</ol></section>'
                f'{feats}<section class="index"><h2 class="rule">Classifieds: the stallholders</h2><div class="classifieds">{classifieds}</div></section>')
        return self.layout(ctx, "", body)

    def stallholders(self, ctx):
        c = ctx.c
        groups = "".join(f'<section id="{esc(cat["slug"])}"><h2 class="rule">{esc(cat["name"])} <small>{len(c.ex_in(cat["id"]))}</small></h2><div class="ex-rows">' + "".join(
            f'<a class="ex-row" href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<span><b>{esc(e["name"])}</b>'
            f'<em>{esc(e["description_text"][:140])}{"&hellip;" if len(e["description_text"]) > 140 else ""}</em></span></a>' for e in c.ex_in(cat["id"]))
            + "</div></section>" for cat in c.ex_cats if c.ex_in(cat["id"]))
        toc = "".join(f'<a href="#{esc(cat["slug"])}">{esc(cat["name"])}</a>' for cat in c.ex_cats if c.ex_in(cat["id"]))
        return self.layout(ctx, "Meet the stallholders", f'<div class="page"><h1>Meet the stallholders</h1><nav class="toc">{toc}</nav>{groups}</div>')

    def stallholder(self, ctx, e, prev, nxt):
        links = "".join(f'<a href="{esc(u)}">{esc(self.link_label(u))}</a>' for u in e["links"])
        body = (f'<article class="story"><p class="kicker">{esc(" / ".join(self.cats_of(ctx, e)))}</p><h1>{esc(e["name"])}</h1>'
                f'{ctx.image(e["image"], "story-img", False, e["name"])}<div class="txt dropcap">{ctx.rewrite_html(e["description_html"])}</div>'
                f'<p class="links">{links}</p>'
                f'<nav class="pn"><a href="{ctx.link("stallholders/" + prev["slug"] + "/")}">&larr; {esc(prev["name"])}</a>'
                f'<a href="{ctx.link("stallholders/" + nxt["slug"] + "/")}">{esc(nxt["name"])} &rarr;</a></nav></article>{page_sourced(ctx, e["source_url"])}')
        return self.layout(ctx, e["name"], body, e["description_text"][:160])

    def journal(self, ctx, n, chunk, total, cat=None):
        c = ctx.c
        title = cat["name"] if cat else "The journal"
        cats = [x for x in sorted(c.post_cats.values(), key=lambda x: -x.get("count", 0)) if x.get("count") and x["slug"] != "uncategorized"]
        toc = f'<a href="{ctx.link("journal/")}">All</a>' + "".join(f'<a href="{ctx.link("journal/category/" + x["slug"] + "/")}">{esc(x["name"])}</a>' for x in cats)
        items = "".join(f'<article class="row"><a href="{ctx.link("journal/" + p["slug"] + "/")}">{ctx.image(p["image"], "", True, "")}'
                        f'<div><p class="kicker">{esc(" / ".join(c.post_cat_names(p)))}</p><h2>{esc(p["title"])}</h2><p class="standfirst">{esc(p["excerpt"])}</p>'
                        f'<p class="byline">{fmt_date(p["date"])}</p></div></a></article>' for p in chunk)
        return self.layout(ctx, title, f'<div class="page"><h1>{esc(title)}</h1><nav class="toc">{toc}</nav>{items}{self.pager(ctx, n, total) if not cat else ""}</div>')

    def post(self, ctx, p):
        body = ctx.rewrite_html(p["body_html"]) if p.get("body_html") is not None else render_blocks(ctx, p.get("blocks"), self)
        return self.layout(ctx, p["title"], f'<article class="story"><p class="kicker">{esc(" / ".join(ctx.c.post_cat_names(p)))}</p><h1>{esc(p["title"])}</h1>'
                           f'<p class="standfirst">{esc(p["excerpt"])}</p><p class="byline">{fmt_date(p["date"])}</p>{ctx.image(p["image"], "story-img", False, "")}'
                           f'<div class="txt dropcap">{body}</div></article>{page_sourced(ctx, p["source_url"])}', p["excerpt"])

    def page(self, ctx, p):
        return self.layout(ctx, p["title"], f'<div class="page generic"><h1>{esc(p["title"])}</h1>{ctx.image(p.get("image"), "story-img", False, "")}'
                           f'{render_blocks(ctx, p["blocks"], self)}</div>{page_sourced(ctx, p["source_url"])}')
