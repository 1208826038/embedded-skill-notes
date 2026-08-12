# -*- coding: utf-8 -*-
"""Merge m05-ghs-tasking.md into 技术文章合集.html as article #60 (59->60),
and update README / study-roadmap / 技能知识点梳理 counts and entries."""
import re, markdown

HTML = "技术文章合集.html"
MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])

base, num, title = (
    "m05-ghs-tasking", 60,
    "GHS 与 TASKING 编译器工程化深度：车规级商用工具链的底层机制与实战",
)

with open("articles/%s.md" % base, "r", encoding="utf-8") as f:
    text = f.read()
MD.reset()
body = MD.convert(text)

toc = '      <li><a href="#%s">%d. %s</a></li>' % (base, num, title)
section = '  <section id="%s" class="art">\n%s\n  </section>\n' % (base, body)

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

html, n1 = re.subn(r"</ol>\s*</nav>", toc + "\n  </ol>\n</nav>", html, count=1)
print("TOC inserted:", n1)
html, n2 = re.subn(r"</main>", section + "\n</main>", html, count=1)
print("section inserted:", n2)
html, n3 = re.subn(r"59 篇详解", "60 篇详解", html)
print("cover 59->60:", n3)
html, n4 = re.subn(r"构建系统 4 篇", "构建系统 5 篇", html)
print("buildsys 4->5:", n4)
with open(HTML, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML size:", len(html))

# README
with open("README.md", "r", encoding="utf-8") as f:
    rd = f.read()
rd, c1 = re.subn(r"技术文章系列（59 篇）", "技术文章系列（60 篇）", rd)
rd, c2 = re.subn(r"59 篇技术长文（含示意图）", "60 篇技术长文（含示意图）", rd)
rd, c3 = re.subn(r"把 59 篇按基础", "把 60 篇按基础", rd)
rd, c4 = re.subn(r"59 篇文章 \+ 学习路线", "60 篇文章 + 学习路线", rd)
rd, c5 = re.subn(r"### 五、构建系统与工具链（4 篇）", "### 五、构建系统与工具链（5 篇）", rd)
# add m05 bullet after m04 bullet
rd, c6 = re.subn(
    r"- \[eMake（Electric Make / CloudBees Accelerator）深度：分布式并行构建的工程化加速\]\(articles/m04-emake.md\)\n",
    "- [eMake（Electric Make / CloudBees Accelerator）深度：分布式并行构建的工程化加速](articles/m04-emake.md)\n"
    "- [GHS 与 TASKING 编译器工程化深度：车规级商用工具链的底层机制与实战](articles/m05-ghs-tasking.md)\n",
    rd,
)
print("README edits:", c1, c2, c3, c4, c5, c6)
with open("README.md", "w", encoding="utf-8") as f:
    f.write(rd)

# study-roadmap
with open("study-roadmap.md", "r", encoding="utf-8") as f:
    sm = f.read()
sm, s1 = re.subn(r"59 篇技术长文", "60 篇技术长文", sm)
sm, s2 = re.subn(r"构建系统 4 篇", "构建系统 5 篇", sm)
sm, s3 = re.subn(r"\*\*构建系统\(m01~m04：", "**构建系统(m01~m05：", sm)
print("roadmap edits:", s1, s2, s3)
with open("study-roadmap.md", "w", encoding="utf-8") as f:
    f.write(sm)

# 技能知识点梳理: add pointer in section 六
with open("技能知识点梳理.md", "r", encoding="utf-8") as f:
    kn = f.read()
kn, k1 = re.subn(
    r"(5\.\*\*编译器差异\*\*.*?跨芯片移植需改编译选项与内联汇编。)",
    r"\1\n\n- **深度专文**：商用编译器（GHS MULTI / TASKING VX-toolset）的驱动、`-O`/`-opt`/`#pragma optimize_level` 优化、LSL 链接脚本、MISRA 抑制、TÜV 功能安全认证与 GCC 迁移，详见 `m05-ghs-tasking.md`。",
    kn,
)
print("梳理 edits:", k1)
with open("技能知识点梳理.md", "w", encoding="utf-8") as f:
    f.write(kn)

print("ALL DONE")
