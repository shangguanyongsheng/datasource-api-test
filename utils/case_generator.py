"""测试用例生成器 - 根据字段配置自动组合测试用例"""
from typing import List, Dict, Any, Generator
from itertools import combinations, product, chain
from utils.sql_parser import DataSourceConfig, DataSourceField
from utils.logger import get_logger

logger = get_logger(__name__)


def powerset(iterable, min_size=0, max_size=None):
    """
    生成所有子集（powerset）

    Args:
        iterable: 可迭代对象
        min_size: 最小子集大小，默认 0（包含空集）
        max_size: 最大子集大小限制

    Examples:
        powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
        powerset([1,2,3], min_size=1) --> (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    s = list(iterable)
    if max_size is None:
        max_size = len(s)
    return chain.from_iterable(combinations(s, r) for r in range(min_size, max_size + 1))


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

    def estimate_combination_count(self) -> Dict[str, int]:
        """
        估算全量组合的数量（不实际生成用例）

        Returns:
            {
                'filter_combos': 过滤组合数,
                'dimension_combos': 维度组合数,
                'index_combos': 指标组合数,
                'order_combos': 排序组合数,
                'total': 总组合数
            }
        """
        filter_count = self._estimate_filter_combinations()
        dimension_count = self._estimate_dimension_combinations()
        index_count = self._estimate_index_combinations()
        order_count = self._estimate_order_combinations()

        total = filter_count * dimension_count * index_count * order_count

        return {
            'filter_combos': filter_count,
            'dimension_combos': dimension_count,
            'index_combos': index_count,
            'order_combos': order_count,
            'total': total,
            'filters_available': len(self.config.filters),
            'dimensions_available': len(self.config.dimensions),
            'index_info_available': len(self.config.index_info),
            'orders_available': len(self.config.orders)
        }

    def _estimate_filter_combinations(self) -> int:
        """估算过滤组合数量（1~N 个过滤器的组合）"""
        if not self.config.filters:
            return 1
        # 2^N - 1（去掉空集），但我们至少需要1个，所以是 2^N - 1
        return sum(1 for r in range(1, len(self.config.filters) + 1)
                   for _ in combinations(self.config.filters, r))

    def _estimate_dimension_combinations(self) -> int:
        """估算维度组合数量（0~M 个维度 + groupByType 3^r）"""
        if not self.config.dimensions:
            return 1
        total = 1  # 空维度
        for r in range(1, len(self.config.dimensions) + 1):
            # 每个维度组合有 3^r 种 groupByType 分配
            total += sum(3 ** r for _ in combinations(self.config.dimensions, r))
        return total

    def _estimate_index_combinations(self) -> int:
        """估算指标组合数量（1~K 个指标）"""
        if not self.config.index_info:
            return 1
        return sum(1 for r in range(1, len(self.config.index_info) + 1)
                   for _ in combinations(self.config.index_info, r))

    def _estimate_order_combinations(self) -> int:
        """估算排序组合数量（0~L 个排序 + ASC/DESC 2^r）"""
        if not self.config.orders:
            return 1
        total = 1  # 无排序
        for r in range(1, len(self.config.orders) + 1):
            total += sum(2 ** r for _ in combinations(self.config.orders, r))
        return total

    def generate_full_combination_cases(self, max_cases: int = 500) -> Generator[Dict[str, Any], None, None]:
        """
        生成全量笛卡尔积组合测试用例（惰性生成，避免内存爆炸）

        组合优先级：最全量组合优先，逐步递减
        - 优先包含所有过滤、所有维度、所有指标、所有排序的组合
        - 然后是参数数量递减的组合

        Args:
            max_cases: 最大用例数量限制，默认 500

        Returns:
            测试用例生成器（惰性生成）
        """
        widget_id = self.config.widget_id

        # 1. 准备各参数的所有组合（惰性获取）
        filter_combos = self._get_filter_combinations_lazy()
        dimension_combos = self._get_dimension_combinations_lazy()
        index_combos = self._get_index_combinations_lazy()
        order_combos = self._get_order_combinations_lazy()

        # 2. 估算总组合数（用于日志）
        estimate = self.estimate_combination_count()
        total_combinations = estimate['total']
        logger.info(f"全量组合统计: "
                   f"过滤组合={estimate['filter_combos']}, "
                   f"维度组合={estimate['dimension_combos']}, "
                   f"指标组合={estimate['index_combos']}, "
                   f"排序组合={estimate['order_combos']}, "
                   f"总组合={total_combinations}")

        # 3. 根据组合数决定策略
        if total_combinations <= max_cases * 10:
            # 组合数可控：按参数数量排序生成
            yield from self._generate_sorted_combinations(
                filter_combos, dimension_combos, index_combos, order_combos,
                widget_id, max_cases
            )
        else:
            # 组合数太多：直接按顺序生成前 N 个（不排序）
            logger.warning(f"组合数过大({total_combinations})，跳过排序直接生成前{max_cases}个")
            yield from self._generate_direct_combinations(
                filter_combos, dimension_combos, index_combos, order_combos,
                widget_id, max_cases
            )

    def _generate_sorted_combinations(self, filter_combos, dimension_combos,
                                       index_combos, order_combos,
                                       widget_id, max_cases) -> Generator[Dict[str, Any], None, None]:
        """按参数数量排序生成（组合数可控时）"""
        # 先收集有限数量的组合用于排序
        collected = []
        count = 0

        for filter_list, dimension_list, index_list, order_list in product(
                filter_combos, dimension_combos, index_combos, order_combos):
            collected.append((filter_list, dimension_list, index_list, order_list))
            count += 1
            # 只收集 max_cases * 2 个，避免内存爆炸
            if count >= max_cases * 2:
                break

        # 按参数数量降序排序
        def get_param_count(combo):
            filter_list, dimension_list, index_list, order_list = combo
            return len(filter_list) + len(dimension_list) + len(index_list) + len(order_list)

        collected.sort(key=get_param_count, reverse=True)

        # 生成前 max_cases 个用例
        for case_num, (filter_list, dimension_list, index_list, order_list) in enumerate(collected[:max_cases], start=1):
            yield self._build_case(case_num, filter_list, dimension_list, index_list, order_list, widget_id)

    def _generate_direct_combinations(self, filter_combos, dimension_combos,
                                       index_combos, order_combos,
                                       widget_id, max_cases) -> Generator[Dict[str, Any], None, None]:
        """直接按顺序生成前 N 个（组合数太大时）"""
        case_num = 0
        for filter_list, dimension_list, index_list, order_list in product(
                filter_combos, dimension_combos, index_combos, order_combos):
            case_num += 1
            yield self._build_case(case_num, filter_list, dimension_list, index_list, order_list, widget_id)
            if case_num >= max_cases:
                break

    def _build_case(self, case_num, filter_list, dimension_list, index_list, order_list, widget_id) -> Dict[str, Any]:
        """构建单个测试用例"""
        # 构建用例名称
        name_parts = []
        if filter_list:
            filter_names = [f['code'] for f in filter_list]
            name_parts.append(f"过滤[{','.join(filter_names)}]")
        if dimension_list:
            dim_names = [f"{d['code']}({d['groupByType']})" for d in dimension_list]
            name_parts.append(f"维度[{','.join(dim_names)}]")
        if index_list:
            index_names = [i['code'] for i in index_list]
            name_parts.append(f"指标[{','.join(index_names)}]")
        if order_list:
            order_names = [f"{o['code']}({o['value']})" for o in order_list]
            name_parts.append(f"排序[{','.join(order_names)}]")

        case_name = "全量组合-" + (", ".join(name_parts) if name_parts else "默认查询")

        param_count = len(filter_list) + len(dimension_list) + len(index_list) + len(order_list)

        return {
            "case_id": f"TC_FULL_{case_num:03d}",
            "name": case_name,
            "widget_id": widget_id,
            "filters": filter_list,
            "dimensions": dimension_list,
            "index_info": index_list,
            "orders": order_list,
            "param_count": param_count,
            "expected": {"status_code": 200}
        }

    def _get_filter_combinations_lazy(self) -> Generator[List[Dict], None, None]:
        """惰性生成过滤条件的所有组合"""
        if not self.config.filters:
            yield []
            return

        # 生成 1~N 个过滤器的组合（至少需要一个）
        for r in range(1, len(self.config.filters) + 1):
            for combo in combinations(self.config.filters, r):
                filter_list = [self._build_filter(f) for f in combo]
                yield filter_list

    def _get_dimension_combinations_lazy(self) -> Generator[List[Dict], None, None]:
        """惰性生成维度的所有组合（带 groupByType 分配）"""
        if not self.config.dimensions:
            yield []
            return

        group_types = ['X', 'Y', 'Z']

        # 生成 0~M 个维度的组合（包括空维度）
        for r in range(0, len(self.config.dimensions) + 1):
            for dim_combo in combinations(self.config.dimensions, r):
                if r == 0:
                    yield []
                else:
                    # 为每个维度组合分配不同的 groupByType
                    for type_assignment in product(group_types, repeat=r):
                        dimension_list = []
                        for i, dim in enumerate(dim_combo):
                            dimension_list.append({
                                "code": dim.code,
                                "groupByType": type_assignment[i]
                            })
                        yield dimension_list

    def _get_index_combinations_lazy(self) -> Generator[List[Dict], None, None]:
        """惰性生成指标的所有组合（至少选择一个指标）"""
        if not self.config.index_info:
            yield [{"code": "amount"}]
            return

        # 生成 1~K 个指标的组合（至少需要一个）
        for r in range(1, len(self.config.index_info) + 1):
            for combo in combinations(self.config.index_info, r):
                index_list = [{"code": f.code} for f in combo]
                yield index_list

    def _get_order_combinations_lazy(self) -> Generator[List[Dict], None, None]:
        """惰性生成排序的所有组合（带 ASC/DESC）"""
        if not self.config.orders:
            yield []
            return

        order_values = ['ASC', 'DESC']

        # 生成 0~L 个排序的组合（包括不排序）
        for r in range(0, len(self.config.orders) + 1):
            for order_combo in combinations(self.config.orders, r):
                if r == 0:
                    yield []
                else:
                    # 为每个排序组合分配 ASC 或 DESC
                    for value_assignment in product(order_values, repeat=r):
                        order_list = []
                        for i, order in enumerate(order_combo):
                            order_list.append({
                                "code": order.code,
                                "value": value_assignment[i]
                            })
                        yield order_list

    def _get_filter_combinations(self) -> List[List[Dict]]:
        """获取过滤条件的所有组合"""
        if not self.config.filters:
            return [[]]  # 无过滤条件时返回空列表的列表

        combos = []
        # 生成 1~N 个过滤器的组合（至少需要一个）
        for r in range(1, len(self.config.filters) + 1):
            for combo in combinations(self.config.filters, r):
                filter_list = [self._build_filter(f) for f in combo]
                combos.append(filter_list)

        return combos

    def _get_dimension_combinations(self) -> List[List[Dict]]:
        """获取维度的所有组合（带 groupByType 分配）"""
        if not self.config.dimensions:
            return [[]]  # 无维度时返回空列表

        combos = []
        group_types = ['X', 'Y', 'Z']  # 可用的 groupByType

        # 生成 0~M 个维度的组合（包括空维度）
        for r in range(0, len(self.config.dimensions) + 1):
            for dim_combo in combinations(self.config.dimensions, r):
                if r == 0:
                    combos.append([])
                else:
                    # 为每个维度组合分配不同的 groupByType
                    for type_assignment in product(group_types, repeat=r):
                        dimension_list = []
                        for i, dim in enumerate(dim_combo):
                            dimension_list.append({
                                "code": dim.code,
                                "groupByType": type_assignment[i]
                            })
                        combos.append(dimension_list)

        return combos

    def _get_index_combinations(self) -> List[List[Dict]]:
        """获取指标的所有组合（至少选择一个指标）"""
        if not self.config.index_info:
            return [[{"code": "amount"}]]  # 默认指标，返回列表的列表

        combos = []
        # 生成 1~K 个指标的组合（至少需要一个）
        for r in range(1, len(self.config.index_info) + 1):
            for combo in combinations(self.config.index_info, r):
                index_list = [{"code": f.code} for f in combo]
                combos.append(index_list)

        return combos

        return combos

    def _get_order_combinations(self) -> List[List[Dict]]:
        """获取排序的所有组合（带 ASC/DESC）"""
        if not self.config.orders:
            return [[]]  # 无排序时返回空列表

        combos = []
        order_values = ['ASC', 'DESC']

        # 生成 0~L 个排序的组合（包括不排序）
        for r in range(0, len(self.config.orders) + 1):
            for order_combo in combinations(self.config.orders, r):
                if r == 0:
                    combos.append([])
                else:
                    # 为每个排序组合分配 ASC 或 DESC
                    for value_assignment in product(order_values, repeat=r):
                        order_list = []
                        for i, order in enumerate(order_combo):
                            order_list.append({
                                "code": order.code,
                                "value": value_assignment[i]
                            })
                        combos.append(order_list)

        return combos

    def generate_all_cases(self, include_full_combination: bool = False, max_cases: int = 500) -> Generator[Dict[str, Any], None, None]:
        """生成所有测试用例（惰性生成，避免内存爆炸）

        Args:
            include_full_combination: 是否包含全量组合测试用例
            max_cases: 全量组合时的最大用例数限制

        Returns:
            测试用例生成器（惰性生成）
        """
        # 基础用例（数量较少，可以直接生成）
        yield from self.generate_basic_cases()
        yield from self.generate_combine_cases()
        yield from self.generate_pagination_cases()
        yield from self.generate_no_pagination_cases()
        yield from self.generate_boundary_cases()

        # 如果启用全量组合，添加全量组合用例（惰性生成）
        if include_full_combination:
            yield from self.generate_full_combination_cases(max_cases)

    def generate_all_cases_as_list(self, include_full_combination: bool = False, max_cases: int = 500) -> List[Dict[str, Any]]:
        """生成所有测试用例并返回列表（仅在需要统计数量时使用）

        注意：此方法会将所有用例加载到内存，仅在必要时使用。

        Args:
            include_full_combination: 是否包含全量组合测试用例
            max_cases: 全量组合时的最大用例数限制

        Returns:
            测试用例列表
        """
        cases = list(self.generate_all_cases(include_full_combination, max_cases))
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


def generate_test_cases_from_sql(sql_content: str, include_full_combination: bool = False, max_cases: int = 500) -> List[Dict[str, Any]]:
    """
    从SQL语句生成测试用例（便捷函数）

    Args:
        sql_content: INSERT SQL语句
        include_full_combination: 是否包含全量组合测试用例
        max_cases: 全量组合时的最大用例数限制

    Returns:
        测试用例列表
    """
    from utils.sql_parser import SQLParser

    parser = SQLParser()
    fields = parser.parse_insert_statement(sql_content)
    config = DataSourceConfig(fields)
    generator = TestCaseGenerator(config)

    return generator.generate_all_cases(include_full_combination, max_cases)