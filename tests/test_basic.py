"""基础场景测试 - 手动编写的测试用例（参考示例）"""
import pytest
from utils.assertion import APIAssertion
from utils.sql_parser import DataSourceConfig


class TestBasicScenarios:
    """基础测试场景（手动编写示例）"""

    def test_query_with_generated_config(
        self,
        data_query_api,
        data_source_config,
        default_params
    ):
        """使用解析后的配置进行测试"""
        if not data_source_config:
            pytest.skip("无数据源配置")

        # 使用配置中的第一个指标
        index_codes = data_source_config.get_index_codes()
        if not index_codes:
            pytest.skip("无指标配置")

        response = data_query_api.query(
            widget_id=data_source_config.widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": index_codes[0]}]
        )

        APIAssertion.assert_success(response)

    def test_single_filter_from_config(
        self,
        data_query_api,
        data_source_config,
        default_params
    ):
        """使用配置中的第一个过滤条件"""
        if not data_source_config or not data_source_config.filters:
            pytest.skip("无过滤条件配置")

        first_filter = data_source_config.filters[0]
        index_codes = data_source_config.get_index_codes()

        response = data_query_api.query(
            widget_id=data_source_config.widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[{
                "code": first_filter.code,
                "value": "1",
                "condition": first_filter.filter_condition or "in"
            }],
            index_info=[{"code": index_codes[0]}] if index_codes else []
        )

        APIAssertion.assert_success(response)

    @pytest.mark.basic
    def test_tc001_query_index_only(self, data_query_api, widget_id, default_params):
        """TC001: 仅查询指标"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

    @pytest.mark.basic
    def test_tc002_single_filter(self, data_query_api, widget_id, default_params):
        """TC002: 单过滤条件"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[{"code": "orgId", "value": "1,2,3", "condition": "in"}],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

    @pytest.mark.basic
    def test_tc003_multi_filter(self, data_query_api, widget_id, default_params):
        """TC003: 多过滤条件"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[
                {"code": "orgId", "value": "1,2,3", "condition": "in"},
                {"code": "year", "value": "2025", "condition": "geq"}
            ],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

    @pytest.mark.basic
    def test_tc004_single_dimension(self, data_query_api, widget_id, default_params):
        """TC004: 单维度分组"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            dimensions=[{"code": "orgId", "groupByType": "X"}],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

    @pytest.mark.basic
    def test_tc005_double_dimension(self, data_query_api, widget_id, default_params):
        """TC005: 双维度分组"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            dimensions=[
                {"code": "orgId", "groupByType": "X"},
                {"code": "month", "groupByType": "Y"}
            ],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

    @pytest.mark.basic
    def test_tc006_order_query(self, data_query_api, widget_id, default_params):
        """TC006: 排序查询"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            orders=[{"code": "amount", "value": "DESC"}]
        )

        APIAssertion.assert_success(response)
        APIAssertion.assert_sorted(response, "amount", "DESC")

    @pytest.mark.basic
    def test_tc007_pagination(self, data_query_api, widget_id, default_params):
        """TC007: 分页查询"""
        # 第一页
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=1,
            size=10
        )

        APIAssertion.assert_success(response)
        data = response.get("data", {})
        assert data.get("current") == 1
        assert data.get("size") == 10