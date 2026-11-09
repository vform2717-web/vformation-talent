"""Build the public booking page for a talent from the editable card's data JSON.
Usage: python3 -I build_public.py <data.json> <headshot.jpg or ''> <out.html>
"""
import base64, html, json, re, sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
photo_path = sys.argv[2]
out = sys.argv[3]
e = lambda s: html.escape(str(s or ""), quote=True)


def href(u):
    u = str(u or "").strip()
    if not u:
        return ""
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u.lstrip("/")
    return u if re.match(r"^https?://[^\s\"'<>]+$", u, re.I) else ""


def split_link(line):
    i = line.rfind("|")
    label, url = (line, "") if i < 0 else (line[:i].strip(), line[i + 1:].strip())
    title, note = label, ""
    c = label.find(": ")
    if 0 < c < 60:
        title, note = label[:c], label[c + 2:]
    return title, note, href(url)


def links_html(items):
    out = []
    for line in items:
        t, n, u = split_link(line)
        name = f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' if u else f"<span>{e(t)}</span>"
        out.append(f'<li>{name}{f"<span class=note>{e(n)}</span>" if n else ""}</li>')
    return f'<ul class="links">{"".join(out)}</ul>'


def talk_cards(items):
    cards = []
    for line in items:
        title, _, rest = line.partition(": ")
        desc, fmt = rest, ""
        m = re.search(r"[.\u201d\"]\s+((Keynote|Workshop)[^.]*\.?)\s*$", rest)
        if m:
            desc, fmt = rest[: m.start() + 1].strip(), m.group(1).rstrip(".")
        desc = desc[:1].upper() + desc[1:]
        cards.append(f'<article class="talk"><h3>{e(title)}</h3>{f"<p>{e(desc)}</p>" if desc else ""}{f"<p class=fmt>{e(fmt)}</p>" if fmt else ""}</article>')
    return f'<div class="talks">{"".join(cards)}</div>'


def ul(items, cls="list"):
    return f'<ul class="{cls}">{"".join(f"<li>{e(x)}</li>" for x in items)}</ul>'


photo = ""
if photo_path:
    b64 = base64.b64encode(open(photo_path, "rb").read()).decode()
    photo = f'<img class="photo" src="data:image/jpeg;base64,{b64}" alt="{e(data["name"])}">'

first = data["name"].split()[0]
agency, agent = data.get("bookingAgency", ""), data.get("bookingAgent", "")
phone, email, sched = data.get("bookingPhone", ""), data.get("bookingEmail", ""), href(data.get("bookingUrl", ""))
tags = data.get("tags", [])[:8]
press = [p for p in data.get("press", [])]
seen_in = [split_link(p)[0] for p in press if "press page" not in p.lower()]

def sec(title, body):
    return f'<section class="sec"><div class="sec-h"><h2>{e(title)}</h2></div>{body}</section>' if body else ""

def split(a, b):
    return f'<div class="split">{a}{b}</div>' if a and b else (a or b)

def stat(x):
    i = x.find(" | ")
    if i > 0:
        num, rest = x[:i].strip(), x[i + 3:].strip()
    else:
        m = re.search(r"\$?\d[\d,.]*\s?[MKB]?\+|\$\d[\d,.]*[MKB]?", x)
        num = m.group(0).strip() if m else ""
        rest = x[len(num):].strip() if num and x.startswith(num) else x
    return f'<li>{f"<span class=num>{e(num)}</span>" if num else ""}<span>{e(rest)}</span></li>'

pub_photos = data.get("stagePhotosPublic", [])[:10]
reel_items = pub_photos * (4 if len(pub_photos) < 3 else 2)
reel_html = (f'<div class="reel" aria-label="Photos of {e(data["name"])} speaking"><div class="reel-track">'
             + "".join(f'<img src="{e(src)}" alt="{e(data["name"]) + " speaking" if i < len(pub_photos) else ""}"{" aria-hidden=true" if i >= len(pub_photos) else ""} loading="lazy">' for i, src in enumerate(reel_items))
             + '</div></div>') if pub_photos else ""
sc_list = data.get("showcasePublic") or []
if isinstance(sc_list, str):
    sc_list = [sc_list] if sc_list else []
sc_list, sc_link = sc_list[:3], href(data.get("showcaseLink", ""))
showcase_html = ""
if sc_list or sc_link:
    PRE = {"bright": "brightness(115%) contrast(105%)", "vivid": "contrast(115%) saturate(145%)", "warm": "sepia(28%) saturate(125%) brightness(104%)", "crisp": "contrast(125%) brightness(103%) saturate(110%)", "bw": "grayscale(100%) contrast(112%)"}
    def vtag(v):
        src, flt = (v, "") if isinstance(v, str) else (v.get("src", ""), PRE.get(v.get("filter", ""), ""))
        return f'<figure><video controls preload="metadata" playsinline src="{e(src)}"{f" style=\"filter:{flt}\"" if flt else ""}></video></figure>'
    body = (f'<div class="vids">{"".join(vtag(v) for v in sc_list)}</div>' if sc_list else "") + (f'<div><a class="btn primary" href="{e(sc_link)}" target="_blank" rel="noopener">Watch {e(first)} in action</a></div>' if sc_link else "")
    showcase_html = f'<section class="sec showcase"><div class="sec-h"><h2>See {e(first)} in action</h2></div>{body}</section>'
