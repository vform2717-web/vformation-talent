"""Build the public talent site (GitHub Pages) from people's card data.
Usage: python3 -I build_site.py <manifest.json> <site_dir> [--all] [--domain talent.vformationconsulting.com]

manifest.json: [{"data": "path/data.json", "headshot": "path.jpg", "photos": ["p1.jpg", ...], "videos": ["v1.mp4", ...]}]
Only profiles whose status is "Ready for outreach" are published unless --all is passed.
Output: <site>/index.html (roster), <site>/<slug>/index.html + <slug>.pdf + photo.jpg + photos/,
        <site>/api/talent.json, <site>/api/<slug>.json, <site>/embed.js, <site>/embed.html, CNAME, .nojekyll
"""
import hashlib, html, json, os, re, shutil, subprocess, sys, tempfile, datetime
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
ALL = "--all" in sys.argv
DOMAIN = "talent.vformationconsulting.com"
if "--domain" in sys.argv:
    DOMAIN = sys.argv[sys.argv.index("--domain") + 1]
    args = [a for a in args if a != DOMAIN]
manifest_path, site = args[0], args[1]
manifest = json.load(open(manifest_path, encoding="utf-8"))
BASE = f"https://{DOMAIN}/"
e = lambda s: html.escape(str(s or ""), quote=True)
slugify = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

PUBLIC_KEYS = ["name", "type", "headline", "location", "formats", "ctaLabel", "summary", "highlights", "tags", "topics",
               "talks", "audiences", "proof", "events", "testimonials", "books", "ventures", "links", "videos", "press",
               "collabWant", "collabOffer", "collabMeet", "showcaseLink", "titles",
               "bookingAgency", "bookingAgent", "bookingPhone", "bookingEmail", "bookingUrl"]


def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()


def save_jpg(src, dst, long_side):
    im = Image.open(src)
    im = im.convert("RGB")
    if max(im.size) > long_side:
        im.thumbnail((long_side, long_side), Image.LANCZOS)
    im.save(dst, "JPEG", quality=86, optimize=True, progressive=True)


def link_parts(line):
    if "|" in line:
        a, b = line.split("|", 1)
        return a.strip(), b.strip()
    return line.strip(), ""


os.makedirs(site, exist_ok=True)
for name in os.listdir(site):  # rebuild cleanly, keep .git
    if name in (".git", "README.md", "tools", "site.json"):
        continue
    p = os.path.join(site, name)
    shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(os.path.join(site, "api"))

