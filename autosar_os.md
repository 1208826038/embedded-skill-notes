# AUTOSAR OS 深度解析

> 本章面向「汽车嵌入式软件工程师」面试与实战，系统拆解 AUTOSAR Classic Platform（CP）操作系统的对象模型、配置项、运行时调度逻辑与各项特性。读完应能在简历里把「AUTOSAR OS / BSW / RTE」讲清楚，也能应对「任务怎么调度」「优先级天花板怎么防死锁」「多核怎么上锁」「时序保护是什么」这类深挖。

## 0. 为什么要有 AUTOSAR OS（定位与渊源）

### 0.1 AUTOSAR 与两种平台

AUTOSAR（AUTomotive Open System ARchitecture）是汽车电子的开放式软件架构标准。它分两条主线：

- **Classic Platform（CP）**：面向资源受限、强实时、高安全的 ECU（车身、底盘、动力、BMS、网关等），运行在 MCU 上，OS 是「静态配置、确定性、可认证」的实时内核。
- **Adaptive Platform（AP）**：面向高算力、需要动态部署的域控制器/中央计算（智驾、座舱），运行在 POSIX 操作系统（如 Linux）之上，用 C++/SOA，带自适应运行时。

本章讲的 **AUTOSAR OS 特指 Classic Platform 的 OS**，它和 MCU 上的 RTOS（FreeRTOS、RTEMS、uC/OS）形态接近，但哲学完全不同：它是**标准定义、代码生成、静态配置**的。

### 0.2 OS 在分层架构里的位置

在 AUTOSAR CP 分层中，自上而下大致是：

- **Application（SWC，软件组件）**：应用算法，只通过 RTE 调用，不碰 OS。
- **RTE（Runtime Environment）**：SWC 与 BSW 的"总线"，把 SWC 的 Runnable 映射到 OS 的任务/事件上。
- **Services 层（BSW）**：操作系统 OS、Com、NvM、Diag、WdgM 等系统服务。
- **ECU Abstraction / MCAL**：硬件抽象与外设驱动。

OS 处在 **Services 层最底层**，为上层（尤其 RTE）提供：任务调度、中断管理、计时（Counter/Alarm/调度表）、事件、资源互斥、多核、内存/时序保护。也就是说，**RTE 的"什么时候跑哪段应用代码"完全由 OS 决定**——OS 才是实时性的真正命脉。

### 0.3 OSEK/VDX 渊源

AUTOSAR OS 不是凭空设计的，它**向后兼容 OSEK/VDX OS 标准**（德国汽车界 90 年代的实时 OS 标准）。很多概念（Basic/Extended Task、Alarm、Event、Resource、优先级天花板、OIL 配置思想）都直接继承自 OSEK。所以你看到 AUTOSAR OS 的很多术语和 OSEK 一模一样——这是历史原因，也是面试加分点。

### 0.4 与通用 RTOS 的本质区别

| 维度 | 通用 RTOS（FreeRTOS 等） | AUTOSAR OS |
|---|---|---|
| 配置方式 | 代码里动态创建任务/队列 | **XML 静态配置 + 代码生成**，对象数量编译期固定 |
| 实时模型 | 优先级抢占，基本够用 | 抢占 + 天花板协议 + 时序保护 + 多核，可认证 |
| 安全 | 一般无内存保护 | 支持 MPU 隔离、Trusted/Non-Trusted、ISO 26262 |
| 标准 | 各家实现不同 | 统一标准，可移植、可换供应商 |
| 工具链 | 手工集成 | 由 DaVinci/ETAS/Vector 等工具链生成 |

核心差异一句话：**AUTOSAR OS 把"实时性、安全、可移植"做成了可认证的标准资产**，而不是一个能跑就行的小内核。

---

## 1. 对象模型总览（OS 管理的所有对象）

AUTOSAR OS 管理的不是"进程线程"那套动态对象，而是**编译期静态配置好的一张对象表**。所有对象都挂在 **OS-Application** 之下。

### 1.1 OS-Application：对象的容器

**OS-Application（操作系统应用）** 是一组相关 OS 对象的逻辑集合——它把 Task、ISR、Counter、Alarm、Resource、ScheduleTable 等圈在一起，作为**内存保护、访问权限、生命周期**的最小边界单位。

- 一个 OS-Application 可以是 **Trusted（可信）** 或 **Non-Trusted（非可信）**。
- Trusted 应用运行在特权模式，能访问所有内存、能调用所有 OS 服务；Non-Trusted 运行在用户模式，受 MPU 限制，越界触发 **Protection Hook**。
- 对象"跨 OS-Application 访问"需要显式声明 `Os*AccessingApplication`，否则编译/链接报错。

> 类比：OS-Application 像"进程"的雏形，但它是静态的、数量固定的；多核场景下每个核上可以跑多个 OS-Application。

### 1.2 对象清单

