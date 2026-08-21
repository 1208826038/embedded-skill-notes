# UDS 统一诊断服务深度解析（ISO 14229-1）

> 面向底层/BSW 工程师：把 UDS 从"听过 $22 读数据"讲透到"会话状态机、传输层分段、AUTOSAR DCM/DEM 怎么落地、刷写流程怎么走"。这是车厂面试和 Bootloader 开发的硬通货。

## 1. UDS 是什么、不是什么

UDS（Unified Diagnostic Services，统一诊断服务）是 **ISO 14229-1** 定义的一套应用层诊断协议，运行在_tester（诊断仪/客户端）与 ECU（服务端）之间，基于**请求-响应**模型：客户端发一帧请求，ECU 回一帧响应。

- 它不是 OBD-II：OBD-II（ISO 15031）是法规排放诊断，只管发动机/排放相关、PID 固定；UDS 是整车所有 ECU 的通用诊断，服务丰富、可扩展。OBD-II 可看作 UDS 的一个子集式存在。
- 它不是传输协议：UDS 是应用层，真正在总线上跑要靠**传输层 ISO-TP（ISO 15765-2，基于 CAN）**或 **DoIP（基于以太网）**。

## 2. 协议栈位置

> 应用层：  UDS (ISO 14229-1)  —— 服务语义
> 传输层：  ISO-TP (15765-2)   —— 长报文分段（CAN 每帧仅 8 字节）
>         或 DoIP (13400)       —— 以太网承载
> 网络层：  网络层 (15765-2 也含寻址)
> 数据链路：CAN (或 Ethernet)
> 物理层：  CAN 收发器 / 车载以太网

在 AUTOSAR 里对应：DCM（诊断通信管理，实现 UDS）+ CanTp/DoIP（传输层）+ Com/CAN（通信）。

## 3. 服务基本格式与负响应

请求帧：`[SID] [子功能] [参数...]`。SID 是服务标识符（如 0x22）。

正响应：`[SID + 0x40] [子功能] [数据...]`。注意正响应 SID = 原 SID + 0x40。例如读数据 $22 的正响应是 $62。

负响应：`0x7F [SID] [NRC]`。NRC（Negative Response Code）说明失败原因。例如 `7F 22 31` 表示读数据请求越界（requestOutOfRange）。

> 关键点：诊断仪判断成败就看回的是 SID+0x40（成功）还是 0x7F（失败带 NRC）。

## 4. 核心服务详解

### 4.1 $10 DiagnosticSessionControl（诊断会话控制）

切换 ECU 会话模式。常见会话：

| 会话 ID | 名称 | 用途 |
|---|---|---|
| 0x01 | defaultSession | 上电默认，多数服务禁用 |
| 0x02 | programmingSession | 刷写/标定 |
| 0x03 | extendedSession | 扩展诊断，解锁更多服务 |
| 0x40+ | 自定义 | OEM 私有 |

多数服务（如 $22/$2E/$27 等）只有在 non-default 会话才可用；default 下只允许少数（如 $3E）。

### 4.2 $11 ECUReset（ECU 复位）

子功能：0x01 hardReset、0x02 keyOffOnReset、0x03 softReset。刷写完或配置变更后常用 softReset 重启生效。

### 4.3 $14 ClearDiagnosticInformation（清除故障）

参数：DTC 组（如 0xFFFFFF 表示全部）。清掉 DEM 里记录的 DTC 及快照。

### 4.4 $19 ReadDTCInformation（读故障，最核心服务之一）

子功能极多，面试常考：

| 子功能 | 含义 |
|---|---|
| 0x01 | 按状态掩码报告 DTC 数量 |
| 0x02 | 按状态掩码报告 DTC 列表 |
| 0x04 | 按 DTC 报告快照数据（Snapshot，故障时环境值） |
| 0x06 | 按 DTC 报告扩展数据（计数/老化） |
| 0x0A | 报告支持的 DTC（全部） |

### 4.5 $22 ReadDataByIdentifier（按 ID 读数据）

最常用的"读任何标定/状态"的接口。DID（Data Identifier）是 2 字节，OEM 自行分配：

