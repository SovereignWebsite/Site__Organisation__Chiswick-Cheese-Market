"""Navigation from a WordPress page's HTML.

The REST API's /menus endpoints need a login, but every theme prints its menus as nested
<ul class="menu ..."><li class="menu-item ..."><a href>...</a><ul class="sub-menu">...</ul></li></ul>.
This reads that structure with the standard library's HTML parser.
"""
from html.parser import HTMLParser
import re


class _Menu(HTMLParser):
    def __init__(self, ul_marker):
        super().__init__(convert_charrefs=True)
        self.marker, self.depth, self.inside = ul_marker, 0, False
        self.root = {"children": []}
        self.stack = [self.root]
        self.cur = None
        self.in_a = False
        self.done = False

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "ul":
            if not self.inside and self.marker in (a.get("id", "") + " " + cls):
                self.inside, self.depth = True, 1
                return
            if self.inside:
                self.depth += 1
                if self.cur is not None:
                    self.cur.setdefault("children", [])
                    self.stack.append(self.cur)
        elif self.inside and tag == "li":
            self.cur = {"label": "", "url": None}
            self.stack[-1]["children"].append(self.cur)
        elif self.inside and tag == "a" and self.cur is not None and not self.cur["label"]:
            href = a.get("href")
            self.cur["url"] = None if href in (None, "#") else href
            self.in_a = True

    def handle_endtag(self, tag):
        if not self.inside or self.done:
            return
        if tag == "a":
            self.in_a = False
        elif tag == "ul":
            self.depth -= 1
            if self.depth == 0:
                self.done = True
            elif len(self.stack) > 1:
                self.cur = self.stack.pop()

    def handle_data(self, data):
        if self.in_a and self.cur is not None:
            self.cur["label"] = (self.cur["label"] + " " + data).strip()


def menu_from_html(page_html, ul_marker="menu-primary-inner", skip=("search",)):
    p = _Menu(ul_marker)
    p.feed(page_html)

    def tidy(items):
        out = []
        for i in items:
            if not i.get("label") or i["label"].lower() in skip:
                continue
            item = {"label": re.sub(r"\s+", " ", i["label"]), "url": i.get("url")}
            if i.get("children"):
                item["children"] = tidy(i["children"])
            out.append(item)
        return out
    return tidy(p.root["children"])


def social_links(page_html):
    return sorted(set(re.findall(r'href="(https?://(?:www\.)?(?:instagram|facebook|x|twitter|tiktok|threads)\.(?:com|net)/[^"]+)"', page_html)))
