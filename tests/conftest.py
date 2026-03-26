"""Pytest配置和fixtures"""
import pytest
import yaml
import time
from pathlib import Path
from typing import Dict, List
from api.client import APIClient
from api.data_query import DataQueryAPI
from utils.logger import get_logger
from utils.sql_parser import SQLParser, DataSourceConfig
from utils.case_generator import TestCaseGenerator

logger = get_logger(__name__)


def detect_encoding(file_path: str) -> str:
    """检测文件编码，支持 GBK 等 Windows 编码和 UTF-8 BOM"""
    # 先检查 BOM
    try:
        with open(file_path, 'rb') as f:
            bom = f.read(3)
            if bom == b'\xef\xbb\xbf':
                return 'utf-8-sig'
    except:
        pass
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    return 'utf-8'


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    encoding = detect_encoding(str(config_path))
    with open(config_path, 'r', encoding=encoding) as f:
        return yaml.safe_load(f)


def load_data_source_configs() -> Dict[int, DataSourceConfig]:
    """
    从SQL文件加载数据源配置

    Returns:
        {widget_id: DataSourceConfig}
    """
    sql_dir = Path(__file__).parent.parent / "config" / "sql_input"
    
    if not sql_dir.exists():
        logger.warning(f"SQL目录不存在: {sql_dir}")
        return {}
    
    parser = SQLParser()

    # 解析所有SQL文件
    all_fields = parser.parse_sql_directory(str(sql_dir))

    # 转换为DataSourceConfig
    configs = {}
    for widget_id, fields in all_fields.items():
        configs[widget_id] = DataSourceConfig(fields)
        logger.info(f"加载数据源 {widget_id}: "
                   f"filters={len(configs[widget_id].filters)}, "
                   f"index_info={len(configs[widget_id].index_info)}, "
                   f"dimensions={len(configs[widget_id].dimensions)}, "
                   f"orders={len(configs[widget_id].orders)}")

    return configs


# 全局配置缓存
_config = None
_data_source_configs = None


def get_config():
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_data_source_configs():
    global _data_source_configs
    if _data_source_configs is None:
        _data_source_configs = load_data_source_configs()
    return _data_source_configs


@pytest.fixture(scope="session")
def config():
    """配置fixture"""
    return get_config()


@pytest.fixture(scope="session")
def data_source_configs():
    """数据源配置fixture（从SQL解析）"""
    return get_data_source_configs()


@pytest.fixture(scope="session")
def api_client(config):
    """API客户端fixture"""
    # 处理 timeout 配置：支持 int 或 [connect, read] 格式
    timeout_config = config['environment'].get('timeout', 30)
    if isinstance(timeout_config, list) and len(timeout_config) == 2:
        timeout = tuple(timeout_config)  # (connect_timeout, read_timeout)
    else:
        timeout = timeout_config  # int
    
    # 获取响应截断配置
    truncate_config = config['environment'].get('response_truncate', {
        'enabled': True,
        'max_records': 100,
        'max_size_kb': 100
    })
    
    logger.info(f"API 客户端配置: timeout={timeout}, truncate={truncate_config}")
    
    client = APIClient(
        base_url=config['environment']['base_url'],
        timeout=timeout,
        truncate_config=truncate_config
    )

    # 设置认证
    auth = config.get('auth', {})
    client.set_auth(
        tenant_id=auth.get('tenant_id', ''),
        user_id=auth.get('user_id', 0),
        token=auth.get('token')
    )

    yield client

    client.close()


@pytest.fixture(scope="session")
def data_query_api(api_client):
    """数据查询API fixture"""
    return DataQueryAPI(api_client)


@pytest.fixture(scope="session")
def default_params(config):
    """默认请求参数"""
    auth = config.get('auth', {})
    return {
        "tenant_id": auth.get('tenant_id', ''),
        "user_id": auth.get('user_id', 0)
    }


@pytest.fixture
def widget_id(data_source_configs):
    """测试用数据源ID（取第一个）"""
    ids = list(data_source_configs.keys())
    return ids[0] if ids else 123


