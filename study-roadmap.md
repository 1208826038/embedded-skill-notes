# 嵌入式 / BMS 工程师文章学习路线导读

> 本导读为仓库内 60 篇技术长文（技能梳理 20 篇 + 外设协议 14 篇 + BMS 进阶 12 篇 + 操作系统进阶 9 篇 + 构建系统 5 篇）设计了一条**由浅入深、理论→实战→面试**的学习路径。每篇均含「场景引入 → 核心原理 → 生动类比 → 代码/时序 → 常见坑 → 面试要点」，并已配 mermaid 示意图。
>
> 用法建议：按阶段顺序推进，每阶段末尾用「阶段自测」检验；想补某块短板可直接跳到对应篇章。全部读完约 6~8 周（每周 5 篇节奏）。

---

## 🗺️ 总览地图

```
地基(全局观) ─▶ 内核与外设基础 ─▶ 汽车电子核心 ─▶ 工程化与质量 ─▶ 冲刺(面试/深挖)
```

| 阶段 | 主题 | 篇数 | 目标 |
|---|---|---|---|
| 阶段 0 | 建立全局观 | 3 | 知道嵌入式/BMS 技术栈长什么样 |
| 阶段 1 | 内核 + 基础外设 | 11 | 能独立写裸机/RTOS 驱动 |
| 阶段 2 | 汽车电子核心 | 9 | 理解功能安全、AUTOSAR、BMS |
| 阶段 3 | 工程化与质量 | 8 | 能交付车规级、可维护的代码 |
| 阶段 4 | 面试冲刺 | 2 | 把知识讲成故事、扛住深挖 |

---

## 阶段 0 · 建立全局观（1 周）

**目标**：先看清"整张地图"，避免一头扎进细节迷路。

1. [通信协议精要：CAN/SPI/I2C 各司其职](articles/05-comm-protocols.md) — 先建立"为什么有这么多总线"的直觉。
2. [ARM Cortex-R/M 内核与底层架构](articles/01-arm-cortex-rm.md) — 芯片到底怎么跑起来的。
3. [RTOS 与系统调优](articles/02-rtos-tuning.md) — 多任务世界的基本法则。

**阶段自测**：能不看资料，画出"一个 ECU 从上电到 main 函数"的流程；能说清 CAN/SPI/I2C 各自的取舍场景。

---

## 阶段 1 · 内核 + 基础外设（2~3 周）

**目标**：能独立配置 MCU 外设、写裸机/RTOS 驱动，理解编译产物。

### 1A 内核与编译
4. [ARM Cortex-R/M 内核与底层架构](articles/01-arm-cortex-rm.md)（精读，配合阶段 0 已读）
5. [编译与链接：GHS/Tasking 下的 map 文件与那些坑](articles/06-compile-link.md) — 读懂 map 文件 = 读懂内存。
6. [RTOS 与系统调优](articles/02-rtos-tuning.md)（精读）

### 1B 基础数字外设
7. [GPIO 通用输入输出](articles/p11-gpio.md) — 最朴素也最易错。
8. [PWM / ICU 定时器接口](articles/p09-pwm-icu.md) — 死区、输入捕获。
9. [ADC 模拟数字转换](articles/p10-adc.md) — 采样保持、BMS 高压精度。
   - 🆕 [DMA 直接内存访问](articles/p14-dma.md) — 总线主设备搬运引擎，与 ADC 配合实现零 CPU 连续采样（循环缓冲 + 半/全中断）。

### 1C 基础串行总线
10. [SPI 串行外设接口](articles/p03-spi.md) — 四线全双工与 CPOL/CPHA。
11. [I²C 与 SMBus](articles/p04-i2c-smbus.md) — 开漏仲裁、电量计。
12. [UART / USART 异步串行](articles/p05-uart.md) — 起始位到波特率误差。
13. [CAN / CAN FD 深度解析](articles/p01-can-canfd.md) — 重点，汽车命脉。
14. [LIN 总线详解](articles/p02-lin.md) — 低成本补充网络。

**阶段自测**：能独立用 SPI 读写一颗传感器；能画出 CAN 标准帧逐字段；能解释"为什么 I²C 需要上拉电阻"。

---

## 阶段 2 · 汽车电子核心（2~3 周）

**目标**：进入汽车电子语境——功能安全、AUTOSAR、BMS。

### 2A 安全与架构
15. [功能安全 ISO 26262](articles/03-functional-safety.md) — ASIL、安全机制、量化指标。
16. [AUTOSAR 架构深度](articles/15-autosar-arch.md) — RTE/COM/DEM/NVM 协作。
17. [MCAL 驱动开发实战](articles/04-mcal-driver.md) — 把数据从硬件搬到应用。

