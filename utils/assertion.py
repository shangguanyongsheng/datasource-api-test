"""断言工具"""
from typing import Any, Dict, List, Optional
import pytest


class APIAssertion:
    """接口断言工具类"""

    @staticmethod
    def assert_status_code(response: Dict, expected: int = 200):
        """断言状态码"""
        actual = response.get("code")
        assert actual == expected, f"状态码不匹配: 期望 {expected}, 实际 {actual}"

    @staticmethod
    def assert_success(response: Dict):
        """断言请求成功"""
        assert response.get("code") == 200, f"请求失败: {response.get('message')}"
        assert response.get("data") is not None, "响应数据为空"

    @staticmethod
    def assert_has_records(response: Dict):
        """断言有数据返回"""
        data = response.get("data", {})
        records = data.get("records", [])
        total = data.get("total", 0)
        assert len(records) > 0, "返回记录为空"
        assert total > 0, "总数为0"

    @staticmethod
    def assert_no_records(response: Dict):
        """断言无数据返回"""
        data = response.get("data", {})
        records = data.get("records", [])
        assert len(records) == 0, f"预期无数据，但返回了 {len(records)} 条记录"

    @staticmethod
    def assert_field_exists(response: Dict, field_path: str):
        """断言字段存在"""
        data = response.get("data", {})
        parts = field_path.split(".")
        current = data

        for part in parts:
            if part not in current:
                pytest.fail(f"字段不存在: {field_path}")
            current = current[part]

    @staticmethod
    def assert_field_type(response: Dict, field_path: str, expected_type: type):
        """断言字段类型"""
        data = response.get("data", {})
        parts = field_path.split(".")
        current = data

        for part in parts:
            current = current.get(part)

        assert isinstance(current, expected_type), \
            f"字段类型不匹配: {field_path}, 期望 {expected_type}, 实际 {type(current)}"

    @staticmethod
    def assert_record_count(response: Dict, expected: int):
        """断言记录数量"""
        data = response.get("data", {})
        records = data.get("records", [])
        assert len(records) == expected, \
            f"记录数量不匹配: 期望 {expected}, 实际 {len(records)}"

    @staticmethod
    def assert_response_time(response_time_ms: float, max_ms: float):
        """断言响应时间"""
        assert response_time_ms <= max_ms, \
            f"响应时间超时: {response_time_ms}ms > {max_ms}ms"

    @staticmethod
    def assert_error_message(response: Dict, expected_msg: str):
        """断言错误消息"""
        actual_msg = response.get("message", "")
        assert expected_msg in actual_msg, \
            f"错误消息不匹配: 期望包含 '{expected_msg}', 实际 '{actual_msg}'"

    @staticmethod
    def assert_sorted(response: Dict, field: str, order: str = "ASC"):
        """断言排序正确"""
        data = response.get("data", {})
        records = data.get("records", [])

        if len(records) < 2:
            return

        values = [r.get(field) for r in records if r.get(field) is not None]

        if order.upper() == "ASC":
            assert values == sorted(values), f"升序排序不正确: {values}"
        else:
            assert values == sorted(values, reverse=True), f"降序排序不正确: {values}"


class PaginationAssertion:
    """分页断言工具类"""

    @staticmethod
    def assert_pagination_metadata(response: Dict, expected_current: int, expected_size: int):
        """断言分页元数据正确"""
        data = response.get("data", {})

        actual_current = data.get("current")
        actual_size = data.get("size")
        total = data.get("total", 0)
        pages = data.get("pages", 0)

        assert actual_current == expected_current, \
            f"当前页码不匹配: 期望 {expected_current}, 实际 {actual_current}"
        assert actual_size == expected_size, \
            f"每页条数不匹配: 期望 {expected_size}, 实际 {actual_size}"
        assert isinstance(total, int), f"total应为整数: {total}"
        assert isinstance(pages, int), f"pages应为整数: {pages}"

        # 验证pages计算正确
        expected_pages = (total + expected_size - 1) // expected_size if total > 0 else 0
        assert pages == expected_pages, \
            f"总页数计算错误: 期望 {expected_pages}, 实际 {pages}"

    @staticmethod
    def assert_record_count_matches_page(response: Dict):
        """断言当前页记录数符合预期"""
        data = response.get("data", {})
        records = data.get("records", [])
        size = data.get("size", 10)
        current = data.get("current", 1)
        total = data.get("total", 0)
        pages = data.get("pages", 0)

        # 如果是最后一页，记录数可能少于size
        if current == pages and pages > 0:
            expected_last_page_size = total - (pages - 1) * size
            assert len(records) == expected_last_page_size, \
                f"最后一页记录数不匹配: 期望 {expected_last_page_size}, 实际 {len(records)}"
        else:
            assert len(records) <= size, \
                f"当前页记录数超过size: {len(records)} > {size}"

    @staticmethod
    def assert_no_duplicate_records(responses: List[Dict], key_field: str = "id"):
        """断言多页数据无重复"""
        all_records = []
        for response in responses:
            data = response.get("data", {})
            records = data.get("records", [])
            all_records.extend(records)

        key_values = [r.get(key_field) for r in all_records if r.get(key_field)]
        duplicates = [k for k in key_values if key_values.count(k) > 1]

        assert len(duplicates) == 0, f"发现重复数据: {set(duplicates)}"

    @staticmethod
    def assert_total_records_match(responses: List[Dict]):
        """断言多页数据总数等于total"""
        if not responses:
            return

        expected_total = responses[0].get("data", {}).get("total", 0)
        actual_count = sum(
            len(r.get("data", {}).get("records", []))
            for r in responses
        )

        assert actual_count == expected_total, \
            f"数据总数不匹配: 期望 {expected_total}, 实际 {actual_count}"

    @staticmethod
    def assert_is_single_record(response: Dict):
        """断言返回单条汇总记录"""
        data = response.get("data", {})
        records = data.get("records", [])
        assert len(records) == 1, f"预期返回1条汇总记录，实际返回 {len(records)} 条"

    @staticmethod
    def assert_limit_records(response: Dict, expected_limit: int):
        """断言返回记录数符合limit限制"""
        data = response.get("data", {})
        records = data.get("records", [])
        assert len(records) <= expected_limit, \
            f"记录数超过limit限制: {len(records)} > {expected_limit}"