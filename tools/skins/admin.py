"""Admin: the WordPress viewer and parser. The one extra link on every page of every design.

  admin/index.html    API map: every namespace and route the site declares, the core ones tested with one GET,
                      CORS, what is public and what needs a login, and a live check from the browser
  admin/raw.html      raw data browser: every raw API response next to the clean record made from it
  admin/parser.html   the page-builder parser: raw shortcodes, the block tree, the rendered page
  admin/charts.html   what the data holds, drawn: shortcodes in use, post types, media by year, routes per namespace
"""
import collections, html, json, os, re
from .common import esc, Ctx, demo_strip, OFFICIAL, og_tags
from .d6_data import hbar, columns, table, months
from wordpress.shortcodes import normalise_shortcodes

LIVE_JS = r"""
document.getElementById('live').addEventListener('click',function(){var o=document.getElementById('liveout');o.textContent='Asking the live API...';
var t0=Date.now();fetch('https://www.chiswickcheesemarket.uk/wp-json/wp/v2/portfolio?per_page=3&_fields=id,slug,title,modified',{credentials:'omit'})
.then(function(r){var n=r.headers.get('X-WP-Total');return r.json().then(function(j){o.textContent='Live answer in '+(Date.now()-t0)+' ms. X-WP-Total: '+n+' stallholders.\n'+JSON.stringify(j,null,1)})})
.catch(function(e){o.textContent='No answer: '+e.message+'\nThe live API did not answer this browser (offline, blocked by an extension, or their CORS setting changed).'})});
"""

RAW_JS = r"""
(function(){var R=window.RAW,C=window.CLEAN,sel=document.getElementById('coll'),list=document.getElementById('items'),q=document.getElementById('find'),
raw=document.getElementById('raw'),clean=document.getElementById('clean'),meta=document.getElementById('meta');
Object.keys(R).forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k+' ('+(Array.isArray(R[k])?R[k].length:Object.keys(R[k]).length)+')';sel.appendChild(o)});
function label(x){var t=x.title&&(x.title.rendered||x.title)||x.name||x.label||x.slug||'';var d=document.createElement('textarea');d.innerHTML=String(t);return d.value}
function items(){var v=R[sel.value];return Array.isArray(v)?v:Object.keys(v).map(function(k){var o=v[k];return (o&&typeof o==='object')?Object.assign({_key:k},o):{_key:k,value:o}})}
function show(x){raw.textContent=JSON.stringify(x,null,1);var c=C[sel.value]&&C[sel.value][x.id];clean.textContent=c?JSON.stringify(c,null,1):'(no separate clean record: this collection is used as it is, or only in part)';
meta.textContent=(JSON.stringify(x).length/1024).toFixed(1)+' KB raw'+(c?', '+(JSON.stringify(c).length/1024).toFixed(1)+' KB clean':'')}
function draw(){var t=q.value.toLowerCase(),it=items();list.innerHTML='';it.filter(function(x){return !t||JSON.stringify(x).toLowerCase().indexOf(t)>=0}).slice(0,400).forEach(function(x){
var b=document.createElement('button');b.type='button';b.innerHTML='<code>'+(x.id||x._key||'')+'</code> '+label(x).replace(/</g,'&lt;');b.onclick=function(){[].forEach.call(list.children,function(y){y.removeAttribute('aria-pressed')});b.setAttribute('aria-pressed','true');show(x)};list.appendChild(b)});
if(list.firstChild)list.firstChild.click();else{raw.textContent='';clean.textContent='';meta.textContent='Nothing matches.'}}
sel.onchange=draw;q.oninput=draw;draw();})();
"""