brand_items = data.get("brandsPublic")
if brand_items is None:
    brand_items = [{"name": b.get("name", "")} for b in (data.get("brands") or [])]
brand_items = [b for b in brand_items if b.get("name")][:10]
brands_html = ""
if brand_items:
    def btile(b, hide):
        inner = f'<img src="{e(b["src"])}" alt="{"" if hide else e(b["name"])}" loading="lazy">' if b.get("src") else f'<span>{e(b["name"])}</span>'
        return f'<li class="brand"{" aria-hidden=true" if hide else ""}>{inner}</li>'
    half = []
    while len(half) < 7:
        half += brand_items
    btitle = (data.get("titles") or {}).get("brands") or f"Brands {first} has worked with"
    brands_html = (f'<section class="sec"><div class="sec-h"><h2>{e(btitle)}</h2></div>'
                   f'<div class="brands" aria-label="{e(btitle)}"><ul class="brand-track">'
                   + "".join(btile(b, i >= len(brand_items)) for i, b in enumerate(half)) + "".join(btile(b, True) for b in half)
                   + f'</ul></div><p class="brand-print">{" · ".join(e(b["name"]) for b in brand_items)}</p></section>')
TT = {**{'talks': 'Keynotes & workshops', 'audiences': "Who it's for", 'proof': 'Track record', 'events': 'Stages', 'testimonials': 'What people say', 'press': 'Press, interviews & podcasts', 'videos': 'Watch', 'books': 'Books & projects', 'ventures': 'Companies'}, **(data.get("titles") or {})}
ckeys = [("collabWant", "Looking for"), ("collabOffer", "Can offer"), ("collabMeet", "Would like to meet")]
collab_html = ""
if any(data.get(k) for k, _ in ckeys):
    cards = "".join(f'<div class="ccard"><h3>{l}</h3>{ul(data[k])}</div>' for k, l in ckeys if data.get(k))
    collab_html = sec("How we can work together", f'<div class="collab">{cards}</div>')
aud = [a.strip() for a in str(data.get("audiences", "")).split(",") if a.strip()]
glance = f"""<div class="sec-h"><h2>At a glance</h2></div><p class="lead">{e(data.get("summary"))}</p>
{f'<ul class="hl">{"".join(stat(h) for h in data.get("highlights", []))}</ul>' if data.get("highlights") else ""}
{f'<p class="seen">As seen in <b>{" · ".join(e(x) for x in seen_in)}</b></p>' if seen_in else ""}"""
blocks = [
    ("white", glance, ""),
    ("light", brands_html, ""),
    ("tint", sec(TT["talks"], talk_cards(data.get("talks", []))) + reel_html, ""),
    (None, split(sec(TT["audiences"], f'<div class="aud">{"".join(f"<span>{e(a)}</span>" for a in aud)}</div>' if aud else ""), sec(f"About {first}", f'<p class="prose">{e(data.get("bio"))}</p>' if data.get("bio") else "")), ""),
    (None, sec(TT["proof"], ul(data.get("proof", []), "list two") if data.get("proof") else ""), ""),
    (None, split(sec(TT["events"], ul(data.get("events", [])) if data.get("events") else ""), sec(TT["testimonials"], "".join(f"<blockquote>{e(t)}</blockquote>" for t in data.get("testimonials", [])))), ""),
    ("dark", sec(TT["press"], links_html(press) if press else "") + sec(TT["videos"], links_html(data.get("videos", [])) if data.get("videos") else ""), ""),
    (None, split(sec(TT["books"], links_html(data.get("books", [])) if data.get("books") else ""), sec(TT["ventures"], links_html(data.get("ventures", [])) if data.get("ventures") else "")), ""),
    (None, collab_html, ""),
    (None, sec(f"Find {first} online", links_html(data.get("links", [])).replace('class="links"', 'class="links pills"') if data.get("links") else ""), ""),
    ("tint", showcase_html, ""),
]
pdf_name = re.sub(r"[^a-z0-9]+", "-", data["name"].lower()).strip("-") + ".pdf"
subject_q = "Booking%20inquiry%3A%20" + "%20".join(data["name"].split())
contact_rows = []
if agent or agency:
    contact_rows.append(f'<div class="crow"><span class="lab">Agent</span><span>{e(agent)}{", " if agent and agency else ""}{e(agency)}</span></div>')
