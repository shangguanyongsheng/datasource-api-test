"""测试用例生成器 - 根据字段配置自动组合测试用例"""
from typing import List, Dict, Any, Generator
from itertools import combinations, product
from utils.sql_parser import DataSourceConfig, DataSourceField
from utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseGenerator:
    """测试用例生成器"""

    # 条件类型映射
    CONDITION_MAP = {
        'in': 'in',
        'notin': 'notin',
        'geq': 'geq',
        'gtr': 'gtr',
        'leq': 'leq',
        'lss': 'lss',
        'eq': 'eq'
    }

    # 默认测试值
    DEFAULT_TEST_VALUES = {
        'orgId': '1,2,3',
        'year': '2025',
        'month': '2025-03',
        'status': '1,2',
        'amount': '1000',
        'default': 'test'
    }

    def __init__(self, config: DataSourceConfig):
        self.config = config

    def generate_basic_cases(self) -> Generator[Dict[str, Any], None, None]:
        """生成基础场景测试用例"""
        widget_id = self.config.widget_id

        # TC001: 仅查询指标
        if self.config.index_info:
            yield {
                "case_id": "TC001",
                "name": "仅查询指标",
                "widget_id": widget_id,
                "index_info": [{"code": f.code} for f in self.config.index_info],
                "expected": {"status_code": 200}  # 只检查状态码，不强制要求数据非空
            }

        # TC002-TC003: 单/多过滤条件
        if self.config.filters:
            # 单过滤条件
            first_filter = self.config.filters[0]
            yield {
                "case_id": "TC002",
                "name": f"单过滤条件-{first_filter.code}",
                "widget_id": widget_id,
                "filters": [self._build_filter(first_filter)],
                "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                "expected": {"status_code": 200}
            }

            # 多过滤条件（取前2个）
            if len(self.config.filters) >= 2:
                yield {
                    "case_id": "TC003",
                    "name": "多过滤条件",
                    "widget_id": widget_id,
                    "filters": [self._build_filter(f) for f in self.config.filters[:2]],
                    "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                    "expected": {"status_code": 200}
                }

        # TC004-TC005: 单/双维度分组
        if self.config.dimensions:
            first_dim = self.config.dimensions[0]
            yield {
                "case_id": "TC004",
                "name": f"单维度分组-{first_dim.code}",
                "widget_id": widget_id,
                "dimensions": [{"code": first_dim.code, "groupByType": "X"}],
                "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                "expected": {"status_code": 200}
            }

            if len(self.config.dimensions) >= 2:
                second_dim = self.config.dimensions[1]
                yield {
                    "case_id": "TC005",
                    "name": "双维度分组",
                    "widget_id": widget_id,
                    "dimensions": [
                        {"code": first_dim.code, "groupByType": "X"},
                        {"code": second_dim.code, "groupByType": "Y"}
                    ],
                    "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                    "expected": {"status_code": 200}
                }

        # TC006: 排序查询
        if self.config.orders:
            first_order = self.config.orders[0]
            yield {
                "case_id": "TC006",
                "name": f"排序查询-{first_order.code}",
                "widget_id": widget_id,
                "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                "orders": [{"code": first_order.code, "value": "DESC"}],
                "expected": {"status_code": 200}
            }

        # TC007: 分页查询
        yield {
            "case_id": "TC007",
            "name": "分页查询",
            "widget_id": widget_id,
            "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
            "current": 1,
            "size": 10,
            "expected": {"status_code": 200}
        }

    def generate_combine_cases(self) -> Generator[Dict[str, Any], None, None]:
        """生成组合场景测试用例"""
        widget_id = self.config.widget_id

        # TC101: 过滤+分组
        if self.config.filters and self.config.dimensions:
            yield {
                "case_id": "TC101",
                "name": "过滤+分组",
                "widget_id": widget_id,
                "filters": [self._build_filter(self.config.filters[0])],
                "dimensions": [{"code": self.config.dimensions[0].code, "groupByType": "X"}],
                "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                "expected": {"status_code": 200}
            }

        # TC102: 过滤+排序
        if self.config.filters and self.config.orders:
            yield {
                "case_id": "TC102",
                "name": "过滤+排序",
                "widget_id": widget_id,
                "filters": [self._build_filter(self.config.filters[0])],
                "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                "orders": [{"code": self.config.orders[0].code, "value": "DESC"}],
                "expected": {"status_code": 200}
            }

        # TC103: 过滤+分组+排序
        if self.config.filters and self.config.dimensions and self.config.orders:
            yield {
                "case_id": "TC103",
                "name": "过滤+分组+排序",
                "widget_id": widget_id,
                "filters": [self._build_filter(self.config.filters[0])],
                "dimensions": [{"code": self.config.dimensions[0].code, "groupByType": "X"}],
                "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
                "orders": [{"code": self.config.orders[0].code, "value": "DESC"}],
                "expected": {"status_code": 200}
            }

        # TC104: 多指标聚合
        if len(self.config.index_info) >= 2:
            yield {
                "case_id": "TC104",
                "name": "多指标聚合",
                "widget_id": widget_id,
                "index_info": [{"code": f.code} for f in self.config.index_info[:3]],
                "expected": {"status_code": 200}
            }

    def generate_pagination_cases(self) -> Generator[Dict[str, Any], None, None]:
        """生成分页场景测试用例"""
        widget_id = self.config.widget_id
        index_code = self.config.index_info[0].code if self.config.index_info else "amount"

        # TC401-TC405: 分页测试
        pagination_tests = [
            ("TC401", "首页查询", {"current": 1, "size": 10}),
            ("TC402", "中间页查询", {"current": 2, "size": 10}),
            ("TC404", "超大页码", {"current": 999999, "size": 10}),
            ("TC405", "大页大小", {"current": 1, "size": 100}),
        ]

        for case_id, name, params in pagination_tests:
            yield {
                "case_id": case_id,
                "name": f"分页-{name}",
                "widget_id": widget_id,
                "index_info": [{"code": index_code}],
                **params,
                "expected": {"status_code": 200}
            }

    def generate_no_pagination_cases(self) -> Generator[Dict[str, Any], None, None]:
        """生成不分页场景测试用例"""
        widget_id = self.config.widget_id
        index_code = self.config.index_info[0].code if self.config.index_info else "amount"

        # TC501: 默认查询（无分页参数）
        yield {
            "case_id": "TC501",
            "name": "不分页-默认查询",
            "widget_id": widget_id,
            "index_info": [{"code": index_code}],
            "expected": {"status_code": 200}
        }

        # TC502: single汇总
        yield {
            "case_id": "TC502",
            "name": "不分页-single汇总",
            "widget_id": widget_id,
            "index_info": [{"code": index_code}],
            "single": True,
            "expected": {"status_code": 200, "single_record": True}
        }

        # TC503: limit限制
        limit_tests = [(9, "limit=9"), (1, "limit=1")]
        for limit_val, desc in limit_tests:
            yield {
                "case_id": f"TC503_{limit_val}",
                "name": f"不分页-{desc}",
                "widget_id": widget_id,
                "index_info": [{"code": index_code}],
                "limit": limit_val,
                "expected": {"status_code": 200, "max_records": limit_val + 1}
            }

    def generate_boundary_cases(self) -> Generator[Dict[str, Any], None, None]:
        """生成边界场景测试用例"""
        widget_id = self.config.widget_id

        # TC201: 空过滤条件
        yield {
            "case_id": "TC201",
            "name": "空过滤条件",
            "widget_id": widget_id,
            "filters": [],
            "index_info": [{"code": self.config.index_info[0].code}] if self.config.index_info else [],
            "expected": {"status_code": 200}
        }

        # TC203: 无效widgetId
        yield {
            "case_id": "TC203",
            "name": "无效widgetId",
            "widget_id": 999999999,
            "index_info": [{"code": "amount"}],
            "expected": {"status_code": 500, "error_msg": "数据源不存在"}
        }

        # TC204: 无效字段编码
        yield {
            "case_id": "TC204",
            "name": "无效字段编码",
            "widget_id": widget_id,
            "filters": [{"code": "invalid_field", "value": "test", "condition": "eq"}],
            "index_info": [{"code": "amount"}],
            "expected": {"status_code": 400}
        }

    def generate_all_cases(self) -> List[Dict[str, Any]]:
        """生成所有测试用例"""
        cases = []

        cases.extend(self.generate_basic_cases())
        cases.extend(self.generate_combine_cases())
        cases.extend(self.generate_pagination_cases())
        cases.extend(self.generate_no_pagination_cases())
        cases.extend(self.generate_boundary_cases())

        logger.info(f"共生成 {len(cases)} 个测试用例")
        return cases

    def _build_filter(self, field: DataSourceField) -> Dict[str, str]:
        """构建过滤条件"""
        condition = field.filter_condition or 'eq'
        value = self.DEFAULT_TEST_VALUES.get(field.code, self.DEFAULT_TEST_VALUES['default'])

        return {
            "code": field.code,
            "value": value,
            "condition": condition
        }


def generate_test_cases_from_sql(sql_content: str) -> List[Dict[str, Any]]:
    """
    从SQL语句生成测试用例（便捷函数）

    Args:
        sql_content: INSERT SQL语句

    Returns:
        测试用例列表
    """
    from utils.sql_parser import SQLParser

    parser = SQLParser()
    fields = parser.parse_insert_statement(sql_content)
    config = DataSourceConfig(fields)
    generator = TestCaseGenerator(config)

    return generator.generate_all_cases()