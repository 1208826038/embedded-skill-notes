# -*- coding: utf-8 -*-
"""Refresh the 02-rtos-tuning section in the HTML ebook from the latest markdown."""
import os, re
import markdown

HTML = "技术文章合集.html"
SRC = os.path.join("articles", "02-rtos-tuning.md")
SEC_ID = "02-rtos-tuning"

MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
with open(SRC, "r", encoding="utf-8") as f:
    text = f.read()
MD.reset()
body = MD.convert(text)

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

start_tag = '<section id="%s" class="art">' % SEC_ID
start = html.find(start_tag)
if start < 0:
    raise SystemExit("section not found: " + SEC_ID)
# end = start of next <section ...> after this one
next_sec = html.find('<section id="', start + len(start_tag))
end = next_sec if next_sec > start else html.find('</main>', start)
new_block = start_tag + "\n" + body + "\n  </section>\n"

html = html[:start] + new_block + html[end:]

with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)
print("refreshed", SEC_ID, "new section len", len(body), "html size", len(html))