| 对象 | 作用 | 归属 |
|---|---|---|
| Task | 基本的执行单元（应用代码载体） | OS-Application |
| ISR（Cat1/Cat2） | 中断服务例程 | OS-Application |
| Counter | 单调递增的计时基准（tick） | OS-Application |
| Alarm | 基于 Counter 的定时动作 | OS-Application |
| ScheduleTable | 多到期点的精确调度编排 | OS-Application |
| Event | 仅 Extended Task 用的同步原语 | Task |
| Resource | 互斥/临界区保护 | OS-Application |
| Spinlock | 跨核自旋锁（多核） | OS-Application |
| IOC | 核间/应用间通信（多核） | OS-Application |

理解这套对象模型是读懂后续所有章节的前提：**Task 是载体，Counter 是时钟，Alarm/调度表是触发器，Event/Resource 是同步与互斥，ISR 是异步入口，OS-Application 是保护边界。**

---

## 2. 任务（Task）

任务是 AUTOSAR OS 里运行应用代码的基本单位。AUTOSAR 把任务设计得极其"静态"：优先级、是否可抢占、激活次数、栈大小全在配置阶段定死。

### 2.1 Basic Task vs Extended Task

这是 OSEK 经典划分，面试几乎必问：

- **Basic Task（基本任务）**：只有 3 个状态——**就绪（Ready）、运行（Running）、挂起（Suspended）**。它不能等待事件，生命周期是"被激活 → 运行到底 → TerminateTask 回到挂起"。Basic Task 实时性好、开销低，适合纯周期性、无阻塞的计算。
- **Extended Task（扩展任务）**：多了第 4 个状态——**等待（Waiting）**。它可以调用 `WaitEvent` 阻塞自己，直到别的任务/ISR `SetEvent` 唤醒。Extended Task 一般常驻（不 terminate），适合"事件驱动"的服务型逻辑（比如一直等 CAN 报文事件）。

状态机：

- Basic：`Suspended --ActivateTask--> Ready --(被调度)--> Running --TerminateTask--> Suspended`
- Extended：在 Running 中可 `Running --WaitEvent--> Waiting --SetEvent--> Ready`，也能 `Running --TerminateTask--> Suspended`。

> 关键区别：Basic Task 没有等待态，所以**不会自己阻塞**；Extended Task 会阻塞，因此它的栈必须一直保留（不能像 Basic 那样运行完就释放）。这也是为什么 Extended Task 通常数量少、优先级低（常驻后台），Basic Task 数量多、抢占频繁。

### 2.2 优先级与抢占模型

- **优先级是静态整数（0 到 N）**，**数值越大优先级越高**（注意：这点与某些 RTOS 相反，但和 OSEK 一致）。
- 任务分两种调度属性：
  - **FULL 抢占（可抢占）**：一旦有更高优先级任务就绪，当前任务立即被抢占。这是默认、最常见的模型。
  - **NON 抢占（不可抢占）**：运行期间不会被同核其他任务抢占，只能主动让出（`Schedule()` 或 terminate）。用于需要原子性但又不想上锁的场景，但会牺牲实时性，慎用。
- **OSEK OS Class**（与可扩展等级是两个概念，别混）：
  - BCC1 / BCC2：只有 Basic Task（B）；ECC1 / ECC2：含 Extended Task（E）。
  - BCC2 / ECC2：允许同一任务**多次激活（激活队列）**；BCC1 / ECC1：每任务只能激活 1 次。
- **同优先级时间片轮转（Round Robin）**：可选特性，多个同优先级任务按配置的时间片轮流跑，避免某一个长期霸占。

### 2.3 任务激活、多次激活、栈

- `ActivateTask(task)`：把任务从 Suspended 置为 Ready（可跨任务/ISR 调用）。
- **多次激活（Activation）**：配置项 `OsTaskActivation` 决定任务能"排队激活"几次（如设为 2，意味着上一次还没终止，又能再激活一次，OS 会在内部排队）。ECC2/BCC2 才支持 >1。
- **任务栈**：每个任务有**独立的私有栈**（配置 `OsTaskStackSize`），上下文切换时保存/恢复寄存器。栈大小必须静态配够，否则栈溢出——OS 可配栈溢出检测（见内存保护章）。

### 2.4 任务 API 四件套

| API | 作用 | 调用者限制 |
|---|---|---|
| `ActivateTask(task)` | 激活任务（Suspended→Ready） | Task / Cat2 ISR / 钩子 |
| `TerminateTask()` | 终止自己，回到 Suspended | 只能任务调自己，且调用前须释放所有 Resource |
| `ChainTask(task)` | 终止自己并激活另一任务（原子地"接力"） | 任务调自己 |
| `Schedule()` | 主动让出 CPU，触发一次重调度（仅 FULL 抢占任务有意义） | 任务调自己 |
| `WaitEvent(mask)` | Extended Task 阻塞等待事件 | 仅 Extended Task |

> `ChainTask` 的妙处：它保证"终止当前 + 激活下一个"是原子操作，**不会在中间插入任何其他任务**，常用于"一段流程跑完接力给下一阶段"的确定性编排。

### 2.5 同优先级轮转示例

假设 TaskA、TaskB 优先级相同且配了 RR 时间片 5ms：A 跑 5ms → 强制切到 B → B 跑 5ms → 切回 A……如此轮流。注意轮转只发生在**同优先级**之间，任何更高优先级任务就绪都会立即打断轮转。

---