### 2B BMS 专项（重点）
18. [BMS 电池管理系统专项](articles/10-bms-system.md) — 守护那块大电池。
19. [DSI3 电芯监控菊花链](articles/p12-dsi3.md) — BMS 与几百节电芯的对话。
20. [PSI5 / SPC 传感器接口](articles/p13-psi5-spc.md) — 安全传感器链路。

### 2C 进阶总线
21. [SENT 单边沿调制](articles/p06-sent.md) — 高精度时间编码。
22. [FlexRay 确定性网络](articles/p07-flexray.md) — TDMA 之道。
23. [车载以太网与 TSN](articles/p08-ethernet.md) — 100BASE-T1、时间敏感网络。

**阶段自测**：能讲清楚"一个 ASIL D 功能怎么从需求落到代码里的机制"；能画出 BMS 主控→从控→电芯监控的通信拓扑。

---

## 阶段 3 · 工程化与质量（2~3 周）

**目标**：从"能跑"到"车规级、可维护、可验证"。

### 3A 可靠性机制
24. [看门狗、ECC 与故障诊断](articles/12-watchdog-ecc.md)
25. [低功耗与电源管理](articles/13-low-power.md) — 休眠唤醒、SBC/PMIC。
26. [存储管理：Flash/FEE](articles/14-storage-management.md) — 磨损均衡、掉电保护。

### 3B 验证与实时
27. [测试验证与 CI](articles/16-testing-ci.md) — HIL/MIL/静态分析。
28. [实时性分析与时序](articles/17-realtime-timing.md) — WCET、中断延迟。

### 3C 车规与协同
29. [芯片准入与车规认证](articles/18-automotive-cert.md) — AEC-Q100/PPAP/IATF 16949。
30. [数字电路与信号完整性](articles/19-signal-integrity.md) — 终端匹配、建立保持。
31. [国产芯片替代与硬件联调](articles/08-domestic-chip.md)
32. [跨团队协同与需求管理](articles/09-cross-team.md) — 把 SOR 变成代码。
33. [工具链自动化与工程效率](articles/07-toolchain-automation.md)

**阶段自测**：能设计一条"提交即跑静态分析+单元测试"的 CI 门禁；能解释"为什么车规 MCU 要做 ECC 和锁步"。

---

## 阶段 4 · 面试冲刺（1 周）

**目标**：把知识讲成有画面的故事，扛住面试官深挖。

34. [诊断与刷写：UDS、Bootloader 与 OTA](articles/11-diag-uds-bootloader.md) — 几乎必问。
35. [项目深挖与高频真题自测](articles/20-project-deep-dive.md) — 用追问链路演练。

**冲刺建议**：
- 每篇"面试高频要点"做成闪卡，每天过一遍。
- 用 [面试神器.html](面试神器.html) 做限时自测，把"模糊/不会"的题反复练。
- 对着镜子或录音，把任意一篇的"场景引入"讲成 1 分钟故事——面试官要的是"你真做过"。

---

## 📌 两条专项快线

- **想深耕 BMS**：阶段 0 → 1B/1C → 2B(18/19/20) → **BMS 进阶(b01~b12：建模/SOC/SOH/均衡/热失控/诊断/充电/标准/应用层/算法/硬件/产品)** → 3A(24/25/26) → 11(诊断) → 20。
- **想补构建系统/工具链**：先读 `06-编译链接`（编译链接四阶段、map 文件）→ `07-工具链自动化`（CI/生成器）→ **构建系统(m01~m05：Makefile 规则与自动依赖 / 编译器驱动与 ABI / CMake target-based 与交叉编译 / eMake 分布式加速)**，把“能点 Build”升级到“可复现、可审计、可并行”的工业化交付；其中 m03 CMake 与 `07` 工程化、m01 Makefile 与 `06` 链接脚本直接呼应。

- **想补 OS 理论体系**：先读 `02-rtos-tuning.md`（RTOS 工程）→ **操作系统进阶(o01~o09：进程线程/调度/同步死锁/内存/中断系统调用/文件系统IO/嵌入式Linux/面试全景/安全与隔离)**，把 RTOS 工程实践回填到经典 OS 理论；其中 o02 调度与 b09 AUTOSAR 优先级、o03 同步与 `02` 死锁章直接呼应。
- **想深耕通信/网络**：阶段 0 → 1C → 2C(21/22/23) → 3B(27/28) → 11(诊断/DoIP)。

## 🔧 配套工具

仓库内另有 3 个可运行的工程化脚本（见仓库说明），以及 [面试神器.html](面试神器.html) 可用于语音陪练与弱项复习。
