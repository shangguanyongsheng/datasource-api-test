"""HTTP客户端封装"""
import requests
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

# 全局变量，存储最后一次请求的详细信息（用于测试报告）
_last_request_info: Dict[str, Any] = {}


def get_last_request_info() -> Dict[str, Any]:
    """获取最后一次请求的详细信息"""
    return _last_request_info.copy()


class APIClient:
    """HTTP客户端基类"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def set_auth(self, tenant_id: str, user_id: int, token: Optional[str] = None):
        """设置认证信息"""
        # 根据实际认证方式调整
        self.session.headers.update({
            'X-Tenant-Id': tenant_id,
            'X-User-Id': str(user_id)
        })
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'

    def post(self, endpoint: str, data: Dict[str, Any]) -> requests.Response:
        """发送POST请求"""
        import json
        global _last_request_info
        
        url = f"{self.base_url}{endpoint}"
        request_body = json.dumps(data, ensure_ascii=False, indent=2)
        
        logger.info(f"POST {url}")
        logger.info(f"请求体:\n{request_body}")

        response = self.session.post(url, json=data, timeout=self.timeout)

        # 记录完整响应
        response_body = response.text
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应体:\n{response_body}")

        # 存储请求详情（用于测试报告）
        _last_request_info = {
            "url": url,
            "method": "POST",
            "request_body": request_body,
            "response_status": response.status_code,
            "response_body": response_body,
            "response_headers": dict(response.headers)
        }

        return response

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送GET请求"""
        global _last_request_info
        
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url}")
        logger.info(f"请求参数: {params}")

        response = self.session.get(url, params=params, timeout=self.timeout)

        response_body = response.text
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应体:\n{response_body}")

        # 存储请求详情
        _last_request_info = {
            "url": url,
            "method": "GET",
            "request_params": params,
            "response_status": response.status_code,
            "response_body": response_body,
            "response_headers": dict(response.headers)
        }

        return response

    def close(self):
        """关闭会话"""
        self.session.close()