roster = []
skipped = []
for item in manifest:
    data = json.load(open(item["data"], encoding="utf-8"))
    if not ALL and data.get("status") != "Ready for outreach" and not item.get("live"):
        skipped.append(data["name"])
        continue
    slug = slugify(data["name"])
    d = os.path.join(site, slug)
    os.makedirs(os.path.join(d, "photos"))
    head = item.get("headshot") or ""
    photo_url = ""
    if head:
        save_jpg(head, os.path.join(d, "photo.jpg"), 900)
        photo_url = f"{slug}/photo.jpg"
    # photos (dedupe exact copies and the headshot itself), max 10
    seen = {sha(head)} if head else set()
    rel_photos = []
    for p in item.get("photos", []):
        h = sha(p)
        if h in seen or len(rel_photos) >= 10:
            continue
        seen.add(h)
        n = len(rel_photos) + 1
        save_jpg(p, os.path.join(d, "photos", f"{n}.jpg"), 1800)
        rel_photos.append(f"photos/{n}.jpg")
    rel_videos = []
    for i, v in enumerate(item.get("videos", [])[:3]):
        src, flt = (v, "") if isinstance(v, str) else (v["src"], v.get("filter", ""))
        os.makedirs(os.path.join(d, "videos"), exist_ok=True)
        ext = os.path.splitext(src)[1] or ".mp4"
        shutil.copy(src, os.path.join(d, "videos", f"{i + 1}{ext}"))
        rel_videos.append({"src": f"videos/{i + 1}{ext}", "filter": flt})

    # brand logos: files named <asset id>.<ext> in the manifest's "assets_dir"; names alone show as wordmarks
    import glob
    brands_pub = []
    for b in (data.get("brands") or [])[:10]:
        item_b = {"name": b.get("name", "")}
        hits = glob.glob(os.path.join(item.get("assets_dir", ""), b["logo"] + ".*")) if b.get("logo") and item.get("assets_dir") else []
        if hits:
            os.makedirs(os.path.join(d, "brands"), exist_ok=True)
            ext = os.path.splitext(hits[0])[1].lower()
            dst = f"brands/{len(brands_pub) + 1}{ext}"
            shutil.copy(hits[0], os.path.join(d, dst))
            item_b["src"] = dst
        if item_b["name"]:
            brands_pub.append(item_b)
    docs_pub = []
    for x in (data.get("docs") or []):
        hits = glob.glob(os.path.join(item.get("assets_dir", ""), x.get("id", "") + ".*")) if item.get("assets_dir") and x.get("id") else []
        if hits:
            os.makedirs(os.path.join(d, "docs"), exist_ok=True)
            dst = f"docs/{len(docs_pub) + 1}{os.path.splitext(hits[0])[1].lower()}"
            shutil.copy(hits[0], os.path.join(d, dst))
            docs_pub.append({"title": x.get("title") or x.get("name", ""), "note": x.get("note", ""), "src": dst})
    pubdata = dict(data, stagePhotosPublic=rel_photos, showcasePublic=rel_videos, brandsPublic=brands_pub, docsPublic=docs_pub)
    with tempfile.TemporaryDirectory() as tmp:
        dj, ph, out = os.path.join(tmp, "d.json"), os.path.join(tmp, "h.jpg"), os.path.join(tmp, "p.html")
        json.dump(pubdata, open(dj, "w", encoding="utf-8"))
        if head:
            save_jpg(head, ph, 480)
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "build_public.py"), dj, ph if head else "", out], check=True, capture_output=True)
        subprocess.run([sys.executable, "-I", os.path.join(HERE, "export_site.py"), out, dj, os.path.join(d, "index.html")], check=True, capture_output=True)
    # canonical + social preview tags
    page = open(os.path.join(d, "index.html"), encoding="utf-8").read()
    extra = (f'<link rel="canonical" href="{BASE}{slug}/">\n<meta property="og:url" content="{BASE}{slug}/">\n'
             + (f'<meta property="og:image" content="{BASE}{photo_url}">\n' if photo_url else "")
             + f'<title>Book {e(data["name"])} | V Formation Consulting</title>\n')
    page = page.replace("<head>\n", "<head>\n" + extra, 1)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)
    subprocess.run(["node", os.path.join(HERE, "mkpdf.js"), os.path.abspath(os.path.join(d, "index.html")), os.path.abspath(os.path.join(d, f"{slug}.pdf"))], check=True, capture_output=True)

    pub = {k: data[k] for k in PUBLIC_KEYS if data.get(k)}
    pub.update({
        "slug": slug,
        "url": f"{BASE}{slug}/",
        "pdf": f"{BASE}{slug}/{slug}.pdf",
        "photo": f"{BASE}{photo_url}" if photo_url else "",
        "photos": [f"{BASE}{slug}/{p}" for p in rel_photos],
        "showcaseVideos": [dict(v, src=f"{BASE}{slug}/{v['src']}") for v in rel_videos],
        "brands": [dict(b, src=f"{BASE}{slug}/{b['src']}") if b.get("src") else b for b in brands_pub],
        "updatedAt": data.get("updatedAt", ""),
        "base": BASE,
    })
    json.dump(pub, open(os.path.join(site, "api", f"{slug}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    roster.append({k: pub.get(k, "") for k in ["slug", "name", "type", "headline", "location", "highlights", "tags", "photo", "url", "pdf", "bookingEmail", "ctaLabel"]})
    print("built", slug, len(rel_photos), "photos", len(rel_videos), "videos")

roster.sort(key=lambda r: r["name"])
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump({"base": BASE, "updated": stamp, "count": len(roster), "talent": roster}, open(os.path.join(site, "api", "talent.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
shutil.copy(os.path.join(HERE, "embed.js"), os.path.join(site, "embed.js"))
if "github.io" not in DOMAIN:
    open(os.path.join(site, "CNAME"), "w").write(DOMAIN.split("/")[0] + "\n")
open(os.path.join(site, ".nojekyll"), "w").write("")

# ---------- roster page ----------
def card(r):
    hl = (r.get("highlights") or [])[:2]
    stats = "".join(f'<li><b>{e(link_parts(h)[0])}</b> {e(link_parts(h)[1])}</li>' for h in hl)
    img = f'<img src="{e(r["slug"])}/photo.jpg" alt="{e(r["name"])}" loading="lazy">' if r.get("photo") else f'<div class="ph">{e(r["name"][:1])}</div>'
    return (f'<article class="card"><a class="img" href="{e(r["slug"])}/">{img}</a><div class="body">'
            f'<h2><a href="{e(r["slug"])}/">{e(r["name"])}</a></h2><p class="hd">{e(r["headline"])}</p>'
            f'{f"<ul class=stats>{stats}</ul>" if stats else ""}'
            f'<div class="row"><a class="btn gold" href="{e(r["slug"])}/">View profile</a><a class="btn ghost" href="{e(r["slug"])}/{e(r["slug"])}.pdf" download>PDF</a></div></div></article>')

STYLE = """:root{--ink:#1E0B33;--ink2:#2E1150;--gold:#E3B94C;--gold2:#F4D78A;--paper:#FBF8F2;--text:#1d1626;--muted:#5d5470;--card:#fff;--line:#e9e2d4}
@media (prefers-color-scheme:dark){:root{--paper:#120720;--text:#f3eefb;--muted:#b9aecb;--card:#1c0d30;--line:#33204d}}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--paper);color:var(--text)}
a{color:inherit}.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
header{background:linear-gradient(160deg,var(--ink),var(--ink2));color:#fff;padding:56px 0 48px}
.vlogo{display:inline-flex;align-items:center;gap:12px;text-decoration:none;color:#E3B94C}.vlogo .vmark{width:46px;height:34px}.vword{display:flex;flex-direction:column;line-height:1}.vword b{font-family:var(--f-display,Inter,system-ui,sans-serif);font-size:20px;letter-spacing:.12em;color:#fff;font-weight:800}.vword small{font-size:10.5px;letter-spacing:.42em;color:#E3B94C;font-weight:700;margin-top:4px}.vtop{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.vrep{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--band-muted,#C4B3DA);font-weight:600}
header .eyebrow{color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-size:12px;font-weight:700;margin:0 0 18px}
header h1{font-size:clamp(30px,5vw,48px);line-height:1.1;margin:0 0 12px;letter-spacing:-.02em}header p{max-width:640px;color:#e6dcf5;margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px;padding:36px 0 56px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 8px 24px rgba(30,11,51,.07)}
.card .img{display:block;aspect-ratio:1/1;background:var(--ink)}.card img{width:100%;height:100%;object-fit:cover;display:block}
.ph{display:grid;place-items:center;height:100%;color:var(--gold);font-size:64px;font-weight:800}
.body{padding:18px;display:flex;flex-direction:column;gap:8px;flex:1}.body h2{margin:0;font-size:21px}.body h2 a{text-decoration:none}
.hd{margin:0;color:var(--muted);font-size:14.5px}.stats{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:4px;font-size:13.5px;color:var(--muted)}
.stats b{color:var(--text)}.row{display:flex;gap:8px;margin-top:auto;padding-top:10px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 16px;border-radius:999px;font-weight:700;font-size:14px;text-decoration:none}
.gold{background:var(--gold);color:var(--ink)}.ghost{border:1.5px solid var(--line)}
footer{border-top:1px solid var(--line);padding:24px 0;color:var(--muted);font-size:14px}"""

agent = next((json.load(open(i["data"]))  for i in manifest), {})
contact = agent.get("bookingEmail", "")
index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Talent roster | V Formation Consulting</title>
<meta name="description" content="Speakers, athletes and leaders represented by V Formation Consulting. Book them for your next event.">
<link rel="canonical" href="{BASE}"><style>{STYLE}</style></head><body>
<header><div class="wrap"><p class="eyebrow"><a class="vlogo" href="https://vformationconsulting.com/" target="_blank" rel="noopener" aria-label="V Formation Consulting"><svg class="vmark" viewBox="0 0 30 22" aria-hidden="true"><g fill="currentColor"><circle cx="15" cy="19" r="2.6"/><circle cx="10.2" cy="13.4" r="2.2"/><circle cx="19.8" cy="13.4" r="2.2"/><circle cx="6" cy="8" r="1.9"/><circle cx="24" cy="8" r="1.9"/><circle cx="2.4" cy="3" r="1.6"/><circle cx="27.6" cy="3" r="1.6"/></g></svg><span class="vword"><b>V FORMATION</b><small>CONSULTING</small></span></a></p><h1>Book our talent</h1>
<p>Speakers, athletes and leaders for keynotes, workshops, assemblies and brand partnerships.</p></div></header>
<main class="wrap"><div class="grid">{"".join(card(r) for r in roster) or "<p>New profiles are on the way.</p>"}</div></main>
<footer><div class="wrap">Booking: {f'<a href="mailto:{e(contact)}">{e(contact)}</a> · ' if contact else ""}<a href="https://vformationconsulting.com/">vformationconsulting.com</a> · <a href="embed.html">Add these profiles to your site</a></div></footer>
</body></html>
"""
open(os.path.join(site, "index.html"), "w", encoding="utf-8").write(index)

# ---------- embed instructions page ----------
first = roster[0]["slug"] if roster else "first-last"
snip_roster = f'<script src="{BASE}embed.js" async></script>\n<vformation-talent roster></vformation-talent>'
snip_one = f'<script src="{BASE}embed.js" async></script>\n<vformation-talent profile="{first}"></vformation-talent>'
snip_tag = f'<script src="{BASE}embed.js" async></script>\n<vformation-talent roster tag="KeynoteSpeaker" limit="6"></vformation-talent>'
snip_frame = f'<iframe src="{BASE}{first}/" style="width:100%;height:1600px;border:0" title="Book this speaker" loading="lazy"></iframe>'
rows = "".join(f'<tr><td>{e(r["name"])}</td><td><code>{e(r["slug"])}</code></td><td><a href="{e(r["slug"])}/">page</a> · <a href="api/{e(r["slug"])}.json">json</a></td></tr>' for r in roster)
embed = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Embed talent profiles | V Formation Consulting</title><style>{STYLE}
pre{{background:var(--ink);color:#f4ecff;padding:14px;border-radius:12px;overflow:auto;font-size:13px;white-space:pre-wrap;word-break:break-all}}
h2{{margin:34px 0 8px}}table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid var(--line);padding:8px 6px;font-size:14px}}.demo{{margin:18px 0 40px}}</style>
<script src="embed.js" async></script></head><body>
<header><div class="wrap"><p class="eyebrow"><a class="vlogo" href="https://vformationconsulting.com/" target="_blank" rel="noopener" aria-label="V Formation Consulting"><svg class="vmark" viewBox="0 0 30 22" aria-hidden="true"><g fill="currentColor"><circle cx="15" cy="19" r="2.6"/><circle cx="10.2" cy="13.4" r="2.2"/><circle cx="19.8" cy="13.4" r="2.2"/><circle cx="6" cy="8" r="1.9"/><circle cx="24" cy="8" r="1.9"/><circle cx="2.4" cy="3" r="1.6"/><circle cx="27.6" cy="3" r="1.6"/></g></svg><span class="vword"><b>V FORMATION</b><small>CONSULTING</small></span></a></p><p class="eyebrow">For web teams</p><h1>Add talent profiles to any website</h1>
<p>Paste one snippet into an HTML block (WordPress, Elementor, Squarespace, Wix, Webflow). It updates on its own whenever a profile changes.</p></div></header>
<main class="wrap">
<h2>The whole roster</h2><pre>{e(snip_roster)}</pre>
<h2>One person</h2><pre>{e(snip_one)}</pre>
<h2>Filter by tag</h2><pre>{e(snip_tag)}</pre>
<h2>Full page in a frame</h2><pre>{e(snip_frame)}</pre>
<h2>Links to share</h2><p>Every profile also has its own page and a PDF one-sheet. Data is at <a href="api/talent.json">api/talent.json</a>.</p>
<table>{rows}</table>
<h2>Preview</h2><div class="demo"><vformation-talent roster></vformation-talent></div>
</main></body></html>
"""
open(os.path.join(site, "embed.html"), "w", encoding="utf-8").write(embed)
print("roster", len(roster), "skipped (not ready):", ", ".join(skipped) or "none")
