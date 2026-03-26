"""GUI界面 - 数据源接口自动化测试工具"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import subprocess
import sys
import os
from pathlib import Path
import yaml
import webbrowser

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def detect_encoding(file_path: str) -> str:
    """检测文件编码，支持 GBK 等 Windows 编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    return 'utf-8'


class DataSourceTestGUI:
    """数据源接口测试 GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("数据源接口自动化测试工具 v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
        
        # 刷新数据源列表
        self.refresh_datasources()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure('Title.TLabel', font=('Microsoft YaHei', 14, 'bold'))
        style.configure('Header.TLabel', font=('Microsoft YaHei', 11, 'bold'))
        style.configure('Run.TButton', font=('Microsoft YaHei', 10))
        style.configure('Success.TLabel', foreground='green', font=('Microsoft YaHei', 10))
        style.configure('Error.TLabel', foreground='red', font=('Microsoft YaHei', 10))
    
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ========== 左侧面板 ==========
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 标题
        title_frame = ttk.Frame(left_panel)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="📝 INSERT 语句输入", style='Header.TLabel').pack(side=tk.LEFT)
        
        # SQL 输入区
        sql_frame = ttk.LabelFrame(left_panel, text="SQL 配置", padding="5")
        sql_frame.pack(fill=tk.BOTH, expand=True)
        
        # 数据源ID输入
        id_frame = ttk.Frame(sql_frame)
        id_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(id_frame, text="数据源ID:").pack(side=tk.LEFT)
        self.widget_id_var = tk.StringVar(value="123")
        ttk.Entry(id_frame, textvariable=self.widget_id_var, width=15).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(id_frame, text="数据源名称:").pack(side=tk.LEFT)
        self.widget_name_var = tk.StringVar(value="测试数据源")
        ttk.Entry(id_frame, textvariable=self.widget_name_var, width=20).pack(side=tk.LEFT, padx=5)
        
        # SQL 文本框
        self.sql_text = scrolledtext.ScrolledText(sql_frame, height=15, font=('Consolas', 10))
        self.sql_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # SQL 示例按钮
        btn_frame = ttk.Frame(sql_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_frame, text="📋 加载示例", command=self.load_example_sql).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="📂 从文件加载", command=self.load_sql_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_sql_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空", command=self.clear_sql).pack(side=tk.LEFT, padx=5)
        
        # ========== 右侧面板 ==========
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 已保存的数据源
        ds_frame = ttk.LabelFrame(right_panel, text="已配置的数据源", padding="5")
        ds_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 数据源列表
        list_frame = ttk.Frame(ds_frame)
        list_frame.pack(fill=tk.X)
        
        self.ds_listbox = tk.Listbox(list_frame, height=6, font=('Consolas', 10))
        self.ds_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 绑定选择事件，选中时自动加载到左侧
        self.ds_listbox.bind('<<ListboxSelect>>', self.on_datasource_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ds_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ds_listbox.config(yscrollcommand=scrollbar.set)
        
        # 列表操作按钮
        list_btn_frame = ttk.Frame(ds_frame)
        list_btn_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(list_btn_frame, text="🔄 刷新", command=self.refresh_datasources).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(list_btn_frame, text="❌ 删除选中", command=self.delete_datasource).pack(side=tk.LEFT, padx=5)
        
        # 配置面板
        config_frame = ttk.LabelFrame(right_panel, text="测试配置", padding="5")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 服务地址
        ttk.Label(config_frame, text="服务地址:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.base_url_var = tk.StringVar(value="http://localhost:8080")
        ttk.Entry(config_frame, textvariable=self.base_url_var, width=40).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 租户ID
        ttk.Label(config_frame, text="租户ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.tenant_id_var = tk.StringVar(value="tenant_001")
        ttk.Entry(config_frame, textvariable=self.tenant_id_var, width=40).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 用户ID
        ttk.Label(config_frame, text="用户ID:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.user_id_var = tk.StringVar(value="1001")
        ttk.Entry(config_frame, textvariable=self.user_id_var, width=40).grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        
        # 测试类型选择
        test_type_frame = ttk.LabelFrame(right_panel, text="测试类型", padding="5")
        test_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.test_types = {
            'basic': tk.BooleanVar(value=True),
            'combine': tk.BooleanVar(value=True),
            'pagination': tk.BooleanVar(value=True),
            'no_pagination': tk.BooleanVar(value=True),
            'boundary': tk.BooleanVar(value=False),
        }
        
        test_labels = {
            'basic': '基础场景 (TC001-007)',
            'combine': '组合场景 (TC101-104)',
            'pagination': '分页场景 (TC401-410)',
            'no_pagination': '不分页场景 (TC501-508)',
            'boundary': '边界场景 (TC201-205)',
        }
        
        for i, (key, var) in enumerate(self.test_types.items()):
            ttk.Checkbutton(test_type_frame, text=test_labels[key], variable=var).grid(
                row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2
            )
        
        # 错误处理选项
        error_frame = ttk.LabelFrame(right_panel, text="错误处理", padding="5")
        error_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.skip_errors_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            error_frame, 
            text="跳过错误继续执行（出错不中断，继续跑下一个用例）", 
            variable=self.skip_errors_var
        ).pack(anchor=tk.W)
        
        self.max_fail_var = tk.StringVar(value="0")
        max_fail_frame = ttk.Frame(error_frame)
        max_fail_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(max_fail_frame, text="最大失败数:").pack(side=tk.LEFT)
        ttk.Entry(max_fail_frame, textvariable=self.max_fail_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(max_fail_frame, text="(0=不限制，出错继续执行)").pack(side=tk.LEFT)
        
        # 数据库验证选项
        self.db_validate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            error_frame, 
            text="启用数据库验证（对比数据库数据）", 
            variable=self.db_validate_var
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # 运行按钮
        run_frame = ttk.Frame(right_panel)
        run_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(run_frame, text="🚀 运行测试", command=self.run_tests, style='Run.TButton', width=20).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(run_frame, text="📊 打开报告", command=self.open_report, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(run_frame, text="⚙️ 保存配置", command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
        
        # 日志输出区
        log_frame = ttk.LabelFrame(right_panel, text="执行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def log(self, message, level="INFO"):
        """输出日志"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        
        color_map = {
            "INFO": "black",
            "SUCCESS": "green",
            "ERROR": "red",
            "WARNING": "orange"
        }
        
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.root.update_idletasks()
    
    def load_config(self):
        """加载配置"""
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        if config_path.exists():
            try:
                encoding = detect_encoding(str(config_path))
                with open(config_path, 'r', encoding=encoding) as f:
                    config = yaml.safe_load(f)
                
                if config:
                    env = config.get('environment', {})
                    auth = config.get('auth', {})
                    database = config.get('database', {})
                    
                    self.base_url_var.set(env.get('base_url', 'http://localhost:8080'))
                    self.tenant_id_var.set(auth.get('tenant_id', 'tenant_001'))
                    self.user_id_var.set(str(auth.get('user_id', 1001)))
                    self.db_validate_var.set(database.get('enabled', False))
                    
                    self.log("配置加载成功", "SUCCESS")
            except Exception as e:
                self.log(f"配置加载失败: {e}", "ERROR")
    
    def save_config(self, silent=False):
        """保存配置"""
        config = {
            'environment': {
                'name': '测试环境',
                'base_url': self.base_url_var.get(),
                'timeout': 30
            },
            'auth': {
                'tenant_id': self.tenant_id_var.get(),
                'user_id': int(self.user_id_var.get())
            },
            'current_widget_id': int(self.widget_id_var.get()),  # 当前选中的数据源ID
            'database': {
                'enabled': self.db_validate_var.get(),  # 数据库验证开关
                'host': 'localhost',
                'port': 3306,
                'database': 'cfs_report',
                'user': 'root',
                'password': 'password'
            },
            'report': {
                'output_dir': 'reports/html',
                'title': '数据源查询接口测试报告'
            }
        }
        
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            self.log("配置保存成功", "SUCCESS")
            if not silent:
                messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            self.log(f"配置保存失败: {e}", "ERROR")
            if not silent:
                messagebox.showerror("错误", f"配置保存失败: {e}")
    
    def load_example_sql(self):
        """加载示例 SQL"""
        widget_id = self.widget_id_var.get() or "123"
        
        example_sql = f"""-- 数据源ID: {widget_id}
-- 数据源名称: 融资统计测试数据源

INSERT INTO rpt_data_source_field (data_source_id, type, code, name, field, agg_type, filter_condition, component_code) VALUES
({widget_id}, 'filter', 'orgId', '组织', 'org_id', NULL, 'in', 'tree-select'),
({widget_id}, 'filter', 'year', '年度', 'year', NULL, 'geq', 'date'),
({widget_id}, 'filter', 'status', '状态', 'status', NULL, 'in', 'select'),
({widget_id}, 'index_info', 'amount', '金额', 'amount', 'sum', NULL, NULL),
({widget_id}, 'index_info', 'balance', '余额', 'balance', 'sum', NULL, NULL),
({widget_id}, 'index_info', 'count', '笔数', 'id', 'count', NULL, NULL),
({widget_id}, 'dimension', 'orgId', '组织', 'org_id', NULL, NULL, NULL),
({widget_id}, 'dimension', 'month', '月份', 'month', NULL, NULL, NULL),
({widget_id}, 'orders', 'amount', '金额', 'amount', NULL, NULL, NULL);"""
        
        self.sql_text.delete(1.0, tk.END)
        self.sql_text.insert(tk.END, example_sql)
        self.log(f"已加载示例 SQL（数据源ID: {widget_id}）", "INFO")
    
    def load_sql_from_file(self):
        """从文件加载 SQL"""
        file_path = filedialog.askopenfilename(
            title="选择 SQL 文件",
            filetypes=[("SQL 文件", "*.sql"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                encoding = detect_encoding(file_path)
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                self.sql_text.delete(1.0, tk.END)
                self.sql_text.insert(tk.END, content)
                self.log(f"已加载文件: {file_path} (编码: {encoding})", "SUCCESS")
            except Exception as e:
                self.log(f"文件加载失败: {e}", "ERROR")
                messagebox.showerror("错误", f"文件加载失败: {e}")
    
    def save_sql_config(self, silent=False):
        """保存 SQL 配置到文件"""
        sql_content = self.sql_text.get(1.0, tk.END).strip()
        
        if not sql_content:
            if not silent:
                messagebox.showwarning("警告", "SQL 内容为空")
            return
        
        widget_id = self.widget_id_var.get()
        widget_name = self.widget_name_var.get()
        
        # 替换 INSERT 语句中的 data_source_id 为当前输入的值
        # 匹配格式: (123, 'filter', ...) 或 (数字, 'type', ...)
        import re
        sql_content = re.sub(
            r'\((\d+),\s*([\'"](?:filter|index_info|dimension|orders)[\'"])',
            f'({widget_id}, \\2',
            sql_content
        )
        
        # 添加注释
        full_content = f"-- 数据源ID: {widget_id}\n-- 数据源名称: {widget_name}\n\n{sql_content}"
        
        # 保存文件
        sql_dir = PROJECT_ROOT / "config" / "sql_input"
        sql_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = sql_dir / f"datasource_{widget_id}.sql"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            self.log(f"SQL 配置已保存: {file_path}", "SUCCESS")
            self.log(f"数据源ID 已更新为: {widget_id}", "INFO")
            if not silent:
                messagebox.showinfo("成功", f"配置已保存到:\n{file_path}")
            
            # 刷新列表
            self.refresh_datasources()
        except Exception as e:
            self.log(f"保存失败: {e}", "ERROR")
            if not silent:
                messagebox.showerror("错误", f"保存失败: {e}")
    
    def clear_sql(self):
        """清空 SQL"""
        self.sql_text.delete(1.0, tk.END)
        self.log("已清空 SQL 内容", "INFO")
    
    def refresh_datasources(self):
        """刷新数据源列表"""
        self.ds_listbox.delete(0, tk.END)
        
        sql_dir = PROJECT_ROOT / "config" / "sql_input"
        if sql_dir.exists():
            for sql_file in sorted(sql_dir.glob("*.sql")):
                # 尝试读取文件头获取名称
                try:
                    encoding = detect_encoding(str(sql_file))
                    with open(sql_file, 'r', encoding=encoding) as f:
                        first_lines = [f.readline() for _ in range(3)]
                    
                    name = sql_file.stem
                    for line in first_lines:
                        if '数据源名称' in line or 'name' in line.lower():
                            name = line.split(':', 1)[-1].strip().lstrip('- ')
                            break
                    
                    self.ds_listbox.insert(tk.END, f"{sql_file.stem} - {name}")
                except:
                    self.ds_listbox.insert(tk.END, sql_file.stem)
        
        self.log(f"已加载 {self.ds_listbox.size()} 个数据源配置", "INFO")
    
    def on_datasource_select(self, event):
        """数据源列表选择事件 - 自动加载到左侧编辑区"""
        selection = self.ds_listbox.curselection()
        if not selection:
            return
        
        item = self.ds_listbox.get(selection[0])
        # 解析 widget_id（格式：datasource_76 - 授信用信单位统计）
        parts = item.split(" - ", 1)
        widget_id = parts[0].replace("datasource_", "")
        widget_name = parts[1] if len(parts) > 1 else ""
        
        # 更新左侧的 ID 和名称
        self.widget_id_var.set(widget_id)
        self.widget_name_var.set(widget_name)
        
        # 加载 SQL 文件内容
        sql_file = PROJECT_ROOT / "config" / "sql_input" / f"datasource_{widget_id}.sql"
        if sql_file.exists():
            try:
                encoding = detect_encoding(str(sql_file))
                with open(sql_file, 'r', encoding=encoding) as f:
                    content = f.read()
                
                self.sql_text.delete(1.0, tk.END)
                self.sql_text.insert(tk.END, content)
                self.log(f"已加载数据源: {widget_id} - {widget_name}", "SUCCESS")
            except Exception as e:
                self.log(f"加载失败: {e}", "ERROR")
    
    def delete_datasource(self):
        """删除选中的数据源"""
        selection = self.ds_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的数据源")
            return
        
        item = self.ds_listbox.get(selection[0])
        widget_id = item.split(" - ")[0]
        
        if messagebox.askyesno("确认", f"确定要删除数据源 {widget_id} 吗？"):
            sql_file = PROJECT_ROOT / "config" / "sql_input" / f"{widget_id}.sql"
            if sql_file.exists():
                sql_file.unlink()
                self.log(f"已删除: {widget_id}", "SUCCESS")
                self.refresh_datasources()
    
    def run_tests(self):
        """运行测试"""
        # 先保存当前 SQL（静默模式，不弹窗）
        self.save_sql_config(silent=True)
        
        # 构建测试标记
        markers = []
        for key, var in self.test_types.items():
            if var.get():
                markers.append(key)
        
        if not markers:
            messagebox.showwarning("警告", "请至少选择一种测试类型")
            return
        
        # 更新配置文件（包含当前选中的数据源ID，静默模式）
        self.save_config(silent=True)
        
        self.log(f"当前测试数据源ID: {self.widget_id_var.get()}", "INFO")
        self.log("开始运行测试...", "INFO")
        self.status_var.set("运行中...")
        
        # 在后台线程运行
        thread = threading.Thread(target=self._run_tests_thread, args=(markers,))
        thread.daemon = True
        thread.start()
    
    def _run_tests_thread(self, markers):
        """在后台线程运行测试"""
        try:
            # 构建 pytest 命令
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/test_dynamic.py",
                "-v",
                f"--html=reports/html/report.html",
                "--self-contained-html",
                "-p", "no:warnings"
            ]
            
            # 添加标记过滤
            marker_expr = " or ".join(markers)
            cmd.extend(["-m", marker_expr])
            
            # 添加错误处理选项
            if self.skip_errors_var.get():
                max_fail = self.max_fail_var.get()
                try:
                    max_fail_int = int(max_fail)
                    cmd.extend([f"--maxfail={max_fail_int}"])
                except ValueError:
                    cmd.extend(["--maxfail=0"])
            
            self.log(f"执行命令: {' '.join(cmd)}", "INFO")
            
            # 执行测试
            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8'
            )
            
            # 实时输出日志
            for line in process.stdout:
                self.log(line.strip(), "INFO")
            
            process.wait()
            
            if process.returncode == 0:
                self.log("测试执行完成 ✓", "SUCCESS")
                self.status_var.set("测试完成")
                self.root.after(0, lambda: messagebox.showinfo("完成", "测试执行完成！\n\n报告已生成: reports/html/report.html"))
            else:
                self.log(f"测试执行完成，部分用例失败 (退出码: {process.returncode})", "WARNING")
                self.status_var.set("测试完成（有失败）")
                self.root.after(0, lambda: messagebox.showwarning("完成", "测试执行完成，部分用例失败\n\n请查看报告了解详情"))
                
        except Exception as e:
            self.log(f"执行失败: {e}", "ERROR")
            self.status_var.set("执行失败")
            self.root.after(0, lambda: messagebox.showerror("错误", f"执行失败:\n{e}"))
    
    def open_report(self):
        """打开测试报告"""
        report_path = PROJECT_ROOT / "reports" / "html" / "report.html"
        
        if report_path.exists():
            webbrowser.open(f"file://{report_path}")
            self.log("已打开测试报告", "INFO")
        else:
            messagebox.showwarning("提示", "报告文件不存在，请先运行测试")


def main():
    """启动 GUI"""
    root = tk.Tk()
    app = DataSourceTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()