| DID 示例 | 内容 |
|---|---|
| 0xF190 | VIN 车辆识别号 |
| 0xF180 | 硬件版本 |
| 0xF181 | 软件版本 |
| 0xF186 | ECU 零件号 |
| 0x0100+ | 业务逻辑数据（电压/温度/SOC…） |

### 4.6 $2E WriteDataByIdentifier（按 ID 写数据）

对应 $22 的写版本，用于写标定、序列号、配置字等。通常需先经 $27 安全解锁。

### 4.7 $23 / $24 读写内存

$23 ReadMemoryByAddress、$24 ReadScalingDataByIdentifier，直接按地址读写，常用于底层调试（也最危险，必须安全门控）。

### 4.8 $27 SecurityAccess（安全访问，Seed-Key）

刷写/写关键数据前的"权限门"。流程：

> 客户端: $27 01            (请求 seed，子功能奇数=请求)
> ECU:    67 01 [seed]      (返回随机数 seed)
> 客户端: 计算 key = f(seed)  (本地算法)
> 客户端: $27 02 [key]      (子功能偶数=发送 key)
> ECU:    67 02             (验证 key 正确 → 解锁)

- 算法 f 是 OEM 私有（常是简单变换或查表），方向相反防逆向。
- 失败 NRC：0x35 invalidKey、0x36 exceedNumberOfAttempts（次数超限锁死）、0x37 requiredTimeDelayNotExpired（需等待）。

### 4.9 $28 CommunicationControl（通信控制）

使能/禁止某些报文收发（如刷写时禁止应用报文，避免总线冲突）：子功能控制"普通报文/网络管理报文/二者"的收发开关。

### 4.10 $2F InputOutputControlByIdentifier（输入输出控制）

强制某 DID 的输入/输出为指定值，用于产线测试或故障排查（如强制输出高电平看执行器）。属"覆盖控制"，用完要恢复。

### 4.11 $31 RoutineControl（例程控制）

启动/停止/查询结果类"函数调用"。子功能：0x01 start、0x02 stop、0x03 requestResults。常用例程：部件自检、擦除内存、校验和。参数里带 routineIdentifier（RID）。

### 4.12 $3E TesterPresent（诊断仪在线）

子功能 0x00（通常）。作用是**保活**：default 会话有 S3 超时，长时间无 $3E 会退回 default，导致已解锁服务失效。刷写/诊断过程中周期性发 $3E。

### 4.13 $85 ControlDTCSetting（DTC 设置控制）

开启/关闭 DTC 的记录（不影响已存 DTC 读取）。刷写或特殊工况时可临时关闭记录避免误报。

### 4.14 刷写四件套 $34/$36/$37

- $34 RequestDownload：告诉 ECU 要下一段数据的格式/长度/地址。
- $36 TransferData：逐块传数据（blockSequenceCounter 递增）。
- $37 RequestTransferExit：传输结束。
- 配合 $31 RoutineControl 做校验和/依赖检查。

## 5. 负响应码 NRC 一览

| NRC | 含义 | 触发场景 |
|---|---|---|
| 0x11 | serviceNotSupported | 当前会话/ECU 不支持该 SID |
| 0x12 | subFunctionNotSupported | 子功能不支持 |
| 0x13 | incorrectMessageLengthOrInvalidFormat | 长度错 |
| 0x22 | conditionsNotCorrect | 前提条件不满足（如不在对应会话） |
| 0x31 | requestOutOfRange | 参数超范围（DID/长度非法） |
| 0x33 | securityAccessDenied | 未解锁 |
| 0x35 | invalidKey | key 错误 |
| 0x36 | exceedNumberOfAttempts | 尝试次数超限 |
| 0x37 | requiredTimeDelayNotExpired | 时间延迟未到 |
| 0x70 | uploadDownloadNotAccepted | 下载不被接受（地址/长度错） |
| 0x72 | generalProgrammingFailure | 编程失败 |
| 0x78 | requestCorrectlyReceived-ResponsePending | 忙，请等待（ECU 延时响应） |

> 0x78 很特殊：ECU 收到请求但要长时间处理（如写 Flash），先回 0x78 让诊断仪别超时，处理完再回正式响应。

