# 数据源接口自动化测试项目

基于 Python + pytest 的数据源查询接口自动化测试框架，支持 GUI 和命令行两种使用方式。

## ✨ 功能特性

- 🖥️ **双模式运行**：GUI 图形界面 + 命令行两种方式
- 🔄 **SQL 解析驱动**：从数据库 INSERT 语句自动解析字段配置
- 🧪 **智能用例生成**：根据字段配置自动组合生成测试用例
- 📊 **HTML 测试报告**：生成美观的测试报告
- 📦 **可打包 EXE**：支持打包成独立可执行文件

## 📁 项目结构

```
datasource-api-test/
├── gui/                     # GUI 界面
│   └── main_window.py      # 主窗口
├── config/                  # 配置文件
│   ├── config.yaml         # 环境配置
│   └── sql_input/          # SQL输入目录
├── tests/                   # 测试用例
│   ├── conftest.py         # pytest fixtures
│   ├── test_dynamic.py     # 动态生成测试
│   ├── test_basic.py       # 基础场景测试
│   ├── test_boundary.py    # 边界场景测试
│   ├── test_pagination.py  # 分页场景测试
│   └── test_no_pagination.py
├── api/                     # 接口封装
├── utils/                   # 工具模块
├── scripts/                 # 脚本
│   └── build.py            # 打包脚本
├── run.py                   # 主入口
├── start.bat / start.sh     # 启动脚本
├── requirements.txt         # 依赖包
└── README.md
```

## 🚀 快速开始

### 方式一：GUI 界面（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 GUI
python run.py --gui

# 或直接运行
python run.py
```

**Windows 用户**：双击 `start.bat` 启动

### 方式二：命令行

```bash
# 运行所有测试
python run.py --test

# 运行指定类型测试
python run.py --test --markers basic,pagination

# 列出所有数据源
python run.py --list

# 生成测试用例
python run.py --generate --widget-id 123
```

## 📝 使用 GUI

### 1. 输入 SQL 配置

在左侧文本框中粘贴 INSERT 语句：

```sql
INSERT INTO rpt_data_source_field (data_source_id, type, code, name, field, agg_type, filter_condition) VALUES
(123, 'filter', 'orgId', '组织', 'org_id', NULL, 'in'),
(123, 'index_info', 'amount', '金额', 'amount', 'sum', NULL),
(123, 'dimension', 'orgId', '组织', 'org_id', NULL, NULL);
```

### 2. 配置测试参数

- 设置服务地址、租户ID、用户ID
- 选择要运行的测试类型

### 3. 运行测试

点击 "🚀 运行测试" 按钮，测试完成后自动生成 HTML 报告。

## 🧪 测试场景

| 类型 | 用例数 | 说明 |
|------|--------|------|
| 基础场景 | 7 | 单过滤、多过滤、分组、排序、分页 |
| 组合场景 | 4 | 过滤+分组、过滤+排序、多指标 |
| 分页场景 | 10 | 首页、末页、超大页码、不同页大小 |
| 不分页场景 | 8 | single汇总、limit限制 |
| 边界场景 | 5 | 空过滤、无效ID、超大IN条件 |

## 📦 打包成 EXE

```bash
# 安装打包工具
pip install pyinstaller

# 执行打包
python scripts/build.py

# 输出位置
# dist/datasource-test-tool.exe (Windows)
# dist/datasource-test-tool-portable/ (便携版)
```

**Windows 用户**：双击 `scripts/build.bat` 打包

## 🔧 配置说明

### config.yaml

```yaml
environment:
  base_url: "http://localhost:8080"
  timeout: 30

auth:
  tenant_id: "tenant_001"
  user_id: 1001
```

### SQL 配置文件

放入 `config/sql_input/` 目录，命名格式：`datasource_{widget_id}.sql`

## 📚 命令行参数

```
用法: run.py [选项]

选项:
  --gui, -g          启动 GUI 界面（默认）
  --test, -t         运行测试
  --generate         生成测试用例
  --list, -l         列出数据源
  --add-sql SQL      添加 SQL 配置

测试选项:
  --markers, -m      测试标记 (basic,combine,pagination,no_pagination,boundary)
  --widget-id, -w    数据源ID
  --output, -o       报告输出路径

示例:
  run.py --gui                        # 启动 GUI
  run.py --test -m basic,pagination   # 运行测试
  run.py --generate -w 123            # 生成用例
```

## 🎯 核心模块

### SQL 解析器

```python
from utils.sql_parser import SQLParser

parser = SQLParser()
fields = parser.parse_sql_file("config/sql_input/datasource_123.sql")
```

### 测试用例生成器

```python
from utils.case_generator import TestCaseGenerator

generator = TestCaseGenerator(config)
cases = generator.generate_all_cases()
```

## 📄 License

MIT