PARSER_JS = r"""
(function(){var P=window.RAW.pages,C=window.CLEAN.pages,sel=document.getElementById('pg'),src=document.getElementById('src'),tree=document.getElementById('tree'),st=document.getElementById('stats'),open=document.getElementById('open');
P.filter(function(p){return C[p.id]}).forEach(function(p){var o=document.createElement('option');o.value=p.id;var d=document.createElement('textarea');d.innerHTML=p.title.rendered;o.textContent=d.value+' ('+p.slug+')';sel.appendChild(o)});
function count(bl,acc){(bl||[]).forEach(function(b){acc[b.type]=(acc[b.type]||0)+1;count(b.blocks,acc)});return acc}
function outline(bl,d){return (bl||[]).map(function(b){var pad=new Array(d+1).join('  ');var s=pad+b.type;
if(b.type==='section'&&b.background)s+=' ['+b.background+']';if(b.width&&b.type==='column')s+=' '+b.width;if(b.text)s+=': '+b.text;if(b.html)s+=': '+b.html.replace(/<[^>]+>/g,'').slice(0,90);
if(b.url)s+=' -> '+b.url;if(b.media)s+=' (image '+b.media+')';if(b.post_type)s+=' ('+b.post_type+(b.categories?' in categories '+b.categories:'')+')';
return s+'\n'+outline(b.blocks,d+1)}).join('')}
function show(){var p=P.filter(function(x){return String(x.id)===sel.value})[0],c=C[p.id];var raw=window.NORM[p.id]||'';
src.textContent=raw;tree.textContent=outline(c.blocks,0);var n=count(c.blocks,{}),sc=(raw.match(/\[[a-z_]+/g)||[]).length;
st.innerHTML='<b>'+sc+'</b> shortcodes and '+(raw.length/1024).toFixed(1)+' KB of builder markup became <b>'+Object.keys(n).reduce(function(a,k){return a+n[k]},0)+'</b> blocks: '+Object.keys(n).map(function(k){return n[k]+' '+k}).join(', ');
open.setAttribute('data-vault-page','designs/1/'+(window.ROUTES[p.slug]||p.slug+'/')+'index.html');open.href='../designs/1/'+(window.ROUTES[p.slug]||p.slug+'/')+'index.html'}
sel.onchange=show;show();})();
"""


class AdminCtx(Ctx):
    def __init__(self, content):
        super().__init__(content, "admin", "")

    def up(self):
        return "../"

    def link(self, route, design=None):
        return f"../designs/{design or '1'}/{route}index.html"


