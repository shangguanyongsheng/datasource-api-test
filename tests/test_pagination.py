"""分页场景测试"""
import pytest
from utils.assertion import APIAssertion, PaginationAssertion


class TestPaginationScenarios:
    """分页测试场景"""

    @pytest.mark.pagination
    def test_tc401_first_page(self, data_query_api, widget_id, default_params):
        """TC401: 分页-首页查询"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=1,
            size=10
        )

        APIAssertion.assert_success(response)
        PaginationAssertion.assert_pagination_metadata(response, expected_current=1, expected_size=10)
        PaginationAssertion.assert_record_count_matches_page(response)

    @pytest.mark.pagination
    def test_tc402_middle_page(self, data_query_api, widget_id, default_params):
        """TC402: 分页-中间页查询"""
        # 先获取总数
        first_response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=1,
            size=10
        )

        total = first_response.get("data", {}).get("total", 0)
        pages = first_response.get("data", {}).get("pages", 0)

        if pages >= 2:
            # 查询第2页
            response = data_query_api.query(
                widget_id=widget_id,
                tenant_id=default_params['tenant_id'],
                user_id=default_params['user_id'],
                index_info=[{"code": "amount"}],
                current=2,
                size=10
            )

            APIAssertion.assert_success(response)
            PaginationAssertion.assert_pagination_metadata(response, expected_current=2, expected_size=10)

            # 验证第1页和第2页数据不重复
            PaginationAssertion.assert_no_duplicate_records(
                [first_response, response],
                key_field="orgId"
            )

    @pytest.mark.pagination
    def test_tc403_last_page(self, data_query_api, widget_id, default_params):
        """TC403: 分页-末页查询"""
        # 先获取总页数
        first_response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=1,
            size=10
        )

        pages = first_response.get("data", {}).get("pages", 0)

        if pages > 0:
            response = data_query_api.query(
                widget_id=widget_id,
                tenant_id=default_params['tenant_id'],
                user_id=default_params['user_id'],
                index_info=[{"code": "amount"}],
                current=pages,
                size=10
            )

            APIAssertion.assert_success(response)
            PaginationAssertion.assert_pagination_metadata(response, expected_current=pages, expected_size=10)

    @pytest.mark.pagination
    def test_tc404_large_page_number(self, data_query_api, widget_id, default_params):
        """TC404: 分页-超大页码"""
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

        # 验证total仍然正确
        data = response.get("data", {})
        assert data.get("total", 0) > 0, "total应该有值"

    @pytest.mark.pagination
    def test_tc405_different_page_sizes(self, data_query_api, widget_id, default_params):
        """TC405: 分页-不同页大小"""
        page_sizes = [10, 20, 50, 100]

        for size in page_sizes:
            response = data_query_api.query(
                widget_id=widget_id,
                tenant_id=default_params['tenant_id'],
                user_id=default_params['user_id'],
                index_info=[{"code": "amount"}],
                current=1,
                size=size
            )

            APIAssertion.assert_success(response)
            PaginationAssertion.assert_pagination_metadata(response, expected_current=1, expected_size=size)

    @pytest.mark.pagination
    def test_tc406_pagination_metadata(self, data_query_api, widget_id, default_params):
        """TC406: 分页-元数据验证"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            current=1,
            size=10
        )

        data = response.get("data", {})

        # 验证所有分页字段存在
        assert "records" in data, "缺少records字段"
        assert "total" in data, "缺少total字段"
        assert "current" in data, "缺少current字段"
        assert "size" in data, "缺少size字段"
        assert "pages" in data, "缺少pages字段"

        # 验证字段类型
        assert isinstance(data["records"], list), "records应为列表"
        assert isinstance(data["total"], int), "total应为整数"
        assert isinstance(data["current"], int), "current应为整数"
        assert isinstance(data["size"], int), "size应为整数"
        assert isinstance(data["pages"], int), "pages应为整数"

    @pytest.mark.pagination
    def test_tc409_pagination_with_filters(self, data_query_api, widget_id, default_params):
        """TC409: 分页+过滤条件"""
        response = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            filters=[
                {"code": "orgId", "value": "1,2,3", "condition": "in"}
            ],
            index_info=[{"code": "amount"}],
            current=1,
            size=10
        )

        APIAssertion.assert_success(response)
        PaginationAssertion.assert_pagination_metadata(response, expected_current=1, expected_size=10)

    @pytest.mark.pagination
    def test_tc410_pagination_with_ordering(self, data_query_api, widget_id, default_params):
        """TC410: 分页+排序"""
        # 获取第1页
        first_page = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            orders=[{"code": "amount", "value": "DESC"}],
            current=1,
            size=10
        )

        APIAssertion.assert_success(first_page)

        # 获取第2页
        second_page = data_query_api.query(
            widget_id=widget_id,
            tenant_id=default_params['tenant_id'],
            user_id=default_params['user_id'],
            index_info=[{"code": "amount"}],
            orders=[{"code": "amount", "value": "DESC"}],
            current=2,
            size=10
        )

        APIAssertion.assert_success(second_page)

        # 验证第1页数据 >= 第2页数据（降序）
        first_records = first_page.get("data", {}).get("records", [])
        second_records = second_page.get("data", {}).get("records", [])

        if first_records and second_records:
            first_max = first_records[-1].get("amount", 0)
            second_min = second_records[0].get("amount", float('inf'))
            assert first_max >= second_min, "分页排序数据不连续"