if phone:
    contact_rows.append(f'<div class="crow"><span class="lab">Phone</span><span class="sel">{e(phone)}</span><button class="btn small" data-copy="{e(phone)}">Copy</button></div>')
if email:
    contact_rows.append(f'<div class="crow"><span class="lab">Email</span><span class="sel">{e(email)}</span><a class="btn small gold no-print" href="mailto:{e(email)}?subject={e(subject_q)}">Email {e(agent.split()[-1] if agent else "us")}</a><button class="btn small" data-copy="{e(email)}">Copy</button></div>')

talk_titles = [t.partition(": ")[0] for t in data.get("talks", [])]

alt = 0
band_html = []
for cls, html_, id_ in blocks:
    if not html_:
        continue
    if cls is None:
        cls = "light" if alt % 2 else "white"; alt += 1
    band_html.append(f'<div class="band {cls}"><div class="wrap">{html_}</div></div>')
BANDS = "".join(band_html)
src_items = []
for line in data.get("sources") or []:
    lab, _, u = line.rpartition("|") if "|" in line else ("", "", line)
    u = href(u.strip()); lab = lab.strip()
    host_ = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", u)) if u else ""
    src_items.append(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(lab or host_)}</a> <span class="host">{e(host_)}</span></li>' if u else f"<li>{e(lab or line)}</li>")
doc_items = [x for x in (data.get("docsPublic") or []) if x.get("src")]
DOCS = (f'<div class="band light"><div class="wrap"><section class="sec"><div class="sec-h"><h2>Credentials & documents</h2></div><ul class="docs">'
        + "".join(f'<li><a href="{e(x["src"])}" target="_blank" rel="noopener">{e(x.get("title") or x.get("name") or "Document")}</a>{f"<span>{e(x.get(chr(110)+chr(111)+chr(116)+chr(101)))}</span>" if x.get("note") else ""}</li>' for x in doc_items)
        + '</ul></section></div></div>') if doc_items else ""
