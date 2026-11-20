"""WPBakery / Uncode page-builder shortcodes -> a small tree -> plain, theme-free blocks.

The REST API returns page-builder pages as raw shortcodes ([vc_row][vc_column]...), with the quotes
inside them "texturised" by WordPress. This module undoes that, parses the shortcodes into a tree and
flattens it into blocks any template can draw:

  section{background, background_image, blocks} > column{width, background_image, blocks} >
  heading{level,text,style,inline_images} | text{html} | button{text,url} | image{media,url} |
  gallery{media[]} | listing{post_type} | embed | form | html{html}

Unknown shortcodes are unwrapped (their children are kept), so a new theme degrades gracefully.
"""
import html, re, urllib.parse
from .html_clean import text, clean_html

QUOTES = {"”": '"', "“": '"', "″": '"', "′": "'", "’": "'", "‘": "'"}

def normalise_shortcodes(raw):
    s = raw
    # WordPress "texturises" the quotes inside shortcode attributes; undo that only inside [...]
    def fix(m):
        t = html.unescape(m.group(0))
        for k, v in QUOTES.items():
            t = t.replace(k, v)
        return t
    s = re.sub(r"\[[a-z_]+[^\]]*\]", fix, s)
    s = s.replace('<div class="wpb-content-wrapper">', "")
    return s

SC = re.compile(r"\[(/?)([a-z_]+)((?:\s+[a-z_0-9-]+=\"[^\"]*\")*)\s*(/?)\]")
ATTR = re.compile(r'([a-z_0-9-]+)="([^"]*)"')
SELF_CLOSING = {"vc_empty_space", "vc_single_image", "uncode_index", "vc_separator",
                "uncode_inline_image", "vc_gallery", "uncode_author_profile", "vc_icon", "uncode_list", "vc_video"}

def parse_shortcodes(s):
    """Returns a tree: {'tag','attrs','children':[node|str]}."""
    root = {"tag": "root", "attrs": {}, "children": []}
    stack = [root]
    pos = 0
    for m in SC.finditer(s):
        if m.start() > pos:
            stack[-1]["children"].append(s[pos:m.start()])
        pos = m.end()
        closing, name, attrs = m.group(1), m.group(2), dict(ATTR.findall(m.group(3)))
        if closing:
            # pop to the matching open tag if there is one
            for i in range(len(stack) - 1, 0, -1):
                if stack[i]["tag"] == name:
                    del stack[i:]
                    break
            continue
        node = {"tag": name, "attrs": attrs, "children": []}
        stack[-1]["children"].append(node)
        if not (m.group(4) or name in SELF_CLOSING):
            stack.append(node)
    stack[-1]["children"].append(s[pos:])
    return root

def inner_html(node):
    out = []
    for c in node["children"]:
        out.append(c if isinstance(c, str) else inner_html(c))
    return "".join(out)

def link_attr(v):
    """vc link='url:...|title:...|target:...' -> (url, title)."""
    parts = dict(p.split(":", 1) for p in v.split("|") if ":" in p)
    return urllib.parse.unquote(parts.get("url", "")), urllib.parse.unquote(parts.get("title", ""))

def ids(v):
    return [int(x) for x in re.findall(r"\d+", v or "")]

def blocks_from_tree(node, media_ids, out=None, bg=None):
    """Flatten builder markup into a list of simple blocks, grouped by row ('section')."""
    if out is None:
        out = []
    for c in node["children"]:
        if isinstance(c, str):
            t = clean_html(c)
            if text(t):
                out.append({"type": "html", "html": t})
            continue
        tag, a = c["tag"], c["attrs"]
        if tag in ("vc_row",):
            sec = {"type": "section", "background": a.get("back_color", ""), "blocks": []}
            if a.get("back_image"):
                sec["background_image"] = int(ids(a["back_image"])[0]); media_ids.update(ids(a["back_image"]))
            blocks_from_tree(c, media_ids, sec["blocks"])
            if sec["blocks"] or sec.get("background_image"):
                out.append(sec)
        elif tag in ("vc_column", "vc_column_inner", "vc_row_inner"):
            col = {"type": "column", "width": a.get("width", "1/1"), "blocks": []}
            if a.get("back_image"):
                col["background_image"] = ids(a["back_image"])[0]; media_ids.update(ids(a["back_image"]))
            blocks_from_tree(c, media_ids, col["blocks"])
            if col["blocks"] or col.get("background_image"):
                out.append(col)
        elif tag == "vc_custom_heading":
            t = text(re.sub(r"\[[^\]]+\]", "", inner_html(c)))
            b = {"type": "heading", "level": a.get("heading_semantic", "h2"), "text": t}
            if a.get("medias"):
                b["inline_images"] = ids(a["medias"]); media_ids.update(ids(a["medias"]))
            if "marquee" in a.get("css_alt_animation", ""):
                b["style"] = "marquee"
            if t or b.get("inline_images"):
                out.append(b)
        elif tag == "vc_column_text":
            h = clean_html(re.sub(r"\[[^\]]+\]", "", inner_html(c)))
            if text(h):
                out.append({"type": "text", "html": h})
        elif tag == "vc_button":
            url, title = link_attr(a.get("link", ""))
            out.append({"type": "button", "text": text(inner_html(c)) or title, "url": url})
        elif tag == "vc_single_image":
            for i in ids(a.get("media", "")):
                media_ids.add(i)
                b = {"type": "image", "media": i}
                if a.get("link"):
                    b["url"] = link_attr(a["link"])[0] if "url:" in a["link"] else a["link"]
                out.append(b)
        elif tag == "vc_gallery":
            g = ids(a.get("medias", ""))
            media_ids.update(g)
            if g:
                out.append({"type": "gallery", "media": g})
        elif tag == "uncode_vertical_text":
            t = text(re.sub(r"\[[^\]]+\]", "", a.get("text", "") or inner_html(c)))
            if t:
                out.append({"type": "heading", "level": "h2", "text": t, "style": "vertical"})
        elif tag == "uncode_index":
            loop = dict(x.split(":", 1) for x in a.get("loop", "").split("|") if ":" in x)
            b = {"type": "listing", "post_type": loop.get("post_type") or a.get("post_type", "post"),
                 "note": "a live list of posts or stallholders, built from posts.json / exhibitors.json"}
            if loop.get("categories"):
                b["categories"] = ids(loop["categories"])
            if loop.get("size", "").isdigit():
                b["size"] = int(loop["size"])
            if loop.get("order_by"):
                b["order_by"] = loop["order_by"]
            out.append(b)
        elif tag == "vc_raw_html":
            out.append({"type": "embed", "note": "third-party embed (newsletter form or feed) not copied"})
        elif tag == "contact-form-7":
            out.append({"type": "form", "note": "contact form on the official site"})
        elif tag in ("vc_empty_space", "vc_separator", "uncode_inline_image"):
            continue
        else:
            blocks_from_tree(c, media_ids, out)
    return out

def page_blocks(raw, media_ids):
    if "[vc_row" not in raw:
        return [{"type": "text", "html": clean_html(raw)}]
    return blocks_from_tree(parse_shortcodes(normalise_shortcodes(raw)), media_ids)