@pytest.fixture
def data_source_config(data_source_configs, widget_id):
    """数据源配置"""
    return data_source_configs.get(widget_id)


@pytest.fixture
def test_case_generator(data_source_config):
    """测试用例生成器"""
    if data_source_config:
        return TestCaseGenerator(data_source_config)
    return None


@pytest.fixture(autouse=True)
def log_test_info(request):
    """自动记录测试信息"""
    logger.info(f"开始执行: {request.node.name}")
    start_time = time.time()

    yield

    elapsed = time.time() - start_time
    logger.info(f"执行完成: {request.node.name}, 耗时: {elapsed:.2f}s")


# ============ 参数化测试用例生成 ============

def _get_all_test_cases():
    """获取所有生成的测试用例"""
    from utils.case_generator import TestCaseGenerator

    all_cases = []
    configs = get_data_source_configs()

    # 从配置文件获取当前选中的数据源ID
    config = get_config()
    current_widget_id = config.get('current_widget_id')

    if current_widget_id and current_widget_id in configs:
        # 只加载当前选中的数据源
        generator = TestCaseGenerator(configs[current_widget_id])
        cases = generator.generate_all_cases()
        all_cases.extend(cases)
        logger.info(f"只加载数据源 {current_widget_id} 的测试用例，共 {len(cases)} 个")
    else:
        # 加载所有数据源（兼容旧逻辑）
        for widget_id, ds_config in configs.items():
            generator = TestCaseGenerator(ds_config)
            cases = generator.generate_all_cases()
            all_cases.extend(cases)
        logger.info(f"加载所有数据源，共 {len(all_cases)} 个测试用例")
    
    # 如果没有SQL配置，生成默认测试用例
    if not all_cases:
        all_cases = [
            {
                "case_id": "TC_DEFAULT",
                "name": "默认测试用例",
                "widget_id": 123,
                "index_info": [{"code": "amount"}],
                "expected": {"status_code": 200}
            }
        ]

    return all_cases


@pytest.fixture
def generated_test_cases(test_case_generator):
    """生成的测试用例列表"""
    if test_case_generator:
        return test_case_generator.generate_all_cases()
    return []


def pytest_generate_tests(metafunc):
    """动态生成测试参数"""
    if "test_case" in metafunc.fixturenames:
        test_cases = _get_all_test_cases()
        ids = [f"{tc['case_id']}_{tc['name']}" for tc in test_cases]
        metafunc.parametrize("test_case", test_cases, ids=ids)


def pytest_collection_modifyitems(config, items):
    """根据测试用例的 case_id 自动添加 marker"""
    marker_map = {
        'TC0': 'basic',       # TC001-TC007
        'TC1': 'combine',     # TC101-TC104
        'TC2': 'boundary',    # TC201-TC205
        'TC4': 'pagination',  # TC401-TC410
        'TC5': 'no_pagination',  # TC501-TC508
    }
    
    for item in items:
        try:
            # 从测试用例 ID 中提取 case_id
            if hasattr(item, 'callspec') and item.callspec:
                test_case = item.callspec.params.get('test_case', {})
                case_id = test_case.get('case_id', '') if isinstance(test_case, dict) else ''
                
                if case_id:
                    # 根据 case_id 前缀匹配 marker
                    for prefix, marker_name in marker_map.items():
                        if case_id.startswith(prefix):
                            item.add_marker(marker_name)
                            break
        except Exception:
            # 忽略获取参数时的异常
            pass


# ============ 测试报告增强：显示完整请求/响应 ============

# 存储每个测试的响应信息（用于报告）
_test_response_info = {}


def pytest_html_results_table_header(cells):
    """添加自定义表头"""
    cells.insert(3, '<th>数据量</th>')
    cells.insert(4, '<th>备注</th>')