SOURCES = (f'<div class="band white sources-band"><div class="wrap"><section class="sec"><div class="sec-h"><h2>Sources</h2></div><ol class="sources">{"".join(src_items)}</ol></section></div></div>' if src_items else "")
page = f'''<title>Book {e(data["name"])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Layout: booking one-sheet. Full-width hero band (photo, name, headline, two booking buttons), "at a glance" with highlights, talk cards, proof, then the booking section with agent contact and an inquiry builder. */
:root{{
  --bg:#F7F4FA; --surface:#FFFFFF; --sunk:#EEE8F4; --ink:#1C1427; --muted:#5E5470; --line:#E3DCEB;
  --accent:#5B2A86; --accent-ink:#FFFFFF; --soft:#F1E9FA;
  --band:#1E0B33; --band-ink:#FBF7FF; --band-muted:#C4B3DA; --band-accent:#E3B94C; --band-line:#3E2460;
  --tint:#F4EEFB; --gold:#B8892A; --gold-hi:#E3B94C; --shadow:rgba(42,16,70,.08);
  --warn:#A35F00; --warn-soft:#FBEBD2; --good:#1D7448; --good-soft:#DDF1E6; --bad:#B0281F;
  --f-display:"Sora",ui-sans-serif,system-ui,sans-serif;
  --f-body:"IBM Plex Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --r:14px;
}}
@media (prefers-color-scheme: dark){{ :root:not([data-theme="light"]){{
  --bg:#120B1C; --surface:#1B1228; --sunk:#160E21; --ink:#F1EAF8; --muted:#AFA2C2; --line:#33264A;
  --accent:#C9A8F0; --accent-ink:#1A0F28; --soft:#2A1B40;
  --band:#0D0616; --band-ink:#F1EAF8; --band-muted:#AFA2C2; --band-accent:#E3B94C; --band-line:#3A2A55;
  --tint:#1A1030; --gold:#E3B94C; --gold-hi:#E8C463; --shadow:rgba(0,0,0,.3);
  --warn:#F0AB4A; --warn-soft:#2E2210; --good:#5BCB92; --good-soft:#12291E; --bad:#F2847A;
  color-scheme:dark }}}}
:root[data-theme="dark"]{{
  --bg:#120B1C; --surface:#1B1228; --sunk:#160E21; --ink:#F1EAF8; --muted:#AFA2C2; --line:#33264A;
  --accent:#C9A8F0; --accent-ink:#1A0F28; --soft:#2A1B40;
  --band:#0D0616; --band-ink:#F1EAF8; --band-muted:#AFA2C2; --band-accent:#E3B94C; --band-line:#3A2A55;
  --tint:#1A1030; --gold:#E3B94C; --gold-hi:#E8C463; --shadow:rgba(0,0,0,.3);
  --warn:#F0AB4A; --warn-soft:#2E2210; --good:#5BCB92; --good-soft:#12291E; --bad:#F2847A;
  color-scheme:dark }}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.55}}
body::before{{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--band)}}
h1,h2,h3{{font-family:var(--f-display);margin:0;letter-spacing:-.01em;text-wrap:balance}}
h2{{font-size:1.15rem;font-weight:600}}
h3{{font-size:.98rem;font-weight:600}}
p{{margin:0}}
a{{color:var(--accent)}}
button,input,select,textarea{{font:inherit;color:inherit}}
:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.wrap{{max-width:820px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.hero{{background:var(--band);color:var(--band-ink)}}
.hero .wrap{{padding-block:28px 30px;display:flex;flex-direction:column;gap:18px}}
.vlogo{{display:inline-flex;align-items:center;gap:12px;text-decoration:none;color:#E3B94C}}.vlogo .vmark{{width:46px;height:34px}}.vword{{display:flex;flex-direction:column;line-height:1}}.vword b{{font-family:var(--f-display,Inter,system-ui,sans-serif);font-size:20px;letter-spacing:.12em;color:#fff;font-weight:800}}.vword small{{font-size:10.5px;letter-spacing:.42em;color:#E3B94C;font-weight:700;margin-top:4px}}.vtop{{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}}.vrep{{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--band-muted,#C4B3DA);font-weight:600}}
.brandline{{display:flex;align-items:center;gap:8px;font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--band-muted);font-weight:600}}
.idrow{{display:flex;gap:20px;align-items:center;flex-wrap:wrap}}
.photo{{width:132px;height:132px;border-radius:14px;object-fit:cover;flex:none;max-width:100%}}
.idtext{{flex:1;min-width:220px;display:flex;flex-direction:column;gap:8px}}
.hero h1{{font-size:2rem;line-height:1.1;font-weight:700}}
.hero .headline{{font-size:1.05rem;color:var(--band-ink)}}
.hero .where{{color:var(--band-muted);font-size:.9rem}}
.tags{{display:flex;flex-wrap:wrap;gap:4px 10px}}
.tag{{color:var(--band-accent);font-weight:600;font-size:.84rem}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{border:1px solid var(--band-muted);color:var(--band-ink);border-radius:999px;padding:3px 10px;font-size:.8rem}}
.cta{{display:flex;gap:10px;flex-wrap:wrap}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:6px;border:1px solid var(--line);background:var(--surface);border-radius:9px;padding:9px 14px;font-size:.92rem;font-weight:600;cursor:pointer;color:var(--ink);text-decoration:none}}
.btn.primary{{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}}
.hero .btn.secondary{{background:transparent;color:var(--band-ink);border-color:var(--band-muted)}}
.btn.small{{padding:4px 10px;font-size:.8rem;font-weight:500}}
main.wrap{{padding-block:24px 56px;display:flex;flex-direction:column;gap:26px}}
.glance{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:20px;display:flex;flex-direction:column;gap:14px}}
.lead{{font-size:1.04rem;line-height:1.62;max-width:68ch}}
.hl{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:0;padding:0;list-style:none}}
.hl li{{background:var(--soft);border-radius:10px;padding:10px 12px;font-weight:500;font-size:.92rem}}
.seen{{font-size:.86rem;color:var(--muted)}}
.seen b{{color:var(--ink);font-weight:600}}
.sec{{display:flex;flex-direction:column;gap:12px}}
.prose{{max-width:68ch}}
.talks{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}}
.talk{{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:6px}}
.talk p{{font-size:.9rem}}
.talk .fmt{{color:var(--muted);font-size:.82rem;margin-top:auto}}
ul.list,ul.links{{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:7px}}
ul.list li{{padding-left:18px;position:relative;max-width:68ch}}
ul.list li::before{{content:"";position:absolute;left:3px;top:.62em;width:6px;height:6px;border-radius:2px;background:var(--accent);transform:rotate(45deg)}}
ul.links li{{display:flex;flex-direction:column;gap:1px}}
ul.links a{{font-weight:500;word-break:break-word}}
ul.links .note{{font-size:.84rem;color:var(--muted)}}
blockquote{{margin:0;padding:10px 14px;border-left:3px solid var(--accent);background:var(--surface);border-radius:0 8px 8px 0;max-width:68ch}}
.book{{background:var(--surface);border:2px solid var(--accent);border-radius:var(--r);padding:20px;display:flex;flex-direction:column;gap:16px;scroll-margin-top:16px}}
.crow{{display:flex;gap:8px 12px;align-items:center;flex-wrap:wrap;font-size:.95rem}}
.lab{{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-weight:600;min-width:52px}}
.sel{{user-select:all;font-weight:600;word-break:break-all}}
.fgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}
.fgrid .wide{{grid-column:1/-1}}
label.f{{display:flex;flex-direction:column;gap:4px;font-size:.8rem;font-weight:600;color:var(--muted);min-width:0}}
.in{{width:100%;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:8px;padding:9px 10px;font-size:.95rem;font-weight:400}}
textarea.in{{min-height:96px;resize:vertical}}
.star{{color:var(--accent)}}
.band.dark .form-card a.btn{{color:var(--ink)}}
.band.dark .form-card .btn.primary{{color:var(--accent-ink)}}
.out{{display:flex;flex-direction:column;gap:10px;background:var(--sunk);border-radius:10px;padding:14px}}
.out pre{{margin:0;white-space:pre-wrap;font-family:var(--f-body);font-size:.9rem}}
/* ---- section bands: alternating grounds, gold accent ---- */
.band{{padding-block:34px}}
.band.white{{background:var(--surface)}}
.band.light{{background:var(--bg)}}
.band.tint{{background:var(--tint)}}
.band.dark{{background:var(--band);color:var(--band-ink)}}
.band.dark .muted,.band.dark .empty,.band.dark .note,.band.dark .fmt{{color:var(--band-muted)}}
.band.dark a{{color:var(--band-accent)}}
.band.dark .btn.ghost{{color:var(--band-accent)}}
.band.dark .sform,.band.dark .form-card{{background:var(--surface);color:var(--ink)}}
.band.dark .sform a{{color:var(--accent)}}
.band > .wrap{{display:flex;flex-direction:column;gap:22px}}
.sec-h h2{{font-size:1.45rem;font-weight:700;display:flex;flex-direction:column;gap:10px}}
.sec-h h2::before{{content:"";width:34px;height:4px;border-radius:2px;background:var(--gold)}}
.split{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:34px}}
.split > *{{min-width:0}}
/* glance */
.lead{{font-size:1.12rem;line-height:1.65;max-width:70ch}}
.hl{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:0;padding:0;list-style:none}}
.hl li{{background:var(--band);color:var(--band-ink);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:6px;border-top:4px solid var(--gold);font-size:.92rem;font-weight:500}}
.hl .num{{font-family:var(--f-display);font-size:1.85rem;line-height:1;font-weight:700;color:var(--gold-hi);font-variant-numeric:tabular-nums}}
.seen{{font-size:.9rem;color:var(--muted)}}
.seen b{{color:var(--ink);font-weight:600}}
/* talks */
.talks{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}}
.talk{{background:var(--surface);border:1px solid var(--line);border-top:5px solid var(--accent);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:8px;box-shadow:0 6px 18px var(--shadow)}}
.talk:nth-child(3n+2){{border-top-color:var(--gold)}}
.talk:nth-child(3n){{border-top-color:var(--band)}}
.talk h3{{font-size:1.05rem}}
.talk p{{font-size:.92rem}}
.talk .fmt{{margin-top:auto;align-self:flex-start;background:var(--soft);color:var(--accent);border-radius:999px;padding:3px 10px;font-size:.78rem;font-weight:600}}
/* audiences */
.aud{{display:flex;flex-wrap:wrap;gap:8px}}
.aud span{{background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-weight:500;font-size:.92rem}}
.band.tint .aud span{{border-color:transparent}}
/* proof */
ul.list.two{{display:block;columns:2 280px;column-gap:34px}}
ul.list.two li{{break-inside:avoid;margin-bottom:10px}}
ul.list li::before{{background:var(--gold)}}
/* press on dark */
.band.dark ul.links{{gap:14px}}
.band.dark ul.links a,.band.dark ul.links > li > span{{font-family:var(--f-display);font-size:1.05rem;font-weight:600}}
/* online links as pills */
ul.links.pills{{flex-direction:row;flex-wrap:wrap;gap:8px}}
ul.links.pills li{{display:block}}
ul.links.pills a{{display:inline-block;border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:7px 14px;text-decoration:none;font-weight:600}}
ul.links.pills .note{{display:none}}
blockquote{{border-left-color:var(--gold);font-size:1rem}}
/* booking band */
.book-h{{display:flex;flex-direction:column;gap:6px}}
.crow .lab{{color:var(--gold-hi)}}
.band.dark .crow .sel{{color:var(--band-ink)}}
.btn.gold{{background:var(--gold-hi);color:#1A1405;border-color:var(--gold-hi)}}
[hidden]{{display:none!important}}
.band.dark a.btn.gold,.band.dark .btn.gold{{color:#1A1405}}
.band.dark a.btn:not(.gold):not(.primary){{color:var(--ink)}}
.band.dark .form-card .muted,.band.dark .form-card .small{{color:var(--muted)}}
.band.dark .form-card h3{{color:var(--ink)}}
.form-card{{border-radius:var(--r);padding:18px;display:flex;flex-direction:column;gap:14px}}

.hero .btn.primary{{background:var(--gold-hi);border-color:var(--gold-hi);color:#241405;font-size:1rem;padding:11px 18px}}
.hero .chip{{border-color:var(--band-line)}}
.hl li{{background:var(--band);border-top-color:var(--gold-hi)}}
.hl .num{{font-size:2rem}}
.talk{{border-top-color:var(--accent)}}
.sec-h h2::before{{background:var(--gold-hi)}}
/* speaking-photo strip: drifts left to right, pauses on hover, static for reduced motion */
.reel{{overflow:hidden;border-radius:14px;-webkit-mask-image:linear-gradient(90deg,transparent,#000 5%,#000 95%,transparent);mask-image:linear-gradient(90deg,transparent,#000 5%,#000 95%,transparent)}}
.reel-track{{display:flex;width:max-content;animation:reel 38s linear infinite}}
.reel img{{height:230px;width:auto;max-width:none;margin-right:12px;border-radius:12px;object-fit:cover;display:block;background:var(--sunk)}}
.reel:hover .reel-track{{animation-play-state:paused}}
.brands{{overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)}}
.brand-track{{display:flex;width:max-content;list-style:none;margin:0;padding:4px 0;animation:brands 34s linear infinite}}
.brands:hover .brand-track{{animation-play-state:paused}}
@keyframes brands{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
.brand{{flex:none;height:84px;min-width:170px;margin:0 14px 0 0;padding:0 26px;display:flex;align-items:center;justify-content:center;background:#fff;border:1px solid #e7e0f0;border-radius:14px;box-shadow:0 4px 14px rgba(30,11,51,.06)}}
.brand img{{max-height:46px;max-width:150px;width:auto;height:auto;object-fit:contain;display:block}}
.brand span{{font-family:var(--f-display);font-weight:700;font-size:18px;letter-spacing:-.01em;color:#1E0B33;white-space:nowrap}}
.brand-print{{display:none}}
@media (prefers-reduced-motion:reduce){{.brands{{overflow-x:auto}}.brand-track{{animation:none}}}}
@media (max-width:560px){{.brand{{height:68px;min-width:136px;padding:0 18px}}.brand span{{font-size:15.5px}}.brand img{{max-height:36px;max-width:116px}}}}
@keyframes reel{{from{{transform:translateX(-50%)}}to{{transform:translateX(0)}}}}
@media (prefers-reduced-motion:reduce){{.reel{{overflow-x:auto}}.reel-track{{animation:none}}}}
@media (max-width:560px){{.reel img{{height:170px}}}}
.thumbs{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.thumbs figure{{margin:0;display:flex;flex-direction:column;gap:4px;align-items:flex-start}}
.thumbs img{{width:84px;height:64px;object-fit:cover;border-radius:8px;display:block;max-width:100%}}
.reel-empty{{border:2px dashed var(--line);border-radius:14px;padding:22px;display:flex;flex-direction:column;gap:10px;align-items:flex-start;background:var(--surface)}}
.showcase video{{width:100%;max-width:100%;border-radius:14px;background:#000;display:block;aspect-ratio:16/9}}
/* print / PDF: light theme, full-bleed bands, no interactive bits */
.print-only{{display:none}}
@media print{{
  @page{{size:Letter;margin:0}}
  html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact;background:#fff}}
  :root{{padding:0}}
  body{{font-size:12.5px}}
  .lead{{font-size:.98rem}}
  .hl li{{padding:12px}}
  .hl .num{{font-size:1.55rem}}
  .sec-h h2{{font-size:1.2rem}}
  .band > .wrap{{gap:14px}}
  .hero h1{{font-size:1.75rem}}
  .photo{{width:112px;height:112px}}
  .book-band{{break-inside:avoid}}
  .no-print,.form-card,#toast,.cta,[data-copy],.reel,.brands{{display:none!important}}
  .brand-print{{display:block!important;font-weight:600}}
  .print-only{{display:block!important}}
  .wrap{{padding-left:40px;padding-right:40px;max-width:none}}
  .hero .wrap{{padding-block:30px}}
  .band{{padding-block:22px}}
  .talk,.hl li,blockquote,.aud,ul.list li,.crow,.sec-h{{break-inside:avoid}}
  .sec-h{{break-after:avoid}}
  .talk{{box-shadow:none}}
  a{{text-decoration:none}}
}}
.collab{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.ccard{{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--gold-hi);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:8px}}
.vids{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.vids figure{{margin:0;min-width:0}}
.small{{font-size:.85rem}}
.muted{{color:var(--muted)}}
footer{{font-size:.8rem;color:var(--muted)}}
ul.docs{{margin:0;padding:0;list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}
ul.docs li{{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--gold-hi);border-radius:12px;padding:12px 14px;display:flex;flex-direction:column;gap:4px}}
ul.docs a{{font-weight:600}}
ul.docs span{{font-size:.88rem;color:var(--muted)}}
ol.sources{{margin:0;padding-left:22px;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:4px 28px;font-size:.84rem;color:var(--muted)}}
ol.sources a{{color:var(--muted);word-break:break-word}}
ol.sources .host{{opacity:.75}}
#toast{{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(20px + env(safe-area-inset-bottom,0px));z-index:30;background:var(--ink);color:var(--bg);padding:9px 16px;border-radius:999px;font-size:.88rem;font-weight:500;max-width:calc(100% - 32px)}}
</style>

<header class="hero"><div class="wrap">
  <div class="vtop"><a class="vlogo" href="https://vformationconsulting.com/" target="_blank" rel="noopener" aria-label="V Formation Consulting"><svg class="vmark" viewBox="0 0 30 22" aria-hidden="true"><g fill="currentColor"><circle cx="15" cy="19" r="2.6"/><circle cx="10.2" cy="13.4" r="2.2"/><circle cx="19.8" cy="13.4" r="2.2"/><circle cx="6" cy="8" r="1.9"/><circle cx="24" cy="8" r="1.9"/><circle cx="2.4" cy="3" r="1.6"/><circle cx="27.6" cy="3" r="1.6"/></g></svg><span class="vword"><b>V FORMATION</b><small>CONSULTING</small></span></a><span class="vrep">Represented by {e(agency or "V Formation Consulting")}</span></div>
  <div class="idrow">{photo}<div class="idtext">
    <h1>{e(data["name"])}</h1>
    <p class="headline">{e(data.get("headline"))}</p>
    <p class="where">{e(data.get("location"))} · {e(data.get("formats") or "Keynotes, workshops and corporate programs")}</p>
    {f'<div class="tags">{"".join(f"<span class=tag>#{e(t)}</span>" for t in tags)}</div>' if tags else ""}
  </div></div>
  {f'<div class="chips">{"".join(f"<span class=chip>{e(t)}</span>" for t in data.get("topics", []))}</div>' if data.get("topics") else ""}
  <div class="cta"><a class="btn primary" href="#book">{e(data.get("ctaLabel") or ("Book " + first + " as your next speaker"))}</a>{f'<a class="btn secondary" href="{e(sched)}" target="_blank" rel="noopener">Schedule a consult</a>' if sched else f'<a class="btn secondary" href="#book">Request a consult</a>'}<a class="btn secondary" href="{e(pdf_name)}" target="_blank" rel="noopener" download data-pdf>Download PDF</a></div>
</div></header>

<main>
{BANDS}
<div class="band dark book-band" id="book"><div class="wrap">
  <div class="book-h"><div class="sec-h"><h2>Book {e(first)}</h2></div><p class="muted no-print">Booking is handled by {e(agency or "V Formation Consulting")}. Reach the agent directly, or send the details below and we'll reply with availability, format and fees.</p><p class="muted print-only">Booking is handled by {e(agency or "V Formation Consulting")}. Contact the agent for availability, format and fees.</p></div>
  <div style="display:flex;flex-direction:column;gap:10px">{"".join(contact_rows)}</div>
  <div class="cta no-print">{f'<a class="btn gold" href="{e(sched)}" target="_blank" rel="noopener">Schedule a 15-minute consult</a>' if sched else ""}<a class="btn gold" href="mailto:{e(email)}?subject={e(subject_q)}">Email {e(agent or "the agent")}</a><a class="btn" href="{e(pdf_name)}" target="_blank" rel="noopener" download data-pdf>Download the PDF one-sheet</a></div>
  <p class="print-only">To book {e(first)}, call {e(phone)} or email {e(email)}.</p>
  <div class="form-card">
    <h3>Send an inquiry</h3><p class="small muted" style="margin-top:-6px">Fill this in and tap the button. Your email app opens with the inquiry addressed to {e(agent or agency)}, ready to send.</p>
    <form id="inq" class="fgrid" novalidate>
      <label class="f" for="q-name"><span>Your name <span class="star">*</span></span><input id="q-name" class="in" autocomplete="name"></label>
      <label class="f" for="q-org"><span>Organization <span class="star">*</span></span><input id="q-org" class="in" autocomplete="organization"></label>
      <label class="f" for="q-email"><span>Email <span class="star">*</span></span><input id="q-email" class="in" type="email" autocomplete="email"></label>
      <label class="f" for="q-phone">Phone<input id="q-phone" class="in" type="tel" autocomplete="tel"></label>
      <label class="f" for="q-type">Event type<select id="q-type" class="in"><option>Keynote</option><option>Workshop</option><option>Corporate training</option><option>Conference</option><option>Podcast or media</option><option>Other</option></select></label>
      <label class="f" for="q-talk">Talk of interest<select id="q-talk" class="in"><option>Not sure yet</option>{"".join(f"<option>{e(t)}</option>" for t in talk_titles)}</select></label>
      <label class="f" for="q-date">Event date<input id="q-date" class="in" type="date"></label>
      <label class="f" for="q-where">City or virtual<input id="q-where" class="in"></label>
      <label class="f" for="q-size">Audience size<select id="q-size" class="in"><option>Not sure yet</option><option>Under 50</option><option>50–200</option><option>200–500</option><option>500+</option></select></label>
      <label class="f" for="q-budget">Budget range<select id="q-budget" class="in"><option>Prefer to discuss</option><option>Under $10,000</option><option>$10,000–$25,000</option><option>$25,000–$50,000</option><option>$50,000+</option></select></label>
      <label class="f wide" for="q-msg">About your event<textarea id="q-msg" class="in" placeholder="Audience, goals, timing, anything else we should know"></textarea></label>
      <div class="wide"><button class="btn primary" type="submit">Email my inquiry</button></div>
    </form>
    <div id="inq-out" class="out" hidden>
      <p class="small"><b>Your inquiry is ready.</b> If your email app didn't open, tap Open in my email app, or copy it and send it to <span class="sel">{e(email)}</span>{f' or call <span class="sel">{e(phone)}</span>' if phone else ""}. Nothing is sent from this page.</p>
      <pre id="inq-text"></pre>
      <div class="cta"><button class="btn primary" id="inq-copy" type="button">Copy inquiry</button><a class="btn" id="inq-mail" href="#">Open in my email app</a></div>
    </div>
  </div>
</div></div>
{DOCS}{SOURCES}<div class="band light"><div class="wrap"><footer>Profile prepared by {e(agency or "V Formation Consulting")}.</footer></div></div>
</main>
<div id="toast" hidden role="status"></div>
<script>
(() => {{
const AGENT_EMAIL = {json.dumps(email)}, TALENT = {json.dumps(data["name"])};
const $ = s => document.querySelector(s);
function toast(m){{ const t = $("#toast"); t.textContent = m; t.hidden = false; clearTimeout(toast.h); toast.h = setTimeout(() => t.hidden = true, 2800); }}
async function copy(text){{ try {{ await navigator.clipboard.writeText(text); toast("Copied."); }} catch(e){{ toast("Select the text and copy it."); }} }}
document.addEventListener("click", ev => {{ const b = ev.target.closest("[data-copy]"); if (b) copy(b.dataset.copy); }});
const v = id => ($("#" + id).value || "").trim();
$("#inq").addEventListener("submit", ev => {{
  ev.preventDefault();
  if (!v("q-name") || !v("q-org") || !/^\\S+@\\S+\\.\\S+$/.test(v("q-email"))){{ toast("Add your name, organization and a valid email."); return; }}
  const fields = [
    `Name: ${{v("q-name")}}`, `Organization: ${{v("q-org")}}`, `Email: ${{v("q-email")}}`, v("q-phone") && `Phone: ${{v("q-phone")}}`,
    `Event type: ${{v("q-type")}}`, `Talk of interest: ${{v("q-talk")}}`, v("q-date") && `Event date: ${{v("q-date")}}`,
    v("q-where") && `Location: ${{v("q-where")}}`, `Audience size: ${{v("q-size")}}`, `Budget: ${{v("q-budget")}}`
  ].filter(Boolean);
  const text = [`Booking inquiry for ${{TALENT}}`, "", ...fields, ...(v("q-msg") ? ["", v("q-msg")] : [])].join("\\n");
  $("#inq-text").textContent = text;
  $("#inq-mail").href = "mailto:" + AGENT_EMAIL + "?subject=" + encodeURIComponent("Booking inquiry: " + TALENT) + "&body=" + encodeURIComponent(text);
  $("#inq-out").hidden = false;
  try {{ window.location.href = $("#inq-mail").href; }} catch(e) {{}}
  $("#inq-out").scrollIntoView({{behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest"}});
}});
$("#inq-copy").addEventListener("click", () => copy($("#inq-text").textContent));
document.addEventListener("click", async ev => {{
  const a = ev.target.closest("[data-pdf]"); if (!a || !(window.claude && window.claude.use)) return;
  ev.preventDefault();
  try {{
    const dl = await window.claude.use("downloads");
    const blob = await (await fetch(a.getAttribute("href"))).blob();
    if (dl) await dl.save({{filename: a.getAttribute("href"), data: blob}});
    else window.open(a.href, "_blank");
  }} catch(e) {{ if (!e || !["cancelled","declined"].includes(e.code)) toast("The PDF couldn't be saved. Try again."); }}
}});
}})();
</script>
'''
open(out, "w", encoding="utf-8").write(page)
print("wrote", out, len(page))
