# 操作系统进阶（七）· 嵌入式 Linux：内核、驱动与启动

> 前面六章是"通用 OS 理论"，本章把它们落到**嵌入式工程师天天打交道的 Linux** 上：内核态与模块、设备树（Device Tree）、字符设备与 platform 驱动、Linux 下的中断与并发、mmap 与内存、根文件系统与启动流程，最后系统性对比 **Linux（通用 OS）vs RTOS（如 FreeRTOS/AUTOSAR OS，见 `02`/`b09`）**。这是连接"理论"与"你仓库里 MCU/RTOS/BMS 实战"的桥。

---

## 一、为什么嵌入式也用 Linux

Cortex-A 这类**带 MMU 的应用处理器**跑 Linux，获得：
- 完整虚拟内存（进程隔离、按需调页，见 `o04`）。
- 丰富的网络/文件系统/多进程生态。
- 标准 POSIX 接口、海量开源库。
- 多核 SMP 调度。

代价：实时性不如 RTOS（主流 Linux 是**软实时**；需硬实时得上 `PREEMPT_RT` 补丁或外层套 RTOS/裸核做 AMP，见 `15-autosar-arch.md` 的 AP/CP 混合）。汽车里常见：**Cortex-A 跑 Linux 做座舱/网关，Cortex-M 跑 RTOS/AUTOSAR 做实时控制，二者 AMP 协同**。

---

## 二、内核态、用户态与模块

### 2.1 特权级

Linux 跑在 CPU 的特权级（ARM 的 EL1/EL0，x86 的 Ring0/3）：内核在特权态，能访问全部硬件；用户程序在非特权态，系统调用陷入内核（`o05` 第四章）。

### 2.2 可加载内核模块（LKM）

驱动常以**模块（`.ko`）** 形式动态加载（`insmod`/`modprobe`），免重编内核。

```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

static int __init hello_init(void) {
    pr_info("hello: module loaded\n");
    return 0;                 /* 0=成功 */
}
static void __exit hello_exit(void) {
    pr_info("hello: module unloaded\n");
}
module_init(hello_init);
module_exit(hello_exit);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("embedded-notes");
```

> 注意：`pr_info` 在内核上下文可用；用户态的 `printf` 在内核里不能用。内核编程**不能随便用浮点、不能睡在原子上下文、栈很小（常 8–16KB）**——与 `o05` 中断上下文约束同源。

---

## 三、设备树（Device Tree）：硬件描述与内核解耦

ARM Linux 早期把板级硬件信息硬编码进内核源码，导致"一板一内核"。后来引入 **Device Tree（DT）**：用 `.dts` 文本描述硬件（CPU、内存、外设寄存器地址、中断号、引脚），编译成 `.dtb` 由 bootloader 传给内核。内核驱动**只写通用逻辑**，具体硬件参数从 DT 来。

```dts
/* 示例片段：一个挂在 I2C1 上的温度传感器 */
&i2c1 {
    status = "okay";
    temp_sensor: lm75@48 {
        compatible = "national,lm75";
        reg = <0x48>;             /* I2C 地址 */
        interrupt-parent = <&gpio1>;
        interrupts = <5 IRQ_TYPE_EDGE_FALLING>;
    };
};
```

驱动靠 `compatible` 字符串匹配 DT 节点（"设备-驱动"匹配模型），实现**一份驱动适配多块板**——这正是 AUTOSAR "配置与代码分离"思想的 Linux 版（`b09`/`15-autosar-arch.md`）。

---

## 四、设备模型：字符设备、块设备、platform

### 4.1 字符设备（最常用）

按字节流访问（串口、传感器、LED、自定义 IP），实现 `open/read/write/release`/`file_operations`。

```c
static ssize_t my_read(struct file *f, char __user *buf, size_t len, loff_t *off) {
    /* 用 copy_to_user 把内核数据搬给用户态（地址空间不同！见 o04） */
    if (copy_to_user(buf, kbuf, len)) return -EFAULT;
    return len;
}
static const struct file_operations my_fops = {
    .owner = THIS_MODULE,
    .read  = my_read,
    .write = my_write,
};
/* 注册：alloc_chrdev_region + cdev_add，再在 /dev 建节点 */
```

### 4.2 platform 设备与驱动（片上外设）

片上外设（UART、I2C 控制器、看门狗）没有"即插即用"枚举，靠 platform 总线把 DT 描述的"platform device"和"platform driver"按 `compatible` 绑定。这是 MCU 外设驱动在 Linux 下的标准形态——对应仓库 `p01-p14` 那些外设（SPI/I2C/UART/CAN...）在 Linux 侧的实现框架。

### 4.3 块设备与网络

- 块设备：按块访问（eMMC/SD/SSD），走通用块层 + I/O 调度（`o06` 第七章）。
- 网络设备：不走 `read/write`，走 `socket` + 协议栈（见 `o06` 多路复用）。

---

## 五、Linux 下的中断与并发

### 5.1 中断处理

Linux 中断也分**上半部（hardirq，不可睡眠）** 与**下半部（softirq/tasklet/workqueue，可睡眠）**，与 `o05` 第五章一致。驱动里用：

```c
ret = request_irq(irq, my_isr, IRQF_TRIGGER_FALLING, "mydev", dev);
/* 下半部用 tasklet 或 workqueue 做耗时活 */
```

### 5.2 并发保护

内核态并发来源多：多核 SMP、中断、抢占。保护手段：
- **自旋锁（spinlock）**：SMP 下短临界区、原子/中断上下文（不能睡）。
- **互斥锁（mutex）**：可睡的临界区（如等 I/O）。
- **原子变量 / RCU / 读写锁**：特定场景（RCU 适合读多写少，无锁读）。
- **关闭本地中断（`local_irq_save`）**：防当前核被中断穿插。

