"""HTML helpers for WordPress content: plain text, cleaned semantic HTML, and the images a body uses."""
import html, re
from html.parser import HTMLParser

VOID = {"br", "img"}


class _Balancer(HTMLParser):
    """Re-serialises a fragment so every tag is closed in order: stray closing tags are dropped,
    tags left open are closed. (Page-builder shortcodes sit inside <p>, so cutting at them leaves halves.)"""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        a = "".join(f' {k}="{html.escape(v or "", quote=True)}"' for k, v in attrs)
        if tag == "p" and "p" in self.stack:  # a <p> cannot hold a <p>
            self.handle_endtag("p")
        self.out.append(f"<{tag}{a}>")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID or tag not in self.stack:
            return
        while self.stack:
            t = self.stack.pop()
            self.out.append(f"</{t}>")
            if t == tag:
                break

    def handle_data(self, d):
        self.out.append(d)

    def handle_entityref(self, n):
        self.out.append(f"&{n};")

    def handle_charref(self, n):
        self.out.append(f"&#{n};")


def balance(h):
    b = _Balancer()
    b.feed(h or "")
    b.close()
    return "".join(b.out) + "".join(f"</{t}>" for t in reversed(b.stack))

def text(s):
    """HTML fragment -> plain text."""
    s = re.sub(r"<br\s*/?>", "\n", s or "")
    s = re.sub(r"</p>\s*<p[^>]*>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t]+", " ", html.unescape(s)).strip()

ALLOWED = {"p", "strong", "b", "em", "i", "a", "ul", "ol", "li", "h2", "h3", "h4", "h5", "h6", "br", "blockquote", "figure", "figcaption", "img"}

def clean_html(s, media_map=None):
    """Keep simple semantic HTML; drop scripts, styles, classes and lazy-load noise."""
    s = s or ""
    s = re.sub(r"<noscript>.*?</noscript>", "", s, flags=re.S)
    s = re.sub(r"<(script|style|iframe|form)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    def img(m):
        tag = m.group(0)
        src = re.search(r'data-src="([^"]+)"', tag) or re.search(r'\ssrc="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        wid = re.search(r"wp-image-(\d+)", tag)
        src = src.group(1) if src else ""
        if src.startswith("data:"):
            return ""
        attrs = f'src="{src}" alt="{alt.group(1) if alt else ""}"'
        if wid:
            attrs += f' data-media-id="{wid.group(1)}"'
        return f"<img {attrs}>"
    s = re.sub(r"<img[^>]*>", img, s)
    def tag(m):
        closing, name, rest = m.group(1), m.group(2).lower(), m.group(3)
        if name not in ALLOWED:
            return ""
        if name == "a" and not closing:
            href = re.search(r'href="([^"]*)"', rest)
            return f'<a href="{href.group(1) if href else "#"}">'
        if name == "img":
            return m.group(0)
        return f"<{closing}{name}>"
    s = re.sub(r"<(/?)([a-zA-Z0-9]+)([^>]*)>", tag, s)
    s = balance(s)
    s = re.sub(r"<p>\s*(&nbsp;)?\s*</p>", "", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()

def content_media(h):
    return {int(x) for x in re.findall(r"wp-image-(\d+)", h or "")}

def content_urls(h):
    """Images shown in a body that carry no attachment id (one URL per image, not every srcset size)."""
    out = set()
    for tag in re.findall(r"<img [^>]+>", clean_html(h)):
        if "data-media-id" in tag:
            continue
        m = re.search(r'src="(https?://www\.chiswickcheesemarket\.uk/wp-content/uploads/[^"]+)"', tag)
        if m:
            out.add(m.group(1))
    return out

