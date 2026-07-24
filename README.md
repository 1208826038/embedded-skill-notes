# 嵌入式 / BMS 工程师成长工具箱

> 个人知识沉淀 + 面试题库 + 实用工程脚本合集，面向汽车嵌入式 / BMS 软件工程师。

本仓库收集了作者在学习与项目中沉淀的资料：**技能梳理文档、外设协议详解、离线模拟面试应用，以及一个可直接复用的 Polyspace 静态分析自动化脚本**。既可以作为复习资料，也可以作为技术作品集对外分享。

---

## 📂 仓库内容

| 文件 | 说明 |
|------|------|
| `技能知识点梳理_章子淳.md` | 20 个模块技能梳理（内核/RTOS/功能安全/MCAL/通信/编译/工具链/BMS/诊断/低功耗/存储/AUTOSAR/测试/实时性/车规/信号完整性…），又深又广 |
| `外设协议详解_章子淳.md` | 13 种外设协议逐字段（逐位/逐参数）详解 + 对应面试题（CAN/LIN/SPI/I²C/SMBus/UART/SENT/FlexRay/车载以太网/PWM/ICU/ADC/GPIO/DSI3/PSI5） |
| `面试神器_章子淳.html` | 单文件离线 Web 应用：模拟面试（145 题 + 语音朗读/作答 + 智能评分 + 弱项复习 + 面试官追问）+ 知识学习（内嵌上述文档，可搜索）+ 收藏进度 |
| `polyspace_automation.py` | **Polyspace 静态分析（MISRA / 功能安全）自动化脚本**，自动建工程、跑分析、处理报告、出 JSON 汇总 |

> 注：原始脚本文件名为 `新建 文本文档.txt`，内容为 Python，已重命名为 `polyspace_automation.py` 便于分享与运行。

---

## 🛠 Polyspace 自动化脚本

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
直接用浏览器打开 `面试神器_章子淳.html` 即可（无需联网，语音朗读离线可用，语音识别需 Chrome/Edge 联网）。功能：
- **模拟面试**：145 道真题，逐题显示参考答案，自评掌握度，统计进度与正确率，支持方向筛选、随机、弱项优先、面试官追问。
- **知识学习**：内嵌三份文档，可搜索高亮、目录跳转。
- **收藏/进度**：localStorage 本地保存。

---

## ⚠️ 免责声明
本仓库为**个人学习与技术沉淀材料**，部分脚本源自实际工程实践、已做脱敏（不含密码 / Token / 内网地址）。`polyspace_automation.py` 依赖特定目录结构与 MATLAB Polyspace 环境，直接套用前请按你的项目结构调整。内容仅供学习参考，欢迎交流指正。
