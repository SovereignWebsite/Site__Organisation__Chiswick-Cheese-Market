#!/usr/bin/env python3
"""
fetch-wp.py - a read-only snapshot of the Chiswick Cheese Market WordPress site.

This is the Chiswick configuration of the generic toolkit in tools/wordpress/ (which works on any
WordPress site). It reads the public REST API (GET only, no login, no write endpoints, small pages,
a pause between requests) and writes:

  data/index.json       manifest: every file, its count, the snapshot time
  data/site.json        name, tagline, navigation, footer menus, social links, logo
  data/pages.json       public pages; page-builder shortcodes turned into plain blocks
  data/posts.json       journal posts
  data/exhibitors.json  stallholders (the WordPress post type 'portfolio')
  data/categories.json  exhibitor categories, journal categories, tags in use
  data/media.json       every image used, with its credit and source URL
  data/api-map.json     every API route the site declares; the core ones tested with one GET
  data/raw/             the raw API responses, so the JSON can be rebuilt offline
  snapshot/media/       with --media: local copies of the images used (at most 1600 px wide)

data/ is committed, so every snapshot is a commit. The designs load images from the market's site,
so local copies are optional (--media) and not committed.

Usage
  python3 tools/fetch-wp.py                    # full snapshot
  python3 tools/fetch-wp.py --media            # also keep local copies of the images
  python3 tools/fetch-wp.py --from-raw data/raw   # rebuild the JSON offline from the raw responses

A scheduled pipeline can rerun this nightly and republish: that is how the static site "runs from
the live data". See docs/live-data.md.
"""
import argparse, html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wordpress.snapshot import Snapshot  # noqa: E402
from wordpress.probe import probe  # noqa: E402

