# Site__Organisation__Chiswick-Cheese-Market

chiswick-cheese-market.organisation.sovereignweb.site: **a demonstration by Sovereign Website for Chiswick Cheese Market. Not the official site**, which is https://www.chiswickcheesemarket.uk.

The market's own content, read from its WordPress site through the public REST API (GET requests only), drawn six ways. WordPress stays exactly as it is; these are new front ends on the same content.

| | |
|---|---|
| `site/designs/1` | The current site: a close copy, built from its own data |
| `site/designs/2` | Journal: editorial, magazine style |
| `site/designs/3` | Poster: bold market-poster type |
| `site/designs/4` | Cellar: dark and warm (parchment in light mode) |
| `site/designs/5` | The makers: built around the stallholders |
| `site/designs/6` | The data: the JSON, a query tool, charts |
| `site/admin` | The WordPress viewer and parser: API map, raw data, parser, charts, dead links |
| `site/buttercup` | Buttercup the cow, from the market's own pictures and journal |

Pictures and the home page video load from chiswickcheesemarket.uk at sizes WordPress already made; none are copied here. Fonts are self-hosted and openly licensed (SIL OFL). No cookies, no tracking, no third-party scripts; every page is `noindex`.

## How it is made

```
python3 tools/fetch-wp.py      # read the WordPress API into data/ (raw responses in data/raw/, API map in data/api-map.json)
python3 tools/check-links.py   # find dead links in their content: data/dead-links.json
python3 tools/build.py         # build site/ from data/
node tools/thumbs.js && python3 tools/thumbs.py   # the "Choose a design" thumbnails, after a design changes
python3 tests/test_wordpress.py
```

`tools/wordpress/` is a small, reusable toolkit for any WordPress site: see `docs/wordpress-toolkit.md`. How the site keeps in step with WordPress: `docs/live-data.md`.
