/* V Formation talent embed. Usage:
   <script src="https://talent.vformationconsulting.com/embed.js" async></script>
   <vformation-talent roster [tag="KeynoteSpeaker"] [limit="6"] [theme="light|dark"]></vformation-talent>
   <vformation-talent profile="beaver-fleming" [theme="light|dark"]></vformation-talent> */
(function () {
  if (window.customElements && customElements.get("vformation-talent")) return;
  var me = document.currentScript || Array.prototype.slice.call(document.querySelectorAll("script[src]")).filter(function (s) { return /\/embed\.js(\?|$)/.test(s.src); }).pop();
  var BASE = me ? me.src.replace(/embed\.js(\?.*)?$/, "") : "https://talent.vformationconsulting.com/";
  var cache = {};
  function get(path) {
    if (!cache[path]) cache[path] = fetch(BASE + path, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
    return cache[path];
  }
  function rebase(o, base) { // keep links working on any host (e.g. owner.github.io before the domain is set up)
    if (!base || base === BASE) return o;
    ["url", "pdf", "photo"].forEach(function (k) { if (typeof o[k] === "string" && o[k].indexOf(base) === 0) o[k] = BASE + o[k].slice(base.length); });
    return o;
  }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function safe(u) { return /^(https?:|mailto:)/i.test(u || "") ? u : "#"; }
  function stat(h) { var p = String(h).split("|"); return "<li><b>" + esc(p[0].trim()) + "</b><span>" + esc((p[1] || "").trim()) + "</span></li>"; }
  function mail(p) { return p.bookingEmail ? "mailto:" + p.bookingEmail + "?subject=" + encodeURIComponent("Booking inquiry: " + p.name) : p.url; }
  function cta(p) { return p.ctaLabel || "Book " + p.name.split(" ")[0]; }

  var CSS = ":host{--ink:#1E0B33;--ink2:#2E1150;--gold:#E3B94C;--paper:#fff;--text:#1d1626;--muted:#5d5470;--line:#e9e2d4;display:block;font:16px/1.55 Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--text)}" +
    ":host([theme=dark]){--paper:#1c0d30;--text:#f3eefb;--muted:#b9aecb;--line:#33204d}" +
    "*{box-sizing:border-box}a{color:inherit}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px}" +
    ".card{background:var(--paper);border:1px solid var(--line);border-radius:18px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 8px 24px rgba(30,11,51,.08)}" +
    ".img{display:block;aspect-ratio:1/1;background:var(--ink)}.img img{width:100%;height:100%;object-fit:cover;display:block}" +
    ".ph{display:grid;place-items:center;height:100%;color:var(--gold);font-size:56px;font-weight:800}" +
    ".body{padding:16px;display:flex;flex-direction:column;gap:6px;flex:1}h3{margin:0;font-size:20px;line-height:1.2}h3 a{text-decoration:none}" +
    ".hd{margin:0;color:var(--muted);font-size:14px}.stats{list-style:none;margin:6px 0 0;padding:0;display:grid;gap:3px;font-size:13px;color:var(--muted)}" +
    ".stats b{color:var(--text);margin-right:5px}.row{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding-top:10px}" +
    ".btn{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:0 15px;border-radius:999px;font-weight:700;font-size:14px;text-decoration:none;border:1.5px solid transparent}" +
    ".gold{background:var(--gold);color:var(--ink)}.ghost{border-color:var(--line)}.light{border-color:rgba(255,255,255,.35);color:#fff}" +
    ".pro{background:linear-gradient(160deg,var(--ink),var(--ink2));color:#fff;border-radius:22px;overflow:hidden;display:grid;grid-template-columns:minmax(0,300px) 1fr}" +
    ".pro .img{aspect-ratio:auto;min-height:100%}.pro .body{padding:26px;gap:10px}.pro h3{font-size:clamp(24px,3.4vw,34px)}" +
    ".eye{color:var(--gold);letter-spacing:.14em;text-transform:uppercase;font-size:11.5px;font-weight:700;margin:0}" +
    ".pro .hd{color:#e6dcf5;font-size:15.5px}.tiles{list-style:none;margin:8px 0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}" +
    ".tiles li{background:rgba(255,255,255,.07);border:1px solid rgba(227,185,76,.35);border-radius:14px;padding:12px}" +
    ".tiles b{display:block;color:var(--gold);font-size:24px;line-height:1.1}.tiles span{font-size:12.5px;color:#e6dcf5}" +
    ".sum{margin:0;color:#efe8fa;font-size:15px}.talks{margin:2px 0 0;padding-left:18px;color:#efe8fa;font-size:14.5px}" +
    ".err{padding:14px;border:1px dashed var(--line);border-radius:12px;color:var(--muted);font-size:14px}" +
    "@media (max-width:640px){.pro{grid-template-columns:1fr}.pro .img{aspect-ratio:4/3}.pro .body{padding:20px}.tiles{grid-template-columns:1fr}.tiles b{font-size:21px}}";

  function photo(p) { return p.photo ? '<img src="' + esc(p.photo) + '" alt="' + esc(p.name) + '" loading="lazy">' : '<div class="ph">' + esc(p.name.charAt(0)) + "</div>"; }

  function rosterCard(p) {
    var hl = (p.highlights || []).slice(0, 2).map(stat).join("");
    return '<article class="card"><a class="img" href="' + esc(safe(p.url)) + '" target="_blank" rel="noopener">' + photo(p) + '</a><div class="body">' +
      '<h3><a href="' + esc(safe(p.url)) + '" target="_blank" rel="noopener">' + esc(p.name) + '</a></h3><p class="hd">' + esc(p.headline) + "</p>" +
      (hl ? '<ul class="stats">' + hl + "</ul>" : "") +
      '<div class="row"><a class="btn gold" href="' + esc(safe(p.url)) + '" target="_blank" rel="noopener">View profile</a>' +
      '<a class="btn ghost" href="' + esc(safe(mail(p))) + '">Book</a></div></div></article>';
  }

  function profileCard(p) {
    var tiles = (p.highlights || []).slice(0, 3).map(stat).join("");
    var talks = (p.talks || []).slice(0, 3).map(function (t) { return "<li>" + esc(String(t).split(":")[0]) + "</li>"; }).join("");
    var sum = String(p.summary || "");
    if (sum.length > 340) sum = sum.slice(0, 330).replace(/\s+\S*$/, "") + "…";
    return '<article class="pro"><a class="img" href="' + esc(safe(p.url)) + '" target="_blank" rel="noopener">' + photo(p) + '</a><div class="body">' +
      '<p class="eye">' + esc(p.formats || "Available to book") + "</p><h3>" + esc(p.name) + '</h3><p class="hd">' + esc(p.headline) + "</p>" +
      (tiles ? '<ul class="tiles">' + tiles + "</ul>" : "") + (sum ? '<p class="sum">' + esc(sum) + "</p>" : "") +
      (talks ? '<ul class="talks">' + talks + "</ul>" : "") +
      '<div class="row"><a class="btn gold" href="' + esc(safe(mail(p))) + '">' + esc(cta(p)) + "</a>" +
      '<a class="btn light" href="' + esc(safe(p.url)) + '" target="_blank" rel="noopener">Full profile</a>' +
      '<a class="btn light" href="' + esc(safe(p.pdf)) + '" target="_blank" rel="noopener">Download PDF</a></div></div></article>';
  }

  class VFTalent extends HTMLElement {
    static get observedAttributes() { return ["profile", "tag", "limit"]; }
    connectedCallback() { if (!this.shadowRoot) this.attachShadow({ mode: "open" }); this.render(); }
    attributeChangedCallback() { if (this.shadowRoot) this.render(); }
    render() {
      var root = this.shadowRoot, slug = this.getAttribute("profile"), tag = (this.getAttribute("tag") || "").toLowerCase().replace(/^#/, ""), limit = parseInt(this.getAttribute("limit"), 10) || 0;
      root.innerHTML = "<style>" + CSS + "</style>";
      var show = function (h) { root.innerHTML = "<style>" + CSS + "</style>" + h; };
      if (slug) {
        get("api/" + encodeURIComponent(slug) + ".json").then(function (p) { show(profileCard(rebase(p, p.base))); }, function () { show('<div class="err">This profile isn’t available right now.</div>'); });
      } else {
        get("api/talent.json").then(function (d) {
          var list = (d.talent || []).map(function (p) { return rebase(p, d.base); }).filter(function (p) { return !tag || (p.tags || []).some(function (t) { return t.toLowerCase() === tag; }); });
          if (limit) list = list.slice(0, limit);
          show(list.length ? '<div class="grid">' + list.map(rosterCard).join("") + "</div>" : '<div class="err">New profiles are on the way.</div>');
        }, function () { show('<div class="err">Profiles aren’t available right now.</div>'); });
      }
    }
  }
  customElements.define("vformation-talent", VFTalent);
})();