def page(ctx, title, nav_here, body, scripts=""):
    tabs = [("index.html", "API map"), ("raw.html", "Raw data"), ("parser.html", "Parser"), ("charts.html", "Charts")]
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h == nav_here else ""}>{t}</a>' for h, t in tabs)
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>{esc(title)} | Admin | Chiswick Cheese Market</title>
{og_tags("admin/" + nav_here, title + " | Admin | Chiswick Cheese Market", "The WordPress viewer and parser: what the public API gives, raw and parsed.")}
<link rel="stylesheet" href="../assets/css/demo.css"><link rel="stylesheet" href="../assets/css/d6.css"><link rel="stylesheet" href="../assets/css/admin.css"></head>
<body><a class="skip" href="#main">Skip to content</a>{demo_strip(ctx)}
<header class="dh"><a class="brand" href="index.html"><span>&#9881;</span> Admin <em>the WordPress viewer and parser</em></a><nav class="tabs">{nav}</nav></header>
<main id="main">{body}</main>
<footer class="df"><p>Read-only. Everything here came from GET requests to the public API at <a href="{OFFICIAL}/wp-json/">{OFFICIAL.replace("https://", "")}/wp-json/</a>
(snapshot {esc(ctx.c.snap_label)}). Nothing logged in, nothing written. Made with the open toolkit in <code>tools/wordpress/</code>.</p></footer>{scripts}</body></html>"""


def build(c, root, out, write):
    ctx = AdminCtx(c)
    amap = json.load(open(os.path.join(root, "data", "api-map.json")))
    raw_dir = os.path.join(root, "data", "raw")
    raw = {k: json.load(open(os.path.join(raw_dir, k + ".json"))) for k in
           ("pages", "posts", "portfolio", "media", "portfolio_category", "categories", "tags", "types", "taxonomies", "index", "chrome")}
    write(out, "assets/css/admin.css", ADMIN_CSS)
    n = 0

    # ---------- API map
    routes = amap["routes"]
    called = [r for r in routes if r["called"]]
    public = [r for r in called if r.get("public")]
    login = [r for r in called if r.get("status") == 401]
    ns_count = collections.Counter(r["namespace"] or "(index)" for r in routes)
    ns_get = collections.Counter(r["namespace"] or "(index)" for r in routes if "GET" in r["methods"])
    writes = sum(1 for r in routes if set(r["methods"]) & {"POST", "PUT", "PATCH", "DELETE"})
    cors = next((r.get("cors_allow_origin") for r in called if r.get("cors_allow_origin")), None)
    cred = next((r.get("cors_allow_credentials") for r in called if r.get("cors_allow_credentials")), None)
    users = next((r for r in called if r["route"] == "/wp/v2/users"), None)
    rows = "".join(f'<tr class="{"ok" if r.get("public") else "no"}"><td><code>{esc(r["route"])}</code></td><td>{r.get("status")}</td>'
                   f'<td>{"" if r.get("total") is None else r["total"]}</td><td>{"public" if r.get("public") else esc(r.get("error") or "needs a login")}</td></tr>' for r in called)
    nsrows = "".join(f'<tr><td><code>{esc(k)}</code></td><td>{v}</td><td>{ns_get[k]}</td><td>{"tested (core content)" if k == "wp/v2" else "listed, not called"}</td></tr>'
                     for k, v in sorted(ns_count.items(), key=lambda kv: -kv[1]))
    tiles = "".join(f'<div class="tile"><b>{v}</b><span>{esc(k)}</span></div>' for k, v in (
        ("namespaces", len(amap["namespaces"])), ("routes declared", len(routes)), ("core routes tested", len(called)),
        ("answer without login", len(public)), ("need a login", len(login))))
    dl = os.path.join(root, "data", "dead-links.json")
    dead = json.load(open(dl)) if os.path.exists(dl) else {"items": []}
    drows = "".join(f'<tr><td><code>{esc(x["url"])}</code></td><td>{x["status"]}</td><td>{f'<a href="{esc(x["found_on"])}">{esc(x["found_on"].replace(OFFICIAL, ""))}</a>' if x.get("found_on") else ""}</td></tr>' for x in dead["items"])
    dead_html = (f'<section class="card"><h2>Links that no longer work</h2><p class="sub">{len(dead["items"])} of the {dead.get("links_checked", "")} links in the market\'s own pages, posts and stallholder '
                 f'descriptions answered 404 twice (checked {esc(dead.get("checked", ""))}, gently, one at a time). The designs show them as plain text, marked. Several point to stallholder pages that have been removed.</p>'
                 f'<div class="scroll" tabindex="0" role="region" aria-label="Dead links"><table><thead><tr><th>link</th><th>status</th><th>found on</th></tr></thead><tbody>{drows}</tbody></table></div></section>') if dead["items"] else ""
    body = f"""<section class="intro"><h1>What the WordPress API gives anyone</h1>
