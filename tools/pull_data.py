"""Copy the card data out of a live card's saved HTML into a person's data.json.
Usage: python3 -I pull_data.py <live.html> <data.json>"""
import json, re, sys
s = open(sys.argv[1], encoding="utf-8").read()
d = json.loads(re.search(r'id="card-data">(.*?)</script>', s, re.S).group(1))
json.dump(d, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pulled", d.get("name"), "stage", len(d.get("stagePhotos", [])), "videos", len(d.get("showcases", [])), "media", len(d.get("media", [])))
