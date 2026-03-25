# 数据源接口自动化测试项目

基于 Python + pytest 的数据源查询接口自动化测试框架，支持 GUI 和命令行两种使用方式。

## ✨ 功能特性

- 🖥️ **双模式运行**：GUI 图形界面 + 命令行两种方式
- 🔄 **SQL 解析驱动**：支持简化格式（8字段）和完整格式（26字段）INSERT 语句解析
- 🧪 **智能用例生成**：根据字段配置自动组合生成测试用例
- 🎯 **单数据源测试**：只运行当前选中的数据源，不干扰其他配置
- 📊 **HTML 测试报告**：生成美观的测试报告
- ⚡ **错误跳过**：支持出错继续执行，不中断测试
- 📦 **可打包 EXE**：支持打包成独立可执行文件

## 📁 项目结构

```
datasource-api-test/
├── gui/                     # GUI 界面
│   └── main_window.py      # 主窗口
├── config/                  # 配置文件
│   ├── config.yaml         # 环境配置
│   └── sql_input/          # SQL输入目录
│       └── datasource_*.sql # 数据源配置文件
├── tests/                   # 测试用例
│   ├── conftest.py         # pytest fixtures
│   └── test_dynamic.py     # 动态生成测试
├── api/                     # 接口封装
│   ├── client.py           # HTTP 客户端
│   └── data_query.py       # 数据查询接口
├── utils/                   # 工具模块
│   ├── sql_parser.py       # SQL 解析器
│   ├── case_generator.py   # 用例生成器
│   └── assertion.py        # 断言工具
├── reports/                 # 测试报告
│   └── html/               # HTML 报告
├── run.py                   # 主入口
├── start.bat / start.sh     # 启动脚本
├── requirements.txt         # 依赖包
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 GUI

```bash
python run.py
```

**Windows 用户**：双击 `start.bat` 启动

### 3. 配置测试

1. 在 GUI 界面输入**数据源ID**和**数据源名称**
2. 粘贴 INSERT 语句到左侧文本框
3. 配置服务地址、租户ID、用户ID
4. 点击 **"🚀 运行测试"**

## 📝 SQL 配置格式

### 完整格式（从数据库导出）

支持 26 字段的完整 INSERT 格式，直接从数据库导出即可使用：

```sql
INSERT INTO `cfs_report`.`u_rpt_data_source_field` 
(`id`, `data_source_id`, `type`, `code`, `decimal_places`, `code_alias`, `field`, 
 `field_value`, `agg_type`, `mapping_field`, `name`, `convert_unit`, `component_code`, 
 `component_option_json`, `show_front`, `allow_wrap`, `variables`, `create_user`, 
 `create_dept`, `create_time`, `update_user`, `update_time`, `status`, `is_deleted`, 
 `filter_condition`, `is_default`) 
VALUES (29240, 76, 'filter', 'orgId', NULL, 'orgId', 'org_id', NULL, NULL, NULL, 
        '组织', 0, 'tree-select', NULL, 1, 1, NULL, 0, 0, '2026-03-12 10:00:00', 
        0, '2026-03-12 10:00:00', 1, 0, 'in', 0);

INSERT INTO `cfs_report`.`u_rpt_data_source_field` (...) VALUES (..., 76, 'index_info', 'amount', ...);
INSERT INTO `cfs_report`.`u_rpt_data_source_field` (...) VALUES (..., 76, 'dimension', 'orgId', ...);
```

### 简化格式（8字段）

也支持简化的 8 字段格式：

```sql
INSERT INTO rpt_data_source_field (data_source_id, type, code, name, field, agg_type, filter_condition, component_code) VALUES
(123, 'filter', 'orgId', '组织', 'org_id', NULL, 'in', 'tree-select'),
(123, 'index_info', 'amount', '金额', 'amount', 'sum', NULL, NULL),
(123, 'dimension', 'orgId', '组织', 'org_id', NULL, NULL, NULL);
```

### 字段类型说明

| type | 说明 |
|------|------|
| `filter` | 过滤条件 |
| `index_info` | 指标字段 |
| `dimension` | 维度字段（分组） |
| `orders` | 排序字段 |

## 🎮 GUI 界面操作

### 选择数据源

在右侧"已配置的数据源"列表中**点击选择**，会自动：
- 填充数据源ID和名称
- 加载 SQL 内容到编辑区

### 运行测试

1. 选择测试类型（基础/组合/分页/不分页/边界）
2. 配置错误处理选项
3. 点击 **"🚀 运行测试"**
4. 测试完成后点击 **"📊 打开报告"** 查看结果

### 配置选项

| 选项 | 说明 |
|------|------|
| **服务地址** | API 服务地址，如 `http://127.0.0.1:8110` |
| **租户ID** | 租户标识 |
| **用户ID** | 用户标识 |
| **跳过错误继续执行** | 出错不中断，继续执行下一个用例 |
| **最大失败数** | 0=不限制 |
| **启用数据库验证** | 对比数据库数据（可选） |

## 🧪 测试场景

| 类型 | 用例编号 | 说明 |
|------|----------|------|
| **基础场景** | TC001-007 | 仅查询指标、单过滤、多过滤、单维度、双维度、排序、分页 |
| **组合场景** | TC101-104 | 过滤+分组、过滤+排序、过滤+分组+排序、多指标 |
| **分页场景** | TC401-405 | 首页、中间页、超大页码、大页大小 |
| **不分页场景** | TC501-503 | 默认查询、single汇总、limit限制 |
| **边界场景** | TC201-204 | 空过滤、无效widgetId、无效字段 |

## 🔧 配置文件

### config.yaml

```yaml
# 环境配置
environment:
  name: "测试环境"
  base_url: "http://127.0.0.1:8110"
  timeout: 30

# 认证配置
auth:
  tenant_id: "999666"
  user_id: 1985220290507186178
  token: ""

# 当前测试的数据源ID（只运行这一个）
current_widget_id: 76

# 数据库配置（用于数据校验，可选）
database:
  enabled: false  # 是否启用数据库验证
  host: "localhost"
  port: 3306
  database: "cfs_report"
  user: "root"
  password: "password"

# 报告配置
report:
  output_dir: "reports/html"
  title: "数据源查询接口测试报告"
```

## 📊 测试报告

测试完成后生成 HTML 报告：

- **位置**：`reports/html/report.html`
- **内容**：测试用例列表、通过/失败状态、执行时间、请求/响应详情

## 🛠️ 命令行使用

```bash
# 运行测试（使用 GUI 保存的配置）
python -m pytest tests/test_dynamic.py -v --html=reports/html/report.html --self-contained-html

# 只运行基础场景
python -m pytest tests/test_dynamic.py -v -m basic --html=reports/html/report.html

# 跳过错误继续执行
python -m pytest tests/test_dynamic.py -v --maxfail=0
```

## 📦 打包成 EXE

```bash
# 安装打包工具
pip install pyinstaller

# 执行打包
pyinstaller build.spec

# 输出位置
# dist/datasource-test-tool.exe
```

## 🔌 API 请求格式

测试工具发送的请求格式：

```json
{
  "widgetId": 76,
  "tenantId": "999666",
  "userId": 1985220290507186178,
  "filters": [],
  "indexInfo": [{"code": "amount"}, {"code": "count"}],
  "dimensions": [],
  "orders": [],
  "current": 1,
  "size": 10
}
```

## 📄 License

MIT