# -*- coding: utf-8 -*-
import io, sys, re

PATH = r"C:\Users\zzc\WorkBuddy\2026-08-03-13-15-39\repo_tmp\面试神器.html"

with io.open(PATH, "r", encoding="utf-8") as f:
    html = f.read()

# ---------- 1) 题库 QA 追加 ----------
# 新题目：[tag, 问题, 答案]
NEW_QA = [
 # ---- Makefile (m01) ----
 ["make","Makefile 里 $@/$</$^ 是什么？","自动变量：$@=目标名，$<=第一个依赖，$^=全部依赖(去重)；避免重复写文件名，模式规则里必用。"],
 ["make","伪目标(.PHONY)有什么用？","声明非文件目标(clean/all)，避免目录里真有同名文件导致 make 误判“已是最新”而跳过执行。"],
 ["make","make 怎么判断要重编？","比对目标与依赖的 mtime；依赖比目标新则重编，这就是增量构建的基础，省去全量编译。"],
 ["make","模式规则 %.o: %.c 怎么理解？","一条规则匹配所有 .o 由同名 .c 生成，通配编译，不用为每个文件各写一遍规则。"],
 ["make","怎么自动生成头文件依赖？","gcc -MMD -MP 编译时输出 .d 文件记录真实依赖，include 进 Makefile；改头文件才精准重编，避免漏编。"],
 ["make","-j 并行构建要注意什么？","依赖图必须写对否则竞态，输出可能交错(用 -O 分组)，递归 Make 并行易错，大项目优先非递归单 Makefile。"],
 ["make","递归 Make(subdir Makefile)有什么坑？","顶层 make 不知道子目录真实依赖，无法全局增量/并行，改一处可能漏编；倾向“非递归单 Makefile+包含”。"],
 ["make","wildcard / patsubst 干什么？","wildcard 收集源文件列表，patsubst 批量改后缀(%.c→%.o)，自动化源文件枚举，少手写路径。"],
 ["make","交叉编译 Makefile 怎么写？","CC=$(CROSS)gcc、指定 sysroot、把库/头文件路径指到工具链别用宿主机的，链接脚本 LD 单独指定。"],
 ["make","static pattern rule 和隐式规则区别？","静态模式显式限定作用对象、报错更明确；隐式规则是内置通用匹配，可能误命中不想要的文件。"],
 # ---- 编译器 / GCC·Clang·GHS·TASKING (m02/m05) ----
 ["compiler","GCC 编译四阶段？","预处理(cpp)→编译(到汇编)→汇编(.o)→链接(可执行)；-E/-S/-c 各停一阶段便于排查。"],
 ["compiler","-O2 和 -Os 怎么取舍？","-O2 性能优先，-Os 体积优先(省 Flash，MCU 常选)，-O0 便于调试但体积大且慢。"],
 ["compiler","LTO 是什么、固件为何常用？","链接时优化：跨文件内联/删死代码，固件更小更快；代价是链接慢、需全量重新链接。"],
 ["compiler","-flto 怎么配合？","编译和链接都加 -flto 且用同编译器同版本，否则链接报 thin LTO 不兼容或符号缺失。"],
 ["compiler","PGO 怎么用？","先插桩编译运行典型负载收集 .profraw，再 -fprofile-use 重编，按真实热点布局代码与分支，提升实际性能。"],
 ["compiler","-Wall -Wextra -Werror 怎么用？","-Wall/-Wextra 开常用警告，-Werror 把警告当错误逼清；但商用编译器下 -Werror 随版本可能误伤，量产常放宽。"],
 ["compiler","__attribute__((aligned/section/weak)) 干什么？","aligned 强制对齐(满足 DMA/cache)，section 指定落段，weak 弱符号可被覆盖(常用于板级钩子)。"],
 ["compiler","内联汇编在移植里怎么用？","asm volatile 直接写指令(如 WFI/DMB/读特殊寄存器)；破坏可移植、跨编译器语法不同，尽量用宏隔离或避免。"],
 ["compiler","AAPCS 是什么？","ARM 过程调用标准：参数用 r0-r3、返回值 r0、栈 8 字节对齐；违反会崩溃或与外部库 ABI 不兼容。"],
 ["compiler","GHS/TASKING 与 GCC 最大区别？","车规认证工具链(TÜV 认证到 ASIL D/SIL4)，针对 TriCore/RH850 深度优化+一体化调试/时间分析；GCC 无认证、通用。"],
 ["compiler","为什么车规必须用认证编译器？","ISO 26262 Part 8 §11 要求论证工具的置信度(TCL)；未认证编译器需自建资质包成本高，直接用认证版省事且可审计。"],
 ["compiler","volatile 用错会怎样？","漏写 volatile 优化会缓存寄存器值→硬件状态(标志位/外设)读不到；多写又阻止优化→性能掉，按需使用。"],
 # ---- CMake (m03) ----
 ["cmake","现代 CMake 为什么强调 target？","用 target_include_directories/link_libraries 把依赖绑在目标上，自动传播不污染全局，告别全局 include 地狱。"],
 ["cmake","PRIVATE/PUBLIC/INTERFACE 区别？","PUBLIC=自己+使用方都可见，PRIVATE=仅自己，INTERFACE=仅使用方；正确设置避免头文件泄漏与耦合。"],
 ["cmake","生成器表达式 $<...> 干什么？","在生成阶段按配置(Debug/Release、编译器)求值，条件选源/flag，解决同一 CMakeLists 多配置差异。"],
 ["cmake","交叉编译怎么配？","写 toolchain.cmake 设 CMAKE_SYSTEM_NAME/编译器/sysroot，cmake -B build --toolchain=...，不碰宿主机的库。"],
 ["cmake","find_package 怎么找库？","按 <Package>Config.cmake 或 Find<Package>.cmake 定位；CONFIG 模式找预装，MODULE 模式找模块脚本。"],
 ["cmake","CMake Presets 有什么用？","把常用配置(生成器/工具链/选项)写成 JSON，团队一键复用，避免每人手敲一长串 -D 参数。"],
 ["cmake","Ninja 比 Make 快在哪？","构建图更紧凑、增量/并行更聪明、无递归 Make 开销；大项目常见 Ninja 替代 Make 作生成器。"],
 ["cmake","add_subdirectory 与 FetchContent 区别？","前者引入本地子目录，后者配置期下载/拉取依赖源码(源码级集成)；现代做法减少系统级依赖。"],
 # ---- eMake (m04) ----
 ["emake","eMake 是什么、为什么快？","CloudBees Accelerator(原 Electric Make)：分布式并行构建，把 GNU Make 任务派到多机 agent 并发，大工程提速数倍到十倍。"],
 ["emake","eMake 怎么保证和单机结果一致？","eMake 分析任务依赖与文件读写冲突做冲突检测、按 history 调度，结果等价于串行/单机 make，不影响产物正确性。"],
 ["emake","eMake 与 distcc 区别？","distcc 只分发“编译”到多机；eMake 分发整个 Make 任务(含链接/脚本)并做全局依赖仲裁，覆盖更全。"],
 ["emake","eMake 与 IncrediBuild 区别？","都做分布式构建；IncrediBuild 偏 Windows/MSVC 生态，eMake 偏 Linux/GNU Make 企业 CI，常与 Jenkins 集成。"],
 ["emake","什么时候不值得用 eMake？","小项目单机几秒编完，引入调度开销与 Agent 集群反而慢；只有巨型单体(分钟级+)才划算。"],
 # ---- 操作系统理论 (o01~o09) ----
 ["os","进程和线程区别？","进程=资源(地址空间)容器，线程=执行流；同进程线程共享内存、切换便宜，跨进程需 IPC；RTOS 轻量任务≈线程。"],
 ["os","用户态和内核态？","CPU 特权级隔离：用户态不能直接访问硬件/内核内存，系统调用(svc)陷入内核提权；MPU/MMU 强制隔离防越权。"],
 ["os","系统调用怎么发生？","用户态执行 SVC(ARM)/syscall(x86)指令→触发异常→内核按号分派处理→返回；开销在特权切换与上下文保存。"],
 ["os","抢占式与协作式调度？","抢占=时钟/高优先级可剥夺当前；协作=任务主动让出；RTOS 多抢占+优先级，桌面也有时间片轮转。"],
 ["os","RM(速率单调)调度怎么排？","周期越短优先级越高；满足可调度性判定 ΣCi/Ti ≤ n(2^(1/n)-1) 则所有死线必达，经典静态优先级。"],
 ["os","EDF(最早截止时间)调度？","动态优先级，截止时间最近的最高；处理器利用率上限 100%，比 RM 更优但运行时开销与抖动更大。"],
 ["os","优先级反转是什么？","低任务持锁被中任务抢，高任务等锁→高任务被中任务间接阻塞；用优先级继承/天花板解决。"],
 ["os","优先级继承与天花板协议？","继承=持锁时升到阻塞它的最高优先级；天花板=一拿锁就升到预设天花板(与谁等待无关)，更确定、可防死锁。"],
 ["os","死锁四个必要条件？","互斥、占有且等待、不可剥夺、循环等待；打破任一即可(如按序加锁破循环等待)。"],
 ["os","银行家算法干什么？","死锁避免：分配前模拟是否仍存在安全序列，有才分配；运行时开销大，嵌入式多用预防+固定上限替代。"],
 ["os","互斥锁与信号量区别？","互斥锁=所有权(谁锁谁解、可递归)，用于临界区；信号量=计数/同步(_ISR 给任务发信号)，无所有权概念。"],
 ["os","自旋锁适用场景？","持锁极短且多核/不可睡眠(中断上下文)，忙等不睡眠；单核关中断更合适，自旋锁在单核无意义且浪费。"],
 ["os","虚拟内存与 MMU 干什么？","把虚拟地址映射物理，隔离进程、按需分页、共享库；MCU 常无 MMU 用 MPU 做静态区域保护。"],
 ["os","TLB 是什么？","页表缓存：加速虚拟→物理转换；切换进程/改映射须刷 TLB 否则旧映射致错，ASID 可减少刷新。"],
 ["os","缺页中断怎么处理？","MMU 发现页不在内存→异常→内核调页(从磁盘/ROM 装入)或报段错误；MCU 一般无此机制。"],
 ["os","中断和异常区别？","中断=异步外部(定时器/外设)，异常=同步内部(指令/缺页)；都走异常向量表，RTOS 用 PendSV 做任务切换。"],
 ["os","中断顶半/底半？","顶半快处理(关中断)、底半延迟处理(线程/软中断)；避免长中断阻塞系统，平衡实时与吞吐。"],
 ["os","VFS 是什么？","虚拟文件系统：统一 open/read/write 接口屏蔽底层(FatFS/ext4/网络)，应用不关心介质；嵌入式常用 FatFs 挂 SD。"],
 ["os","缓冲与缓存区别？","缓冲 buffer=削峰/批处理(写队列)，缓存 cache=加速重复读(命中免 IO)；都减少慢速设备等待。"],
 ["os","嵌入式 Linux 启动流程？","BootROM→SPL/U-Boot→kernel(dtb 设备树)→rootfs→init；设备树描述硬件，驱动按 compatible 匹配。"],
 ["os","设备树(device tree)解决什么？","把硬件描述(寄存器/中断/时钟)从内核代码移到 dts，同 SoC 不同板只改 dts 不需重编内核，平台驱动模型核心。"],
 ["os","TrustZone 怎么隔离安全世界？","ARM 把 CPU/内存/外设打 NS 位分安全/非安全世界，只能安全态切换；TEE(OP-TEE)跑敏感代码，普通 App 碰不到密钥。"],
 # ---- BMS 进阶 (b01~b12) ----
 ["bmsadv","SOC 估算主流方法？","安时积分(简单有漂移)+OCV 查表修正(静置准)+模型(EKF/UKF 融合电流电压温度)；工程上多法融合。"],
 ["bmsadv","EKF 与 UKF 估计 SOC 区别？","EKF 对非线性线性化(雅可比)，UKF 用 sigma 点采样更准确但更重；都用电压模型+电流观测，温度进模型。"],
 ["bmsadv","SOH 怎么估？","容量衰减(满充容量比初始)、内阻增长(直流/交流内阻)、循环数；在线用充放电窗口算可用容量。"],
 ["bmsadv","ICA(dQ/dV)干什么？","对电压微分看峰位/峰面积，峰漂移反映老化/析锂；用于 SOH 与析锂预警，需高精度慢采。"],
 ["bmsadv","主动均衡与被动均衡选型？","被动简单便宜但耗能发热；主动能量转移效率高、适合大容量/快充，拓扑(flyback/电容/变压器)复杂成本高。"],
 ["bmsadv","热失控怎么防？","温度/电压监控+热蔓延阻隔(气凝胶/云母)、单体温升率判定、提前断高压；GB 38031 是电池包安全强标。"],
 ["bmsadv","绝缘检测原理？","电桥法在正负母线对地加已知电阻测分压，算绝缘电阻；低于阈值(通常 >500Ω/V)报绝缘故障并断高压。"],
 ["bmsadv","HVIL 互锁怎么工作？","高压连接器回路串低压环，连接器断开即回路断→BMS 检测断开立即断高压；防带电插拔触电。"],
 ["bmsadv","充电协议 GB/T 27930 是什么？","国标充电桩与 BMS 通信(CAN)：握手→配置→充电参数→充电→结束；BMS 按电池状态要电压电流，桩响应。"],
 ["bmsadv","AFE(模拟前端)干什么？","专用电芯监控 IC(如 LTC681x/MC3377x)采集数十节电压+温度，经菊花链(DSI3/isoSPI)上报；精度/均衡/诊断是关键指标。"],
 ["bmsadv","BMS 功能安全怎么落地？","ASIL C/D 等级，电压/温度/绝缘诊断覆盖率达标；电压采样冗余+合理性校验，故障进安全状态(断高压/限功率)。"],
 ["bmsadv","BMS 产品工程关注什么？","产线标定(每包校准)、一致性分选、售后诊断(读快照/DTC)、寿命预测、成本与可靠性权衡、车规流程(APQP/PPAP)。"],
]

