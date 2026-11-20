"""Design 6: The data. The JSON behind every design, documented and downloadable, a query tool that
runs in the page (filter by category, search text), and charts drawn as inline SVG at build time.
No third-party scripts. Fonts: IBM Plex Mono and Inter (SIL OFL)."""
import collections, datetime, json, os
from .common import esc, Ctx, demo_strip, fmt_date, OFFICIAL, og_tags

QUERY_JS = r"""
(function(){var D=window.CCM;if(!D)return;
var ds=document.getElementById('ds'),cat=document.getElementById('cat'),q=document.getElementById('qq'),
tb=document.getElementById('res'),cnt=document.getElementById('cnt'),api=document.getElementById('api'),js=document.getElementById('json');
function cats(){var list=ds.value==='exhibitors'?D.exhibitor_categories:D.post_categories;
cat.innerHTML='<option value="">Any category</option>'+list.map(function(c){return '<option value="'+c.id+'">'+c.name+' ('+c.count+')</option>'}).join('');}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function run(){var items=D[ds.value],c=cat.value?+cat.value:null,t=q.value.toLowerCase().trim();
var r=items.filter(function(x){return (!c||x.categories.indexOf(c)>=0)&&(!t||(x.name+' '+x.text).toLowerCase().indexOf(t)>=0)});
cnt.textContent=r.length+' of '+items.length;setTimeout(function(){[].forEach.call(tb.querySelectorAll('a[data-href]'),function(a){a.setAttribute('href',a.getAttribute('data-href'))})});
tb.innerHTML=r.map(function(x){return '<tr><td>'+x.id+'</td><td><a data-href="'+x.page+'">'+esc(x.name)+'</a></td><td>'+esc(x.cats)+'</td><td>'+(x.date||'')+'</td></tr>'}).join('')||'<tr><td colspan=4>Nothing matches.</td></tr>';
var base='https://www.chiswickcheesemarket.uk/wp-json/wp/v2/'+(ds.value==='exhibitors'?'portfolio':'posts');
var p=[];if(c)p.push((ds.value==='exhibitors'?'portfolio_category':'categories')+'='+c);if(t)p.push('search='+encodeURIComponent(t));
api.textContent=base+(p.length?'?'+p.join('&'):'');
js.textContent=JSON.stringify(r.slice(0,3).map(function(x){return {id:x.id,name:x.name,categories:x.categories,date:x.date}}),null,1)+(r.length>3?'\n... '+(r.length-3)+' more':'');}
ds.addEventListener('change',function(){cats();run()});cat.addEventListener('change',run);q.addEventListener('input',run);cats();run();})();
"""


def hbar(rows, unit, label):
    """Horizontal bar chart, one series. rows: [(name, value)]."""
    if not rows:
        return ""
    mx = max(v for _, v in rows) or 1
    W, lw, rh, bh = 640, 230, 34, 20
    H = rh * len(rows) + 8
    out = [f'<svg class="viz" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">']
    for i, (n, v) in enumerate(rows):
        y = 4 + i * rh
        w = 0 if v == 0 else max(4, (W - lw - 50) * v / mx)
        r = min(4, w)
        path = f"M{lw},{y + 7} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{bh - 2 * r} a{r},{r} 0 0 1 -{r},{r} h-{w - r:.1f} z" if w else ""
        out.append(f'<g class="row"><title>{esc(n)}: {v} {unit}</title><rect class="hit" x="0" y="{y}" width="{W}" height="{rh}"></rect>'
                   f'<text class="lab" x="{lw - 10}" y="{y + 21}" text-anchor="end">{esc(n)}</text>'
                   f'{f"<path class=bar d={chr(34)}{path}{chr(34)}></path>" if path else ""}'
                   f'<text class="val" x="{lw + w + 8:.1f}" y="{y + 21}">{v}</text></g>')
    out.append(f'<line class="base" x1="{lw}" y1="0" x2="{lw}" y2="{H}"></line></svg>')
    return "".join(out)


def columns(series, label, ticks_every=6):
    """Column timeline, one series. series: [(datetime.date month, value)]."""
    if not series:
        return ""
    mx = max(v for _, v in series) or 1
    W, H, pl, pb, pt = 720, 240, 34, 30, 12
    n = len(series)
    slot = (W - pl - 8) / n
    bw = min(16, slot - 2)
    out = [f'<svg class="viz" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">']
    step = 5 if mx > 10 else 2 if mx > 4 else 1
    for g in range(0, mx + 1, step):
        y = H - pb - (H - pb - pt) * g / mx
        out.append(f'<line class="grid" x1="{pl}" y1="{y:.1f}" x2="{W}" y2="{y:.1f}"></line><text class="tick" x="{pl - 6}" y="{y + 4:.1f}" text-anchor="end">{g}</text>')
    for i, (m, v) in enumerate(series):
        x = pl + i * slot + (slot - bw) / 2
        h = (H - pb - pt) * v / mx
        y = H - pb - h
        r = min(4, h, bw / 2)
        path = f"M{x:.1f},{H - pb} v-{h - r:.1f} a{r},{r} 0 0 1 {r},-{r} h{bw - 2 * r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - r:.1f} z" if v else ""
        out.append(f'<g class="row"><title>{m:%B %Y}: {v} post{"s" if v != 1 else ""}</title><rect class="hit" x="{pl + i * slot:.1f}" y="{pt}" width="{slot:.1f}" height="{H - pb - pt}"></rect>'
                   f'{f"<path class=bar d={chr(34)}{path}{chr(34)}></path>" if path else ""}</g>')
        if m.month == 1 or i == 0:
            out.append(f'<text class="tick" x="{x + bw / 2:.1f}" y="{H - 10}" text-anchor="middle">{m:%b %Y}</text>')
    out.append(f'<line class="base" x1="{pl}" y1="{H - pb}" x2="{W}" y2="{H - pb}"></line></svg>')
    return "".join(out)


