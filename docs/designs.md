# The six designs

All six are drawn from the same data (`data/`) by one generator (`tools/build.py`), with the same routes, so
"Choose a design" keeps your place. Dinis Cruz, 20 Nov 2026: each extra design needs "its own centre of gravity,
focus, UX and design". Pass 1 of the design rounds (design.b.rounds, with design.b) set these.

## 1 The current site
- Centre: the market as it presents itself today. Focus: the video header and "The UK's only specialist cheese market". Primary action: Getting here.
- A faithful copy of chiswickcheesemarket.uk from its own data; only accessibility fixes.

## 2 The Market Paper
- Centre: the news. Focus: the lead story. Primary action: read the lead (and, beside it, "The next market" box with date, hours, address and Getting here).
- Masthead between rules with a dateline naming the next market; a three-column front (lead, Latest, the next market); the market's words in two columns with a drop cap; market days as a listings box; the stallholders as classifieds. On phones the next market box comes straight after the masthead.

## 3 The Poster Wall
- Centre: the next market as an event. Focus: the date, huge. Primary action: Add to calendar (a .ics file made at build time from the site's own date, hours and address).
- Then the market's own posters (`data/posters.json`): the next market's poster full width, the year's posters pasted up whole and slightly turned, last year's as a small greyed strip. Still images on the wall; the animated GIF only on request, with its size. Then the year's calendar, the kinds of stall, the journal.

## 4 The Cave
- Centre: the cheese and the makers. Focus: the first shelf. Primary action: open a maker.
- Dark in both modes. A welcome band with no photograph behind the text; then one shelf per kind of stall, every maker a round portrait with a gold label on a wooden ledge (on phones each shelf scrolls sideways, as its own labelled region); tasting notes as parchment cards. Each maker's page ends with "On the same shelf".

## 5 The Makers (the organisers' favourite in the synthetic-user run)
- Centre: the stallholders. Focus: the finder, in the first screen. Primary action: find a stall (search, or a counted kind of stall).
- List or Map: the Map is rows by kind with the real counts, labelled "Drawn by category, not the real stall plan". Each maker's page lists every journal post that names them, and similar stalls. A bottom tab bar on phones.

## 6 The data
- Centre: the data itself. Focus: the numbers and the query tool. Primary action: ask the data (filter and search), with the same question shown as a live WordPress API address.

Admin (`/admin/`) and Buttercup (`/buttercup/`) are shared by all six.
