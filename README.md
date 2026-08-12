# 嵌入式 / BMS 工程师成长工具箱

> 个人知识沉淀 + 面试题库 + 实用工程脚本合集，面向汽车嵌入式 / BMS 软件工程师。

本仓库收集了笔者在学习与项目中沉淀的资料：**技能梳理文档、外设协议详解、离线模拟面试应用、60 篇技术长文（含示意图）、学习路线导读，以及一套可打印的电子书**。既可以作为复习资料，也可以作为技术作品集对外分享。工程脚本（Polyspace / QAC / DBC 转换）已独立存放于私有仓库 [`embedded-scripts`](https://github.com/1208826038/embedded-scripts)。

### 五、构建系统与工具链（5 篇）

> 从“人肉点 Build”到工业化交付的底层支柱——Makefile 规则原语与自动依赖、GCC/Clang 编译器驱动与 ABI/诊断、CMake 现代 target-based 实践与交叉编译、eMake 分布式并行构建加速，与 `06-编译链接`、`07-工具链自动化` 互为纵深。

- [Makefile 工程化全解：从规则原语到大型嵌入式构建](articles/m01-makefile-deep.md)
- [编译器工程化深度：GCC/Clang 驱动、选项体系、ABI 与诊断](articles/m02-compiler-deep.md)
- [CMake 现代实践：从“全局变量地狱”到 target-based 工程](articles/m03-cmake-deep.md)
- [eMake（Electric Make / CloudBees Accelerator）深度：分布式并行构建的工程化加速](articles/m04-emake.md)
- [GHS 与 TASKING 编译器工程化深度：车规级商用工具链的底层机制与实战](articles/m05-ghs-tasking.md)


---

## 📂 仓库内容

| 文件 | 说明 |
|------|------|
| `技能知识点梳理.md` | 20 个模块技能梳理（内核/RTOS/功能安全/MCAL/通信/编译/工具链/BMS/诊断/低功耗/存储/AUTOSAR/测试/实时性/车规/信号完整性…），又深又广 |
| `外设协议详解.md` | 14 种外设协议逐字段（逐位/逐参数）详解 + 对应面试题（CAN/LIN/SPI/I²C/SMBus/UART/SENT/FlexRay/车载以太网/PWM/ICU/ADC/GPIO/DSI3/PSI5/DMA） |
| `面试神器.html` | 单文件离线 Web 应用：模拟面试（145 题 + 语音朗读/作答 + 智能评分 + 弱项复习 + 面试官追问）+ 知识学习（内嵌上述文档，可搜索）+ 收藏进度 |
| `study-roadmap.md` | **文章学习路线导读**：把 60 篇按基础→进阶→专项分层，给出学习顺序、各阶段目标与自测建议 |
| `技术文章合集.html` | **电子书（HTML 版）**：60 篇文章 + 学习路线聚合为单文件，含目录侧栏，mermaid 示意图在线渲染，可浏览器直接阅读或打印为 PDF |
| `技术文章合集.pdf` | **电子书（PDF 版）**：由 HTML 版经 weasyprint 导出，含全部正文（示意图以源码呈现，建议优先用 HTML 版看动态图） |

> 📦 **工程脚本已移至私有仓库 [`embedded-scripts`](https://github.com/1208826038/embedded-scripts)**（Polyspace / QAC / DBC→TCAN 转换三件套）。主仓库保持「文档 + 文章 + 电子书」公开可分享；脚本因涉及具体工程目录结构，故独立私有保管。

---

## 🛠 Polyspace 自动化脚本（用法说明）

> 脚本本体已移至私有仓库 [`embedded-scripts`](https://github.com/1208826038/embedded-scripts)，以下为使用文档，供参考。

### 它能做什么
- 自动探测编译系统：**CMake** 或 **eMake**（从 `Build.bat` 判断）。
- 解析源码与头文件（`#include`）依赖，自动生成 `.psprj` Polyspace 工程文件。
- 调用 **Polyspace Code Prover** 执行 MISRA-C / 功能安全检查。
- 后处理 HTML 报告：增加「未报告 orange 统计」增强列、按**模块白名单**过滤。
- 输出结构化 **JSON 汇总**，支持**增量分析**（CI 模式只分析变更文件）。

### 环境要求
- **Python 3.8+**
- Python 依赖：
  ```bash
  pip install colorama openpyxl lxml
  ```
- **MATLAB Polyspace R2023b**（Code Prover Server 或 Desktop）。脚本会校验版本，非 2023b 会报错（可按需放宽）。
- **Windows**（脚本内部使用 `.bat` 与 Windows 路径）。

### 配置：`Build/VerifyCfg/config.ini`
```ini
[polyspace]
matlab_path = C:/Program Files/MATLAB/R2023b   ; Polyspace 安装路径；也可改用环境变量 CI_POLYSPACE_BASE
compiler   = <编译器标识>
target     = <目标芯片/平台>
option     = -check-rules MISRA-C-2012|-dosomething   ; 以 | 分隔的 Polyspace 选项
; polyspace_path 可省略，默认 <Build>/CodeVerify/Polyspace
```
模块白名单 / 规则清单：`Build/VerifyCfg/polyspace_check.ini`

### 运行
```bash
# 全量分析（本地）
python polyspace_automation.py -mode=normal -analysismode=full

# 增量分析（CI，只分析变更文件）
python polyspace_automation.py -mode=ci -analysismode=specify -file=./changedFiles.txt
```

命令行参数：

| 参数 | 取值 | 说明 |
|------|------|------|
| `-mode` | `normal` / `ci` | 本地全量 / CI 增量 |
| `-analysismode` | `full` / `specify` / `guard` | 分析范围模式 |
| `-file` | 路径 | 增量分析的文件清单（配合 `-mode=ci`） |

### 工作流
1. 读取 `config.ini`，初始化全局路径（项目根 / Build / 配置 / 模板）。
2. 遍历源码、递归解析 `#include`，生成 `polyspace.psprj`。
3. 生成 `launchingCommand.bat` / `options_command.txt`，运行 Code Prover。
4. 收集结果，处理 HTML 报告（增强列 + 模块白名单）。
5. 汇总生成 JSON 结果文件。

### 适配说明（给他人使用）
脚本默认按作者所在项目的目录约定（`Customer/Build`、`BSW`/`ASW`/`APP`/`SourceCode`、`VerifyCfg`、`Tools/Components/Polyspace/templates`）定位文件。换项目时需调整 `Util` 中的路径探测逻辑或相应的 `config.ini` / 模板路径。

---

## 🧪 面试神器（HTML）用法
直接用浏览器打开 `面试神器.html` 即可（无需联网，语音朗读离线可用，语音识别需 Chrome/Edge 联网）。功能：
- **模拟面试**：145 道真题，逐题显示参考答案，自评掌握度，统计进度与正确率，支持方向筛选、随机、弱项优先、面试官追问。
- **知识学习**：内嵌三份文档，可搜索高亮、目录跳转。
- **收藏/进度**：localStorage 本地保存。

---

## 📝 技术文章系列（60 篇）

基于仓库内两份梳理文档，为每个知识点撰写的长文深讲（场景引入 → 核心原理 → 生动类比 → 代码/时序 → 常见坑 → 面试要点），适合系统复习，也可作为个人技术博客 / 作品集。

### 一、技能梳理（20 篇）

1. [ARM Cortex-R/M 内核与底层架构](articles/01-arm-cortex-rm.md)
2. [RTOS 与系统调优](articles/02-rtos-tuning.md)
3. [功能安全 ISO 26262](articles/03-functional-safety.md)
4. [MCAL 驱动开发实战](articles/04-mcal-driver.md)
5. [车载通信协议精要](articles/05-comm-protocols.md)
6. [编译与链接](articles/06-compile-link.md)
7. [工具链自动化与工程效率](articles/07-toolchain-automation.md)
8. [国产芯片替代与硬件联调](articles/08-domestic-chip.md)
9. [跨团队协同与需求管理](articles/09-cross-team.md)
10. [BMS 电池管理系统专项](articles/10-bms-system.md)
11. [诊断与刷写（UDS/Bootloader/OTA）](articles/11-diag-uds-bootloader.md)
12. [看门狗、ECC 与故障诊断](articles/12-watchdog-ecc.md)
13. [低功耗与电源管理](articles/13-low-power.md)
14. [存储管理](articles/14-storage-management.md)
15. [AUTOSAR 架构深度](articles/15-autosar-arch.md)
16. [测试验证与 CI](articles/16-testing-ci.md)
17. [实时性分析与时序](articles/17-realtime-timing.md)
18. [芯片准入与车规认证](articles/18-automotive-cert.md)
19. [数字电路与信号完整性](articles/19-signal-integrity.md)
20. [项目深挖与高频真题自测](articles/20-project-deep-dive.md)

### 二、外设协议（14 篇）

- [CAN / CAN FD 深度解析](articles/p01-can-canfd.md)
- [LIN 总线详解](articles/p02-lin.md)
- [SPI 串行外设接口](articles/p03-spi.md)
- [I²C 与 SMBus](articles/p04-i2c-smbus.md)
- [UART / USART 异步串行](articles/p05-uart.md)
- [SENT 单边沿调制](articles/p06-sent.md)
- [FlexRay](articles/p07-flexray.md)
- [车载以太网](articles/p08-ethernet.md)
- [PWM / ICU 定时器接口](articles/p09-pwm-icu.md)
- [ADC 模拟数字转换](articles/p10-adc.md)
- [GPIO 通用输入输出](articles/p11-gpio.md)
- [DSI3 电芯监控菊花链](articles/p12-dsi3.md)
- [PSI5 / SPC 传感器接口](articles/p13-psi5-spc.md)
- [DMA 直接内存访问](articles/p14-dma.md)

### 三、BMS 进阶专项（12 篇）

> 行业硬核算法与领域技能补充，与第 10 篇「BMS 专项」互为纵深——把 SOC/SOH/热/均衡/故障/充电/标准、AUTOSAR 应用层、算法工程化、硬件设计、产品工程从"概念"讲到"能落地"。

- [电池等效电路模型与参数辨识](articles/b01-bms-battery-modeling.md)
- [SOC 高精度估计算法（EKF/UKF/数据驱动）](articles/b02-bms-soc-advanced.md)
- [SOH 健康度与 RUL 剩余寿命估计](articles/b03-bms-soh-rul.md)
- [主动均衡拓扑与控制策略](articles/b04-bms-active-balancing.md)
- [电池热建模与热失控传播防护](articles/b05-bms-thermal-runaway.md)
- [BMS 故障诊断与预测性维护](articles/b06-bms-fault-diagnosis.md)
- [充电策略与快充管理](articles/b07-bms-charging.md)
- [BMS 标准法规与认证体系](articles/b08-bms-standards.md)
- [AUTOSAR 应用层与 BMS 软件组件设计](articles/b09-bms-autosar-application.md)
- [BMS 核心算法全景与工程化部署](articles/b10-bms-algorithm-overview.md)
- [BMS 硬件设计深解（选型/原理图/PCB/EMC）](articles/b11-bms-hardware-design.md)
- [BMS 产品工程（需求/平台/成本/质量/竞品）](articles/b12-bms-product-engineering.md)

### 四、操作系统进阶专项（9 篇）

> 把 `02-rtos-tuning.md` 偏工程的 RTOS 内容，补上经典 OS 理论体系与嵌入式 Linux 落地——进程/线程、CPU 调度、同步死锁、虚拟内存、中断与系统调用、文件系统与 I/O、嵌入式 Linux 内核驱动、OS 全景与面试，与 RTOS/AUTOSAR/BMS 实战逐章呼应。

- [进程、线程与执行流抽象](articles/o01-os-process-thread.md)
- [CPU 调度算法：从指标到实时调度](articles/o02-os-scheduling.md)
- [同步、互斥与死锁](articles/o03-os-sync-deadlock.md)
- [内存管理：从分段到虚拟内存](articles/o04-os-memory.md)
- [中断、异常与系统调用](articles/o05-os-interrupt-syscall.md)
- [文件系统与 I/O 管理](articles/o06-os-fs-io.md)
- [嵌入式 Linux：内核、驱动与启动](articles/o07-os-embedded-linux.md)
- [OS 全景图、发展趋势与面试总览](articles/o08-os-overview-interview.md)
- [操作系统安全与隔离：TrustZone / TEE / MPU / 容器与虚拟机](articles/o09-os-security.md)

---

## ⚠️ 免责声明
本仓库为**个人学习与技术沉淀材料**，部分脚本源自实际工程实践、已做脱敏（不含密码 / Token / 内网地址）。`polyspace_automation.py` 依赖特定目录结构与 MATLAB Polyspace 环境，直接套用前请按你的项目结构调整。内容仅供学习参考，欢迎交流指正。
