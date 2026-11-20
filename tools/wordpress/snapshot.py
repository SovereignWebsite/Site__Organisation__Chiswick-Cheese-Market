"""A generic, read-only snapshot of a WordPress site into documented JSON files.

    from wordpress.snapshot import Snapshot
    Snapshot(base="https://example.org", out=".", types={"posts": "posts", "portfolio": "exhibitors"}).run()

It reads the site index, the public post types and taxonomies (discovered, not guessed), every item of
the post types you name, the menus printed on the homepage, and only the media those items use.
Page-builder bodies become plain blocks (see shortcodes.py). Each output file carries the snapshot
time and every item its source URL on the live site. Raw API responses are kept in data/raw/, so the
JSON can be rebuilt offline (from_raw) when the cleaning rules improve.
"""
import datetime, hashlib, html, json, os, re

from .client import WPClient
from .html_clean import text, clean_html, content_media, content_urls
from .shortcodes import page_blocks
from .menus import menu_from_html, social_links
from .media import pick_size, save_image, local_name

ITEM_FIELDS = "id,date_gmt,modified_gmt,slug,link,title,content,excerpt,featured_media,parent,menu_order,categories,tags,author"
TERM_FIELDS = "id,name,slug,count,description,link,parent"
MEDIA_FIELDS = "id,slug,title,alt_text,caption,source_url,media_details,link,mime_type"


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Snapshot:
    def __init__(self, base, out=".", types=None, skip_slugs=(), credit=None, menus=None, user_agent=None,
                 media_dir="site/media", from_raw=None, download_media=True, pause=1.0, media_pause=0.4, log=None):
        self.base = base.rstrip("/")
        self.out = out
        self.types = types or {"pages": "pages", "posts": "posts"}   # rest_base -> output name
        self.skip = set(skip_slugs)
        self.credit = credit or f"Image: {self.base}"
        self.menus = menus or {"navigation": "menu-primary-inner"}   # output key -> <ul> id/class marker
        self.media_dir = media_dir
        self.download_media = download_media
        self.media_pause = media_pause
        self.c = WPClient(self.base, user_agent=user_agent or "wordpress-snapshot/1.0 (read-only)", pause=pause,
                          from_raw=from_raw, log=log)
        self.log = self.c.log
        self.media_ids, self.extra_urls = set(), set()

    # ------------------------------------------------------------ items
    def _use(self, h, featured):
        self.media_ids.update(content_media(h))
        self.extra_urls |= content_urls(h)
        if featured:
            self.media_ids.add(featured)

    def item(self, p, taxonomies):
        h = (p.get("content") or {}).get("rendered", "")
        self._use(h, p.get("featured_media"))
        builder = "[vc_row" in h
        rec = {
            "id": p["id"], "slug": p["slug"], "title": text(p["title"]["rendered"]),
            "date": (p.get("date_gmt") or "") + "Z", "modified": (p.get("modified_gmt") or "") + "Z",
            "image": p.get("featured_media") or None,
            "excerpt": text((p.get("excerpt") or {}).get("rendered", "")).replace(" […]", "…"),
            "body_html": None if builder else clean_html(h),
            "body_text": text(re.sub(r"\[[^\]]+\]", " ", h)) if not builder else None,
            "blocks": page_blocks(h, self.media_ids) if builder else None,
            "links": sorted(l for l in set(re.findall(r'href="(https?://[^"]+)"', h)) if self.host() not in l),
            "source_url": p.get("link"),
        }
        if p.get("parent"):
            rec["parent"] = p["parent"]
        for tax in taxonomies:
            if tax in p:
                rec[tax] = p[tax]
        return rec

    def host(self):
        return re.sub(r"^https?://(www\.)?", "", self.base)

    # ------------------------------------------------------------ chrome
    def chrome(self):
        if self.c.from_raw:
            return self.c._cached("chrome")
        h = self.c.bytes(self.base + "/").decode("utf-8", "replace")
        out = {k: menu_from_html(h, marker) for k, marker in self.menus.items()}
        out["social"] = social_links(h)
        logo = re.search(r'class="logo-image[^"]*main-logo[^>]*>\s*<img[^>]+src="([^"]+)"', h) or \
            re.search(r'<img[^>]+class="[^"]*custom-logo[^"]*"[^>]+src="([^"]+)"', h)
        out["logo_url"] = logo.group(1) if logo else None
        foot = re.search(r"(&copy;|©)\s*(\d{4})[^<]*All Rights Reserved\.?\s*(?:<a[^>]*>)?([^<]*)", h)
        out["copyright"] = f"© {foot.group(2)}. All Rights Reserved. {foot.group(3).strip()}" if foot else None
        # The theme's page header (on Uncode, an 'uncodeblock'): its background image and video, if any.
        seg = h[h.find('id="page-header"'):][:6000] if 'id="page-header"' in h else ""
        bg = re.search(r"background-image:\s*url\(([^)]+)\)", seg)
        vid = re.search(r'<source[^>]+src="([^"?]+\.mp4)', seg)
        out["home_header"] = {"image_url": bg.group(1) if bg else None, "video_url": vid.group(1) if vid else None}
        out["source"] = self.base + "/"
        self.c.raw["chrome"] = out
        return out

    # ------------------------------------------------------------ media
    def media(self):
        self.media_ids.discard(0)
        rec = {}
        for m in self.c.by_ids("media", self.media_ids, MEDIA_FIELDS):
            src = pick_size(m)
            rec[m["id"]] = {"id": m["id"], "title": text(m["title"]["rendered"]), "alt": m.get("alt_text") or "",
                            "caption": text((m.get("caption") or {}).get("rendered", "")),
                            "original_url": m["source_url"], "download_url": src,
                            "file": "media/" + local_name(m["id"], src), "page_url": m.get("link"), "credit": self.credit,
                            "width": (m.get("media_details") or {}).get("width"), "height": (m.get("media_details") or {}).get("height"),
                            "sizes": {k: {"url": v.get("source_url"), "width": v.get("width"), "height": v.get("height")}
                                      for k, v in ((m.get("media_details") or {}).get("sizes") or {}).items()}}
        for u in sorted(self.extra_urls):
            key = "u" + hashlib.sha1(u.encode()).hexdigest()[:10]
            rec[key] = {"id": key, "original_url": u, "download_url": u, "file": "media/" + local_name(key, u), "credit": self.credit}
        return rec

    def download(self, media, extra_urls=()):
        base_dir = os.path.join(self.out, os.path.dirname(self.media_dir.rstrip("/")))
        todo = list(media.values())
        for n, m in enumerate(todo):
            path = os.path.join(base_dir, m["file"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.exists(path):
                continue
            self.log(f"IMG {n + 1}/{len(todo)} {m['download_url']}")
            try:
                save_image(m["download_url"], path, self.c.bytes)
            except Exception as e:
                self.log("  skipped:", e)
                m["file"] = None

    # ------------------------------------------------------------ run
    def run(self, extra=None):
        started = now()
        data_dir = os.path.join(self.out, "data")
        os.makedirs(data_dir, exist_ok=True)
        index = self.c.index()
        types, taxes = self.c.types()
        results, terms = {}, {}
        for rest_base, name in self.types.items():
            tdef = next((t for t in types.values() if t.get("rest_base") == rest_base), {})
            tax_names = [taxes[t]["rest_base"] for t in (tdef.get("taxonomies") or []) if t in taxes]
            items = [self.item(p, tax_names) for p in self.c.collection(rest_base, {"_fields": ITEM_FIELDS + "," + ",".join(tax_names)})]
            results[name] = [i for i in items if i["slug"] not in self.skip]
            for t in tax_names:
                if t not in terms:
                    terms[t] = self.c.collection(t, {"_fields": TERM_FIELDS})
        chrome = self.chrome()
        if chrome.get("logo_url") and self.c.from_raw:
            chrome["logo_file"] = "media/" + os.path.basename(chrome["logo_url"].split("?")[0])
        if chrome.get("logo_url") and not self.c.from_raw and self.download_media:
            name = os.path.basename(chrome["logo_url"].split("?")[0])
            p = os.path.join(self.out, self.media_dir, name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not os.path.exists(p):
                open(p, "wb").write(self.c.bytes(chrome["logo_url"]))
            chrome["logo_file"] = "media/" + name
        for k in ("image_url", "video_url"):
            u = (chrome.get("home_header") or {}).get(k)
            if u and self.c.from_raw:
                chrome["home_header"][k.replace("_url", "_file")] = "media/header-" + os.path.basename(u.split("?")[0])
            if u and self.download_media and not self.c.from_raw:
                name = "header-" + os.path.basename(u.split("?")[0])
                p = os.path.join(self.out, self.media_dir, name)
                if not os.path.exists(p):
                    open(p, "wb").write(self.c.bytes(u))
                chrome["home_header"][k.replace("_url", "_file")] = "media/" + name
        media = self.media()
        if self.download_media and not self.c.from_raw:
            self.download(media)
        finished = now()
        if self.c.from_raw:
            t = self.c._cached("snapshot")
            started, finished = t["snapshot_started"], t["snapshot_finished"]
        self.c.raw["snapshot"] = {"snapshot_started": started, "snapshot_finished": finished}
        snap = {"snapshot_started": started, "snapshot_finished": finished, "source": self.base,
                "api": self.base + "/wp-json/", "tool": "tools/fetch-wp.py (tools/wordpress)"}
        return dict(index=index, types=types, taxonomies=taxes, items=results, terms=terms, chrome=chrome,
                    media=media, snapshot=snap, data_dir=data_dir)

    def write(self, name, payload, about, fields, snap, data_dir):
        doc = {"about": about, "snapshot": snap, "fields": fields,
               "count": len(payload) if isinstance(payload, list) else None, "items": payload}
        with open(os.path.join(data_dir, name), "w") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        return {"file": "data/" + name, "about": about, "count": doc["count"]}

    def save_raw(self, data_dir):
        if not self.c.from_raw:
            self.c.save_raw(os.path.join(data_dir, "raw"))