def fmt_qa(entries):
    out = []
    for tag, q, a in entries:
        out.append("  ['" + tag + "','" + q + "','" + a + "'],")
    return "\n".join(out)

qa_block = fmt_qa(NEW_QA)

# 锚定 QA 数组最后一行(无尾逗号) + 闭括号
qa_anchor_last = "['p_psi5','和 SENT 区别？','PSI5 两线供电通信一体多用于安全传感器；SENT 单线纯信号。']\n];"
assert qa_anchor_last in html, "QA anchor not found"
qa_replacement = "['p_psi5','和 SENT 区别？','PSI5 两线供电通信一体多用于安全传感器；SENT 单线纯信号。'],\n" + qa_block + "\n];"
html = html.replace(qa_anchor_last, qa_replacement, 1)

# ---------- 2) CATS 映射追加新 tag ----------
cats_old = "  p_gpio:'GPIO', p_dsi3:'DSI3', p_psi5:'PSI5/SPC'"
cats_new = "  p_gpio:'GPIO', p_dsi3:'DSI3', p_psi5:'PSI5/SPC',\n  make:'Makefile', compiler:'编译器工具链', cmake:'CMake', emake:'eMake分布式', os:'操作系统', bmsadv:'BMS进阶'"
assert cats_old in html, "CATS anchor not found"
html = html.replace(cats_old, cats_new, 1)

