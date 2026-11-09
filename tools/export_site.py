"""Wrap a public page into a standalone HTML document for hosting on your own site.
Usage: python3 -I export_site.py <public.html> <data.json> <out.html>"""
import html, json, sys
s = open(sys.argv[1], encoding="utf-8").read()
d = json.load(open(sys.argv[2], encoding="utf-8"))
s = s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
i = s.index("</style>") + len("</style>")
desc = html.escape((d.get("summary") or d.get("headline") or "").split(". ")[0][:200], quote=True)
title = html.escape(f'Book {d["name"]}', quote=True)
doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       f'<meta name="description" content="{desc}">\n<meta property="og:title" content="{title}">\n<meta property="og:description" content="{desc}">\n'
       '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
       + s[:i] + "\n</head>\n<body>\n" + s[i:] + "\n</body>\n</html>\n")
open(sys.argv[3], "w", encoding="utf-8").write(doc)
print("wrote", sys.argv[3])
