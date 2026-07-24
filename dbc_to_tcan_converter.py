import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import codecs
import locale
from pathlib import Path
import sys
import getopt


class DbcToTcanConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("DBC to TCAN Config Converter")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 获取系统默认编码
        self.system_encoding = locale.getpreferredencoding(False)

        # 配置文件路径 - 简化的相对路径表示
        self.pbcfg_relative_path = "../../../Source/CDD/Can_44_TCAN4x5x/src/Can_44_TCAN4x5x_PBcfg.c"

        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))

        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(main_frame, text="DBC to TCAN Configuration Converter", style="Header.TLabel").pack(pady=(0, 20))

        # DBC文件选择
        dbc_frame = ttk.Frame(main_frame)
        dbc_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dbc_frame, text="DBC File:").pack(side=tk.LEFT, padx=(0, 10))

        self.dbc_path_var = tk.StringVar()
        dbc_entry = ttk.Entry(dbc_frame, textvariable=self.dbc_path_var, width=50)
        dbc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(dbc_frame, text="Browse...", command=self.browse_dbc).pack(side=tk.RIGHT)

        # 编码选择
        encoding_frame = ttk.Frame(main_frame)
        encoding_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(encoding_frame, text="File Encoding:").pack(side=tk.LEFT, padx=(0, 10))

        # 常见编码列表，将系统默认编码放在前面
        common_encodings = [self.system_encoding, "utf-8", "gbk", "gb2312", "latin-1", "iso-8859-1", "cp1252"]
        # 去重
        common_encodings = list(dict.fromkeys(common_encodings))

        self.encoding_var = tk.StringVar(value=self.system_encoding)
        encoding_combobox = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding_var,
            values=common_encodings,
            state="readonly",
            width=15
        )
        encoding_combobox.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(encoding_frame, text="Try Common Encodings", command=self.try_common_encodings).pack(side=tk.LEFT)

        # 输出文件选择 - Cfg.h
        cfg_frame = ttk.Frame(main_frame)
        cfg_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(cfg_frame, text="Output Cfg.h File:").pack(side=tk.LEFT, padx=(0, 10))

        self.output_cfg_var = tk.StringVar()
        cfg_entry = ttk.Entry(cfg_frame, textvariable=self.output_cfg_var, width=50)
        cfg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(cfg_frame, text="Browse...", command=self.browse_output_cfg).pack(side=tk.RIGHT)

        # 输出文件选择 - CanIf_TCAN4x5x_Lcfg.c
        lcfg_frame = ttk.Frame(main_frame)
        lcfg_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(lcfg_frame, text="Output CanIf_TCAN4x5x_Lcfg.c File:").pack(side=tk.LEFT, padx=(0, 10))

        self.output_lcfg_var = tk.StringVar()
        lcfg_entry = ttk.Entry(lcfg_frame, textvariable=self.output_lcfg_var, width=50)
        lcfg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        ttk.Button(lcfg_frame, text="Browse...", command=self.browse_output_lcfg).pack(side=tk.RIGHT)

        # 配置选项
        config_frame = ttk.LabelFrame(main_frame, text="Configuration Options")
        config_frame.pack(fill=tk.X, pady=(0, 20))

        # DEV_ERROR_DETECT配置
        dev_error_frame = ttk.Frame(config_frame)
        dev_error_frame.pack(fill=tk.X, pady=(10, 5), padx=10)

        ttk.Label(dev_error_frame, text="CANIF_TCAN4X5X_DEV_ERROR_DETECT:").pack(side=tk.LEFT, padx=(0, 10))

        self.dev_error_var = tk.StringVar(value="STD_OFF")
        dev_error_off = ttk.Radiobutton(dev_error_frame, text="STD_OFF", variable=self.dev_error_var, value="STD_OFF")
        dev_error_off.pack(side=tk.LEFT, padx=(0, 10))

        dev_error_on = ttk.Radiobutton(dev_error_frame, text="STD_ON", variable=self.dev_error_var, value="STD_ON")
        dev_error_on.pack(side=tk.LEFT)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 20))

        # 状态标签
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var).pack(pady=(0, 20))

        # 转换按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(button_frame, text="Convert", command=self.convert, style="TButton").pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Exit", command=root.quit).pack(side=tk.RIGHT, padx=(0, 10))

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="Conversion Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        self.log_text.config(state=tk.DISABLED)

    def browse_dbc(self):
        """浏览选择DBC文件，并自动建议以DBC名称命名的输出文件"""
        filename = filedialog.askopenfilename(
            title="Select DBC File",
            filetypes=[("DBC Files", "*.dbc"), ("All Files", "*.*")]
        )
        if filename:
            self.dbc_path_var.set(filename)
            # 获取DBC文件名（不含扩展名）
            dbc_basename = os.path.splitext(os.path.basename(filename))[0]
            dir_name = os.path.dirname(filename)

            # 自动建议输出文件名，使用DBC名称作为前缀
            # 默认输出路径设置为../../../Source/CDD/Can_44_TCAN4x5x/include和src
            include_dir = os.path.abspath(os.path.join(dir_name, "../../../Source/CDD/Can_44_TCAN4x5x/include"))
            src_dir = os.path.abspath(os.path.join(dir_name, "../../../Source/CDD/Can_44_TCAN4x5x/src"))

            # 创建目录（如果不存在）
            os.makedirs(include_dir, exist_ok=True)
            os.makedirs(src_dir, exist_ok=True)

            if not self.output_cfg_var.get():
                self.output_cfg_var.set(os.path.join(include_dir, f"CanIf_TCAN4x5x_Cfg.h"))

            if not self.output_lcfg_var.get():
                self.output_lcfg_var.set(os.path.join(src_dir, "CanIf_TCAN4x5x_Lcfg.c"))

    def browse_output_cfg(self):
        """浏览选择Cfg.h输出文件"""
        # 获取当前DBC文件名作为默认配置文件名
        dbc_path = self.dbc_path_var.get()
        default_filename = "CanIf_TCAN4x5x_Cfg.h"

        # 默认输出路径设置为../../../Source/CDD/Can_44_TCAN4x5x/include
        initialdir = None
        if dbc_path:
            dir_name = os.path.dirname(dbc_path)
            initialdir = os.path.abspath(os.path.join(dir_name, "../../../Source/CDD/Can_44_TCAN4x5x/include"))
            os.makedirs(initialdir, exist_ok=True)

        filename = filedialog.asksaveasfilename(
            title="Save CanIf_TCAN4x5x_Cfg.h File",
            defaultextension=".h",
            filetypes=[("Header Files", "*.h"), ("All Files", "*.*")],
            initialfile=default_filename,
            initialdir=initialdir
        )
        if filename:
            self.output_cfg_var.set(filename)

    def browse_output_lcfg(self):
        """浏览选择CanIf_TCAN4x5x_Lcfg.c输出文件"""
        # 默认输出路径设置为../../../Source/CDD/Can_44_TCAN4x5x/src
        dbc_path = self.dbc_path_var.get()
        initialdir = None
        if dbc_path:
            dir_name = os.path.dirname(dbc_path)
            initialdir = os.path.abspath(os.path.join(dir_name, "../../../Source/CDD/Can_44_TCAN4x5x/src"))
            os.makedirs(initialdir, exist_ok=True)

        filename = filedialog.asksaveasfilename(
            title="Save CanIf_TCAN4x5x_Lcfg.c File",
            defaultextension=".c",
            filetypes=[("C Files", "*.c"), ("All Files", "*.*")],
            initialfile="CanIf_TCAN4x5x_Lcfg.c",
            initialdir=initialdir
        )
        if filename:
            self.output_lcfg_var.set(filename)

    def log(self, message):
        """向日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
        self.root.update_idletasks()

    def try_common_encodings(self):
        """尝试常见编码并找到可行的编码"""
        dbc_path = self.dbc_path_var.get()
        if not dbc_path or not os.path.exists(dbc_path):
            messagebox.showerror("Error", "Please select a valid DBC file first")
            return

        self.log("Trying common encodings...")

        # 常见编码列表，优先尝试系统编码
        encodings_to_try = [self.system_encoding, "utf-8", "gbk", "gb2312", "latin-1", "iso-8859-1", "cp1252"]

        # 读取部分内容用于测试
        try:
            with open(dbc_path, 'rb') as f:
                test_data = f.read(10000)  # 读取前10KB
        except Exception as e:
            self.log(f"Error reading file: {str(e)}")
            return

        # 测试每种编码
        working_encodings = []
        for encoding in encodings_to_try:
            try:
                # 尝试解码测试数据
                test_data.decode(encoding)
                working_encodings.append(encoding)
                self.log(f"Encoding works: {encoding}")
            except UnicodeDecodeError:
                self.log(f"Encoding failed: {encoding}")
            except LookupError:
                self.log(f"Encoding not supported: {encoding}")

        if working_encodings:
            self.log(f"Found {len(working_encodings)} working encodings")
            self.encoding_var.set(working_encodings[0])
            return working_encodings[0]
        else:
            self.log("No working encodings found. Will use fallback mode.")
            return None

    def read_dbc_file(self, dbc_file_path):
        """读取DBC文件，尝试多种编码"""
        # 获取用户选择的编码
        selected_encoding = self.encoding_var.get()

        # 先尝试用户选择的编码
        try:
            with codecs.open(dbc_file_path, 'r', encoding=selected_encoding) as f:
                content = f.read()
            self.log(f"Successfully read file with selected encoding: {selected_encoding}")
            return content
        except UnicodeDecodeError:
            self.log(f"Failed to read with selected encoding: {selected_encoding}")
        except LookupError:
            self.log(f"Selected encoding is not supported: {selected_encoding}")
        except Exception as e:
            self.log(f"Error reading with selected encoding: {str(e)}")

        # 如果用户选择的编码失败，尝试常见编码
        self.log("Trying common encodings as fallback...")
        encodings_to_try = [self.system_encoding, "utf-8", "gbk", "gb2312", "latin-1", "iso-8859-1", "cp1252"]

        # 排除已经尝试过的编码
        if selected_encoding in encodings_to_try:
            encodings_to_try.remove(selected_encoding)

        for encoding in encodings_to_try:
            try:
                with codecs.open(dbc_file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.log(f"Successfully read file with fallback encoding: {encoding}")
                self.encoding_var.set(encoding)  # 更新选择的编码
                return content
            except UnicodeDecodeError:
                self.log(f"Fallback failed with encoding: {encoding}")
            except LookupError:
                self.log(f"Fallback encoding not supported: {encoding}")
            except Exception as e:
                self.log(f"Error with fallback encoding {encoding}: {str(e)}")

        # 如果所有编码都失败，使用替换错误的方式读取
        try:
            with open(dbc_file_path, 'rb') as f:
                raw_content = f.read()
            content = raw_content.decode('utf-8', errors='replace')
            self.log("Using final fallback: replaced undecodable characters with  ")
            return content
        except Exception as e:
            self.log(f"Final fallback failed: {str(e)}")
            return None

    def parse_dbc(self, dbc_file_path):
        """解析DBC文件，提取报文和信号信息，新增识别GenSigStartValue和ByteOrder"""
        self.log(f"Parsing DBC file: {dbc_file_path}")
        self.update_progress(10)

        # 读取DBC文件（带编码处理）
        dbc_content = self.read_dbc_file(dbc_file_path)
        if dbc_content is None:
            self.log("Failed to read DBC file with any encoding")
            return None

        self.update_progress(20)

        # 提取所有节点
        bu_match = re.search(r'BU_: (.*?)\n', dbc_content, re.DOTALL)
        nodes = []
        if bu_match:
            nodes = [node.strip() for node in bu_match.group(1).split()]
        self.log(f"Found nodes: {', '.join(nodes)}")

        # 提取所有GenSigStartValue属性
        gen_sig_start_values = {}
        gen_sig_pattern = re.compile(r'BA_ "GenSigStartValue" SG_ \d+ (\w+) (\d+);')
        for match in gen_sig_pattern.finditer(dbc_content):
            sig_name = match.group(1)
            start_value = int(match.group(2))
            gen_sig_start_values[sig_name] = start_value
            self.log(f"Found GenSigStartValue for {sig_name}: {start_value}")

        # 提取所有报文
        bo_pattern = re.compile(r'BO_ (\d+) (\w+): (\d+) (\w+)\s+(.*?)(?=BO_|BS_|$)', re.DOTALL)
        messages = []

        self.log("Extracting messages...")
        self.update_progress(30)

        matches = list(bo_pattern.finditer(dbc_content))
        total_messages = len(matches)

        for i, match in enumerate(matches):
            msg_id, msg_name, msg_length, sender = match.group(1, 2, 3, 4)
            signals_content = match.group(5)

            # 提取信号
            sg_pattern = re.compile(
                r'SG_ (\w+) : (\d+)\|(\d+)@(\d)([+-]) \(([^,]+),([^)]+)\) \[([^|]+)\|([^]]+)\] "([^"]*)"  (\w+)',
                re.DOTALL)
            signals = []

            for sg_match in sg_pattern.finditer(signals_content):
                sig_name = sg_match.group(1)
                start_bit = int(sg_match.group(2))
                sig_length = int(sg_match.group(3))
                endianness = sg_match.group(4)  # @后面的数字，0=Motorola, 1=Intel
                sign = sg_match.group(5)
                factor = sg_match.group(6)
                offset = sg_match.group(7)
                min_val = sg_match.group(8)
                max_val = sg_match.group(9)
                unit = sg_match.group(10)
                receiver = sg_match.group(11)

                # 确定信号方向 (Tx/Rx)
                direction = "Tx" if sender == "BMU" else "Rx"

                # 获取初始值，如果不存在则默认为0
                start_value = gen_sig_start_values.get(sig_name, 0)

                signals.append({
                    'name': sig_name,
                    'start_bit': start_bit,
                    'length': sig_length,
                    'endianness': endianness,  # 保存原始值，0=Motorola, 1=Intel
                    'ByteOrder': int(endianness),  # 转换为整数用于结构体
                    'sign': sign,
                    'factor': factor,
                    'offset': offset,
                    'min_val': min_val,
                    'max_val': max_val,
                    'unit': unit,
                    'receiver': receiver,
                    'direction': direction,
                    'start_value': start_value  # 新增初始值属性
                })

            messages.append({
                'id': msg_id,  # 报文ID（十进制）
                'id_int': int(msg_id),  # 报文ID整数形式
                'hex_id': f"0x{int(msg_id):X}",  # 报文ID（十六进制）
                'name': msg_name,
                'length': msg_length,
                'sender': sender,
                'signals': signals
            })

            # 更新进度
            progress = 30 + (i / total_messages) * 30
            self.update_progress(progress)

        self.log(f"Extracted {len(messages)} messages with {sum(len(m['signals']) for m in messages)} signals")
        self.update_progress(60)

        return {
            'nodes': nodes,
            'messages': messages
        }

    def generate_tcan_config_header(self, dbc_data, output_file_path):
        """生成CanIf_TCAN4x5x_Cfg.h文件，更新SigInfoType移除PduPosition，添加ByteOrder成员"""
        self.log(f"Generating configuration header: {output_file_path}")

        # 分离Tx和Rx报文
        tx_messages = [msg for msg in dbc_data['messages'] if msg['sender'] == 'BMU']
        rx_messages = [msg for msg in dbc_data['messages'] if msg['sender'] != 'BMU']

        max_rx_pdu = len(rx_messages)
        max_tx_pdu = len(tx_messages)

        self.log(f"Found {len(tx_messages)} Tx messages and {len(rx_messages)} Rx messages")
        self.update_progress(70)

        try:
            # 处理冲突的PDU名称
            all_signal_names = set()
            all_pdu_names = set()
            for msg in dbc_data['messages']:
                all_pdu_names.add(msg['name'])
                for sig in msg['signals']:
                    all_signal_names.add(sig['name'])

            conflicting_names = all_signal_names.intersection(all_pdu_names)
            pdu_name_mapping = {}
            for msg in dbc_data['messages']:
                original_name = msg['name']
                if original_name in conflicting_names:
                    suffix = 0
                    while f"{original_name}_{suffix}" in all_signal_names or f"{original_name}_{suffix}" in pdu_name_mapping.values():
                        suffix += 1
                    new_name = f"{original_name}_{suffix}"
                    pdu_name_mapping[original_name] = new_name
                    self.log(f"Renamed PDU '{original_name}' to '{new_name}' to resolve conflict")
                else:
                    pdu_name_mapping[original_name] = original_name

            # 收集所有信号
            all_signals = []
            for msg in dbc_data['messages']:
                all_signals.extend(msg['signals'])

            # 生成CanIf_TCAN4x5x_Cfg.h内容
            with codecs.open(output_file_path, 'w', encoding='utf-8') as f:
                # 头文件保护
                header_guard = output_file_path.split(os.sep)[-1].replace('.', '_').upper()
                f.write(f"#ifndef {CANIF_TCAN4X5X_CFG_H}\n")
                f.write(f"#define {CANIF_TCAN4X5X_CFG_H}\n\n")

                # 包含文件
                f.write("#include \"Std_Types.h\"\n")
                f.write("#include \"Can_44_TCAN4x5x.h\"\n\n")

                # 模块配置开关
                f.write("/* Module configuration switches */\n")
                f.write(f"#define CANIF_TCAN4X5X_DEV_ERROR_DETECT    {self.dev_error_var.get()}\n")
                f.write("#define CANIF_TCAN4X5X_VERSION_INFO_API    STD_OFF\n\n\n")

                # 硬件参数
                f.write("/* Hardware parameters */\n")
                f.write("#define CANIF_TCAN4X5X_MAX_CONTROLLERS     1\n")
                f.write(f"#define CANIF_TCAN4X5X_MAX_RX_PDU          {max_rx_pdu}\n")
                f.write(f"#define CANIF_TCAN4X5X_MAX_TX_PDU          {max_tx_pdu}\n\n\n")

                # Tx Pdu宏定义
                f.write("/* Tx Pdu */\n")
                for i, msg in enumerate(tx_messages):
                    pdu_name = pdu_name_mapping[msg['name']]
                    # 确保格式对齐
                    f.write(f"#define {pdu_name.ljust(30)} {i}u\n")
                f.write("\n\n")

                # Rx Pdu宏定义
                f.write("/* Rx Pdu */\n")
                for i, msg in enumerate(rx_messages):
                    pdu_name = pdu_name_mapping[msg['name']]
                    # 确保格式对齐
                    f.write(f"#define {pdu_name.ljust(30)} {i}u\n")
                f.write("\n\n")

                # DET错误代码
                f.write("/* DET error codes */\n")
                f.write("typedef enum {\n")
                f.write("    CANIF_TCAN4X5X_E_NO_ERROR,\n")
                f.write("    CANIF_TCAN4X5X_E_PARAM_POINTER,\n")
                f.write("    CANIF_TCAN4X5X_E_PARAM_CONTROLLER,\n")
                f.write("    CANIF_TCAN4X5X_E_PARAM_PDU,\n")
                f.write("    CANIF_TCAN4X5X_E_UNINIT,\n")
                f.write("    CANIF_TCAN4X5X_E_TX_BUFFER_FULL,\n")
                f.write("    CANIF_TCAN4X5X_E_RX_BUFFER_FULL\n")
                f.write("} CanIf_TCAN4x5x_ErrorType;\n\n\n")

                # CAN帧结构
                f.write("/* CAN frame structure */\n")
                f.write("typedef struct {\n")
                f.write("    uint32 CanId;\n")
                f.write("    uint8  Data[8];\n")
                f.write("    uint8  Dlc;\n")
                f.write("    PduIdType PduId;\n")
                f.write("} CanIf_TCAN4x5x_FrameType;\n\n\n")

                # PDU配置
                f.write("/* PDU configuration */\n")
                f.write("typedef struct {\n")
                f.write("    uint32 PduId;\n")
                f.write("    uint32 CanId;\n")
                f.write("    uint8  BufferId;\n")
                f.write("    Can_HwHandleType Hth;\n")
                f.write("} CanIf_TCAN4x5x_PduConfigType;\n\n\n")

                # 控制器配置
                f.write("/* Controller configuration */\n")
                f.write("typedef struct {\n")
                f.write("    uint8 ControllerId;\n")
                f.write("    CanIf_TCAN4x5x_PduConfigType RxPdu[CANIF_TCAN4X5X_MAX_RX_PDU];\n")
                f.write("    CanIf_TCAN4x5x_PduConfigType TxPdu[CANIF_TCAN4X5X_MAX_TX_PDU];\n")
                f.write("    uint8 NumRxPdu;\n")
                f.write("    uint8 NumTxPdu;\n")
                f.write("} CanIf_TCAN4x5x_ControllerConfigType;\n\n\n")

                # 模块全局配置
                f.write("/* Module global configuration */\n")
                f.write("typedef struct {\n")
                f.write("    const CanIf_TCAN4x5x_ControllerConfigType* Controllers[CANIF_TCAN4X5X_MAX_CONTROLLERS];\n")
                f.write("    uint8 NumControllers;\n")
                f.write("    boolean InterruptMode;\n")
                f.write("} CanIf_TCAN4x5x_ConfigType;\n\n\n")

                # 信号信息结构 - 移除PduPosition，添加ByteOrder成员
                f.write("typedef struct\n")
                f.write("{\n")
                f.write("    uint8 *Data;\n")
                f.write("    uint8 SignalSize;\n")
                f.write("    uint8 PduId;\n")
                f.write("    uint32 CanId;\n")
                f.write("    uint8 ByteOrder;    /* 0 = Motorola, 1 = Intel */\n")
                f.write("    uint8 StartBit;\n")
                f.write("    uint8 SignalLength;\n")
                f.write("} SigInfoType;\n\n\n")

                # 全局配置extern声明
                f.write("extern const CanIf_TCAN4x5x_ConfigType CanIf_TCAN4x5x_Config;\n\n\n")

                # 信号变量和SigInfoType extern声明
                for signal in all_signals:
                    # 根据信号长度确定变量类型
                    if signal['length'] <= 8:
                        var_type = 'uint8'
                    elif signal['length'] <= 16:
                        var_type = 'uint16'
                    elif signal['length'] <= 32:
                        var_type = 'uint32'
                    else:
                        var_type = 'uint64'

                    f.write(f"extern {var_type} {signal['name']};\n")
                    f.write(f"extern SigInfoType SG_{signal['name']};\n")

                # 为信号创建ComType类型定义
                for signal in all_signals:
                    # 根据信号长度确定变量类型
                    if signal['length'] <= 8:
                        var_type = 'uint8'
                    elif signal['length'] <= 16:
                        var_type = 'uint16'
                    elif signal['length'] <= 32:
                        var_type = 'uint32'
                    else:
                        var_type = 'uint64'

                    direction_prefix = "Tx" if signal['direction'] == "Tx" else "Rx"
                    f.write(f"typedef {var_type} ComType_CHCAN_{direction_prefix}_{signal['name']}_B;\n")

                # RTE函数声明 - Tx使用值传递，Rx使用指针传递
                for signal in all_signals:
                    direction = signal['direction']
                    signal_name = signal['name']

                    if direction == "Tx":
                        # Tx函数使用值传递
                        f.write(
                            f"extern FUNC(Std_ReturnType, RTE_CODE) Rte_Write_COMC_Com_CHCAN_Tx_{signal_name}_B(ComType_CHCAN_Tx_{signal_name}_B data);\n")
                    else:
                        # Rx函数使用指针传递
                        f.write(
                            f"extern FUNC(Std_ReturnType, RTE_CODE) Rte_Read_COMC_Com_CHCAN_Rx_{signal_name}_B(ComType_CHCAN_Rx_{signal_name}_B *data);\n")

                # 头文件结束
                f.write(f"\n#endif /* {CANIF_TCAN4X5X_CFG_H} */")

            # 创建PDU名称到ID的映射，供Lcfg.c使用
            pdu_id_mapping = {}
            for i, msg in enumerate(tx_messages):
                pdu_name = pdu_name_mapping[msg['name']]
                pdu_id_mapping[pdu_name] = i

            for i, msg in enumerate(rx_messages):
                pdu_name = pdu_name_mapping[msg['name']]
                pdu_id_mapping[pdu_name] = i

            return True, tx_messages, rx_messages, pdu_name_mapping, pdu_id_mapping, all_signals

        except Exception as e:
            self.log(f"Error writing header file: {str(e)}")
            return False, [], [], {}, {}, []

    def generate_canif_lcfg_c(self, tx_messages, rx_messages, pdu_name_mapping, pdu_id_mapping,
                              all_signals, output_file_path):
        """生成CanIf_TCAN4x5x_Lcfg.c文件，使用GenSigStartValue初始化信号并设置ByteOrder"""
        self.log(f"Generating CanIf_TCAN4x5x_Lcfg.c file: {output_file_path}")

        try:
            with codecs.open(output_file_path, 'w', encoding='utf-8') as f:
                # 文件头部包含
                f.write("#include \"CanIf_TCAN4x5x_Cfg.h\"\n")
                f.write("#include \"Std_Types.h\"\n\n")

                # 信号变量定义 - 使用GenSigStartValue作为初始值
                f.write("/* Signal variables with initial values from GenSigStartValue */\n")
                for signal in all_signals:
                    # 根据信号长度确定变量类型
                    if signal['length'] <= 8:
                        var_type = 'uint8'
                    elif signal['length'] <= 16:
                        var_type = 'uint16'
                    elif signal['length'] <= 32:
                        var_type = 'uint32'
                    else:
                        var_type = 'uint64'

                    # 使用从DBC提取的初始值，默认为0
                    start_value = signal['start_value']
                    f.write(f"{var_type} {signal['name']} = {start_value}u;\n")
                f.write("\n\n")

                # 信号信息结构体定义 - 移除PduPosition，添加ByteOrder成员
                f.write("/* Signal information structures with ByteOrder */\n")
                for signal in all_signals:
                    # 查找信号所属的消息
                    msg = next((m for m in tx_messages + rx_messages if signal in m['signals']), None)
                    if not msg:
                        continue

                    pdu_name = pdu_name_mapping[msg['name']]

                    # 根据根据信号长度确定SignalSize
                    if signal['length'] <= 8:
                        signal_size = 1
                    elif signal['length'] <= 16:
                        signal_size = 2
                    elif signal['length'] <= 32:
                        signal_size = 4
                    else:
                        signal_size = 8

                    # 输出结构体，移除PduPosition，包含ByteOrder、StartBit和SignalLength
                    f.write(f"SigInfoType SG_{signal['name']} = \n")
                    f.write("{\n")
                    f.write(f"    .Data  = (uint8*)&{signal['name']},\n")
                    f.write(f"    .SignalSize = {signal_size},\n")
                    f.write(f"    .PduId = {pdu_name},\n")
                    f.write(f"    .CanId = {msg['hex_id']},\n")
                    # 添加ByteOrder，0=Motorola, 1=Intel
                    f.write(
                        f"    .ByteOrder = {signal['ByteOrder']}    /* {'Intel' if signal['ByteOrder'] == 1 else 'Motorola'} */,\n")
                    # 添加StartBit和SignalLength
                    f.write(f"    .StartBit = {signal['start_bit']},\n")
                    f.write(f"    .SignalLength = {signal['length']}\n")
                    f.write("};\n\n")

                # Controller 0 配置
                f.write("/* Controller 0 configuration */\n")
                f.write("static const CanIf_TCAN4x5x_ControllerConfigType CanIf_TCAN4x5x_Controller0 = {\n")
                f.write("    .ControllerId = 0,\n")
                f.write("    .RxPdu = {\n")

                # RxPdu内容 - 使用数字ID
                rx_count = len(rx_messages)
                for i, msg in enumerate(rx_messages):
                    hrh_value = i  # 使用索引作为默认值
                    pdu_name = pdu_name_mapping[msg['name']]
                    pdu_id = pdu_id_mapping[pdu_name]

                    comma = "," if i < rx_count - 1 else ""
                    # 格式化输出，确保对齐美观
                    f.write(
                        f"        {{ .PduId = {pdu_id}u, .CanId = {msg['hex_id']}, .BufferId = {i}, .Hth = {hrh_value} }}  /* {pdu_name} */{comma}\n")

                f.write("    },\n")
                f.write("    .TxPdu = {\n")

                # TxPdu内容 - Hth值4和5交替
                tx_count = len(tx_messages)
                for i, msg in enumerate(tx_messages):
                    # Hth值在4和5之间交替
                    htx_value = 4 if i % 2 == 0 else 5
                    pdu_name = pdu_name_mapping[msg['name']]
                    pdu_id = pdu_id_mapping[pdu_name]

                    comma = "," if i < tx_count - 1 else ""
                    # 格式化输出，确保对齐美观
                    f.write(
                        f"        {{ .PduId = {pdu_id}u, .CanId = {msg['hex_id']}, .BufferId = {i}, .Hth = {htx_value} }}  /* {pdu_name} */{comma}\n")

                f.write("    },\n")
                f.write(f"    .NumRxPdu = {rx_count},\n")
                f.write(f"    .NumTxPdu = {tx_count}\n")
                f.write("};\n\n\n")

                # 全局配置
                f.write("/* Global module configuration */\n")
                f.write("const CanIf_TCAN4x5x_ConfigType CanIf_TCAN4x5x_Config = {\n")
                f.write("    .Controllers = { &CanIf_TCAN4x5x_Controller0 },\n")
                f.write("    .NumControllers = 1,\n")
                f.write("    .InterruptMode = FALSE     /* Using polling mode */\n")
                f.write("};\n\n\n")

                # 添加位操作宏定义
                f.write("/* Bit manipulation macros */\n")
                f.write("#define GET_BIT(data, bit_pos)    (((data) >> (bit_pos)) & 0x01u)\n")
                f.write("#define SET_BIT(data, bit_pos)    ((data) |= (0x01u << (bit_pos)))\n")
                f.write("#define CLEAR_BIT(data, bit_pos)  ((data) &= ~(0x01u << (bit_pos)))\n")
                f.write(
                    "#define MASK_BITS(length)         ((length) < 32 ? ((1u << (length)) - 1u) : 0xFFFFFFFFu)\n\n\n")

                # 添加位提取函数声明
                f.write("/* Bit extraction functions */\n")
                f.write("static uint64 extract_bits_intel(const uint8 *data, uint8 start_bit, uint8 length);\n")
                f.write("static uint64 extract_bits_motorola(const uint8 *data, uint8 start_bit, uint8 length);\n")
                f.write("static void intel_to_motorola(uint8 *data, uint8 length);\n\n\n")

                # 位提取函数实现 - Intel格式
                f.write("static uint64 extract_bits_intel(const uint8 *data, uint8 start_bit, uint8 length)\n")
                f.write("{\n")
                f.write("    uint64 result = 0u;\n")
                f.write("    uint8 current_bit = 0u;\n")
                f.write("    uint8 byte_index = start_bit / 8u;\n")
                f.write("    uint8 bit_index = start_bit % 8u;\n")
                f.write("\n")
                f.write("    while (current_bit < length)\n")
                f.write("    {\n")
                f.write("        if (bit_index >= 8u)\n")
                f.write("        {\n")
                f.write("            byte_index++;\n")
                f.write("            bit_index = 0u;\n")
                f.write("        }\n")
                f.write("\n")
                f.write("        if (GET_BIT(data[byte_index], bit_index))\n")
                f.write("        {\n")
                f.write("            SET_BIT(result, current_bit);\n")
                f.write("        }\n")
                f.write("        else\n")
                f.write("        {\n")
                f.write("            CLEAR_BIT(result, current_bit);\n")
                f.write("        }\n")
                f.write("\n")
                f.write("        current_bit++;\n")
                f.write("        bit_index++;\n")
                f.write("    }\n")
                f.write("\n")
                f.write("    return result & MASK_BITS(length);\n")
                f.write("}\n\n\n")

                # 位提取函数实现 - Motorola格式
                f.write("static uint64 extract_bits_motorola(const uint8 *data, uint8 start_bit, uint8 length)\n")
                f.write("{\n")
                f.write("    uint64 result = 0u;\n")
                f.write("    uint8 current_bit = 0u;\n")
                f.write("    uint8 byte_index = start_bit / 8u;\n")
                f.write("    uint8 bit_index = 7u - (start_bit % 8u);\n")
                f.write("\n")
                f.write("    while (current_bit < length)\n")
                f.write("    {\n")
                f.write("        if (bit_index >= 8u)\n")
                f.write("        {\n")
                f.write("            byte_index++;\n")
                f.write("            bit_index = 7u;\n")
                f.write("        }\n")
                f.write("\n")
                f.write("        if (GET_BIT(data[byte_index], bit_index))\n")
                f.write("        {\n")
                f.write("            SET_BIT(result, current_bit);\n")
                f.write("        }\n")
                f.write("        else\n")
                f.write("        {\n")
                f.write("            CLEAR_BIT(result, current_bit);\n")
                f.write("        }\n")
                f.write("\n")
                f.write("        current_bit++;\n")
                f.write("        bit_index--;\n")
                f.write("        if (bit_index >= 8u)  /* Handle underflow */\n")
                f.write("        {\n")
                f.write("            byte_index++;\n")
                f.write("            bit_index = 7u;\n")
                f.write("        }\n")
                f.write("    }\n")
                f.write("\n")
                f.write("    return result & MASK_BITS(length);\n")
                f.write("}\n\n\n")

                # Motorola到Intel字节序转换函数
                f.write("static void intel_to_motorola(uint8 *data, uint8 length)\n")
                f.write("{\n")
                f.write("    uint8 i;\n")
                f.write("    for (i = 0; i < length; i++)\n")
                f.write("    {\n")
                f.write("        /* Reverse the bits in each byte */\n")
                f.write("        data[i] = ((data[i] >> 1) & 0x55u) | ((data[i] << 1) & 0xAAu);\n")
                f.write("        data[i] = ((data[i] >> 2) & 0x33u) | ((data[i] << 2) & 0xCCu);\n")
                f.write("        data[i] = ((data[i] >> 4) & 0x0Fu) | ((data[i] << 4) & 0xF0u);\n")
                f.write("    }\n")
                f.write("}\n\n\n")

                # 发送和接收函数定义
                f.write("/* Signal send and receive functions */\n")
                for signal in all_signals:
                    direction = signal['direction']
                    signal_name = signal['name']

                    if direction == "Tx":
                        # 发送函数 - 使用值传递
                        f.write(
                            f"FUNC(Std_ReturnType, RTE_CODE) Rte_Write_COMC_Com_CHCAN_Tx_{signal_name}_B(ComType_CHCAN_Tx_{signal_name}_B data) /* PRQA S 0850, 1505 */ /* MD_MSR_19.8, MD_MSR_8.10 */\n")
                        f.write("{\n")
                        f.write("  Std_ReturnType ret = 0u;\n")
                        f.write(f"  {signal_name} = data;\n")
                        f.write(
                            f"  ret |= CanIf_TCAN4x5x_SendSignal(&SG_{signal_name}); /* PRQA S 0850 */ /* MD_MSR_19.8 */\n\n")
                        f.write("  return ret;\n")
                        f.write("} /* PRQA S 6010, 6030, 6050 */ /* MD_MSR_STPTH, MD_MSR_STCYC, MD_MSR_STCAL */\n\n")
                    else:
                        # 接收函数 - 使用指针传递
                        f.write(
                            f"FUNC(Std_ReturnType, RTE_CODE) Rte_Read_COMC_Com_CHCAN_Rx_{signal_name}_B(ComType_CHCAN_Rx_{signal_name}_B *data)\n")
                        f.write("{\n")
                        f.write(f"    CanIf_TCAN4x5x_ReceiveSignal(&SG_{signal_name});\n")
                        f.write(f"    *data = {signal_name};\n")
                        f.write("    return E_OK;\n")
                        f.write("}\n\n")

            self.update_progress(100)
            return True

        except Exception as e:
            self.log(f"Error writing CanIf_TCAN4x5x_Lcfg.c file: {str(e)}")
            return False

    def convert(self):
        """执行转换过程，生成配置文件"""
        dbc_path = self.dbc_path_var.get()
        cfg_path = self.output_cfg_var.get()
        lcfg_path = self.output_lcfg_var.get()

        # 检查是否在命令行模式（主窗口被隐藏）
        is_cli_mode = not self.root.winfo_ismapped()

        # 验证输入
        if not dbc_path:
            if is_cli_mode:
                print("Error: Please specify DBC file with --dbc option")
                sys.exit(1)
            else:
                messagebox.showerror("Error", "Please select a DBC file")
            return

        if not cfg_path:
            if is_cli_mode:
                print("Error: Please specify output Cfg.h file with --cfg option")
                sys.exit(1)
            else:
                messagebox.showerror("Error", "Please select an output Cfg.h file")
            return

        if not lcfg_path:
            if is_cli_mode:
                print("Error: Please specify output CanIf_TCAN4x5x_Lcfg.c file with --lcfg option")
                sys.exit(1)
            else:
                messagebox.showerror("Error", "Please select an output CanIf_TCAN4x5x_Lcfg.c file")
            return

        if not os.path.exists(dbc_path):
            if is_cli_mode:
                print(f"Error: DBC file not found: {dbc_path}")
                sys.exit(1)
            else:
                messagebox.showerror("Error", f"DBC file not found: {dbc_path}")
            return

        # 清空日志和进度
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_progress(0)
        self.status_var.set("Converting...")

        # 解析DBC
        dbc_data = self.parse_dbc(dbc_path)
        if not dbc_data:
            self.status_var.set("Conversion failed")
            if is_cli_mode:
                print("Error: Failed to parse DBC file")
                sys.exit(1)
            else:
                messagebox.showerror("Error", "Failed to parse DBC file")
            return

        self.update_progress(75)

        # 生成Cfg.h配置文件
        cfg_success, tx_messages, rx_messages, pdu_name_mapping, pdu_id_mapping, all_signals = self.generate_tcan_config_header(
            dbc_data, cfg_path)
        if not cfg_success:
            self.status_var.set("Conversion failed")
            if is_cli_mode:
                print("Error: Failed to generate CanIf_TCAN4x5x_Cfg.h file")
                sys.exit(1)
            else:
                messagebox.showerror("Error", "Failed to generate CanIf_TCAN4x5x_Cfg.h file")
            return

        # 生成CanIf_TCAN4x5x_Lcfg.c文件
        lcfg_success = self.generate_canif_lcfg_c(tx_messages, rx_messages, pdu_name_mapping,
                                                  pdu_id_mapping, all_signals, lcfg_path)
        if not lcfg_success:
            self.status_var.set("Conversion partially failed")
            if is_cli_mode:
                print("Error: Generated Cfg.h but failed to generate CanIf_TCAN4x5x_Lcfg.c")
                sys.exit(1)
            else:
                messagebox.showerror("Error", "Generated Cfg.h but failed to generate CanIf_TCAN4x5x_Lcfg.c")
            return

        self.update_progress(100)
        self.status_var.set("Conversion completed successfully")
        self.log("Conversion completed successfully!")

        if is_cli_mode:
            print("Conversion completed successfully!")
            print(f"Configuration files generated:")
            print(f"  Cfg.h: {cfg_path}")
            print(f"  Lcfg.c: {lcfg_path}")
            # 退出命令行模式下自动退出
            sys.exit(0)
        else:
            messagebox.showinfo("Success", f"Configuration files generated:\n{cfg_path}\n{lcfg_path}")


def print_usage():
    """打印使用说明"""
    print("DBC to TCAN Configuration Converter")
    print("Usage:")
    print(" 图形界面模式: python dbc_to_tcan_converter.py")
    print(" 命令行模式: python dbc_to_tcan_converter.py [options]")
    print("\nOptions:")
    print("  --dbc <file>              DBC input file (required)")
    print("  --cfg <file>              Output Cfg.h file (required)")
    print("  --lcfg <file>             Output CanIf_TCAN4x5x_Lcfg.c file (required)")
    print("  --dev-error-detect <val>  CANIF_TCAN4X5X_DEV_ERROR_DETECT value (STD_ON/STD_OFF)")
    print("  --encoding <encoding>     File encoding (e.g. utf-8, gbk)")
    print("  -h, --help                Print this help message")


def main():
    """
    主函数，支持命令行参数和图形界面两种模式
    """
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        try:
            opts, args = getopt.getopt(sys.argv[1:], "h", [
                "help", "dbc=", "cfg=", "lcfg=", "dev-error-detect=", "encoding="
            ])
        except getopt.GetoptError as e:
            print(f"Error: {e}")
            print_usage()
            sys.exit(1)

        # 解析命令行参数
        dbc_file = None
        cfg_file = None
        lcfg_file = None
        dev_error_detect = "STD_OFF"  # 默认值
        encoding = None

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print_usage()
                sys.exit(0)
            elif opt == "--dbc":
                dbc_file = arg
            elif opt == "--cfg":
                cfg_file = arg
            elif opt == "--lcfg":
                lcfg_file = arg
            elif opt == "--dev-error-detect":
                if arg.upper() in ("STD_ON", "STD_OFF"):
                    dev_error_detect = arg.upper()
                else:
                    print(f"Error: Invalid value for --dev-error-detect: {arg}")
                    print("Valid values are STD_ON and STD_OFF")
                    sys.exit(1)
            elif opt == "--encoding":
                encoding = arg

        # 检查必需参数
        if not dbc_file or not cfg_file or not lcfg_file:
            print("Error: Missing required parameters")
            print("Required: --dbc, --cfg, --lcfg")
            print_usage()
            sys.exit(1)

        # 检查文件是否存在
        if not os.path.exists(dbc_file):
            print(f"Error: DBC file not found: {dbc_file}")
            sys.exit(1)

        # 使用无头模式运行转换
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        app = DbcToTcanConverter(root)

        # 设置参数
        app.dbc_path_var.set(dbc_file)
        app.output_cfg_var.set(cfg_file)
        app.output_lcfg_var.set(lcfg_file)
        app.dev_error_var.set(dev_error_detect)

        if encoding:
            app.encoding_var.set(encoding)

        # 执行转换
        app.convert()

    else:
        # 图形界面模式
        root = tk.Tk()
        app = DbcToTcanConverter(root)
        root.mainloop()


if __name__ == "__main__":
    main()
E:\1_workcode_git\ebus2015huawe_0303\BSW\Source\CDD\Can_44_TCAN4x5x\include\CanIf_TCAN4x5x_Cfg.h
Found 20 Tx messages and 21 Rx messages
Error writing header file: name 'CANIF_TCAN4X5X_CFG_H' is not defined报着错，修一下