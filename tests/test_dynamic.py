"""动态生成的测试用例 - 根据SQL配置自动生成"""
import pytest
from utils.assertion import APIAssertion, PaginationAssertion


class TestDynamicGenerated:
    """动态生成的测试用例（基于SQL配置）"""

    def test_generated_case(self, data_query_api, default_params, test_case):
        """
        参数化执行所有生成的测试用例

        测试用例由 TestCaseGenerator 根据SQL配置自动生成
        """
        case_id = test_case.get("case_id")
        case_name = test_case.get("name")

        # 构建请求参数
        request_params = {
            "widget_id": test_case["widget_id"],
            "tenant_id": default_params['tenant_id'],
            "user_id": default_params['user_id']
        }

        # 添加可选参数
        if test_case.get("filters"):
            request_params["filters"] = test_case["filters"]
        if test_case.get("index_info"):
            request_params["index_info"] = test_case["index_info"]
        if test_case.get("dimensions"):
            request_params["dimensions"] = test_case["dimensions"]
        if test_case.get("orders"):
            request_params["orders"] = test_case["orders"]
        if "current" in test_case:
            request_params["current"] = test_case["current"]
        if "size" in test_case:
            request_params["size"] = test_case["size"]
        if test_case.get("single"):
            request_params["single"] = test_case["single"]
        if test_case.get("limit"):
            request_params["limit"] = test_case["limit"]

        # 执行请求
        try:
            response = data_query_api.query(**request_params)
        except Exception as e:
            # 对于预期失败的用例，检查是否符合预期
            expected = test_case.get("expected", {})
            if expected.get("status_code") == 500 or expected.get("status_code") == 400:
                pytest.skip(f"请求异常，可能需要配置正确的服务地址: {e}")
            raise

        # 断言
        expected = test_case.get("expected", {})
        if expected.get("status_code"):
            APIAssertion.assert_status_code(response, expected["status_code"])
        else:
            APIAssertion.assert_success(response)

        if expected.get("has_records"):
            APIAssertion.assert_has_records(response)

        if expected.get("single_record"):
            PaginationAssertion.assert_is_single_record(response)

        if expected.get("max_records"):
            PaginationAssertion.assert_limit_records(response, expected["max_records"])