## 3. 中断（ISR）

中断是 OS 之外"异步打断"的来源。AUTOSAR OS 把 ISR 分成两类，区别在"OS 管不管你"。

### 3.1 Category 1 vs Category 2

- **Category 1 ISR（一类中断）**：**不调用任何 OS 服务**，OS 甚至"不知道"它存在——硬件直接跳进去跑，跑完直接返回。它最快、确定性最好，但**不能**激活任务、不能 SetEvent、不能上锁。适合极短、纯硬件操作的临界代码（清标志、置位）。
- **Category 2 ISR（二类中断）**：**受 OS 管理**，可以调用 OS 服务（`ActivateTask`、`SetEvent`、`IncrementCounter` 等）。OS 会在进入/退出时做必要的上下文与重调度处理。绝大多数业务相关中断（CAN 接收、定时器）都走 Cat2。

> 经验法则：只想最快清个硬件位用 Cat1；要在中断里唤醒任务/触发逻辑，必须 Cat2。Cat1 的中断延迟最低，但 Cat2 提供了和任务系统的桥梁。

### 3.2 中断优先级 vs 任务优先级

这是经典混淆点，必须讲清：

- **任务优先级** 只在同一核内的任务之间比较、只决定任务间谁抢占谁。
- **中断优先级（硬件 NVIC 优先级）** 高于**所有任务**。任何 Cat2 中断一来，都会打断当前任务（前提是没被更高硬件优先级的中断或 OS 锁屏蔽）。
- 中断之间按**硬件优先级**嵌套；Cat2 ISR 退出时，OS 会做一次重调度，决定回到原任务还是切到被它激活的更高优先级任务。
- 中断里仍然受 `OsIsrResource`（中断级资源）和"中断禁用时间"时序保护约束。

### 3.3 ISR 与 Counter/Alarm 的协同

硬件定时器的中断（Cat2）通常就是某个 **Counter 的驱动源**：每次 tick 中断里调用 `IncrementCounter(counter)`，Counter 累加后，OS 自动检查挂在这个 Counter 上的 Alarm 和 ScheduleTable 是否到期。这条链路是 AUTOSAR 整个"时间驱动"的发动机。

---

## 4. 计数器（Counter）

### 4.1 概念

**Counter 是一个单调递增的整数 tick 计数器**，是 AUTOSAR OS 一切时间相关机制（Alarm、ScheduleTable、Timing Protection）的计时基准。两类：

- **硬件 Counter（HARDWARE）**：由硬件定时器中断驱动，每次中断 `IncrementCounter` 加 1。这是真实的"时钟心跳"。
- **软件 Counter（SOFTWARE）**：不绑定硬件，由别的 Counter 通过 Alarm 的 `IncrementCounter` 动作或显式 API 推动，用于产生不同时间粒度的衍生计数。

### 4.2 关键配置参数（面试常考）

| 参数 | 含义 |
|---|---|
| `OsCounterMaxAllowedValue` | Counter 能取到的最大值（到顶后回绕到 0） |
| `OsCounterTicksPerBase` | 多少个硬件 tick 才让 Counter 加 1（分频） |
| `OsCounterMinCycle` | 对该 Counter 上 Alarm/调度表允许的最小周期（防止太频繁） |
| `OsCounterSecondsPerTick` | 每个 Counter tick 代表的真实秒数（物理时间基准） |
| `OsCounterType` | HARDWARE / SOFTWARE |

### 4.3 时间换算公式

设 `SecondsPerTick = S`，`TicksPerBase = T`，硬件晶振周期 `H`：

- 一个 Counter tick 的时间 = `TicksPerBase × H`（即 `S`）。
- 要产生 `D` 秒的周期：`Alarm Cycle = D / S`（向上取整，且不能小于 `MinCycle`，不能大于 `MaxAllowedValue`）。
- **回绕（wraparound）**：由于 Counter 是有限整数，设置相对 Alarm 时算的是"模 MaxAllowedValue+1"的偏移，OS 内部会正确处理跨零点。

> 举例：若 `SecondsPerTick = 1ms`、`MaxAllowedValue = 2^32-1`，那一个 Counter 理论上能计到约 49 天不回绕。若你要 10ms 周期的任务，Alarm Cycle = 10。

---

## 5. 闹钟（Alarm）

### 5.1 基于 Counter

**Alarm 不是独立时钟，它挂在某个 Counter 上**，当 Counter 走到指定值时触发一个动作。Alarm 是 AUTOSAR 实现"周期性/一次性定时任务"最基础的机制。

### 5.2 四种动作（Action）

配置 Alarm 时必须指定到期后要干什么，四选一：

| 动作 | 效果 |
|---|---|
| `ACTIVATETASK` | 激活指定任务（最常用，周期任务的来源） |
| `SETEVENT` | 给指定 Extended Task 设置事件（唤醒等待中的任务） |
| `INCREMENTCOUNTER` | 推动另一个软件 Counter（链式计时） |
| `ALARMCALLBACK` | 调用一个回调函数（Callback，轻量、不在任务上下文） |

### 5.3 设置 API

