#!/usr/bin/env python3
"""
check-links.py - find the links in the market's own content that no longer work, gently.

  python3 tools/check-links.py          # writes data/dead-links.json

Reads every link in pages, posts and stallholders (not images), asks each one once (HEAD, then GET if
HEAD is refused), one at a time with a pause. 404 or 410 counts as dead, twice in a row; anything else
(403, 429, timeouts) is not counted, because many sites refuse automated checks. The designs then show a
dead link as plain text marked "link no longer works", and Admin lists them for the organisers.
"""
import datetime, json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "SovereignWebsite-linkcheck/1.0 (read-only; gentle)"


def links():
    found = {}
    def scan(h, where):
        for u in re.findall(r'href="(https?://[^"#]+)', h or ""):
            found.setdefault(u, where)
    def walk(bl, where):
        for b in bl or []:
            if b.get("type") == "button" and b.get("url", "").startswith("http"):
                found.setdefault(b["url"].split("#")[0], where)
            scan(b.get("html"), where)
            walk(b.get("blocks"), where)
    d = lambda n: json.load(open(os.path.join(ROOT, "data", n)))["items"]
    for p in d("pages.json"):
        walk(p["blocks"], p["source_url"])
    for p in d("posts.json"):
        scan(p.get("body_html"), p["source_url"]); walk(p.get("blocks"), p["source_url"])
    for e in d("exhibitors.json"):
        scan(e.get("description_html"), e["source_url"])
    return found


def status(u):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue
            return e.code
        except Exception:
            return None
    return None


def main():
    found = links()
    dead = []
    for i, (u, where) in enumerate(sorted(found.items())):
        s = status(u); time.sleep(0.5)
        if s in (404, 410):
            time.sleep(1); s2 = status(u); time.sleep(0.5)
            if s2 in (404, 410):
                dead.append({"url": u, "status": s2, "found_on": where})
        print(f"{i + 1}/{len(found)} {s} {u}", file=sys.stderr)
    out = {"about": "Links in the market's own content that no longer work. The designs show them as plain text, marked.",
           "checked": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "links_checked": len(found),
           "how": "One HEAD (or GET) per link, one at a time with a pause; 404 or 410 twice counts as dead.", "items": dead}
    json.dump(out, open(os.path.join(ROOT, "data", "dead-links.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(dead)} dead of {len(found)}", file=sys.stderr)


if __name__ == "__main__":
    main()
