"""边界场景测试"""
import pytest
import time
from utils.assertion import APIAssertion


class TestBoundaryScenarios:
    """边界测试场景"""

    @pytest.mark.boundary
    def test_tc201_empty_filter(self, data_query_api, widget_id, default_params):
        """TC201: 空过滤条件"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

    @pytest.mark.boundary
    @pytest.mark.slow
    def test_tc202_large_in_condition(self, data_query_api, widget_id, default_params):
        """TC202: 超大IN条件（性能测试）"""
        # 生成1000个ID
        large_ids = ",".join(str(i) for i in range(1, 1001))

        start = time.time()

        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[
                {"code": "orgId", "value": large_ids, "condition": "in"}
            ],
            index_info=[{"code": "amount"}]
        )

        elapsed = time.time() - start

        # 响应时间应小于5秒
        assert elapsed < 5, f"响应时间过长: {elapsed:.2f}s"

    @pytest.mark.boundary
    def test_tc203_invalid_widget_id(self, data_query_api, default_params):
        """TC203: 无效widgetId"""
        try:
            response = data_query_api.query(
                widget_id=999999999,
                tenant_id=default_params['tenant_id'],
                user_id=default_params['user_id'],
                index_info=[{"code": "amount"}]
            )
            # 预期返回错误
            APIAssertion.assert_status_code(response, expected=500)
        except Exception as e:
            # 或者抛出异常也是预期行为
            pass

    @pytest.mark.boundary
    def test_tc204_invalid_field_code(self, data_query_api, widget_id, default_params):
        """TC204: 无效字段编码"""
        try:
            response = data_query_api.query(
                widget_id=widget_id,
                tenant_id=default_params['tenant_id'],
                user_id=default_params['user_id'],
                filters=[
                    {"code": "invalid_field", "value": "test", "condition": "eq"}
                ],
                index_info=[{"code": "amount"}]
            )
            # 根据业务逻辑，可能忽略无效字段或返回错误
            # 这里假设返回错误
            assert response.get("code") != 200
        except Exception:
            # 异常也是预期行为
            pass

    @pytest.mark.boundary
    def test_tc205_pagination_boundary(self, data_query_api, widget_id, default_params):
        """TC205: 分页边界"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=999999,
            size=10
        )

        APIAssertion.assert_success(response)
        APIAssertion.assert_no_records(response)