| API | 作用 |
|---|---|
| `SetRelAlarm(alarm, offset, cycle)` | 相对"现在"偏移 `offset` 后首次触发，每 `cycle` 重复（`cycle=0` 表示单次） |
| `SetAbsAlarm(alarm, start, cycle)` | 在 Counter 绝对值 `start` 处首次触发 |
| `CancelAlarm(alarm)` | 取消（停止）该 Alarm |
| `GetAlarm(alarm, &tick)` | 查询距离下次触发还有多少 tick |

### 5.4 单次 vs 周期

- `cycle = 0`：一次性 Alarm（到点触发一次后自动停止）。
- `cycle > 0`：周期性 Alarm，每 `cycle` tick 重复触发，直到被 `CancelAlarm`。
- Alarm 可配置 **Autostart**（系统启动 `StartOS` 时按指定 AppMode 自动起），也可运行时动态 `SetRelAlarm`。

---

## 6. 调度表（Schedule Table）

### 6.1 动机：为什么不用一堆 Alarm

一个 10ms 周期里你要在 0ms 激活任务 A、2ms SetEvent B、5ms 激活 C、8ms 回调 D……如果用 4 个 Alarm 分别配，它们彼此独立、漂移累积、难以整体同步。

**Schedule Table（调度表）就是为"在一个周期内精确编排多个到期点"而生**：它把"哪个时刻做什么动作"打包成一张表，由单一 Counter 驱动，天然对齐、无漂移。

### 6.2 结构：Expiry Point

调度表由一串 **Expiry Point（到期点）** 组成，每个到期点有：

- `Offset`：相对表起点的偏移 tick。
- 一组 **Action**（和 Alarm 的四种动作相同：ActivateTask / SetEvent / IncrementCounter / Callback）。
- `OsScheduleTableExpiryPoint` 还可配 `OsScheduleTableCell` 指向具体动作对象。

表末尾还有 `OsScheduleTableFinalDelay`（到终点后到下一轮起点的间隔）。

### 6.3 同步策略（重点，面试易深挖）

调度表启动后，如何和全局时间/其他表对齐？三种策略：

| 策略 | 含义 |
|---|---|
| `NONE` | 不同步，启动后自顾自跑，可能有抖动 |
| `IMPLICIT` | 以"驱动它的 Counter"为时间基准，在 Counter 的特定点（如系统滴答）隐式同步 |
| `EXPLICIT` | OS 提供 `SyncScheduleTable` / `SetScheduleTableAsync` 等 API 显式校准，可主动"拉长/缩短"对齐到全局时基（如整车时间同步） |

- EXPLICIT 同步允许 `OsScheduleTableMaxShortening` / `MaxLengthening` 限制每次校准能"偷/补"的最大 tick 数，保证抖动有界。
- **对齐误差（deviation）**：显式同步时 OS 会计算当前表与理想时基的偏差，并在允许的缩短/拉长范围内修正，使多个 ECU 上的调度表步调一致（对时间敏感网络/协同控制很重要）。

### 6.4 状态机与启动 API

状态：`STOPPED` → `RUNNING`（或 `RUNNING_AND_SYNCHRONOUS` 当已对齐）→ 到终点后若 `Repeating` 则循环，否则 `WAITING` → 可被停止。

| API | 作用 |
|---|---|
| `StartScheduleTableAbs(table, start)` | 在 Counter 绝对值 `start` 处启动 |
| `StartScheduleTableRel(table, offset)` | 相对当前偏移启动 |
| `StopScheduleTable(table)` | 停止 |
| `NextScheduleTable(t1, t2)` | 平滑切换到下一张表（t1 跑完切 t2，不丢节拍） |
| `SyncScheduleTable(table, value)` | 显式同步校准 |

> `NextScheduleTable` 是发动机工况切换（如怠速表 → 行驶表）的利器，保证切换"无感、不重叠、不漏触发"。

### 6.5 调度表 vs Alarm 怎么选

- 单点、简单周期 → **Alarm** 足够轻量。
- 单周期内多点、且要求彼此严格对齐/漂移可控 → **Schedule Table**。
- 需要整车级时间同步 → 必须 **EXPLICIT 同步的 Schedule Table**。
- 实际项目常是"关键时序用调度表，零散延时用 Alarm"混合。

---

## 7. 事件（Event）

### 7.1 仅 Extended Task 拥有

Event 是 **Extended Task 专有的同步原语**。Basic Task 没有事件（它不能等待）。一个 Extended Task 可拥有多个事件位，用 **事件掩码（Event Mask）** 区分。

### 7.2 核心 API

| API | 作用 |
|---|---|
| `SetEvent(task, mask)` | 给某任务设置事件位（Task / Cat2 ISR 均可调用，用于唤醒） |
| `WaitEvent(mask)` | 任务阻塞，直到 `mask` 中任一位被置位 |
| `ClearEvent(mask)` | 清除自己关心的事件位（通常在处理前清，防止重复触发） |
| `GetEvent(task, &mask)` | 查询某任务的事件状态 |

### 7.3 用法与配合

典型模式：Extended Task 常驻，在一个循环里 `WaitEvent(MY_EVT)` → `ClearEvent(MY_EVT)` → 处理 → 再 `WaitEvent`。CAN 接收的 Cat2 ISR 收到报文后 `SetEvent(canTask, RX_EVT)`，唤醒任务去解析。