这些和 `o03` 的锁理论一一对应，只是 API 是内核版。

---

## 六、内存：kmalloc / vmalloc / mmap

- **kmalloc**：分配**物理连续、虚拟也连续**的小块内核内存（类似 `malloc`，但用于内核）。
- **vmalloc**：虚拟连续但物理可不连续，用于大块。
- **用户态 mmap**：把设备寄存器或 DMA 缓冲**映射到用户空间**，让用户程序免 `read/write` 直接访问（常用于高速数据采集、帧缓冲）。

```c
/* 驱动把一段物理缓冲映射给用户态 */
static int my_mmap(struct file *f, struct vm_area_struct *vma) {
    return remap_pfn_range(vma, vma->vm_start,
                           phys_addr >> PAGE_SHIFT,
                           vma->vm_end - vma->vm_start,
                           vma->vm_page_prot);
}
```

> MMIO 呼应：设备寄存器经 MMIO 映射到地址空间（`o06` 第五章），`ioremap` 把物理寄存器映射到内核虚拟地址后才能访问——本质就是 `o04` 的"虚拟地址翻译"用在设备寄存器上。

---

## 七、根文件系统（rootfs）与启动流程

### 7.1 启动链

```
ROM/BootROM → SPL(可选) → U-Boot(引导加载) → 加载 zImage + DTB → 启动内核
   → 内核解压、初始化子系统
   → 挂载根文件系统（initramfs 或真实 rootfs）
   → 运行第一个用户进程 /init（或 systemd）
   → 拉起服务、shell/应用
```

### 7.2 根文件系统

嵌入式常用 **BusyBox**（把几十个基础命令打包成单个二进制）做精简 rootfs，配合 **initramfs**（内存根，用来挂载真实根或做早期初始化）、**overlayfs**（只读根 + 可写层，防磨损/易恢复）。选型呼应 `o06` 的掉电安全 FS（NAND 用 UBIFS，eMMC 用 ext4+F2FS）。

---

## 八、Linux vs RTOS：一张对照表

| 维度 | 嵌入式 Linux（Cortex-A） | RTOS（FreeRTOS/AUTOSAR OS，Cortex-M） |
| --- | --- | --- |
| 内存管理 | MMU 虚拟内存、按需调页 | 无 MMU，MPU 仅保护，共享物理空间 |
| 调度 | 通用（CFS）+ 实时（PREEMPT_RT 补丁） | 抢占/时间片，静态配置（AUTOSAR） |
| 任务模型 | 进程/线程（重，隔离强） | Task（轻，共享地址空间） |
| 切换开销 | 高（换页表+TLB） | 低（不换页表） |
| 实时性 | 软实时（打补丁才硬） | 硬实时（可静态分析 WCET） |
| 生态 | 网络/文件/多进程丰富 | 精简、确定、可认证 |
| 适用 | 座舱/网关/HPC | 控制/安全关键 ECU |
| 调试 | gdb/ftrace/perf | 逻辑分析仪/RTT/Tracealyzer |

> 工程结论：要**确定性的硬实时控制**用 RTOS/AUTOSAR（`02`/`b09`）；要**丰富生态与多进程并发**用 Linux；复杂域控二者 AMP 共存（见 `15-autosar-arch.md`）。

---

## 九、常见坑

1. **内核里用用户态函数**：`printf`/`malloc` 不行，要用 `pr_info`/`kmalloc`，并区分能否睡眠。
2. **忘了 `copy_to/from_user`**：内核与用户地址空间不同（`o04`），直接解引用用户指针会崩（`-EFAULT`）。
3. **DT 与驱动 `compatible` 不匹配**：设备不probe，驱动白写；检查 dts 与驱动 `of_match_table`。
4. **原子上下文睡大觉**：在中断/持自旋锁时调用会睡眠的函数，死机。
5. **模块未释放资源**：`rmmod` 后中断/内存没清，第二次 `insmod` 冲突。
6. **mmap 没考虑 cache 一致性**：DMA 缓冲若被 CPU cache 缓存，需 `dma_alloc_coherent` 或刷 cache，否则看到旧数据。
7. **把 Linux 当 RTOS 用**：拿普通 Linux 跑硬实时控制环，错过死线——该上 PREEMPT_RT 或外包给 RTOS 核。

---

## 十、面试要点

1. **Linux 内核态与用户态怎么切换？** 系统调用/中断/异常陷入内核，执行完 `iret/sysret` 返回（见 `o05`）。
2. **设备树解决什么？** 把硬件描述从内核代码解耦，一份驱动靠 `compatible` 适配多块板；类 AUTOSAR 配置分离。
3. **字符设备驱动核心结构？** `file_operations`（open/read/write/release）+ 注册 `cdev` + 建 `/dev` 节点；用户数据用 `copy_to/from_user`。
4. **platform 驱动干嘛用？** 管理片上无枚举外设，DT 的 platform device 与 driver 按 compatible 绑定。
5. **kmalloc vs vmalloc？** 前者物理+虚拟都连续（小块），后者仅虚拟连续（大块）。
6. **mmap 在驱动里做什么？** 把设备寄存器/DMA 缓冲映射到用户空间，免系统调用直接访问。
7. **Linux 与 RTOS 本质区别？** MMU 虚拟内存+重进程 vs 无 MMU 共享空间+轻任务；硬实时靠 RTOS/AUTOSAR，丰富生态靠 Linux，复杂系统 AMP 共存。
