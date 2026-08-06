# -*- coding: utf-8 -*-
"""Register o09 and bump article counts 54 -> 55 in index files."""
import os

def patch(path, repls):
    with open(path, "r", encoding="utf-8") as f:
        s = f.read()
    for old, new in repls:
        n = s.count(old)
        if n == 0 and old.strip():
            print("  [WARN] not found in", path, ":", old[:40])
        s = s.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    print("patched", path)

# ---- README.md ----
patch("README.md", [
    ("54 篇技术长文", "55 篇技术长文"),
    ("把 54 篇", "把 55 篇"),
    ("54 篇文章", "55 篇文章"),
    ("技术文章系列（54 篇）", "技术文章系列（55 篇）"),
    ("操作系统进阶专项（8 篇）", "操作系统进阶专项（9 篇）"),
    ("- [OS 全景图、发展趋势与面试总览](articles/o08-os-overview-interview.md)",
     "- [OS 全景图、发展趋势与面试总览](articles/o08-os-overview-interview.md)\n"
     "- [操作系统安全与隔离：TrustZone / TEE / MPU / 容器与虚拟机](articles/o09-os-security.md)"),
])

# ---- study-roadmap.md ----
patch("study-roadmap.md", [
    ("54 篇技术长文（技能梳理 20 篇 + 外设协议 14 篇 + BMS 进阶 12 篇 + 操作系统进阶 8 篇）",
     "55 篇技术长文（技能梳理 20 篇 + 外设协议 14 篇 + BMS 进阶 12 篇 + 操作系统进阶 9 篇）"),
    ("操作系统进阶(o01~o08：", "操作系统进阶(o01~o09："),
    ("面试全景)**，把", "面试全景/安全与隔离)**，把"),
])

# ---- 技能知识点梳理.md ----
patch("技能知识点梳理.md", [
    ("（详见 `o07-os-embedded-linux.md`）。",
     "（详见 `o07-os-embedded-linux.md`）。\n"
     "- **OS-安全隔离**：TrustZone 把单核劈成安全/非安全两个世界（NS 位 + SAU/TZASC），TEE/OP-TEE 在安全世界托管密钥与敏感算法；MPU/MMU（XN/PXN/PAN）做硬件隔离让越权\"撞墙\"；多系统强隔离用容器（LXC/Docker）与虚拟机（Kata 背书容器、Jailhouse 静态分区、Xen 车载域、ARM EL2 Stage-2）；叠加漏洞缓解（canary/RELRO/PIE/CFI）与最小权限（seccomp/capability），流程上打通 ISO 21434/TARA（详见 `o09-os-security.md`）。"),
])

print("DONE")
