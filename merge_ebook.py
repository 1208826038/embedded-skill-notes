# -*- coding: utf-8 -*-
"""Merge new markdown articles into 技术文章合集.html ebook.
Converts each article with the Python `markdown` lib (tables+fenced_code+toc)
to match the existing ebook's rendering, then inserts TOC entries and sections.
Also fixes mermaid rendering and bumps article counts."""
import os, re, io
import markdown

ART_DIR = "articles"
HTML = "技术文章合集.html"

# (filename_without_ext, TOC_number) in desired order
NEW = [
    ("p14-dma", 34),
    ("b01-bms-battery-modeling", 35),
    ("b02-bms-soc-advanced", 36),
    ("b03-bms-soh-rul", 37),
    ("b04-bms-active-balancing", 38),
    ("b05-bms-thermal-runaway", 39),
    ("b06-bms-fault-diagnosis", 40),
    ("b07-bms-charging", 41),
    ("b08-bms-standards", 42),
    ("b09-bms-autosar-application", 43),
    ("b10-bms-algorithm-overview", 44),
    ("b11-bms-hardware-design", 45),
    ("b12-bms-product-engineering", 46),
    ("o01-os-process-thread", 47),
    ("o02-os-scheduling", 48),
    ("o03-os-sync-deadlock", 49),
    ("o04-os-memory", 50),
    ("o05-os-interrupt-syscall", 51),
    ("o06-os-fs-io", 52),
    ("o07-os-embedded-linux", 53),
    ("o08-os-overview-interview", 54),
    ("o09-os-security", 55),
]

MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])

def convert(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    MD.reset()
    body = MD.convert(text)
    # first heading line is the title (for TOC label)
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else os.path.basename(path)
    return title, body

def main():
    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()

    toc_entries = []
    sections = []
    for base, num in NEW:
        path = os.path.join(ART_DIR, base + ".md")
        if not os.path.exists(path):
            print("MISSING:", path)
            continue
        title, body = convert(path)
        toc_entries.append(
            '      <li><a href="#%s">%d. %s</a></li>' % (base, num, title)
        )
        sections.append(
            '  <section id="%s" class="art">\n%s\n  </section>\n' % (base, body)
        )
        print("converted", base, "->", num, "len", len(body))

    new_toc = "\n".join(toc_entries)
    new_sections = "\n".join(sections)

    # 1) insert TOC entries before sidebar </ol></nav>
    html, n1 = re.subn(r"</ol>\s*</nav>", new_toc + "\n  </ol>\n</nav>", html, count=1)
    print("TOC inserted:", n1)

    # 2) insert sections before </main>
    html, n2 = re.subn(r"</main>", new_sections + "\n</main>", html, count=1)
    print("sections inserted:", n2)

    # 3) fix mermaid rendering (transform pre.language-mermaid -> div.mermaid, then run)
    old_script = "  if (window.mermaid) { mermaid.initialize({startOnLoad:true, theme:'dark'}); }"
    new_script = (
        "  document.addEventListener('DOMContentLoaded', function() {\n"
        "    document.querySelectorAll('pre.language-mermaid').forEach(function(pre) {\n"
        "      var code = pre.querySelector('code');\n"
        "      if (!code) return;\n"
        "      var div = document.createElement('div');\n"
        "      div.className = 'mermaid';\n"
        "      div.textContent = code.textContent;\n"
        "      pre.replaceWith(div);\n"
        "    });\n"
        "    if (window.mermaid) {\n"
        "      mermaid.initialize({startOnLoad:false, theme:'dark'});\n"
        "      mermaid.run();\n"
        "    }\n"
        "  });"
    )
    html, n3 = re.subn(re.escape(old_script), new_script, html, count=1)
    print("mermaid fix applied:", n3)

    # 4) bump counts
    html, n4 = re.subn(r"33 篇详解", "55 篇详解", html)
    html, n5 = re.subn(
        r"33 篇技术长文（技能梳理 20 篇 \+ 外设协议 13 篇）",
        "55 篇技术长文（技能梳理 20 篇 + 外设协议 14 篇 + BMS 进阶 12 篇 + OS 进阶 9 篇）",
        html,
    )
    print("cover count:", n4, "roadmap count:", n5)

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("DONE. new html size:", len(html))

if __name__ == "__main__":
    main()
