"""不分页场景测试"""
import pytest
from utils.assertion import APIAssertion, PaginationAssertion


class TestNoPaginationScenarios:
    """不分页测试场景"""

    @pytest.mark.no_pagination
    def test_tc501_default_no_pagination(self, data_query_api, widget_id, default_params):
        """TC501: 不分页-默认查询"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}]
        )

        APIAssertion.assert_success(response)

        data = response.get("data", {})
        records = data.get("records", [])

        # 验证返回数据（可能有默认限制）
        assert len(records) > 0, "应有数据返回"

    @pytest.mark.no_pagination
    def test_tc502_single_aggregation(self, data_query_api, widget_id, default_params):
        """TC502: 不分页-single汇总"""
        # 先获取全部数据汇总
        all_response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            single=True
        )

        APIAssertion.assert_success(all_response)
        PaginationAssertion.assert_is_single_record(all_response)

        # 获取分页数据对比
        paged_response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=1,
            size=100
        )

        # 验证汇总值正确（如果数据量不大）
        single_amount = all_response.get("data", {}).get("records", [{}])[0].get("amount", 0)
        paged_total = paged_response.get("data", {}).get("total", 0)

        assert single_amount > 0, "汇总金额应大于0"

    @pytest.mark.no_pagination
    def test_tc503_limit_restriction(self, data_query_api, widget_id, default_params):
        """TC503: 不分页-limit限制"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            limit=9
        )

        APIAssertion.assert_success(response)
        PaginationAssertion.assert_limit_records(response, expected_limit=9)

    @pytest.mark.no_pagination
    def test_tc504_limit_one(self, data_query_api, widget_id, default_params):
        """TC504: 不分页-limit=1"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            limit=1
        )

        APIAssertion.assert_success(response)

        data = response.get("data", {})
        records = data.get("records", [])

        # limit=1 可能返回1条明细 + 1条其他汇总（8+1场景）
        assert len(records) <= 2, f"limit=1应返回最多2条记录，实际 {len(records)} 条"

    @pytest.mark.no_pagination
    def test_tc505_aggregation_verification(self, data_query_api, widget_id, default_params):
        """TC505: 不分页-汇总验证"""
        # 获取明细数据
        detail_response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            dimensions=[{"code": "orgId", "groupByType": "X"}],
            current=1,
            size=1000
        )

        # 获取汇总数据
        summary_response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            single=True
        )

        # 计算明细汇总
        detail_records = detail_response.get("data", {}).get("records", [])
        detail_sum = sum(r.get("amount", 0) or 0 for r in detail_records)

        # 获取汇总值
        summary_records = summary_response.get("data", {}).get("records", [])
        if summary_records:
            summary_amount = summary_records[0].get("amount", 0)

            # 允许一定误差（浮点数精度）
            if detail_sum > 0:
                error_rate = abs(summary_amount - detail_sum) / detail_sum
                assert error_rate < 0.01, f"汇总金额误差过大: 明细汇总={detail_sum}, 单条汇总={summary_amount}"

    @pytest.mark.no_pagination
    def test_tc506_no_pagination_with_filters(self, data_query_api, widget_id, default_params):
        """TC506: 不分页+过滤"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[
                {"code": "orgId", "value": "1", "condition": "in"}
            ],
            index_info=[{"code": "amount"}],
            single=True
        )

        APIAssertion.assert_success(response)
        PaginationAssertion.assert_is_single_record(response)

    @pytest.mark.no_pagination
    def test_tc507_no_pagination_with_grouping(self, data_query_api, widget_id, default_params):
        """TC507: 不分页+分组"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            dimensions=[{"code": "orgId", "groupByType": "X"}]
        )

        APIAssertion.assert_success(response)

        # 验证返回所有分组数据
        data = response.get("data", {})
        records = data.get("records", [])

        # 分组查询应该返回多条记录
        assert len(records) >= 1, "分组查询应返回至少1条记录"

    @pytest.mark.no_pagination
    def test_tc508_detail_list_boolean(self, data_query_api, widget_id, default_params):
        """TC508: 明细查询不分页"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            listBoolean=True
        )

        APIAssertion.assert_success(response)

        # 明细查询可能返回更多字段
        data = response.get("data", {})
        records = data.get("records", [])

        if records:
            # 验证明细数据结构
            assert "amount" in records[0], "明细数据应包含amount字段"