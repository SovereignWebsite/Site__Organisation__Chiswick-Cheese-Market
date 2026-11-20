"""Design 5: The makers. A site built around the stallholders: filter and search the stalls, and on
each maker's page, every journal post that mentions them (found in the data, not written by hand).
Friendly, rounded, app-like on a phone. Space Grotesk and Inter (SIL OFL)."""
import re
from .base import Skin
from .common import esc, home_facts, fmt_date, ordinal, render_blocks, page_sourced

FILTER_JS = """(function(){var q=document.getElementById('q'),cards=[].slice.call(document.querySelectorAll('.mk')),
chips=[].slice.call(document.querySelectorAll('.f-chip')),cat='',out=document.getElementById('count');
function run(){var t=(q.value||'').toLowerCase().trim(),n=0;cards.forEach(function(c){var ok=(!cat||c.dataset.cats.split(' ').indexOf(cat)>=0)&&(!t||c.dataset.text.indexOf(t)>=0);c.hidden=!ok;if(ok)n++;});out.textContent=n+(n===1?' stall':' stalls');}
q.addEventListener('input',run);chips.forEach(function(b){b.addEventListener('click',function(){cat=b.dataset.cat;chips.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});run();});});run();})();"""


class Makers(Skin):
    folder, name, css, body_class, theme_color = "5", "The makers", "d5.css", "d5", "#fff4d6"

    def mentions(self, ctx, e):
        """Journal posts whose text names this stallholder (whole name, case-insensitive)."""
        cache = getattr(self, "_m", None)
        if cache is None:
            cache = self._m = {}
        if e["id"] not in cache:
            pat = re.compile(r"\b" + re.escape(e["name"].lower()) + r"\b")
            cache[e["id"]] = [p for p in ctx.c.posts if pat.search((p["title"] + " " + (p.get("body_text") or "") + " " + p["excerpt"]).lower())]
        return cache[e["id"]]

    def header(self, ctx):
        tabs = [("", "Home", "⌂"), ("stallholders/", "Makers", "★"), ("journal/", "Journal", "✎"), ("visit-us/", "Visit", "⌖")]
        tabbar = "".join(f'<a href="{ctx.link(r)}"{" aria-current=page" if ctx.route == r or (r and ctx.route.startswith(r)) else ""}><span aria-hidden="true">{i}</span>{l}</a>' for r, l, i in tabs)
        return (f'<header class="top"><a class="logo" href="{ctx.link("")}"><span class="dot"></span>Chiswick Cheese Market</a>'
                f'<details class="more"><summary>All pages</summary><nav aria-label="Main"><ul>{self.nav_items(ctx)}</ul></nav></details></header>'
                f'<nav class="tabbar" aria-label="Quick">{tabbar}</nav>')

    def footer(self, ctx):
        c = ctx.c
        return (f'<footer class="foot"><p><b>Chiswick Cheese Market</b> · {esc(c.site["tagline"])}</p><p>{esc(c.site.get("copyright") or "")}</p>'
                f'<p class="small">Everything here comes from the market\'s own site, chiswickcheesemarket.uk (snapshot {esc(c.snap_label)}). '
                f'Type: Space Grotesk and Inter (SIL Open Font License).</p></footer>')

    def card(self, ctx, e):
        cats = " ".join(f"c{i}" for i in e["categories"])
        first = re.split(r"(?<=[.!?])\s", e["description_text"].strip(), maxsplit=1)[0] if e["description_text"] else ""
        tags = "".join(f'<span class="tag t{i % 6}">{esc(ctx.c.ex_cat[i]["name"])}</span>' for i in e["categories"] if i in ctx.c.ex_cat)
        n = len(self.mentions(ctx, e))
        return (f'<li class="mk" data-cats="{cats}" data-text="{esc((e["name"] + " " + e["description_text"]).lower())}">'
                f'<a href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<div class="mk-b"><div class="tags">{tags}</div>'
                f'<h3>{esc(e["name"])}</h3><p>{esc(first[:150])}{"…" if len(first) > 150 else ""}</p>'
                f'{f"<p class=mentions>In the journal: {n} post{"s" if n != 1 else ""}</p>" if n else ""}</div></a></li>')

    def finder(self, ctx, title, tag="h2"):
        c = ctx.c
        chips = '<button type="button" class="f-chip" data-cat="" aria-pressed="true">All</button>' + "".join(
            f'<button type="button" class="f-chip t{x["id"] % 6}" data-cat="c{x["id"]}" aria-pressed="false">{esc(x["name"])} <small>{len(c.ex_in(x["id"]))}</small></button>'
            for x in c.ex_cats if c.ex_in(x["id"]))
        cards = "".join(self.card(ctx, e) for e in c.exhibitors)
        return (f'<section class="finder"><div class="finder-head"><{tag}>{title}</{tag}><p id="count" aria-live="polite"></p></div>'
                f'<label class="search"><span>Search the stalls</span><input id="q" type="search" placeholder="Try: goat, bread, Alpine, honey" autocomplete="off"></label>'
                f'<div class="chips" role="group" aria-label="Kind of stall">{chips}</div><ul class="cards">{cards}</ul></section><script>{FILTER_JS}</script>')

    def home(self, ctx):
        c = ctx.c
        f = home_facts(c)
        nm = c.next_market()
        kinds = len([x for x in c.ex_cats if c.ex_in(x["id"])])
        newest = sorted(c.exhibitors, key=lambda e: e["date"], reverse=True)[:4]
        new_html = "".join(f'<a class="new" href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<span>{esc(e["name"])}</span></a>' for e in newest)
        intro = "".join(f'<div class="txt">{ctx.rewrite_html(h)}</div>' for h in f["intro"][:1])
        body = (f'<section class="hello"><div><p class="pill-next">{f"Next market · Sunday {ordinal(nm.day)} {nm:%B}" if nm else ""}</p>'
                f'<h1>Meet the {len(c.exhibitors)} stallholders of Chiswick Cheese Market</h1>{intro}'
                f'<p class="stats"><b>{len(c.exhibitors)}</b> stalls <b>{kinds}</b> kinds <b>{len(c.posts)}</b> journal posts</p></div>'
                f'<div class="new-wrap"><p class="lbl">Most recently added to the site</p><div class="news">{new_html}</div></div></section>'
                f'{self.finder(ctx, "Find a stall")}'
                f'<section class="gap"><h2>What the data does not have yet</h2><p>The market\'s site keeps a description and a photograph for each stallholder, '
                f'but no link to their own website or social accounts. One extra field in WordPress, filled in once per stall, would let every design here '
                f'send visitors straight to the makers, and later show their own news beside the market\'s.</p></section>')
        return self.layout(ctx, "", body)

    def stallholders(self, ctx):
        return self.layout(ctx, "Meet the stallholders", f'<div class="pad">{self.finder(ctx, "All the stallholders", "h1")}</div>')

    def stallholder(self, ctx, e, prev, nxt):
        c = ctx.c
        tags = "".join(f'<span class="tag t{i % 6}">{esc(c.ex_cat[i]["name"])}</span>' for i in e["categories"] if i in c.ex_cat)
        ms = self.mentions(ctx, e)
        mhtml = "".join(f'<li><a href="{ctx.link("journal/" + p["slug"] + "/")}">{ctx.image(p["image"], "", True, "")}<span><b>{esc(p["title"])}</b>'
                        f'<small>{fmt_date(p["date"])}</small></span></a></li>' for p in ms)
        same = [x for x in c.exhibitors if x["id"] != e["id"] and set(x["categories"]) & set(e["categories"])][:6]
        shtml = "".join(f'<a class="new" href="{ctx.link("stallholders/" + x["slug"] + "/")}">{ctx.image(x["image"], "", True, "")}<span>{esc(x["name"])}</span></a>' for x in same)
        own = "".join(f'<a class="cta" href="{esc(u)}">Visit {esc(self.link_label(u))}</a>' for u in e["links"])
        body = (f'<article class="maker"><div class="m-img">{ctx.image(e["image"], "", False, e["name"])}</div><div class="m-card"><div class="tags">{tags}</div>'
                f'<h1>{esc(e["name"])}</h1><div class="txt">{ctx.rewrite_html(e["description_html"])}</div>'
                f'{own or "<p class=nolink>No website or social link for this stall in the market&rsquo;s data yet.</p>"}'
                f'<a class="cta ghost" href="{esc(e["source_url"])}">Their page on the official site</a></div></article>'
                f'{f"<section class=pad><h2>In the journal</h2><ul class=ments>{mhtml}</ul></section>" if ms else ""}'
                f'{f"<section class=pad><h2>Similar stalls</h2><div class=news>{shtml}</div></section>" if same else ""}'
                f'<nav class="pn pad"><a href="{ctx.link("stallholders/" + prev["slug"] + "/")}">← {esc(prev["name"])}</a><a href="{ctx.link("stallholders/" + nxt["slug"] + "/")}">{esc(nxt["name"])} →</a></nav>')
        return self.layout(ctx, e["name"], body, e["description_text"][:160])

    def journal(self, ctx, n, chunk, total, cat=None):
        c = ctx.c
        title = cat["name"] if cat else "Journal"
        cats = [x for x in sorted(c.post_cats.values(), key=lambda x: -x.get("count", 0)) if x.get("count") and x["slug"] != "uncategorized"]
        toc = f'<a class="f-chip" href="{ctx.link("journal/")}"{"" if cat else " aria-current=page"}>All</a>' + "".join(
            f'<a class="f-chip" href="{ctx.link("journal/category/" + x["slug"] + "/")}"{" aria-current=page" if cat and cat["id"] == x["id"] else ""}>{esc(x["name"])}</a>' for x in cats)
        items = "".join(f'<li class="mk"><a href="{ctx.link("journal/" + p["slug"] + "/")}">{ctx.image(p["image"], "", True, "")}<div class="mk-b"><div class="tags">'
                        + "".join(f'<span class="tag t{i % 6}">{esc(c.post_cats[i]["name"])}</span>' for i in p["categories"] if i in c.post_cats and c.post_cats[i]["slug"] != "uncategorized")
                        + f'</div><h3>{esc(p["title"])}</h3><p>{fmt_date(p["date"])}</p></div></a></li>' for p in chunk)
        return self.layout(ctx, title, f'<div class="pad"><h1>{esc(title)}</h1><div class="chips">{toc}</div><ul class="cards">{items}</ul>{self.pager(ctx, n, total) if not cat else ""}</div>')

    def post(self, ctx, p):
        c = ctx.c
        body = ctx.rewrite_html(p["body_html"]) if p.get("body_html") is not None else render_blocks(ctx, p.get("blocks"), self)
        named = [e for e in c.exhibitors if p in self.mentions(ctx, e)]
        nhtml = "".join(f'<a class="new" href="{ctx.link("stallholders/" + e["slug"] + "/")}">{ctx.image(e["image"], "", True, "")}<span>{esc(e["name"])}</span></a>' for e in named)
        return self.layout(ctx, p["title"], f'<article class="read pad"><p class="small">{fmt_date(p["date"])} · {esc(", ".join(c.post_cat_names(p)))}</p><h1>{esc(p["title"])}</h1>'
                           f'{ctx.image(p["image"], "lead", False, "")}<div class="txt">{body}</div></article>'
                           f'{f"<section class=pad><h2>Stallholders in this post</h2><div class=news>{nhtml}</div></section>" if named else ""}{page_sourced(ctx, p["source_url"])}', p["excerpt"])

    def page(self, ctx, p):
        return self.layout(ctx, p["title"], f'<div class="pad generic"><h1>{esc(p["title"])}</h1>{ctx.image(p.get("image"), "lead", False, "")}'
                           f'{render_blocks(ctx, p["blocks"], self)}</div>{page_sourced(ctx, p["source_url"])}')