<p>A WordPress site describes its own API at <code>/wp-json/</code>. Chiswick Cheese Market's lists <b>{len(routes)}</b> routes in <b>{len(amap["namespaces"])}</b> namespaces,
from WordPress itself (<code>wp/v2</code>) and from its plugins. We called each core content route once (GET, one item, with a browser-style Origin header) and listed the plugin routes without calling them.</p>
<div class="tiles">{tiles}</div></section>
<section class="card"><h2>Findings</h2><ul class="find">
<li><b>All the content is readable without a login</b>: pages, posts, the stallholders (<code>portfolio</code>), their categories, tags and the whole media library ({next((r["total"] for r in called if r["route"] == "/wp/v2/media"), "")} files). That is what the six designs are built from.</li>
<li><b>CORS is open.</b> Asked from <code>{esc(amap.get("origin_sent", ""))}</code>, the API answered <code>Access-Control-Allow-Origin: {esc(cors or "")}</code>{f" with <code>Allow-Credentials: {esc(cred)}</code>" if cred else ""}. This is WordPress's default: it echoes back whatever site asks, so a page on any website can read the content in a visitor's browser.</li>
<li><b>Menus need a login</b> (<code>/wp/v2/menus</code>, <code>/wp/v2/menu-items</code> answer 401), so the toolkit reads the navigation from the public homepage instead.</li>
<li><b>The theme's reusable blocks are public</b> (<code>/wp/v2/uncodeblock</code>, {next((r["total"] for r in called if r["route"] == "/wp/v2/uncodeblock"), "")} items), and so are the pop-ups. The home page's video header lives in one of them.</li>
{f'<li><b>The user list is public</b>: <code>/wp/v2/users</code> answers with {users.get("total")} accounts. We did not keep or show them. This is common on WordPress; many sites close it, and it is worth a look.</li>' if users and users.get("public") else ""}
<li><b>{writes}</b> declared routes accept writes (POST, PUT, PATCH or DELETE). They all need authentication; we never called them.</li>
<li>Plugins add their own namespaces (forms, redirects, SEO, security, an AI assistant, user management, site kit). Their routes are listed below as declared; we did not call any.</li></ul></section>
{dead_html}
<section class="card"><h2>Ask the live API now</h2><p class="sub">One GET for three stallholders, straight from your browser to theirs.</p>
<p><button id="live" type="button">Check the live API</button></p><pre id="liveout" tabindex="0">Not asked yet.</pre></section>
<section class="card"><h2>Core routes, tested</h2><div class="scroll" tabindex="0" role="region" aria-label="Core routes"><table><thead><tr><th>route</th><th>status</th><th>items</th><th>access</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="card"><h2>Every namespace</h2><div class="scroll" tabindex="0" role="region" aria-label="Namespaces"><table><thead><tr><th>namespace</th><th>routes</th><th>with GET</th><th>what we did</th></tr></thead><tbody>{nsrows}</tbody></table></div>
<p class="sub">The full list, with each route's methods and parameters, is <a href="../data/api-map.json">data/api-map.json</a>.</p></section>"""
    write(out, "admin/index.html", page(ctx, "API map", "index.html", body, f"<script>{LIVE_JS}</script>")); n += 1

    # ---------- raw data browser
    clean = {"pages": {p["id"]: p for p in c.pages.values()}, "posts": {p["id"]: p for p in c.posts},
             "portfolio": {e["id"]: e for e in c.exhibitors}, "media": {m["id"]: m for m in c.media.values() if isinstance(m["id"], int)}}
    norm = {p["id"]: normalise_shortcodes(p["content"]["rendered"]) for p in raw["pages"]}
    routes_js = {"home": "", "meet-the-stallholders": "stallholders/", "journal": "journal/"}
    write(out, "admin/raw-data.js", "window.RAW=" + json.dumps(raw, ensure_ascii=False, separators=(",", ":")) + ";\nwindow.CLEAN=" +
          json.dumps(clean, ensure_ascii=False, separators=(",", ":")) + ";\nwindow.NORM=" + json.dumps(norm, ensure_ascii=False, separators=(",", ":")) +
          ";\nwindow.ROUTES=" + json.dumps(routes_js) + ";")
    body = """<section class="intro"><h1>Raw data</h1><p>Each collection exactly as the API returned it (left), and the clean record the toolkit makes from it (right).
Search looks through the raw JSON.</p></section>
<section class="card"><div class="q"><label>Collection<select id="coll"></select></label><label class="grow">Search<input id="find" type="search" placeholder="a word, a slug, an id"></label></div>
<div class="browser"><div class="items" id="items" role="listbox" aria-label="Items"></div><div class="panes"><p class="sub" id="meta"></p>
<div class="two"><div><h3>Raw, from WordPress</h3><pre id="raw" tabindex="0"></pre></div><div><h3>Clean, from the toolkit</h3><pre id="clean" tabindex="0"></pre></div></div></div></div></section>"""
    write(out, "admin/raw.html", page(ctx, "Raw data", "raw.html", body, f'<script src="raw-data.js"></script><script>{RAW_JS}</script>')); n += 1

    # ---------- parser
    body = """<section class="intro"><h1>The parser</h1><p>The site's pages are built with a page builder (WPBakery, in the Uncode theme). The API returns them as raw
shortcodes, like <code>[vc_row][vc_column width="1/2"][vc_custom_heading]...</code>, with the quotes typographically "curled". The toolkit straightens the quotes,
parses the shortcodes into a tree and keeps only what a design needs: sections, columns, headings, text, buttons, images and listings.</p></section>
<section class="card"><div class="q"><label class="grow">Page<select id="pg"></select></label><a id="open" class="btnlink" href="#">Open it in Design 1</a></div>
<p class="sub" id="stats"></p><div class="two"><div><h3>1. Raw builder markup (quotes straightened)</h3><pre id="src" class="wrap" tabindex="0"></pre></div>
<div><h3>2. Blocks (outline of pages.json)</h3><pre id="tree" tabindex="0"></pre></div></div></section>"""
    write(out, "admin/parser.html", page(ctx, "Parser", "parser.html", body, f'<script src="raw-data.js"></script><script>{PARSER_JS}</script>')); n += 1

    # ---------- charts
    sc = collections.Counter()
    for p in raw["pages"]:
        sc.update(re.findall(r"\[([a-z_]+)", normalise_shortcodes(p["content"]["rendered"])))
    sc_rows = sc.most_common(14)
    types = [(r["route"].rsplit("/", 1)[-1], r["total"]) for r in called if r.get("total") and r["route"].count("/") == 3 and r["route"].rsplit("/", 1)[-1] not in ("search",)]
    types.sort(key=lambda r: -r[1])
    years = collections.Counter()
    for m in raw["media"]:
        y = re.search(r"/uploads/(\d{4})/", m.get("source_url", ""))
        if y:
            years[y.group(1)] += 1
    yrows = sorted(years.items())
    nsr = [(k, v) for k, v in ns_count.most_common(12)]
    per_year = collections.Counter(p["date"][:4] for p in c.posts)
    body = f"""<section class="intro"><h1>What is there, drawn</h1><p>Counts from the API map and the snapshot. Hover a bar for its value; each chart has a table.</p></section>
<section class="card"><h2>Items per content type</h2><p class="sub">X-WP-Total from one GET to each public collection.</p>{hbar(types, "items", "Items per content type")}{table(types, ["Type", "Items"])}</section>
<section class="card"><h2>Page-builder shortcodes in use</h2><p class="sub">Across the {len(raw["pages"])} pages. The parser turns these into blocks.</p>{hbar(sc_rows, "uses", "Shortcodes in use")}{table(sc_rows, ["Shortcode", "Uses"])}</section>
<section class="card"><h2>Images the designs use, by upload year</h2><p class="sub">{len(raw["media"])} of the library's files are used by the public pages, posts and stallholders.</p>{hbar(yrows, "images", "Images by upload year")}{table(yrows, ["Year", "Images"])}</section>
<section class="card"><h2>Journal posts per year</h2>{hbar(sorted(per_year.items()), "posts", "Posts per year")}</section>
<section class="card"><h2>Routes per namespace</h2><p class="sub">What WordPress and each plugin declare. Only <code>wp/v2</code> was called.</p>{hbar(nsr, "routes", "Routes per namespace")}{table(nsr, ["Namespace", "Routes"])}</section>"""
    write(out, "admin/charts.html", page(ctx, "Charts", "charts.html", body)); n += 1
    return n