# ---------- 3) buildChips 分组追加新 tag ----------
groups_old = "  const groups=[['技术基础',['cortex','rtos','safety','mcal','build','tools','realtime','si']],\n                ['通信/外设',['comms','p_can','p_lin','p_spi','p_i2c','p_uart','p_sent','p_flexray','p_eth','p_pwm','p_icu','p_adc','p_gpio','p_dsi3','p_psi5']],\n                ['汽车/工程',['bms','diag','wdt','power','storage','autosar','test','cert','local','collab']]];"
groups_new = "  const groups=[['技术基础',['cortex','rtos','safety','mcal','build','tools','make','compiler','cmake','emake','os','realtime','si']],\n                ['通信/外设',['comms','p_can','p_lin','p_spi','p_i2c','p_uart','p_sent','p_flexray','p_eth','p_pwm','p_icu','p_adc','p_gpio','p_dsi3','p_psi5']],\n                ['汽车/工程',['bms','bmsadv','diag','wdt','power','storage','autosar','test','cert','local','collab']]];"
assert groups_old in html, "groups anchor not found"
html = html.replace(groups_old, groups_new, 1)

# ---------- 4) FOLLOWUPS 追问追加 ----------
NEW_FU = {
 "make":[["大项目头文件改了却只重编了部分目标，怎么查？","看 .d 是否真被 include、Makefile 是否把生成头当 order-only 依赖；用 touch 触发全编对比，确认是依赖缺失而非缓存。"],
        ["非递归单 Makefile 和无数小 Makefile 怎么权衡？","巨型工程单 Makefile+include 全局依赖最准(增量/并行好)但文件大维护重；中小项目子目录 Make+显式依赖声明也可。"]],
 "compiler":[["LTO 下某函数被“优化没了”导致启动异常怎么查？","确认是否缺 used 属性被链接器当死代码删；保留入口加 __attribute__((used)) 或 -Wl,--whole-archive，对照 map 文件确认。"],
           ["车规要求“可复现构建”具体怎么做？","固定编译器版本/选项、嵌入构建时间戳与 git sha、关闭随机化、归档 .map 与产物哈希，保证任何一次构建结果字节一致可审计。"]],
 "cmake":[["交叉编译时 find_package 找到了宿主机的库怎么办？","toolchain 里设 CMAKE_FIND_ROOT_PATH 并把模式设 ONLY/BOTH 让 find 只在 sysroot 找，或显式指定 <Package>_ROOT。"],
         ["target 依赖传错(头文件不该暴露使用方)怎么修？","把对应 include 从 PUBLIC 降到 PRIVATE/INTERFACE，避免 ABI/头文件泄漏导致使用方意外耦合。"]],
 "emake":[["eMake 结果和本地 make 偶发不一致怎么定位？","看 eMake 的 annotation 报告找冲突文件/未声明依赖，补 order-only 依赖或显式串行，让依赖图完整。"],
         ["Agent 集群与单机构建产物哈希不同正常吗？","内容应一致(仅时间戳/路径可能不同)；若字节不同先查构建是否嵌入了机器名/路径等非确定性信息。"]],
 "os":[["多核下自旋锁和关中断能混用吗？","不能简单混：关中断只挡本核挡不住他核；跨核临界区用自旋锁+内存屏障(DMB/DSB)，必要时关抢占而非关中断。"],
      ["TrustZone 下普通世界怎么调用安全世界服务？","走 SMC 指令进入监视器(EL3)转发到 TEE，参数经共享内存；普通世界看不到密钥只拿到结果，形成可信边界。"]],
 "bmsadv":[["SOC 在快充大电流下误差大怎么补偿？","模型法对电流噪声敏感，改用 EKF 并加电流滤波/温度补偿；快充段用电压平台、CV 段 OCV 修正，分段估计。"],
          ["绝缘检测在潮湿整车怎么避免误报？","加环境湿度/温度补偿、多次采样取稳、区分真实绝缘下降与瞬时漏电，阈值留余量并配合延时报出。"]],
}
def fmt_fu(d):
    out = []
    for tag, lst in d.items():
        items = ",\n          ".join("['" + q + "','" + a + "']" for q, a in lst)
        out.append("  " + tag + ":[" + items + "]")
    return ",\n".join(out)

