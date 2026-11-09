"""Write a build manifest from card data files.
Usage: python3 -I tools/prepare.py <work_dir> <manifest.json>
work_dir holds one folder per talent id: <id>/data.json (from pull_data.py) and <id>/assets/<asset id>.<ext>
(the headshot, speaking photos, logos and documents downloaded from the ID card). Reads site.json for alwaysLive."""
import glob, json, os, sys
work, out = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site.json")))
items = []
for tid in sorted(os.listdir(work)):
    dj = os.path.join(work, tid, "data.json")
    if not os.path.exists(dj):
        continue
    d = json.load(open(dj, encoding="utf-8"))
    adir = os.path.join(work, tid, "assets")
    find = lambda aid: (glob.glob(os.path.join(adir, aid + ".*")) or [""])[0] if aid else ""
    items.append({"data": dj, "assets_dir": adir, "live": tid in cfg.get("alwaysLive", []),
                  "headshot": find(d.get("photo", "")),
                  "photos": [p for p in (find(x.get("id")) for x in d.get("stagePhotos") or []) if p],
                  "videos": [{"src": p, "filter": x.get("filter", "")} for x, p in ((x, find(x.get("id"))) for x in d.get("showcases") or []) if p]})
    print(tid, d.get("name"), d.get("status"), "live" if items[-1]["live"] else "", "photos", len(items[-1]["photos"]))
json.dump(items, open(out, "w"), indent=1)