ADMIN_CSS = """
.tabs a{color:var(--text-secondary);text-decoration:none;padding:4px 10px;border-radius:999px}
.tabs a[aria-current]{background:var(--text-primary);color:var(--bg)}
.find li{margin:0 0 10px;color:var(--text-secondary)}.find b{color:var(--text-primary)}
tr.no td{color:var(--muted)}
button,.btnlink{font:600 14px 'Inter',sans-serif;background:var(--text-primary);color:var(--bg);border:0;border-radius:8px;padding:10px 16px;cursor:pointer;text-decoration:none;display:inline-block}
.browser{display:grid;grid-template-columns:280px minmax(0,1fr);gap:16px;margin-top:14px}
.items{max-height:640px;overflow:auto;border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column}
.items button{background:none;color:var(--text-primary);text-align:left;border-radius:0;border-bottom:1px solid var(--line);font-weight:400;padding:8px 10px}
.items button[aria-pressed]{background:var(--bg);box-shadow:inset 3px 0 0 var(--series-1)}
.items code{color:var(--muted);font-size:12px}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px}
.two>div,.panes,.browser>*{min-width:0}
.card td:first-child{color:var(--text-primary)}
.two h3{font-size:13px;color:var(--text-secondary);margin:0 0 6px;font-weight:600}
.two pre{max-height:600px}
pre.wrap{white-space:pre-wrap;word-break:break-word}
@media (max-width:860px){.browser,.two{grid-template-columns:1fr}.items{max-height:260px}}
"""