fu_block = fmt_fu(NEW_FU)
fu_anchor = "};\n\n/* ===================== 状态 ===================== */"
assert fu_anchor in html, "FOLLOWUPS anchor not found"
html = html.replace(fu_anchor, ",\n" + fu_block + "\n};\n/* ===================== 状态 ===================== */", 1)

# ---------- 5) md-adv 文档追加三大块 ----------
adv_sections = """
## 十一、构建系统与工具链（Makefile / 编译器 / CMake / eMake / GHS·TASKING）
- Makefile：规则=目标:依赖+命令；自动变量 `$@/$</$^`、模式规则 `%.o:%.c`、`.PHONY` 防误判；`gcc -MMD -MP` 自动产头文件依赖，改头才精准重编；`-j` 并行依赖图必须写对，大项目倾向“非递归单 Makefile+include”而非递归 sub-make。
- 编译器驱动四阶段：预处理→编译→汇编→链接；`-O2` 性能 / `-Os` 体积(固件常选) / `-O0` 调试；LTO 跨文件优化减小固件但链接慢；PGO 按真实热点重排；`-Wall -Wextra` 开警告，`-Werror` 量产常放宽防误伤。
- 车规必须用认证工具链：ISO 26262 Part 8 §11 要求论证工具置信度(TCL)，GHS MULTI / TASKING VX 经 TÜV 认证到 ASIL D/SIL4，针对 TriCore/RH850 深度优化+一体化 TimeMachine/WinIDEA 调试；GCC 无认证需自建资质包。`__attribute__((aligned/section/weak))`、内联汇编、AAPCS 调用约定是移植关键。
- CMake：现代写法以 target 为中心，`target_include_directories(PUBLIC/PRIVATE/INTERFACE)` 控制依赖传播，生成器表达式 `$<...>` 按配置求值；交叉编译靠 `toolchain.cmake` + `--toolchain`；`find_package`/Presets/Ninja 提升团队一致性；FetchContent 做源码级依赖。
- eMake(CloudBees Accelerator)：分布式并行构建，把 GNU Make 任务派到多机 agent 并发，大工程提速数倍~十倍；靠依赖与读写冲突检测保证结果等价于单机 make；与 distcc(仅编译)/IncrediBuild(偏 MSVC)定位不同，仅巨型单体划算。

## 十二、操作系统理论（进程线程 / 调度 / 同步死锁 / 内存 / 中断系统调用 / 文件IO / 嵌入式Linux / 安全隔离）
- 进程=资源容器、线程=执行流；用户态/内核态靠 CPU 特权级+MPU/MMU 隔离，系统调用(svc)陷入内核提权。
- 调度：抢占式(时钟/高优先级剥夺) vs 协作式(主动让出)；RM(速率单调)静态优先级、周期短者优先、可调度性判定 `ΣCi/Ti ≤ n(2^(1/n)-1)`；EDF 动态优先级、利用率上限 100% 但抖动大。
- 同步与死锁：优先级反转用继承/天花板协议；死锁四必要条件(互斥/占有等待/不可剥夺/循环等待)；互斥锁有所有权、信号量做同步、自旋锁用于极短多核临界区；TLB 加速地址转换、切换进程需刷。
- 中断与异常：中断异步外部、异常同步内部，RTOS 用 PendSV 做任务切换；顶半快处理+底半延迟平衡实时与吞吐。
- 文件系统：VFS 统一接口屏蔽 FatFs/ext4/网络；缓冲(buffer)削峰、缓存(cache)加速重复读。
- 嵌入式 Linux：BootROM→U-Boot→kernel(dtb)→rootfs；设备树把硬件描述移出内核，同 SoC 不同板只改 dts；平台驱动按 compatible 匹配。
- 安全隔离：TrustZone 把 CPU/内存/外设打 NS 位分安全/非安全世界，TEE(OP-TEE)跑密钥等敏感逻辑，普通世界经 SMC 调用只拿结果。

## 十三、BMS 进阶深度（电池建模 / SOC·SOH / 均衡 / 热失控 / 故障诊断 / 充电 / 硬件 AFE / 产品工程）
- 电池建模：等效电路模型(Rint/Thevenin/DP)描述端电压随电流/SoC/温度的非线性，是 SOC 与功率估算基础；参数随老化漂移需在线辨识。
- SOC/SOH：SOC=安时积分+OCV 修正+模型(EKF/UKF)融合；SOH 看容量衰减与内阻增长；ICA(dQ/dV)峰漂移反映老化/析锂，用于 SOH 与析锂预警。
- 均衡：被动(电阻耗散)简单便宜、主动(双向 Buck-Boost/flyback/电容)能量转移效率高，按容量与成本权衡。
- 热安全：温度/电压监控+热蔓延阻隔(气凝胶/云母)+单体温升率判定，提前断高压；GB 38031 电池包安全强标。
- 高压安全：绝缘检测(电桥法，>500Ω/V 阈值)、HVIL 互锁(连接器断开即断高压)、预充防继电器粘连。
- 充电：GB/T 27930 桩-BMS CAN 通信握手→配置→参数→充电→结束；ISO 15118 即插即充(Plug&Charge)走 TLS。
- 硬件 AFE：LTC681x/MC3377x 等专用监控 IC 采数十节电压+温度，经 DSI3/isoSPI 隔离菊花链上报。
- 产品工程：产线标定/一致性分选/售后诊断/寿命预测/成本可靠性权衡/车规流程(APQP/PPAP)，把算法真正落地为可量产产品。
"""
idx = html.find('id="md-adv">')
assert idx != -1, "md-adv not found"
end = html.find('</script>', idx)
html = html[:end] + adv_sections + html[end:]

with io.open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

# 统计题数
total = html.count("\n  ['") + html.count("\n['")  # 粗略；用更准的方式
import re
cnt = len(re.findall(r"^\s*\['[a-z0-9_]+',", html, re.M))
print("OK. 新增题目:", len(NEW_QA), " 题库总计约:", cnt, " 题")
