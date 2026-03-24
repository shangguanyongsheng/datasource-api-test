"""数据查询接口封装"""
from typing import List, Dict, Any, Optional
from api.client import APIClient


class DataQueryAPI:
    """数据源查询接口"""

    ENDPOINT = "/data/dashboard/load-data"

    def __init__(self, client: APIClient):
        self.client = client

    def query(
        self,
        widget_id: int,
        tenant_id: str,
        user_id: int,
        filters: Optional[List[Dict]] = None,
        index_info: Optional[List[Dict]] = None,
        dimensions: Optional[List[Dict]] = None,
        orders: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行数据查询

        Args:
            widget_id: 数据源ID
            tenant_id: 租户ID
            user_id: 用户ID
            filters: 过滤条件列表 [{"code": "orgId", "value": "1,2", "condition": "in"}]
            index_info: 指标列表 [{"code": "amount"}]
            dimensions: 维度列表 [{"code": "orgId", "groupByType": "X"}]
            orders: 排序列表 [{"code": "amount", "value": "DESC"}]
            **kwargs: 其他参数（current, size, contain等）

        Returns:
            响应数据
        """
        payload = {
            "widgetId": widget_id,
            "tenantId": tenant_id,
            "userId": user_id
        }

        if filters:
            payload["filters"] = filters
        if index_info:
            payload["indexInfo"] = index_info
        if dimensions:
            payload["dimensions"] = dimensions
        if orders:
            payload["orders"] = orders

        # 添加其他参数
        payload.update(kwargs)

        response = self.client.post(self.ENDPOINT, payload)
        response.raise_for_status()

        return response.json()

    def query_with_filters(
        self,
        widget_id: int,
        tenant_id: str,
        user_id: int,
        filters: List[Dict]
    ) -> Dict[str, Any]:
        """带过滤条件的查询"""
        return self.query(
            widget_id=widget_id,
            tenant_id=tenant_id,
            user_id=user_id,
            filters=filters,
            index_info=[{"code": "amount"}]
        )

    def query_with_grouping(
        self,
        widget_id: int,
        tenant_id: str,
        user_id: int,
        dimensions: List[Dict]
    ) -> Dict[str, Any]:
        """带分组的查询"""
        return self.query(
            widget_id=widget_id,
            tenant_id=tenant_id,
            user_id=user_id,
            dimensions=dimensions,
            index_info=[{"code": "amount"}]
        )

    def query_paged(
        self,
        widget_id: int,
        tenant_id: str,
        user_id: int,
        current: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """分页查询"""
        return self.query(
            widget_id=widget_id,
            tenant_id=tenant_id,
            user_id=user_id,
            index_info=[{"code": "amount"}],
            current=current,
            size=size
        )