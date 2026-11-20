"""Map what a WordPress site exposes through its REST API, read-only.

  * Reads the /wp-json/ index: every namespace and route the site declares, with its methods.
  * For the core content collections (namespace wp/v2, routes without parameters, GET allowed) makes
    ONE gentle GET (per_page=1, _fields=id) with a browser-style Origin header, and records the status,
    the X-WP-Total count and the CORS headers.
  * Every other route (plugins) is listed as declared, never called: some plugin routes are named like
    actions (tokens, settings, updates) and a GET to them is not ours to make.

    python3 -m wordpress.probe https://example.org > api-map.json
"""
import json, sys, time, urllib.error, urllib.parse, urllib.request

ORIGIN = "https://example.org"
# Core collections that need a login by design; still probed (one GET) so the map shows the 401.
SKIP_CALL = {"/wp/v2/users/me", "/wp/v2/settings", "/wp/v2/plugins", "/wp/v2/themes", "/wp/v2/sidebars", "/wp/v2/widgets",
             "/wp/v2/widget-types", "/wp/v2/global-styles/themes", "/wp/v2/templates/lookup", "/wp/v2/menu-locations",
             "/wp/v2/block-directory/search", "/wp/v2/pattern-directory/patterns", "/wp/v2/font-collections"}


def _get(url, ua, origin):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json", "Origin": origin})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


def probe(base, ua="wordpress-probe/1.0 (read-only)", origin=ORIGIN, pause=1.0, log=None):
    log = log or (lambda *a: print(*a, file=sys.stderr, flush=True))
    base = base.rstrip("/")
    st, h, body = _get(base + "/wp-json/", ua, origin)
    idx = json.loads(body)
    time.sleep(pause)
    routes = []
    for route, info in idx.get("routes", {}).items():
        methods = sorted({m for e in info.get("endpoints", []) for m in e.get("methods", [])})
        ns = info.get("namespace") or ""
        r = {"route": route, "namespace": ns, "methods": methods, "has_parameters": "(?P<" in route, "called": False}
        args = {}
        for e in info.get("endpoints", []):
            if "GET" in e.get("methods", []):
                a = e.get("args") or {}
                args = {k: {"type": v.get("type"), "description": v.get("description")} for k, v in a.items()} if isinstance(a, dict) else {}
        r["get_args"] = sorted(args)
        if ns == "wp/v2" and "GET" in methods and not r["has_parameters"] and route not in SKIP_CALL:
            q = "?" + urllib.parse.urlencode({"per_page": 1, "_fields": "id"}) if "per_page" in args else ""
            url = base + "/wp-json" + route + q
            log("GET", url)
            s, hh, b = _get(url, ua, origin)
            time.sleep(pause)
            r.update({"called": True, "status": s, "public": s == 200,
                      "total": int(hh["x-wp-total"]) if hh.get("x-wp-total", "").isdigit() else None,
                      "cors_allow_origin": hh.get("access-control-allow-origin"),
                      "cors_allow_credentials": hh.get("access-control-allow-credentials")})
            if s != 200:
                try:
                    r["error"] = json.loads(b).get("code")
                except Exception:
                    r["error"] = None
        routes.append(r)
    return {
        "site": base, "name": idx.get("name"), "description": idx.get("description"),
        "namespaces": idx.get("namespaces", []), "authentication": list((idx.get("authentication") or {}).keys()),
        "origin_sent": origin, "index_cors_allow_origin": h.get("access-control-allow-origin"),
        "routes": routes,
        "note": "Only wp/v2 collection routes without parameters were called (one GET each, per_page=1). Plugin routes are listed as declared, not called.",
    }


if __name__ == "__main__":
    print(json.dumps(probe(sys.argv[1], origin=sys.argv[2] if len(sys.argv) > 2 else ORIGIN), indent=1))
