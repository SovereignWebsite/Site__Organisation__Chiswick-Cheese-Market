"""Tests for tools/wordpress. Run: python3 -m pytest tests  (or python3 tests/test_wordpress.py)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from wordpress.shortcodes import page_blocks, parse_shortcodes, normalise_shortcodes, link_attr
from wordpress.html_clean import text, clean_html, content_media
from wordpress.menus import menu_from_html

RAW = ('<div class="wpb-content-wrapper"><p>[vc_row back_color=”color-690767″][vc_column width=”1/2″]'
       '[vc_custom_heading heading_semantic=”h1″]The UK’s only specialist cheese market[/vc_custom_heading]'
       '[vc_column_text]<strong>Every third Sunday</strong>[/vc_column_text]'
       '[vc_button link=”url:https%3A%2F%2Fexample.org%2Fvisit-us%2F|title:Getting%20here”]Getting here[/vc_button]'
       '[/vc_column][vc_column width=”1/2″ back_image=”2908″][vc_single_image media=”3209″][/vc_column][/vc_row]'
       '[vc_row][vc_column][uncode_vertical_text]2026 Market Dates[/uncode_vertical_text][uncode_index post_type=”portfolio”][/vc_column][/vc_row]</p></div>')


def test_blocks():
    ids = set()
    b = page_blocks(RAW, ids)
    assert b[0]["type"] == "section" and b[0]["background"] == "color-690767"
    left, right = b[0]["blocks"]
    assert left["width"] == "1/2"
    kinds = [x["type"] for x in left["blocks"]]
    assert kinds == ["heading", "text", "button"], kinds
    assert left["blocks"][0]["text"] == "The UK’s only specialist cheese market"
    assert left["blocks"][2] == {"type": "button", "text": "Getting here", "url": "https://example.org/visit-us/"}
    assert right["background_image"] == 2908 and right["blocks"][0] == {"type": "image", "media": 3209}
    assert {2908, 3209} <= ids
    second = b[1]["blocks"][0]["blocks"]
    assert second[0]["style"] == "vertical" and second[0]["text"] == "2026 Market Dates"
    assert second[1]["type"] == "listing" and second[1]["post_type"] == "portfolio"


def test_link_attr():
    assert link_attr("url:https%3A%2F%2Fa.b%2F|title:Hi%20there|target:_blank") == ("https://a.b/", "Hi there")


def test_clean_html_keeps_semantics_drops_noise():
    h = ('<p class="x" style="y">Hi <strong>there</strong> <a href="https://a.b/" class="c">link</a></p>'
         '<script>alert(1)</script><img src="data:image/gif;base64,AA" data-src="https://s/x-225x300.jpg" class="wp-image-12" alt="A">'
         '<noscript><img src="https://s/x.jpg"></noscript>')
    c = clean_html(h)
    assert "<script" not in c and "class=" not in c and "style=" not in c and "noscript" not in c
    assert '<a href="https://a.b/">link</a>' in c
    assert '<img src="https://s/x-225x300.jpg" alt="A" data-media-id="12">' in c
    assert content_media(h) == {12}
    assert text("<p>A &amp; B</p><p>C</p>") == "A & B\n\nC"


def test_balance():
    from wordpress.html_clean import balance
    assert balance("Hi</p><p>there <strong>you") == "Hi<p>there <strong>you</strong></p>"
    assert clean_html("<p>a<p>b</p>") == "<p>a</p><p>b</p>"


def test_menu():
    h = ('<ul id="menu-main" class="menu"><li class="menu-item menu-item-has-children"><a href="#">About</a>'
         '<ul class="sub-menu"><li class="menu-item"><a href="/story/">Our story</a></li><li><a href="/team/">Team</a></li></ul></li>'
         '<li class="menu-item"><a href="/news/">News</a></li><li><a href="#">Search</a></li></ul><ul id="other"><li><a href="/x">X</a></li></ul>')
    assert menu_from_html(h, "menu-main") == [
        {"label": "About", "url": None, "children": [{"label": "Our story", "url": "/story/"}, {"label": "Team", "url": "/team/"}]},
        {"label": "News", "url": "/news/"}]


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