def table(rows, head):
    return ("<details class='tbl'><summary>Show as a table</summary><table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) +
            "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></details>")


def months(posts, end):
    cnt = collections.Counter(datetime.date.fromisoformat(p["date"][:10]).replace(day=1) for p in posts)
    if not cnt:
        return []
    m, out = min(cnt), []
    while m <= end:
        out.append((m, cnt.get(m, 0)))
        m = (m.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return out


class DataSkin:
    folder, name = "6", "The data"

    def layout(self, ctx, title, body):
        return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>{esc(title)} | Chiswick Cheese Market data</title>
{og_tags(f"designs/6/{ctx.route}", title + " | Chiswick Cheese Market data", "The market's content as open data: files, a query tool and charts.")}
<link rel="stylesheet" href="{ctx.asset('css/demo.css')}"><link rel="stylesheet" href="{ctx.asset('css/d6.css')}"></head>
<body><a class="skip" href="#main">Skip to content</a>{demo_strip(ctx)}
<header class="dh"><a class="brand" href="{ctx.link('')}"><span>{{ }}</span> Chiswick Cheese Market <em>data</em></a>
<nav><a href="{ctx.link('')}">Explore</a><a href="{ctx.link('files/')}">Files and fields</a><a href="{ctx.up()}admin/index.html">Admin: the WordPress API</a></nav></header>
<main id="main">{body}</main>
<footer class="df"><p>All content: Chiswick Cheese Market, read-only from <a href="{OFFICIAL}/wp-json/">their public WordPress API</a>, snapshot {esc(ctx.c.snap_label)}.
Charts are inline SVG made when the site is built; the query tool is 40 lines of plain JavaScript; no third-party scripts, no cookies, no tracking.</p></footer>
</body></html>"""

    def data_js(self, c, ctx):
        """window.CCM: a compact copy of the data, so the query tool works from a file with no fetch at all."""
        ex = [{"id": e["id"], "name": e["name"], "categories": e["categories"], "cats": ", ".join(c.ex_cat[i]["name"] for i in e["categories"] if i in c.ex_cat),
               "text": e["description_text"], "date": e["date"][:10], "page": ctx.link("stallholders/" + e["slug"] + "/", "1"),
               "vp": f"designs/1/stallholders/{e['slug']}/index.html"} for e in c.exhibitors]
        po = [{"id": p["id"], "name": p["title"], "categories": p["categories"], "cats": ", ".join(c.post_cat_names(p)),
               "text": p["excerpt"] + " " + (p.get("body_text") or ""), "date": p["date"][:10], "page": ctx.link("journal/" + p["slug"] + "/", "1"),
               "vp": f"designs/1/journal/{p['slug']}/index.html"} for p in c.posts]
        d = {"exhibitors": ex, "posts": po,
             "exhibitor_categories": [{"id": x["id"], "name": x["name"], "count": x.get("count", 0)} for x in c.ex_cats],
             "post_categories": [{"id": x["id"], "name": x["name"], "count": x.get("count", 0)} for x in sorted(c.post_cats.values(), key=lambda x: -x.get("count", 0)) if x.get("count")]}
        return "window.CCM=" + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";"

    def build(self, c, out, write):
        ctx = Ctx(c, "6", "")
        write(out, "designs/6/ccm-data.js", self.data_js(c, ctx))
        # numbers
        kinds = [(x["name"], len(c.ex_in(x["id"]))) for x in c.ex_cats]
        pc = sorted(((x["name"], sum(1 for p in c.posts if x["id"] in p["categories"])) for x in c.post_cats.values() if x["slug"] != "uncategorized"), key=lambda r: -r[1])
        pc = [r for r in pc if r[1]]
        ms = months(c.posts, c.snap_date.replace(day=1))
        first = min(p["date"] for p in c.posts) if c.posts else ""
        nm = c.next_market()
        tiles = "".join(f'<div class="tile"><b>{v}</b><span>{esc(k)}</span></div>' for k, v in (
            ("stallholders", len(c.exhibitors)), ("journal posts", len(c.posts)), ("public pages", len(c.pages)), ("images", len(c.media)),
            ("market days in " + str(c.market_dates[0].year) if c.market_dates else "market days", len(c.market_dates))))
        body = f"""
<section class="intro"><h1>The market's content, as open data</h1>
<p>Everything in all six designs comes from these files. They were read from Chiswick Cheese Market's own WordPress site through its public API
(GET requests only) on {esc(c.snap_label)}, cleaned, and saved as plain JSON. A nightly job can refresh them; every change is then a commit you can see and undo.</p>
<div class="tiles">{tiles}</div>
{f'<p class="next">Next market in the data: <b>Sunday {nm.day} {nm:%B %Y}</b> (from the market dates on the home page).</p>' if nm else ''}</section>

<section class="card"><h2>Ask the data</h2><p class="sub">Filter by category and search the text. This runs in your browser over the snapshot; the line under it is the same question asked of the live WordPress API.</p>
<div class="q"><label>Dataset<select id="ds"><option value="exhibitors">Stallholders</option><option value="posts">Journal posts</option></select></label>
<label>Category<select id="cat"></select></label><label class="grow">Text<input id="qq" type="search" placeholder="for example: goat, Comté, honey, award"></label></div>
<p class="cnt"><b id="cnt"></b> match</p>
<p class="apiq">Live API equivalent: <code id="api"></code></p>
<div class="twocol"><div class="scroll" tabindex="0" role="region" aria-label="Results"><table class="res"><thead><tr><th>id</th><th>name</th><th>categories</th><th>date</th></tr></thead><tbody id="res"></tbody></table></div>
<div><p class="sub">First results as JSON</p><pre id="json" tabindex="0"></pre></div></div></section>

<section class="card"><h2>Stallholders by category</h2><p class="sub">From exhibitors.json and categories.json. A stall can be in more than one category.</p>
{hbar(kinds, "stallholders", "Stallholders per category")}{table(kinds, ["Category", "Stallholders"])}</section>

<section class="card"><h2>Journal posts per month</h2><p class="sub">From posts.json, {fmt_date(first) if first else ""} to {c.snap_date:%-d %B %Y}.</p>
{columns(ms, "Journal posts per month")}{table([(f"{m:%B %Y}", v) for m, v in ms], ["Month", "Posts"])}</section>

<section class="card"><h2>Journal posts by category</h2><p class="sub">A post can carry several categories.</p>
{hbar(pc, "posts", "Journal posts per category")}{table(pc, ["Category", "Posts"])}</section>

<section class="card"><h2>A map?</h2><p class="sub">Not drawn. The data holds one place, the market itself (The Old Market Place, Chiswick High Road, W4 2DR, on the Visit us page),
and no locations for the stallholders or their farms. A location field per stall in WordPress would make a map of where the cheese comes from possible.</p></section>
<script src="ccm-data.js"></script><script>{QUERY_JS}</script>"""
        write(out, "designs/6/index.html", self.layout(ctx, "Explore", body))
        write(out, "designs/6/files/index.html", self.files_page(c, Ctx(c, "6", "files/")))
        return 2

    def files_page(self, c, ctx):
        idx = c.index
        rows = []
        for f in idx["files"]:
            doc = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), f["file"])))
            fields = "".join(f"<li><code>{esc(k)}</code> {esc(v)}</li>" for k, v in (doc.get("fields") or {}).items())
            rows.append(f'<article class="card file"><h2><a href="{ctx.up()}{esc(f["file"])}">{esc(f["file"])}</a> <small>{f["count"] if f["count"] is not None else ""}</small></h2>'
                        f'<p>{esc(f["about"])}</p><ul class="fields">{fields}</ul></article>')
        ex = c.exhibitors[0] if c.exhibitors else {}
        sample = json.dumps({k: ex.get(k) for k in ("id", "slug", "name", "categories", "image", "date", "source_url")}, ensure_ascii=False, indent=1)
        body = f"""<section class="intro"><h1>Files and fields</h1>
<p>Each file carries an <code>about</code> line, the <code>snapshot</code> time, a <code>fields</code> guide and its <code>items</code>. Images stay on the market's site; <code>media.json</code> lists each one with the sizes WordPress made and a credit. Any page or tool can fetch them.</p></section>
{''.join(rows)}
<section class="card"><h2>One stallholder, as JSON</h2><pre tabindex="0">{esc(sample)}</pre></section>
<section class="card"><h2>Using the files</h2>
<p class="sub">In a browser:</p><pre>const r = await fetch('data/exhibitors.json');
const {{ items }} = await r.json();
items.filter(e =&gt; e.categories.includes(6)).map(e =&gt; e.name);</pre>
<p class="sub">On the command line, with jq:</p><pre>jq -r '.items[] | select(.categories | index(6)) | .name' data/exhibitors.json</pre>
<p class="sub">Straight from WordPress (their API, public and read-only):</p><pre>curl 'https://www.chiswickcheesemarket.uk/wp-json/wp/v2/portfolio?per_page=20&amp;_fields=id,slug,title,portfolio_category'</pre></section>"""
        return self.layout(ctx, "Files and fields", body)
