# The six designs: how each one is laid out

All six are drawn from the same data (`data/`) by one generator (`tools/build.py`), with the same routes, so
"Choose a design" keeps your place. What differs is the layout of each page type, not only colour and type.

| Design | The idea | Home | Stallholders | One stallholder |
|---|---|---|---|---|
| 1 The current site | A faithful copy of chiswickcheesemarket.uk, from its own data | The live site's builder rows, in its palette: video header, tilted marquee band, cards, market dates | Category chips, then a grid per category | Yellow text half beside the photograph, previous and next with round thumbnails |
| 2 Journal | A newspaper front page | Masthead with dateline and next market; lead story and a "Latest" column; the market's words set as a feature; a calendar strip; an A to Z index of stallholders | A contents line, then rows per category: thumbnail, name, first lines | A long-read: kicker, headline, photograph, drop cap |
| 3 Poster | One long stacked market poster | The site's tagline in giant condensed type beside a rotated "next market" sticker; a 12-box year calendar with past dates struck through; stalls by kind as big counted boxes and a run-on list of every name; numbered features; the journal as a type list | A giant type index per category, photos in greyscale until hovered | Split poster: photograph against a huge name |
| 4 Cellar | A tasting menu in a cheese cave | Full-bleed photograph with a veil; a short centred welcome; chapters numbered I, II with photo mosaics; makers as portrait cards; market days as a two-column list | Chapters per category with portrait cards | A full-height portrait beside the text |
| 5 The makers | An app built around the stallholders | Next-market pill, the counts, the most recently added stalls; a live finder (search box and category chips, no page reload); a note on what the data does not hold yet | The same finder | Their photograph and card, every journal post that mentions them (found in the data), similar stalls; a bottom tab bar on phones |
| 6 The data | The data itself | Hero numbers, a query tool that shows the same question as a live API address, inline SVG charts with tables | (links to Design 1) | (links to Design 1) |

Admin (`/admin/`) and Buttercup (`/buttercup/`) are shared by all six.
