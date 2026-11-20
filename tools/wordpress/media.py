"""Choosing an image size from a WordPress media record, and saving a resized local copy."""
import io, os, re, urllib.parse

MAX_W = 1600

def pick_size(m):
    sizes = (m.get("media_details") or {}).get("sizes") or {}
    for k in ("1536x1536", "large", "medium_large", "full"):
        if k in sizes and sizes[k].get("width", 0) <= MAX_W:
            return sizes[k]["source_url"]
    return m.get("source_url")

def save_image(url, path, fetch):
    """fetch(url) -> bytes. Resizes to at most MAX_W wide and re-encodes to keep the copy small."""
    data = fetch(url)
    if path.endswith((".svg", ".gif")):  # vector or animated: keep as is
        with open(path, "wb") as f:
            f.write(data)
        return None, None
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)))
        fmt = "PNG" if path.endswith(".png") else "JPEG"
        if fmt == "JPEG" and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, fmt, **({"quality": 80, "optimize": True, "progressive": True} if fmt == "JPEG" else {"optimize": True}))
        data = buf.getvalue()
        w, hgt = im.width, im.height
    except Exception:
        w = hgt = None
    with open(path, "wb") as f:
        f.write(data)
    return w, hgt

def local_name(mid, url):
    base = os.path.basename(urllib.parse.urlparse(url).path)
    stem, ext = os.path.splitext(base)
    ext = {".png": ".png", ".svg": ".svg", ".gif": ".gif"}.get(ext.lower(), ".jpg")
    stem = re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-")[:60]
    return f"{mid}-{stem}{ext}"