- **多事件等待**：`WaitEvent(EVT_A | EVT_B)` 等任一即可；醒来后用 `GetEvent` 判断是哪个。
- **与 Resource 配合**：不能在持有 Resource 时 `WaitEvent`（否则死锁——资源永远不释放），所以 WaitEvent 前必须释放资源。

---

## 8. 资源与优先级天花板

### 8.1 为什么需要资源

多任务并发访问共享数据（全局变量、外设寄存器、链表）必须互斥，否则数据撕裂。AUTOSAR OS 用 **Resource（资源）** 提供互斥，并配套一套**无死锁、无优先级反转**的协议。

### 8.2 OSEK 优先级天花板协议（Priority Ceiling Protocol）

这是 AUTOSAR OS 互斥的核心算法，必须理解：

- 每个 Resource 配一个 **天花板优先级（Ceiling Priority）** = 所有可能锁定它的任务中**最高优先级**。
- 当一个任务 `GetResource(R)` 时，OS **临时把它提升到 R 的天花板优先级**（哪怕它原本优先级低）。
- 这样，**任何锁定 R 的任务在持有期间都不会被"也可能用 R 的更低优先级任务"以外的任务打断**，从而：
  - 杜绝**优先级反转**（低任务持锁被中任务抢占、高任务又等锁的 chain 反转）。
  - 杜绝**死锁**（协议规定按天花板提升 + 释放顺序约束，递归持锁会直接报错 `E_OS_ACCESS`）。

### 8.3 API 与规则

| API | 作用 |
|---|---|
| `GetResource(res)` | 获取资源（提升自身到天花板优先级） |
| `ReleaseResource(res)` | 释放资源（恢复原本优先级） |

规则：
- 资源**必须成对、按逆序释放**（先拿 A 后拿 B，要先放 B 再放 A）。
- 持锁期间**不能** `TerminateTask` / `ChainTask` / `WaitEvent`（会破坏一致性），OS 会报错。
- 持锁时间越短越好——锁内不要做耗时运算。

### 8.4 系统资源 RES_SCHEDULER

有一个特殊资源 **`RES_SCHEDULER`**：获取它等于"禁止本核任务抢占"（等同于关任务调度，但不关中断）。`GetResource(RES_SCHEDULER)` 后，同核其他任务无法抢占你；`ReleaseResource` 后恢复。它常用于需要"一段代码原子执行、但不想关中断"的短临界区。

> 注意：`RES_SCHEDULER` 只挡任务抢占，不挡中断。要挡中断用 `DisableAllInterrupts()`/`SuspendAllInterrupts()`（但会拉长中断延迟，受时序保护约束，慎用）。

---

## 9. 多核（Multicore）

AUTOSAR 4.x 起 OS 原生支持**单芯片多核（如多核锁步/异构 MCU）**。这是现代域控的刚需。

### 9.1 OsCore 与核亲和性

- 系统被划分为多个 **OsCore**（逻辑核），每个任务/ISR/对象在配置时通过 `OsTaskOsCoreRef` / `OsIsrOsCoreRef` 绑定到某个核。
- **核内**按前述优先级抢占调度；**核间**默认互不影响（各自独立调度）。
- `StartOS` / `StartupHook` 按核分别执行；`ShutdownOS` 可由任一核触发，但全系统一起停。

### 9.2 Spinlock（跨核自旋锁）

当两份核上代码要访问**跨核共享资源**（共享 RAM、共享外设、跨核变量）时，不能用品任务级的 Resource（那是核内优先级天花板），要用 **Spinlock**：

- `GetSpinlock(lock)`：在某个核上"自旋"等待锁空闲，拿到后继续。
- `ReleaseSpinlock(lock)`：释放。
- 自旋期间该核被占住（忙等），所以**自旋锁持有时长必须极短**，否则浪费核。
- 配 `OsSpinlockLockMethod`（如 ALL_CORES 全局自旋、或按核组合），并可与 Resource 组合成"跨核+核内"双重保护。

### 9.3 IOC（Inter-OS-Application Communication）

多核/多 OS-Application 之间传递数据用 **IOC**。它不是 OS 任务，而是一组**原子数据搬运 API**（如 `IocSend`、`IocReceive`），保证在发送/接收瞬间数据一致（内部用关中断/自旋 + 双缓冲实现），避免你手写跨核共享变量踩坑。

### 9.4 核间中断（ICI）

一个核要"踢"另一个核（比如唤醒其上的任务），用 **Inter-Core Interrupt（核间中断）**。AUTOSAR OS 把 ICI 封装好，配合 `ActivateTask`（可跨核激活）和 IOC，构成多核协同的骨架。

---

## 10. 内存保护与可信模型

车规 OS 不能"一个任务写崩全系统"。AUTOSAR OS 提供多层保护。

### 10.1 Trusted vs Non-Trusted

