"""A gentle, read-only WordPress REST API client.

GET only. Small pages, a pause between requests, retries with back-off, a clear User-Agent.
Every collection it reads can be kept in a raw folder, and the same client can replay that folder
with no network at all (from_raw), so templates can be rebuilt offline and the raw data kept in git.
"""
import json, os, sys, time, urllib.parse, urllib.request


class WPClient:
    def __init__(self, base, user_agent="wordpress-snapshot/1.0 (read-only)", pause=1.0, per_page=20, from_raw=None, log=None):
        self.base = base.rstrip("/")
        self.api = self.base + "/wp-json/wp/v2"
        self.ua, self.pause, self.per_page, self.from_raw = user_agent, pause, per_page, from_raw
        self.raw = {}
        self.log = log or (lambda *a: print(*a, file=sys.stderr, flush=True))

    def _get(self, url, binary=False):
        req = urllib.request.Request(url, headers={"User-Agent": self.ua, "Accept": "*/*" if binary else "application/json"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = r.read()
                    return (data if binary else json.loads(data)), {k.lower(): v for k, v in r.headers.items()}
            except Exception as e:
                self.log(f"  retry {attempt + 1} {url}: {e}")
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("failed: " + url)

    def _cached(self, key):
        with open(os.path.join(self.from_raw, key + ".json")) as f:
            return json.load(f)

    def bytes(self, url):
        """A file (an image, the homepage HTML). Always network; callers cache what they keep."""
        self.log("GET", url)
        data, _ = self._get(url, binary=True)
        time.sleep(self.pause)
        return data

    def index(self):
        """The site's /wp-json/ index: name, tagline, timezone, icon."""
        if self.from_raw:
            return self._cached("index")
        d, _ = self._get(self.base + "/wp-json/")
        time.sleep(self.pause)
        keep = {k: d.get(k) for k in ("name", "description", "url", "home", "timezone_string", "site_icon_url")}
        self.raw["index"] = keep
        return keep

    def collection(self, endpoint, params=None, key=None):
        """Every item of a collection (pages, posts, a custom post type, a taxonomy), page by page."""
        key = key or endpoint.replace("/", "_")
        if self.from_raw:
            return self._cached(key)
        out, page = [], 1
        while True:
            q = dict(params or {}, per_page=self.per_page, page=page)
            url = f"{self.api}/{endpoint}?{urllib.parse.urlencode(q)}"
            self.log("GET", url)
            items, headers = self._get(url)
            time.sleep(self.pause)
            out += items
            if page >= int(headers.get("x-wp-totalpages") or 1) or not items:
                break
            page += 1
        self.raw[key] = out
        return out

    def by_ids(self, endpoint, ids, fields=None, key=None):
        """Items of a collection by id (for example only the media a snapshot uses)."""
        key = key or endpoint
        ids = sorted(set(i for i in ids if i))
        if self.from_raw:
            wanted = set(ids)
            return [m for m in self._cached(key) if m["id"] in wanted]
        out = []
        for i in range(0, len(ids), self.per_page):
            q = {"include": ",".join(map(str, ids[i:i + self.per_page])), "per_page": self.per_page}
            if fields:
                q["_fields"] = fields
            url = f"{self.api}/{endpoint}?{urllib.parse.urlencode(q)}"
            self.log("GET", url)
            items, _ = self._get(url)
            time.sleep(self.pause)
            out += items
        self.raw[key] = out
        return out

    def types(self):
        """Public post types and taxonomies, so custom types (like a 'portfolio') are found, not guessed."""
        if self.from_raw:
            return self._cached("types"), self._cached("taxonomies")
        t, _ = self._get(self.api + "/types"); time.sleep(self.pause)
        x, _ = self._get(self.api + "/taxonomies"); time.sleep(self.pause)
        t = {k: {"name": v.get("name"), "slug": v.get("slug"), "rest_base": v.get("rest_base"), "taxonomies": v.get("taxonomies")} for k, v in t.items()}
        x = {k: {"name": v.get("name"), "slug": v.get("slug"), "rest_base": v.get("rest_base"), "types": v.get("types")} for k, v in x.items()}
        self.raw["types"], self.raw["taxonomies"] = t, x
        return t, x

    def save_raw(self, folder, extra=None):
        os.makedirs(folder, exist_ok=True)
        for k, v in dict(self.raw, **(extra or {})).items():
            with open(os.path.join(folder, k + ".json"), "w") as f:
                json.dump(v, f, ensure_ascii=False)