## 6. 会话 / 安全状态机与时序

- **会话状态机**：上电 default → 收 $10 03 进 extended → 可解锁服务；进 $10 02 programming 才能刷写。default 下 S3 超时（典型几千 ms）自动回 default，已解锁状态清空。
- **安全等级**：每个会话可有多个安全等级（security level），不同等级允许不同服务/$27 算法。
- **时序参数**：
  - P2：ECU 收到请求到开始响应的超时（默认 ~50ms）。
  - P2*：发过 0x78 后的扩展超时（~5000ms）。
  - S3：诊断仪两次通信间的最大间隔（保活超时）。

## 7. 传输层 ISO-TP（为什么需要分段）

CAN 一帧只有 8 字节（经典 CAN），而 UDS 请求/响应（如 $34/$36 刷写数据、长 DID 读）远超 8 字节。ISO-TP 四种帧：

| 帧类型 | 用途 |
|---|---|
| SF 单帧 | 数据 ≤ 7 字节，一帧搞定 |
| FF 首帧 | 长报文第一帧，带总长度 |
| CF 连续帧 | 后续分片（带序号 0~15 循环） |
| FC 流控帧 | 接收方告诉发送方：继续/等待/溢出，以及块大小/间隔 |

多帧拼接后才是完整的 UDS 报文。DoIP（以太网）则是 TCP/UDP 承载，天然支持大包，用于高速刷写。

## 8. AUTOSAR 中的诊断实现

- **DCM（Diagnostic Communication Manager）**：实现 UDS。分三层：DSL（状态机/会话/时序/P2/S3）、DSD（服务分发/验 NRC）、DSP（具体服务处理）。配置 DID、RID、会话、安全等级。
- **DEM（Diagnostic Event Manager）**：管理 DTC 的置位/清除/Debounce/老化/快照/扩展数据，供 $19 读取。DTC 状态字（8 位：测试失败/确认/_pending 等）按 ISO 14229 定义。
- **FiM（Function Inhibition Manager）**：根据 DEM 事件抑制某些功能（如某传感器故障→禁用例程）。
- **传输层模块**：CanTp（CAN）或 DoIP（以太网），把长 UDS 报文分段/重组。

> 配置视角：你在 EB tresos / DaVinci 里配的是 DCM 的 DID 列表、$19 子功能使能、DEM 的 Event→DTC 映射、CanTp 的帧参数——不是手写协议栈。

## 9. 典型刷写（Bootloader）流程

> 1. 进入 extendedSession ($10 03)
> 2. 关 DTC 记录 ($85 02) + 禁应用报文 ($28)
> 3. 进 programmingSession ($10 02)
> 4. 安全解锁 ($27 01/02, seed-key)
> 5. 擦除 ($31 routine 擦除)
> 6. 请求下载 ($34) → 传数据 ($36 ×N) → 结束 ($37)
> 7. 校验 ($31 routine 校验和)
> 8. 复位 ($11) 或 回 default

## 10. 工程坑与面试高频

- **坑**：忘了周期 $3E，会话超时掉回 default，刷写到一半解锁失效；ISO-TP 流控帧没发导致发送卡死；$78 被诊断仪当失败；DID 读写未配安全等级导致越权；多帧首帧长度算错。
- **高频题**：
  1. UDS 和 OBD-II 区别？
  2. 正响应 SID 怎么算？负响应格式？
  3. $22 和 $2E 区别？DID 是什么？
  4. $19 有哪些子功能？DTC 状态字几位？
  5. $27 seed-key 流程？NRC 35/36/37 含义？
  6. 为什么需要 ISO-TP 分段？四种帧？
  7. DoIP 是什么，为什么用以太网？
  8. P2/P2*/S3 是什么？
  9. 0x78 负响应什么意思？
  10. AUTOSAR 里 DCM/DEM/FiM 各管什么？
  11. 刷写完整流程？
  12. 安全访问失败次数超限怎么处理？
  13. 多帧报文怎么重组？
  14. $3E 不发的后果？
  15. 为什么写关键数据前要解锁？
