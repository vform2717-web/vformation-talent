"""Light / Medium / Dark switch shared by the public talent pages, the roster page and the Digital ID cards.
Default follows the viewer's device setting; a choice is remembered on that device (try/catch, never required)."""

# Card + public talent page tokens (--bg, --surface, ...). Medium = softer, lower-glare middle ground.
CARD_CSS = """
:root[data-theme="light"]{color-scheme:light}
:root[data-theme="medium"]{
  --bg:#E3DDE9; --surface:#EEE9F2; --sunk:#D7CFE0; --ink:#211A2C; --muted:#4C4359; --line:#CBC1D7;
  --accent:#50277A; --accent-ink:#FFFFFF; --soft:#DDD0EC;
  --band:#2B1846; --band-ink:#F4EEFB; --band-muted:#CDBFDF; --band-accent:#E8C463; --band-line:#4C3369;
  --tint:#E6DEF0; --gold:#8E681C; --gold-hi:#E3B94C; --shadow:rgba(42,16,70,.12);
  --warn:#8A4F00; --warn-soft:#EFDCBD; --good:#17603C; --good-soft:#C9E3D3; --bad:#9E221A;
  color-scheme:light }
"""

# Roster / embed page tokens (--paper, --text, ...).
SITE_CSS = """
:root[data-theme="light"]{--paper:#FBF8F2;--text:#1d1626;--muted:#5d5470;--card:#fff;--line:#e9e2d4;color-scheme:light}
:root[data-theme="medium"]{--paper:#E3DDE9;--text:#211A2C;--muted:#4C4359;--card:#EEE9F2;--line:#CBC1D7;color-scheme:light}
:root[data-theme="dark"]{--paper:#120720;--text:#f3eefb;--muted:#b9aecb;--card:#1c0d30;--line:#33204d;color-scheme:dark}
"""

TOGGLE_CSS = """
.vf-theme{position:fixed;right:max(12px,env(safe-area-inset-right,0px));bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:50;display:flex;gap:2px;padding:3px;border-radius:999px;background:rgba(20,10,32,.88);box-shadow:0 6px 20px rgba(0,0,0,.25);font:600 13px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.vf-theme button{appearance:none;border:0;background:transparent;color:#E9E1F5;min-height:40px;min-width:44px;padding:0 12px;border-radius:999px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;font:inherit}
.vf-theme button[aria-pressed="true"]{background:#E3B94C;color:#1E0B33}
.vf-theme button:focus-visible{outline:2px solid #E3B94C;outline-offset:2px}
.vf-theme svg{width:16px;height:16px;flex:none}
@media (max-width:420px){.vf-theme .lbl{display:none}.vf-theme button{padding:0 10px}}
@media print{.vf-theme{display:none}}
body{padding-bottom:64px}
"""

TOGGLE_JS = r"""<script>(function(){
var K="vf-theme",R=document.documentElement,S={light:'<circle cx="8" cy="8" r="3.2"/><path d="M8 1v1.6M8 13.4V15M1 8h1.6M13.4 8H15M3 3l1.1 1.1M11.9 11.9 13 13M3 13l1.1-1.1M11.9 4.1 13 3"/>',medium:'<circle cx="8" cy="8" r="6.2"/><path d="M8 1.8v12.4A6.2 6.2 0 0 0 8 1.8z" fill="currentColor"/>',dark:'<path d="M13.5 10.2A6 6 0 0 1 5.8 2.5a6 6 0 1 0 7.7 7.7z"/>'};
function saved(){try{return localStorage.getItem(K)||""}catch(e){return""}}
function store(t){try{localStorage.setItem(K,t)}catch(e){}}
var q="";try{q=(new URLSearchParams(location.search).get("theme")||"").toLowerCase()}catch(e){}
var t=/^(light|medium|dark)$/.test(q)?q:saved();if(t)R.setAttribute("data-theme",t);
function cur(){return R.getAttribute("data-theme")||(window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light")}
function paint(){var c=cur();document.querySelectorAll(".vf-theme button").forEach(function(b){b.setAttribute("aria-pressed",b.getAttribute("data-t")===c?"true":"false")})}
function build(){if(document.querySelector(".vf-theme"))return;var w=document.createElement("div");w.className="vf-theme";w.setAttribute("role","group");w.setAttribute("aria-label","Color theme");
["light","medium","dark"].forEach(function(k){var b=document.createElement("button");b.type="button";b.setAttribute("data-t",k);b.setAttribute("aria-label",k.charAt(0).toUpperCase()+k.slice(1)+" colors");
b.innerHTML='<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">'+S[k]+'</svg><span class="lbl">'+k.charAt(0).toUpperCase()+k.slice(1)+'</span>';
b.addEventListener("click",function(){R.setAttribute("data-theme",k);store(k);paint()});w.appendChild(b)});document.body.appendChild(w);paint()}
if(window.matchMedia){try{matchMedia("(prefers-color-scheme: dark)").addEventListener("change",paint)}catch(e){}}
if(document.body)build();else document.addEventListener("DOMContentLoaded",build);
})();</script>"""


def inject(html_text, token_css):
    """Append theme tokens + switch (a late <style> wins ties with the page's own rules) and the switch script."""
    add = "<style id=\"vf-theme-css\">" + token_css + TOGGLE_CSS + "</style>" + TOGGLE_JS
    if "vf-theme-css" in html_text:
        return html_text
    k = html_text.rfind("</body>")
    if k >= 0 and html_text[k:].replace("</body>", "", 1).replace("</html>", "", 1).strip() == "":
        return html_text[:k] + add + html_text[k:]
    return html_text.rstrip() + "\n" + add + "\n"
