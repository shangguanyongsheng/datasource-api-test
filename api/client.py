"""HTTP客户端封装"""
import requests
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError
from typing import Dict, Any, Optional, Tuple, Union
from utils.logger import get_logger

logger = get_logger(__name__)

# 全局变量，存储最后一次请求的详细信息（用于测试报告）
_last_request_info: Dict[str, Any] = {}


def get_last_request_info() -> Dict[str, Any]:
    """获取最后一次请求的详细信息"""
    return _last_request_info.copy()


class APIClient:
    """HTTP客户端基类"""

    def __init__(self, base_url: str, timeout: Union[int, Tuple[int, int]] = (10, 30)):
        """
        初始化客户端
        
        Args:
            base_url: API 基础地址
            timeout: 超时设置，可以是：
                - int: 连接和读取超时都是这个值（秒）
                - (connect_timeout, read_timeout): 分别设置连接和读取超时
                默认 (10, 30) 表示连接超时 10 秒，读取超时 30 秒
        """
        self.base_url = base_url.rstrip('/')
        
        # 处理超时参数
        if isinstance(timeout, int):
            self.timeout = (timeout, timeout)
        else:
            self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"API客户端初始化: base_url={self.base_url}, timeout={self.timeout}")

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
        logger.info(f"超时设置: 连接={self.timeout[0]}s, 读取={self.timeout[1]}s")

        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
        except ConnectTimeout:
            error_msg = f"连接超时：无法在 {self.timeout[0]} 秒内连接到服务器"
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ReadTimeout:
            error_msg = f"读取超时：服务器在 {self.timeout[1]} 秒内未返回响应"
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ConnectionError as e:
            error_msg = f"连接错误：无法连接到服务器 {self.base_url}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

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
        logger.info(f"超时设置: 连接={self.timeout[0]}s, 读取={self.timeout[1]}s")

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except ConnectTimeout:
            error_msg = f"连接超时：无法在 {self.timeout[0]} 秒内连接到服务器"
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ReadTimeout:
            error_msg = f"读取超时：服务器在 {self.timeout[1]} 秒内未返回响应"
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ConnectionError as e:
            error_msg = f"连接错误：无法连接到服务器 {self.base_url}"
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

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