- **Trusted OS-Application**：运行在特权（Supervisor）模式，可访问任意内存、调用全部 OS API。通常是供应商自研、经过安全认证的 BSW 模块。
- **Non-Trusted OS-Application**：运行在用户（User）模式，受 **MPU（Memory Protection Unit）** 限制，只能访问被授权给它的一块内存，越界访问会触发 **Protection Hook**。

配置 `OsApplicationTrusted = true/false` 决定。Non-Trusted 适合隔离"不太可信"的第三方/应用代码，是功能安全隔离的手段之一。

### 10.2 内存保护（MPU）与 Protection Hook

- 每个 OS-Application 配 `OsApplicationMemRef`，声明它能访问的内存区间（代码、数据、栈）。
- 越界（写别人内存、执行不该执行的区）由硬件 MPU 捕获 → OS 调用 **`ProtectionHook`**，参数说明违规类型（内存/时间/等）。
- `ProtectionHook` 可决定：终止违规应用、关闭 OS、或（若安全）重启该应用。

### 10.3 时序保护（Timing Protection）——重点

除了内存，AUTOSAR OS 还能保护"时间"不被吃穿。可针对每个 OS-Application 或任务配置：

- **Execution Budget（执行时间预算）**：任务一次运行**最长**能占多少时间，超限 → Protection Hook。
- **Lock Budget（锁定时间预算）**：持资源 / 关中断**最长**多久，超限报警（防止死循环持锁拖垮系统）。
- **Interrupt Disable Budget（中断禁用预算）**：`DisableAllInterrupts` 等最多禁用多久。

这三者共同保证：**任何单个任务/中断失控，都不会让整个 ECU 失去实时性**。这是通用 RTOS 几乎没有、而车规 ISO 26262 强烈要求的特性。

### 10.4 栈溢出检测

可配栈监测：OS 在任务栈底/顶放哨兵或在上下文切换时检查栈指针是否越界，发现溢出即触发保护。**栈一定要按最坏路径配够**，尤其 Extended Task（常驻、栈一直占着）。

---

## 11. 钩子函数（Hooks）

OS 在关键生命周期点回调用户代码，用于埋点、统计、故障处理：

| Hook | 触发时机 | 典型用途 | 限制 |
|---|---|---|---|
| `StartupHook` | `StartOS` 后、调度开始前 | 板级初始化收尾、变量清零 | 不能调阻塞 OS 服务 |
| `ShutdownHook` | `ShutdownOS` 时 | 进入安全状态、保存现场 | 最后关头 |
| `ErrorHook` | OS 服务返回错误（`E_OS_*`）时 | 错误日志、看门狗喂狗兜底 | 不能调可能再错的同服务 |
| `PreTaskHook` | 任务切换**进入**某任务前 | 性能计数、栈检查 | 不能调阻塞服务 |
| `PostTaskHook` | 任务切换**离开**前 | 统计、清资源 | 同左 |
| `ProtectionHook` | 发生保护违规（内存/时间）时 | 故障仲裁、安全响应 | 决定系统命运 |

> 钩子本质是"OS 预留的回调插槽"。`PreTaskHook/PostTaskHook` 常被用来做**每任务 CPU 占用统计**（车规项目常用，证明各任务实时性达标）。

---

## 12. 错误处理与 Shutdown

- OS 服务出错返回标准错误码：`E_OS_ACCESS`（权限/顺序错）、`E_OS_RESOURCE`（资源未释放）、`E_OS_CALLEVEL`（调用层级错，如在中断里调不能调的）、`E_OS_LIMIT`（激活超限）、`E_OS_ID`、`E_OS_STATE` 等。
- **EXTENDED Status**（扩展状态）下 OS 会做更多参数/状态校验（配 `OsStatus = EXTENDED`），开发期排错强，但有一点开销；**STANDARD Status** 更省，假设调用都正确。
- `ShutdownOS(error)`：进入有序关闭，调用 `ShutdownHook`，ECU 进入安全状态（如切断高压、点亮故障灯）。功能安全场景下，"该停就停"比"带病运行"安全。

---

## 13. 调度与运行时逻辑（核心）

这一章是"OS 到底怎么跑"的灵魂，结合前面所有对象。

### 13.1 重调度时机（调度点）

OS **不是时刻都在调度**，而是在固定"调度点"判断是否要切换。调度点包括：

1. 任务调用 `TerminateTask` / `ChainTask` / `Schedule` 主动让出。
2. 任务调用 `ReleaseResource` / `ReleaseSpinlock` 释放了（可能提升过的）优先级。
3. 任务调用 `SetEvent` / `ActivateTask`（特别在 Cat2 ISR 里）使更高优先级任务就绪。
4. Cat2 中断**结束**返回时（OS 检查是否有更高优先级任务被中断唤醒）。
5. Alarm / 调度表到期触发动作使任务就绪。
6. `WaitEvent` 使当前任务进入 Waiting（主动让出）。

> 关键洞察：**抢占只发生在调度点**。即使高优先级任务已就绪，也要等当前任务跑到下一个调度点（如释放资源、ISR 返回）才真正切换——这就是"确定性的来源"。

### 13.2 抢占与立即抢占

