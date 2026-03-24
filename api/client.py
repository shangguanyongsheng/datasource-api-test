"""HTTP客户端封装"""
import requests
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


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
        url = f"{self.base_url}{endpoint}"
        logger.info(f"POST {url}")
        logger.debug(f"Request: {data}")

        response = self.session.post(url, json=data, timeout=self.timeout)

        logger.info(f"Response: {response.status_code}")
        logger.debug(f"Response Body: {response.text[:500]}")

        return response

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送GET请求"""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url}")

        response = self.session.get(url, params=params, timeout=self.timeout)

        logger.info(f"Response: {response.status_code}")

        return response

    def close(self):
        """关闭会话"""
        self.session.close()