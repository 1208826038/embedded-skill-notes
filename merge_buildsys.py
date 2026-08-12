# -*- coding: utf-8 -*-
"""Merge build-system chapters (m01-m04) into 技术文章合集.html and update indexes.
Numbers 56-59. Converts with python markdown (tables+fenced_code+toc) to match ebook style.
Also bumps article counts 55->59 and updates README / study-roadmap / 技能梳理."""
import os, re
import markdown

ART_DIR = "articles"
HTML = "技术文章合集.html"

NEW = [
    ("m01-makefile-deep", 56, "Makefile 工程化全解：从规则原语到大型嵌入式构建"),
    ("m02-compiler-deep", 57, "编译器工程化深度：GCC/Clang 驱动、选项体系、ABI 与诊断"),
    ("m03-cmake-deep",    58, 'CMake 现代实践：从“全局变量地狱”到 target-based 工程'),
    ("m04-emake",         59, "eMake（Electric Make / CloudBees Accelerator）深度：分布式并行构建的工程化加速"),
]

MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])

def convert(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    MD.reset()
    body = MD.convert(text)
    return body

def main():
    with open(HTML, "r", encoding="utf-8") as f:
        html = f.read()

    toc_entries, sections = [], []
    for base, num, title in NEW:
        path = os.path.join(ART_DIR, base + ".md")
        if not os.path.exists(path):
            print("MISSING:", path); continue
        body = convert(path)
        toc_entries.append('      <li><a href="#%s">%d. %s</a></li>' % (base, num, title))
        sections.append('  <section id="%s" class="art">\n%s\n  </section>\n' % (base, body))
        print("converted", base, "->", num, "len", len(body))

    new_toc = "\n".join(toc_entries)
    new_sections = "\n".join(sections)

    # 1) sidebar TOC: insert before </ol></nav>
    html, n1 = re.subn(r"</ol>\s*</nav>", new_toc + "\n  </ol>\n</nav>", html, count=1)
    print("TOC inserted:", n1)

    # 2) sections before </main>
    html, n2 = re.subn(r"</main>", new_sections + "\n</main>", html, count=1)
    print("sections inserted:", n2)

    # 3) bump cover counts
    html, n3 = re.subn(r"55 篇详解", "59 篇详解", html)
    html, n4 = re.subn(
        r"55 篇技术长文（技能梳理 20 篇 \+ 外设协议 14 篇 \+ BMS 进阶 12 篇 \+ OS 进阶 9 篇）",
        "59 篇技术长文（技能梳理 20 篇 + 外设协议 14 篇 + BMS 进阶 12 篇 + OS 进阶 9 篇 + 构建系统 4 篇）",
        html,
    )
    print("cover count:", n3, "roadmap count:", n4)

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML DONE size:", len(html))

    # ---------------- README ----------------
    with open("README.md", "r", encoding="utf-8") as f:
        rd = f.read()
    rd, c1 = re.subn(r"技术文章系列（55 篇）", "技术文章系列（59 篇）", rd)
    rd, c2 = re.subn(r"55 篇技术长文（含示意图）", "59 篇技术长文（含示意图）", rd)
    rd, c3 = re.subn(r"把 55 篇按基础", "把 59 篇按基础", rd)
    rd, c4 = re.subn(r"55 篇文章 \+ 学习路线", "59 篇文章 + 学习路线", rd)
    # add section 五 before the trailing ---
    sec5 = (
        "### 五、构建系统与工具链（4 篇）\n\n"
        "> 从“人肉点 Build”到工业化交付的底层支柱——Makefile 规则原语与自动依赖、GCC/Clang 编译器驱动与 ABI/诊断、"
        "CMake 现代 target-based 实践与交叉编译、eMake 分布式并行构建加速，与 `06-编译链接`、`07-工具链自动化` 互为纵深。\n\n"
        "- [Makefile 工程化全解：从规则原语到大型嵌入式构建](articles/m01-makefile-deep.md)\n"
        "- [编译器工程化深度：GCC/Clang 驱动、选项体系、ABI 与诊断](articles/m02-compiler-deep.md)\n"
        "- [CMake 现代实践：从“全局变量地狱”到 target-based 工程](articles/m03-cmake-deep.md)\n"
        "- [eMake（Electric Make / CloudBees Accelerator）深度：分布式并行构建的工程化加速](articles/m04-emake.md)\n\n"
    )
    rd, c5 = re.subn(r"(\n---\n\n## )", "\n" + sec5 + r"\1", rd, count=1)
    print("README edits:", c1, c2, c3, c4, c5)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(rd)

    # ---------------- study-roadmap ----------------
    with open("study-roadmap.md", "r", encoding="utf-8") as f:
        sm = f.read()
    sm, s1 = re.subn(
        r"55 篇技术长文（技能梳理 20 篇 \+ 外设协议 14 篇 \+ BMS 进阶 12 篇 \+ 操作系统进阶 9 篇）",
        "59 篇技术长文（技能梳理 20 篇 + 外设协议 14 篇 + BMS 进阶 12 篇 + 操作系统进阶 9 篇 + 构建系统 4 篇）",
        sm,
    )
    sm, s2 = re.subn(
        r"(想补 OS 理论体系\*\*：先读 `02-rtos-tuning.md`)",
        r"- **想补构建系统/工具链**：先读 `06-编译链接`（编译链接四阶段、map 文件）→ `07-工具链自动化`（CI/生成器）→ **构建系统(m01~m04：Makefile 规则与自动依赖 / 编译器驱动与 ABI / CMake target-based 与交叉编译 / eMake 分布式加速)**，把“能点 Build”升级到“可复现、可审计、可并行”的工业化交付；其中 m03 CMake 与 `07` 工程化、m01 Makefile 与 `06` 链接脚本直接呼应。\n\n\1",
        sm,
    )
    print("roadmap edits:", s1, s2)
    with open("study-roadmap.md", "w", encoding="utf-8") as f:
        f.write(sm)

    # ---------------- 技能知识点梳理 ----------------
    with open("技能知识点梳理.md", "r", encoding="utf-8") as f:
        kn = f.read()
    block = (
        "## 二十二、构建系统与工具链（Makefile / 编译器 / CMake / eMake）\n\n"
        "- **Makefile**：规则=目标+依赖+配方；自动变量 `$@/$</$*`、模式规则 `%.o:%.c`、自动依赖 `gcc -MMD` 生成 `.d` 由 `-include` 纳入，实现头文件级增量编译；递归 Make 用 `$(MAKE) -C` 跨子目录，但推荐 non-recursive 单一数据库避免重复展开；`make -j` 并行、`$(MAKEFLAGS)` 透传、`make -k` 容错、`--debug` 查依赖。\n"
        "- **交叉编译**：`CROSS_COMPILE=arm-none-eabi-` + `CC/AR/OBJCOPY` 分离；`CFLAGS`(编译)/`LDFLAGS`(链接)/`LDLIBS`(库)职责分清；`-MMD -MP` 自动依赖、`-Wall -Wextra -Werror` 质量门禁、`-O2 -g` 平衡尺寸与可调试。\n"
        "- **编译器(GCC/Clang)**：驱动四阶段预处理→编译→汇编→链接；`-O0/-O1/-O2/-Os/-O3` 与 LTO(`-flto`)、PGO(`-fprofile-use`)；`-f` 语义选项(`-fno-strict-aliasing`/`-fdata-sections`/`-ffunction-sections` 配 `--gc-sections`)；AAPCS/AAPCS-VFP ABI、`-mcpu/-mfpu/-mfloat-abi`；`__attribute__((aligned/section/weak/always_inline))`、内联汇编、内建原子；UB 与诊断(`-fsanitize`/`-Wshadow`)。\n"
        "- **CMake**：target-based(`add_library/executable` + `target_*`)，拒绝全局 `include_directories`；生成器表达式 `$<...>` 做构建期条件；`find_package`/`FetchContent` 取依赖；toolchain file 封装交叉编译器与 sysroot；`cmake --preset` 统一配置；`ctest`/`cpack` 测包一体；`install(EXPORT)` 导出可复用包。\n"
        "- **eMake(CloudBees Accelerator)**：GNU Make 兼容的分布式并行构建，emake 把 job 派发到 agent 集群并靠 history 文件做冲突检测/缓存命中，典型 C/C++ 单体仓库加速 5~20×；与 distcc/ccache/IncrediBuild/Bazel 各有边界（eMake 重在“不改 Makefile 即可分布式”，Bazel 重在“强内容寻址缓存 + 严格依赖图”）。\n\n"
    )
    kn, k1 = re.subn(r"(## 速记清单（面试前 10 分钟过一遍）)", block + r"\1", kn, count=1)
    print("梳理 edits:", k1)
    with open("技能知识点梳理.md", "w", encoding="utf-8") as f:
        f.write(kn)

    print("ALL DONE")

if __name__ == "__main__":
    main()