def pytest_html_results_table_row(report, cells):
    """添加自定义列内容"""
    # 获取测试的响应信息
    test_name = getattr(report, 'nodeid', '')
    response_info = _test_response_info.get(test_name, {})
    
    # 数据量列
    data_count = response_info.get('data_count', '-')
    total = response_info.get('total', None)
    status = response_info.get('status', '')
    
    if status == 'success_zero':
        # 成功但 total=0，黄色警告
        cells.insert(3, f'<td style="color: #d97706; font-weight: bold;">{data_count} (total=0)</td>')
    elif status == 'success_with_data':
        # 成功且有数据，绿色
        cells.insert(3, f'<td style="color: #059669;">{data_count}</td>')
    elif status == 'failed':
        # 失败，红色
        cells.insert(3, f'<td style="color: #dc2626;">请求失败</td>')
    else:
        cells.insert(3, f'<td>{data_count}</td>')
    
    # 备注列
    remark = response_info.get('remark', '')
    if status == 'success_zero':
        remark = '⚠️ 返回数据为空'
    cells.insert(4, f'<td>{remark}</td>')


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在测试报告中添加完整的请求和响应信息"""
    outcome = yield
    report = outcome.get_result()
    
    # 只在测试调用阶段处理（不是 setup 或 teardown）
    if call.when == "call":
        # 获取最后一次请求的信息
        try:
            from api.client import get_last_request_info
            request_info = get_last_request_info()
            
            if request_info:
                # 解析响应
                response_body = request_info.get('response_body', '')
                response_status = request_info.get('response_status', 0)
                
                # 分析响应数据
                data_count = '-'
                total = None
                status = ''
                remark = ''
                
                if response_status == 200:
                    try:
                        import json
                        parsed = json.loads(response_body)
                        
                        # 获取 total
                        if isinstance(parsed, dict):
                            total = parsed.get('total', 0)
                            data = parsed.get('data', {})
                            
                            # 计算 data_count
                            if isinstance(data, dict):
                                records = data.get('records', [])
                                data_count = len(records)
                            elif isinstance(data, list):
                                data_count = len(data)
                            
                            # 判断状态
                            if total == 0:
                                status = 'success_zero'
                                remark = f'响应成功，但 total=0，records={data_count}'
                            else:
                                status = 'success_with_data'
                                remark = f'total={total}, records={data_count}'
                    except:
                        status = 'parse_error'
                        remark = '响应解析失败'
                else:
                    status = 'failed'
                    remark = f'HTTP {response_status}'
                
                # 存储响应信息（用于报告表格）
                _test_response_info[item.nodeid] = {
                    'data_count': data_count,
                    'total': total,
                    'status': status,
                    'remark': remark
                }
                
                # 格式化请求/响应信息（用于详情展开）
                extra_info = []
                extra_info.append(f"\n{'='*60}")
                extra_info.append("📤 请求信息")
                extra_info.append(f"{'='*60}")
                extra_info.append(f"URL: {request_info.get('url', 'N/A')}")
                extra_info.append(f"方法: {request_info.get('method', 'N/A')}")
                
                if request_info.get('request_body'):
                    extra_info.append(f"\n请求体:\n{request_info['request_body']}")
                if request_info.get('request_params'):
                    extra_info.append(f"\n请求参数: {request_info['request_params']}")
                
                extra_info.append(f"\n{'='*60}")
                extra_info.append("📥 响应信息")
                extra_info.append(f"{'='*60}")
                extra_info.append(f"状态码: {response_status}")
                
                if response_body:
                    # 尝试格式化 JSON
                    try:
                        import json
                        parsed = json.loads(response_body)
                        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
                        extra_info.append(f"\n响应体:\n{formatted}")
                    except:
                        extra_info.append(f"\n响应体:\n{response_body}")
                
                # 添加数据量摘要
                extra_info.append(f"\n{'='*60}")
                extra_info.append("📊 数据摘要")
                extra_info.append(f"{'='*60}")
                extra_info.append(f"状态: {remark}")
                
                extra_info.append(f"\n{'='*60}")
                
                # 将信息添加到报告中
                report.sections.append(('API请求/响应详情', '\n'.join(extra_info)))
                
        except Exception as e:
            logger.warning(f"获取请求信息失败: {e}")