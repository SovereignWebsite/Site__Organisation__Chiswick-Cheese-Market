# Running the site from the live WordPress data

Chiswick Cheese Market's current site is WordPress. WordPress already publishes its content through a
public, read-only REST API at https://www.chiswickcheesemarket.uk/wp-json/. On 20 November 2026 it
answered without a login and sent `Access-Control-Allow-Origin` for any origin, so a browser on another
site could read it too. Pages, journal posts, stallholders (the `portfolio` post type), their
categories and the media library are all there. Only the menus need a login, so the navigation is
read from the public homepage instead.

`tools/fetch-wp.py` reads that API (GET requests only, small pages, a pause between requests, a clear
User-Agent) and writes clean JSON into `data/` (committed, so the history is in git). With `--media` it can also keep local copies of the images in `snapshot/media/` (not committed); the public designs load images from the market's site instead. The designs
are static pages built from that JSON.

There are two ways to keep a static site in step with WordPress.

## 1. Nightly snapshot by a pipeline (what we recommend)

A scheduled job (for example a GitHub Action at 03:00 every night) runs `tools/fetch-wp.py`, rebuilds
the pages and republishes.

- Fast: visitors get plain static files from a CDN; no call to WordPress per visit.
- Works when WordPress is down, slow or being upgraded: the last good snapshot keeps serving.
- History in git: every night's content is a commit, so any change can be seen, compared and undone,
  and the JSON files double as an open, versioned data set.
- Safe: nothing on the public site can reach the WordPress admin; WordPress could even move behind a
  login, used only as the editing tool.
- Cost: changes appear after the next run (nightly, or on demand from a button or webhook that starts
  the same job).

## 2. The browser reads the API live

The page loads, then the browser asks `https://www.chiswickcheesemarket.uk/wp-json/wp/v2/...` for the
latest items and draws them. Their CORS settings allow this today.

- Always current: an edit in WordPress shows on the next page load.
- Depends on WordPress being up and quick for every visitor; a slow API means a slow page.
- Each visit adds load on the WordPress host, and the visitor's browser contacts the WordPress server.
- The CORS setting is the organisers' to change; if it is tightened, the live mode stops working.
- Nothing is kept: there is no history and no open data set.

A good middle path is both: serve the snapshot, and optionally refresh one small part (say, the next
market date or the latest journal post) live.

## In this demonstration

The demonstration is public, at chiswick-cheese-market.organisation.sovereignweb.site, marked on every page as
not the official site, and kept out of search engines (noindex). It uses both ideas at once:

- The words and structure come from the snapshot in `data/`, committed to git, so every refresh is a commit.
- The pictures and the home page video are not copied: every page loads them from chiswickcheesemarket.uk,
  at a size WordPress already made (`media.json` lists the sizes). If the market replaces a picture under
  the same address, the designs show the new one at once.
- Admin has a "Check the live API" button that asks their WordPress for three stallholders, live, from the
  visitor's browser.

## Rerunning the snapshot

```
python3 tools/fetch-wp.py            # data/*.json and data/api-map.json
python3 tools/build.py               # rebuilds site/ (six designs and Admin) from data/
```

Every JSON file carries `snapshot.snapshot_started`, `snapshot.snapshot_finished` (UTC) and the
`source_url` of every item on the official site.
