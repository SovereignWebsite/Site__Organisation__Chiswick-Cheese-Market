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
                f'<p class="small">Design 4, the Cave: the cheese and the makers, shelf by shelf. Words and photographs: Chiswick Cheese Market, chiswickcheesemarket.uk, snapshot {esc(c.snap_label)}. '
                f'Type: Playfair Display and Inter (SIL Open Font License).</p></footer>')

    def shelf(self, ctx, x, es):
        rounds = "".join(f'<li><a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "round", "round", "")}<span class="label">{esc(e["name"])}</span></a></li>' for e in es)
        return (f'<section class="shelf" id="{esc(x["slug"])}"><h2 class="shelf-name">{esc(x["name"])} <small>{len(es)}</small></h2>'
                f'<div class="ledge" tabindex="0" role="region" aria-label="{esc(x["name"])}, {len(es)}"><ul>{rounds}</ul></div></section>')

    def home(self, ctx):
        """A tasting menu: one course per kind of stall, each featuring one maker (the first alphabetically
        not already on another course, filling the smallest kinds first), closing with the newest tasting note. The full shelves are on the stallholders page."""
        c = ctx.c
        f = home_facts(c)
        nm = c.next_market()
        roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
        kinds = [x for x in c.ex_cats if c.ex_in(x["id"])]
        pick, served = {}, set()
        for x in sorted(kinds, key=lambda x: len(c.ex_in(x["id"]))):  # smallest kind first, so every course gets its own maker
            es = c.ex_in(x["id"])
            e = next((e for e in es if e["id"] not in served), es[0])
            pick[x["id"]] = e; served.add(e["id"])
        courses = []
        for x in kinds:
            es = c.ex_in(x["id"])
            e = pick[x["id"]]
            t = (e["description_text"] or "").strip()
            first = t.split(". ")[0] if ". " in t[:200] else t
            first = first if len(first) <= 170 else first[:170].rsplit(" ", 1)[0] + "\u2026"
            first = first if first.endswith((".", "\u2026", "!")) else first + "."
            more = len(es) - 1
            shelf_url = ctx.link("stallholders/") + "#" + x["slug"]
            more_html = f'<p class="more-on"><a href="{esc(shelf_url)}">and {more} more on the shelf</a></p>' if more else ""
            courses.append(f'<li class="course"><p class="course-no">Course {roman[len(courses)]}</p><h2 class="course-name">{esc(x["name"])}</h2>'
                           f'<a class="dish" href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "round", "round", "")}'
                           f'<span><b>{esc(e["name"])}</b><em>{esc(first)}</em></span></a>'
                           f'{more_html}</li>')
        note = next((p for p in c.posts if "Tasting Notes" in c.post_cat_names(p)), None) or next((p for p in c.posts if "Lucy's Cheese of the Month" in c.post_cat_names(p)), None)
        close = (f'<li class="course last"><p class="course-no">To finish</p><h2 class="course-name">Tasting notes</h2>'
                 f'<a class="dish" href="{ctx.link("journal/" + note["slug"] + "/")}">{ctx.image(note["image"], "round", "round", "")}'
                 f'<span><b>{esc(note["title"])}</b><em>{esc(note["excerpt"])}</em></span></a></li>') if note else ""
        dates = "".join(f'<li class="{"past" if d < c.snap_date else ""}{" next" if d == nm else ""}">Sunday {ordinal(d.day)} {d:%B}{"<span class=sr> (past)</span>" if d < c.snap_date else ""}</li>' for d in c.market_dates)
        intro = "".join(f'<div class="txt">{ctx.rewrite_html(h)}</div>' for h in f["intro"][:1])
        body = (f'<section class="menu-wrap"><div class="menu"><p class="eyebrow">Tasting menu</p><h1>{esc(f["tagline"] or c.site["name"])}</h1>'
                f'{f"<p class=when>Served on <em>Sunday {ordinal(nm.day)} {nm:%B %Y}</em></p>" if nm else ""}{intro}'
                f'<ol class="courses">{"".join(courses)}{close}</ol>'
                f'<p class="menu-foot"><a class="gold" href="{ctx.link("stallholders/")}">All {len(c.exhibitors)} makers, shelf by shelf</a> '
                f'<a class="gold" href="{ctx.link("visit-us/")}">Getting here</a></p></div></section>'
                f'<section class="chapter dates"><p class="num">&#10022;</p><h2>Market days</h2><ol>{dates}</ol></section>')
        return self.layout(ctx, "", body)

    def stallholders(self, ctx):
        c = ctx.c
        shelves = "".join(self.shelf(ctx, x, c.ex_in(x["id"])) for x in c.ex_cats if c.ex_in(x["id"]))
        return self.layout(ctx, "Meet the stallholders", f'<section class="title"><p class="eyebrow">Stallholders</p><h1>The shelves</h1></section><section class="cave">{shelves}</section>')

    def stallholder(self, ctx, e, prev, nxt):
        links = "".join(f'<a class="gold" href="{esc(u)}">{esc(self.link_label(u))}</a>' for u in e["links"])
        cat = next((x for x in ctx.c.ex_cats if x["id"] in e["categories"]), None)
        others = [x for x in ctx.c.ex_in(cat["id"]) if x["id"] != e["id"]] if cat else []
        same = self.shelf(ctx, {"slug": "same-shelf", "name": "On the same shelf: " + cat["name"]}, others).replace('<section class="shelf"', '<section class="shelf cave"') if others else ""
        body = (f'<article class="portrait"><div class="p-img">{ctx.image(e["image"], "", False, e["name"])}</div><div class="p-txt">'
                f'<p class="eyebrow">{esc(" & ".join(self.cats_of(ctx, e)))}</p><h1>{esc(e["name"])}</h1><div class="txt">{ctx.rewrite_html(e["description_html"])}</div>{links}'
                f'<nav class="pn"><a href="{ctx.link("stallholders/" + prev["slug"] + "/")}">&larr; {esc(prev["name"])}</a><a href="{ctx.link("stallholders/" + nxt["slug"] + "/")}">{esc(nxt["name"])} &rarr;</a></nav>'
                f'</div></article>{same}{page_sourced(ctx, e["source_url"])}')
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