- 在 FULL 抢占模型下，一旦调度点发现**有更高优先级任务就绪，且当前不是持有 `RES_SCHEDULER`/未关抢占**，立即切换过去。
- 同优先级不互相抢占（除非 RR 时间片到）。
- NON 抢占任务一旦运行，只有自己 `Schedule()` 或终止才会让出。

### 13.3 一个完整调度时序（文字推演）

假设：任务 H（prio 高）、M（中）、L（低）都配在核 0，全 FULL 抢占。

1. 初始 L 在跑（处理共享数据，持有资源 R，R 天花板 = H）。
2. 定时器 Cat2 中断到来 → OS 打断 L，进 ISR；ISR 里 `ActivateTask(H)`。
3. ISR 返回 → 调度点：H 就绪且优先级最高 → **抢占 L，切到 H**。
4. H 跑，需要 R，但 R 被 L 拿着 → H 阻塞等 R（H 优先级高，但资源被占，只能等）。
5. 回到 L 继续（因为 L 持 R 时被提升到 R 的天花板 = H，所以中间不会被 M 抢，保证 L 尽快放锁）。
6. L `ReleaseResource(R)` → 调度点：H 立刻拿到 R 并继续跑完 → `TerminateTask`。
7. 回到 M（次高）跑 → 最后 L。

这个例子同时展示了**优先级天花板如何消除优先级反转**（步骤 5 中 L 持锁期间不被 M 抢占，快速放锁，H 尽快拿到）。

### 13.4 确定性从哪来

- 对象数量、优先级、栈、周期**全静态** → 最坏执行时间（WCET）可分析。
- 调度点固定 → 响应延迟可上界计算。
- 时序保护 → 失控有兜底。
- 这套组合让 AUTOSAR OS 能过 **ISO 26262 ASIL-D** 这样的严格功能安全认证——这是它存在的根本价值。

---

## 14. 与 RTE / BSW 的协同

### 14.1 Task ↔ Runnable 映射

在 AUTOSAR 设计工具里，SWC 的 **Runnable（可执行实体）** 被"分配"到某个 OS Task 上：

- 多个 Runnable 可以映射到**同一个 Task**（它们在该任务上下文里顺序执行）。
- 一个 Runnable 也可以独占一个 Task（确定性最强，开销最大）。

RTE 生成代码，把"Runnable 调用"塞进 Task 的函数体里。所以**你写的 SWC 应用代码，最终是被 OS 任务带着跑的**——开发者通常不直接碰 OS API，RTE 和工具链替你接好。

### 14.2 Event 触发 Runnable

RTE 常用 OS Event 实现"数据到达才跑"：比如 CAN 接收 ISR `SetEvent(rxTask, DATA_RDY)`，rxTask 上的 Runnable 被唤醒去读数据。定时器类 Runnable 则由 Alarm/调度表 `ActivateTask` 周期性触发。

### 14.3 模式管理与 BSW 调度

- **EcuM（ECU State Manager）** 管 ECU 上下电状态机，`StartOS`/`ShutdownOS` 由它驱动。
- **BswM（BSW Mode Manager）** 根据模式（如正常运行/诊断/升级）切换 OS 的 AppMode、启停 ScheduleTable、激活/挂起任务。
- **BswM 的 MainFunction** 本身也是个被 OS 周期性调度的任务，负责"模式仲裁 + 执行动作"。
- 所以 OS 不光跑应用，还跑 BSW 自己的周期服务（Com_MainFunction、NvM_MainFunction、WdgM 等），这些 MainFunction 都是挂在 Task/Alarm 上的。

---

## 15. 配置项详解（AUTOSAR XML 容器）

AUTOSAR OS 全部由 **XML（arxml）** 静态配置（老 OSEK 用 OIL 语言，AUTOSAR 用 XML 描述，本质一样：声明式配置生成 C 代码）。以下是核心配置容器与关键参数（面试"配置项"考点）：

### 15.1 顶层 Os 配置（`/Os/OsOS`）

| 参数 | 含义 |
|---|---|
| `OsStatus` | STANDARD / EXTENDED（是否做扩展错误检查） |
| `OsScalabilityClass` | SC1 / SC2 / SC3 / SC4（见第 16 章） |
| `OsClass` | BCC1 / BCC2 / ECC1 / ECC2（OSEK OS 类） |
| `OsUseGetServiceId` | 是否在 ErrorHook 里提供错误服务 ID |
| `OsUseParameterAccess` | 是否提供出错参数 |
| `OsUseResScheduler` | 是否启用 RES_SCHEDULER 系统资源 |

### 15.2 Counter / Alarm / ScheduleTable

| 容器 | 关键参数 | 说明 |
|---|---|---|
| `OsCounter` | MaxAllowedValue, TicksPerBase, MinCycle, SecondsPerTick, Type | 计时基准 |
| `OsAlarm` | CounterRef, Action(ActivateTask/SetEvent/IncrementCounter/Callback), ActivateTaskRef, SetEventRef, EventRef, IncrementCounterRef, CallbackName, Autostart | 定时动作 |
| `OsScheduleTable` | CounterRef, ExpiryPoint[], Offset, Repeating, SyncStrategy(IMPLICIT/EXPLICIT/NONE), MaxShortening, MaxLengthening, FinalDelay, Autostart | 多点到点调度 |

