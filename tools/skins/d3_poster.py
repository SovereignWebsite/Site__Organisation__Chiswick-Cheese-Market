"""Design 3: Poster. Bold market-poster typography: huge condensed type, a calendar of the year's
market days, stallholders as a big type index. Bebas Neue and Work Sans (SIL OFL)."""
from .base import Skin
from .common import esc, home_facts, fmt_date, ordinal, render_blocks, page_sourced, market_facts, ics, poster_month, pick_size_url


class Poster(Skin):
    folder, name, css, body_class, theme_color = "3", "Poster", "d3.css", "d3", "#111111"

    def header(self, ctx):
        return (f'<header class="bar"><a class="mark" href="{ctx.link("")}">Chiswick<br>Cheese<br>Market</a>'
                f'<nav aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></header>')

    def footer(self, ctx):
        c = ctx.c
        return (f'<footer class="foot"><p class="huge">#Cheesewick</p><p class="idea">Design 3, the Poster Wall: the next market as an event, on the market\'s own posters.</p><p>{esc(c.site.get("copyright") or "")}</p>'
                f'<p class="small">All words and images: Chiswick Cheese Market, chiswickcheesemarket.uk, snapshot {esc(c.snap_label)}. '
                f'Type: Bebas Neue and Work Sans (SIL Open Font License).</p></footer>')

    def extra_files(self, c):
        """A calendar file per upcoming market day, from the site's own dates, hours and address."""
        out = {}
        for d in c.market_dates:
            if d >= c.snap_date:
                body = ics(c, d)
                if body:
                    out[f"calendar/{d:%Y-%m-%d}.ics"] = body
        return out

    def poster_img(self, ctx, p, eager=False, size=900):
        sz = sorted((v for k, v in p["sizes"].items() if v.get("url") and v.get("width") and "woocommerce" not in k and k not in ("full", "thumbnail")), key=lambda v: v["width"])
        pick = next((v for v in sz if v["width"] >= size), sz[-1] if sz else {"url": p["url"], "width": p["width"], "height": p["height"]})
        ym = poster_month(p)
        label = f"{['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][ym[1]]} {ym[0]}" if ym else p["title"]
        small = [v for v in sz if v["width"] <= pick["width"]][-3:]
        srcset = ", ".join(f'{esc(v["url"])} {v["width"]}w' for v in small) if len(small) > 1 else ""
        extra = f' srcset="{srcset}" sizes="(max-width: 700px) 92vw, {min(pick["width"], 640)}px"' if srcset else ""
        return (f'<img src="{esc(pick["url"])}"{extra} width="{pick.get("width") or ""}" height="{pick.get("height") or ""}" alt="Chiswick Cheese Market poster, {esc(label)}"'
                f'{"" if eager else " loading=lazy"}>'), label

    def gif_link(self, p):
        mb = (p.get("bytes") or 0) / 1e6
        return f'<a class="gif" href="{esc(p["url"])}">Animated poster (GIF, {mb:.1f} MB)</a>' if mb else f'<a class="gif" href="{esc(p["url"])}">Animated poster (GIF)</a>'

    def home(self, ctx):
        c = ctx.c
        mf = market_facts(c)
        nm = c.next_market()
        by_month = {}
        for p in c.posters:
            ym = poster_month(p)
            if ym:
                by_month.setdefault(ym, p)  # the first poster for a month
        hero = ""
        first_poster = by_month.get((nm.year, nm.month)) if nm else None
        if nm:
            cal = f'<a class="btn" href="calendar/{nm:%Y-%m-%d}.ics">Add to calendar</a>' if "start" in mf else ""
            side = ""
            if first_poster:
                img, label = self.poster_img(ctx, first_poster, eager=True, size=1000)
                side = f'<figure class="paste hero-poster">{img}<figcaption>{esc(label)} {self.gif_link(first_poster)}</figcaption></figure>'
            hero = (f'<section class="date-hero{" with-poster" if side else ""}"><div class="dh-text"><h1><span class="d">{nm.day}</span><span class="m">{nm:%b}</span></h1>'
                    f'<p class="when">Next market: Sunday {ordinal(nm.day)} {nm:%B %Y}{", " + esc(mf["hours"]) if mf.get("hours") else ""}{", " + esc(mf["place"]) if mf.get("place") else ""}.</p>'
                    f'<p><a class="btn" href="{ctx.link("visit-us/")}">Getting here</a> {cal}</p></div>{side}</section>')
        upcoming = []
        for d in [d for d in c.market_dates if d >= c.snap_date and not (first_poster and d == nm)]:
            p = by_month.get((d.year, d.month))
            if not p:
                continue
            img, label = self.poster_img(ctx, p, eager=True, size=1200)
            upcoming.append(f'<article class="big-poster"><figure class="paste">{img}<figcaption>Sunday {ordinal(d.day)} {d:%B %Y}</figcaption></figure>'
                            f'<p class="acts"><a class="btn" href="calendar/{d:%Y-%m-%d}.ics">Add to calendar</a> {self.gif_link(p)}</p></article>')
        shown = {(d.year, d.month) for d in c.market_dates if d >= c.snap_date}
        this_year = [p for ym, p in sorted(by_month.items()) if ym[0] == c.snap_date.year and ym not in shown]
        older = [p for ym, p in sorted(by_month.items()) if ym[0] < c.snap_date.year]
        months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        missing = [months[d.month] for d in c.market_dates if d.year == c.snap_date.year and (d.year, d.month) not in by_month]
        missing_note = ""
        if missing:
            names = missing[0] if len(missing) == 1 else ", ".join(missing[:-1]) + " and " + missing[-1]
            missing_note = f'<p class="missing">No poster on the market\'s site for {esc(names)} {c.snap_date.year}.</p>'
        wall = ""
        for k, p in enumerate(this_year):
            img, label = self.poster_img(ctx, p, size=760)
            wall += f'<figure class="paste t{k % 4}">{img}<figcaption>{esc(label)} {self.gif_link(p)}</figcaption></figure>'
        strip = ""
        for p in older:
            img, label = self.poster_img(ctx, p, size=400)
            strip += f'<figure>{img}<figcaption>{esc(label)}</figcaption></figure>'
        cal = "".join(f'<li class="{"past" if d < c.snap_date else ("next" if d == nm else "")}"><b>{d:%d}</b><span>{d:%b}</span>{"<span class=sr> (past)</span>" if d < c.snap_date else ""}</li>' for d in c.market_dates)
        cats = "".join(f'<li><a href="{ctx.link("stallholders/")}#{esc(x["slug"])}"><b>{len(c.ex_in(x["id"]))}</b>{esc(x["name"])}</a></li>'
                       for x in c.ex_cats if c.ex_in(x["id"]))
        news = "".join(f'<li><a href="{ctx.link("journal/" + p["slug"] + "/")}"><span>{fmt_date(p["date"], "%d.%m.%y")}</span>{esc(p["title"])}</a></li>' for p in c.posts[:8])
        upcoming_html = f'<section class="band" aria-label="Upcoming">{"".join(upcoming)}</section>' if upcoming else ""
        body = (f'{hero}{upcoming_html}'
                f'{f"<section class=band><h2>{c.snap_date.year} on the wall</h2><div class=wall>{wall}</div>{missing_note}</section>" if wall else ""}'
                f'{f"<section class=band><h2>Past posters</h2><div class=past-strip>{strip}</div></section>" if strip else ""}'
                f'<section class="band"><h2>{c.market_dates[0].year if c.market_dates else ""} market days</h2><ol class="cal">{cal}</ol></section>'
                f'<section class="band black"><h2>Stalls by kind</h2><ol class="cats">{cats}</ol></section>'
                f'<section class="band"><h2>Journal</h2><ol class="news">{news}</ol><p><a class="btn" href="{ctx.link("journal/")}">Read the journal</a></p></section>')
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
