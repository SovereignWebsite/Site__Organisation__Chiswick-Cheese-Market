"""A small, dependency-light toolkit for reading a WordPress site read-only and turning it into
clean JSON that any static design can be built from.

  client      gentle GET-only REST client (paging, pauses, retries, raw cache for offline rebuilds)
  shortcodes  WPBakery / Uncode page-builder shortcodes -> plain blocks
  html_clean  plain text, cleaned semantic HTML, images used in a body
  menus       navigation from the public homepage (the menus API needs a login)
  media       image size choice and resized local copies
  snapshot    a generic snapshot of pages, posts, any custom post type and taxonomy, and media

Nothing here logs in or writes to WordPress. Apache-2.0.
"""