### 15.3 Task / ISR / Event / Resource / Spinlock

| 容器 | 关键参数 |
|---|---|
| `OsTask` | Priority, Activation(最大激活次数), Schedule(FULL/NON), Type(BASIC/EXTENDED), ResourceRef[], EventRef[], StackSize, OsCoreRef, AccessingApplication[] |
| `OsISRObject` | Category(CATEGORY_1/CATEGORY_2), Priority, ResourceRef[], OsCoreRef |
| `OsEvent` | Mask, TaskRef |
| `OsResource` | Property(STANDARD/INTERNAL/LINKED), Priority(天花板优先级), LinkedResourceRef, OsCoreRef |
| `OsSpinlock` | LockMethod, ResourceRef[], OsCoreRef |
| `OsApplication` | Trusted, MemRef[], OsCoreRef, TimingProtection[...] |
| `OsAppMode` | 模式名（用于 StartOS/Autostart 按模式启动） |

> 配置经验：优先级分配要"高实时/高频率在前"；Resource 天花板优先级要 ≥ 所有会用它的任务优先级；栈大小按 WCET 最坏调用深度留余量；多核资源用 Spinlock 而非 Resource。

### 15.4 OIL vs XML

- **OIL（OSEK Implementation Language）**：OSEK 时代的文本配置语言，语法类似 `TASK myTask { PRIORITY = 10; ... };`。
- **AUTOSAR XML（arxml）**：AUTOSAR 用统一 XML Schema 描述整个 ECU 配置（含 OS、BSW、RTE），工具（DaVinci Configurator、ETAS ISOLAR、Vector MICROSAR）读 arxml 生成 OS 的 C 代码与链接脚本。
- 两者思想一致：**声明对象 + 属性 → 工具生成静态 OS**。

---

## 16. 可扩展等级（Scalability Classes）

AUTOSAR OS 定义了 4 个可扩展等级，决定你能用哪些高级特性（直接影响功能安全等级与资源占用）：

| 特性 | SC1 | SC2 | SC3 | SC4 |
|---|---|---|---|---|
| 基础调度（Task/ISR/Alarm/Event） | ✓ | ✓ | ✓ | ✓ |
| 多核（Multicore） | ✗ | ✓ | ✗ | ✓ |
| 内存保护（MPU/Trusted） | ✗ | ✗ | ✓ | ✓ |
| 时序保护（Timing Protection） | ✗ | ✓ | ✓ | ✓ |

记忆口诀：**SC2 = 多核；SC3 = 保护；SC4 = 全都要**。SC1 最轻量（单核、无保护），适合简单低成本 ECU；ASIL 高的安全关键 ECU 通常上 SC3/SC4。

> 注意区分两个"等级"概念，面试极易被绕：
> - **OSEK OS Class（BCC1/BCC2/ECC1/ECC2）**：描述"任务类型与多次激活能力"，是对象能力的等级。
> - **AUTOSAR Scalability Class（SC1–SC4）**：描述"多核/保护/时序"等系统特性的等级。
> 它们正交——一个 SC4 系统里仍然可以只用 BCC1 任务。

---

## 17. 工程实践与面试深挖锚点

### 17.1 常见坑

- **死锁**：持资源时 WaitEvent / TerminateTask → `E_OS_RESOURCE`。务必"先清事件、放资源，再让出"。
- **优先级反转**：忘记天花板协议、或天花板优先级配低 → 高任务被低任务拖死。Resource 天花板必须 ≥ 所有潜在持锁任务优先级。
- **栈溢出**：Extended Task 常驻且栈一直占着，WCET 最坏路径没算够就溢出。
- **中断里调错 API**：Cat1 不能调 OS 服务；某些 API 不能在特定调用层级（Call Level）调，否则 `E_OS_CALLEVEL`。
- **多核自旋锁持太久**：自旋是忙等，核被占死，必须极短。
- **ScheduleTable 同步漂移**：忘了配 EXPLICIT 同步导致多 ECU 步调不一致，时间敏感场景出诡异 bug。

### 17.2 与功能安全的挂钩

- OS 的**内存保护 + 时序保护 + Protection Hook** 是 ISO 26262 里"避免干扰（Freedom From Interference, FFI）"和"故障响应"的落地手段。
- Trusted/Non-Trusted 隔离让"未认证的应用代码"不能污染"已认证的安全相关 BSW"。
- 这部分常是面试从"你会用 AUTOSAR OS"深挖到"你懂不懂安全"的跳板。

### 17.3 与题库的衔接

本章与题库 `autosar` 标签、`rtos` 标签、`safety` 标签的题目互为表里：本章讲"OS 是什么、为什么这么设计"，题库题讲"面试官会怎么问、真实翻车点"。配合《进阶深挖》《技能知识点梳理》里的总线、MCAL、功能安全章节一起复习，AUTOSAR OS 这一关基本稳。

> 一句话收尾：**AUTOSAR OS 不是"更快的 RTOS"，而是一套"为车规功能安全而生的、静态配置、可认证、带保护的操作系统标准"——理解它的对象模型与调度逻辑，才算真正摸到了汽车嵌入式软件的脉搏。**
