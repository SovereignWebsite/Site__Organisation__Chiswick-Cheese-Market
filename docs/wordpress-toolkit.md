# The WordPress toolkit (tools/wordpress)

A small Python package, standard library plus Pillow (only for optional image copies), that reads any WordPress
site read-only and turns it into clean JSON a static design can be built from. Dinis Cruz, 20 Nov 2026: "even if
somebody doesn't change the backend from WordPress, the fact that we can skin a WordPress website and give them
5 variations of the same skin without touching the website is actually a very good transition."

| Module | What it does |
|---|---|
| `client.py` | Gentle GET-only REST client: small pages, a pause between requests, retries, a clear User-Agent. Keeps every raw response so the JSON can be rebuilt offline (`from_raw`). Discovers post types and taxonomies instead of guessing. |
| `shortcodes.py` | WPBakery / Uncode page-builder shortcodes, which the API returns raw, with "curled" quotes: straightened, parsed into a tree, flattened into plain blocks (section, column, heading, text, button, image, gallery, listing). Unknown shortcodes are unwrapped, so other themes degrade gracefully. |
| `html_clean.py` | Plain text, cleaned semantic HTML (no classes, scripts, lazy-load noise), balanced tags, the images a body uses. |
| `menus.py` | Navigation from the public homepage HTML (the menus API needs a login). |
| `media.py` | Picks an image size from a media record; optional resized local copies. |
| `snapshot.py` | A generic snapshot: site index, post types, items, taxonomies, menus, the theme's page header, only the media used. |
| `probe.py` | The API map: every namespace and route declared; core collections tested with one GET each (status, count, CORS). Plugin routes are listed, never called. |

Chiswick's configuration is `tools/fetch-wp.py` (about 100 lines): the base URL, the post types to read
(`portfolio` becomes `exhibitors`), the menus to read, the pages to skip.

Rules it keeps: GET only; never logs in; never calls a write endpoint or a plugin route; small pages and pauses.

## Next steps worth doing

- One extra field per stallholder in WordPress (their website, Instagram, where they farm) would let the designs
  link straight to the makers, map them, and later show the makers' own news beside the market's.
- A nightly GitHub Action: `fetch-wp.py`, `build.py`, commit, publish. Every change to the market's content then
  becomes a commit.