BASE = "https://www.chiswickcheesemarket.uk"
CREDIT = "Image: Chiswick Cheese Market (chiswickcheesemarket.uk)"
# Member-only or account plumbing pages; not part of the public site.
SKIP = {"profile", "account", "register", "password-reset", "log-in", "trader-newsletter"}
MENUS = {"navigation": "menu-main-menu", "topbar": "menu-top-menu", "footer_1": "menu-footer-1",
         "footer_2": "menu-footer-2", "bottom_bar": "menu-bottom-bar"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--media", action="store_true", help="also keep local copies of the images in snapshot/media/")
    ap.add_argument("--no-probe", action="store_true", help="skip the API map (data/api-map.json)")
    ap.add_argument("--from-raw", help="rebuild data/*.json from a saved data/raw/ folder, no network")
    a = ap.parse_args()
    s = Snapshot(BASE, out=a.out, types={"pages": "pages", "posts": "posts", "portfolio": "exhibitors"},
                 skip_slugs=SKIP, credit=CREDIT, menus=MENUS, media_dir="snapshot/media", from_raw=a.from_raw, download_media=a.media,
                 user_agent="SovereignWebsite-snapshot/1.0 (read-only static demo; gentle)")
    r = s.run()
    snap, d = r["snapshot"], r["data_dir"]
    items = r["items"]
    for e in items["exhibitors"]:  # name the fields for what they are on this site
        e["name"] = e.pop("title")
        e["categories"] = e.pop("portfolio_category", [])
        e["description_html"], e["description_text"] = e.pop("body_html"), e.pop("body_text")
    for p in items["pages"]:
        for k in ("excerpt", "categories", "tags"):
            p.pop(k, None)
    idx = r["index"]
    m = []
    m.append(s.write("site.json", {"name": html.unescape(idx.get("name") or ""), "tagline": html.unescape(idx.get("description") or ""),
                                   "url": BASE, "timezone": idx.get("timezone_string"), "icon": idx.get("site_icon_url"), **r["chrome"]},
                     "Site name, tagline, menus and social links. Menus are read from the public homepage, as the menus API needs a login.",
                     {"navigation": "main menu; items with children are dropdowns", "topbar": "the small bar above the header",
                      "footer_1, footer_2, bottom_bar": "footer menus", "social": "official social profiles linked from the site",
                      "logo_file": "local copy of the logo under site/"}, snap, d))
    m.append(s.write("exhibitors.json", items["exhibitors"], "Stallholders (WordPress post type 'portfolio', shown on the site as Stallholders).",
                     {"id": "WordPress id", "slug": "URL slug", "name": "stall name", "categories": "ids into categories.json exhibitor_categories",
                      "description_html": "cleaned HTML", "description_text": "plain text", "image": "id into media.json",
                      "links": "outbound links in the description (their own websites, Instagram)", "date": "first published, UTC",
                      "source_url": "the stallholder's page on the official site"}, snap, d))
    m.append(s.write("posts.json", items["posts"], "Journal posts (news, market highlights, tasting notes, recipes ...).",
                     {"date": "published, UTC", "categories": "ids into categories.json post_categories", "tags": "ids into categories.json tags",
                      "excerpt": "plain text", "body_html": "cleaned HTML (null when the post uses page-builder blocks)",
                      "blocks": "page-builder content as blocks (see pages.json)", "image": "id into media.json",
                      "source_url": "the post on the official site"}, snap, d))
    m.append(s.write("pages.json", items["pages"], "Public pages. The site's page builder (WPBakery / Uncode) shortcodes are converted to plain blocks.",
                     {"blocks": "section > column > heading | text | button | image | gallery | listing | embed | form",
                      "image": "the page's header image, id into media.json", "source_url": "the page on the official site"}, snap, d))
    # The market's monthly posters: the animated GIF banners in the media library (one GET).
    gifs = s.c.collection("media", {"mime_type": "image/gif", "_fields": "id,date_gmt,slug,title,alt_text,source_url,media_details,link"}, key="media_gif")
    posters = []
    for g in sorted(gifs, key=lambda g: g["date_gmt"]):
        md = g.get("media_details") or {}
        posters.append({"id": g["id"], "title": html.unescape(g["title"]["rendered"]), "date": g["date_gmt"] + "Z", "url": g["source_url"],
                        "width": md.get("width"), "height": md.get("height"), "bytes": md.get("filesize"),
                        "sizes": {k: {"url": v.get("source_url"), "width": v.get("width"), "height": v.get("height")} for k, v in (md.get("sizes") or {}).items()},
                        "page_url": g.get("link"), "credit": CREDIT})
    m.append(s.write("posters.json", posters, "The market's own posters: the animated GIF banners in its media library, oldest first.",
                     {"url": "the full animated GIF on the market's site (some are large)", "sizes": "smaller copies WordPress made (usually still, not animated)",
                      "bytes": "file size of the full GIF"}, snap, d))
    t = r["terms"]
    m.append(s.write("categories.json", {"exhibitor_categories": t.get("portfolio_category", []), "post_categories": t.get("categories", []),
                                         "tags": [x for x in t.get("tags", []) if x.get("count")]},
                     "Exhibitor categories (portfolio_category), journal categories and the tags in use.", {"count": "number of items in WordPress"}, snap, d))
    m.append(s.write("media.json", sorted(r["media"].values(), key=lambda x: str(x["id"]).zfill(8)),
                     "Every image the snapshot uses. All images belong to Chiswick Cheese Market and are used here only to show their own content back to them.",
                     {"file": "local copy under site/ (at most 1600 px wide)", "original_url": "the image on the official site", "credit": "credit line"}, snap, d))
    with open(os.path.join(d, "index.json"), "w") as f:
        json.dump({"about": "Chiswick Cheese Market content snapshot, read-only from the public WordPress REST API.",
                   "snapshot": snap, "files": m}, f, ensure_ascii=False, indent=1)
    s.save_raw(d)
    if not a.from_raw and not a.no_probe:
        amap = probe(BASE, ua="SovereignWebsite-snapshot/1.0 (read-only static demo; gentle)",
                     origin="https://chiswick-cheese-market.organisation.sovereignweb.site")
        amap["snapshot"] = snap
        with open(os.path.join(d, "api-map.json"), "w") as f:
            json.dump(amap, f, ensure_ascii=False, indent=1)
    s.log("done", snap)


if __name__ == "__main__":
    main()
