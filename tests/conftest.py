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


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
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
    client = APIClient(
        base_url=config['environment']['base_url'],
        timeout=config['environment']['timeout']
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

    for widget_id, config in configs.items():
        generator = TestCaseGenerator(config)
        cases = generator.generate_all_cases()
        all_cases.extend(cases)
    
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