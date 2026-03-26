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

    def __init__(self, base_url: str, timeout: Union[int, Tuple[int, int]] = (10, 30),
                 truncate_config: Optional[Dict[str, Any]] = None):
        """
        初始化客户端
        
        Args:
            base_url: API 基础地址
            timeout: 超时设置，可以是：
                - int: 连接和读取超时都是这个值（秒）
                - (connect_timeout, read_timeout): 分别设置连接和读取超时
                默认 (10, 30) 表示连接超时 10 秒，读取超时 30 秒
            truncate_config: 响应截断配置，避免大数据导致内存问题
                - enabled: 是否启用截断（默认 True）
                - max_records: 最多保留的记录数（默认 100）
                - max_size_kb: 响应体大小阈值 KB（默认 100）
        """
        self.base_url = base_url.rstrip('/')
        
        # 处理超时参数
        if isinstance(timeout, int):
            self.timeout = (timeout, timeout)
        else:
            self.timeout = timeout
        
        # 响应截断配置
        self.truncate_config = truncate_config or {
            'enabled': True,
            'max_records': 100,
            'max_size_kb': 100
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"API客户端初始化: base_url={self.base_url}, timeout={self.timeout}, truncate={self.truncate_config}")

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
        
        logger.info(f"POST {url}")
        logger.info(f"请求体: {json.dumps(data, ensure_ascii=False)}")

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

        # 记录响应
        response_body = response.text
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应体大小: {len(response_body)} 字节")

        # 智能处理响应体（避免大响应导致内存问题）
        stored_response_body = self._smart_truncate_response(response_body)

        # 存储请求详情（用于测试报告）- 存储原始数据，由报告层格式化
        _last_request_info = {
            "url": url,
            "method": "POST",
            "request_body": data,  # 存储原始 dict
            "response_status": response.status_code,
            "response_body": stored_response_body,
            "response_headers": dict(response.headers)
        }

        return response

    def get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送GET请求"""
        global _last_request_info
        
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url}")
        if params:
            logger.info(f"请求参数: {params}")

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
        logger.info(f"响应体大小: {len(response_body)} 字节")

        # 智能处理响应体
        stored_response_body = self._smart_truncate_response(response_body)

        # 存储请求详情
        _last_request_info = {
            "url": url,
            "method": "GET",
            "request_params": params,
            "response_status": response.status_code,
            "response_body": stored_response_body,
            "response_headers": dict(response.headers)
        }

        return response
    
    def _smart_truncate_response(self, response_body: str) -> str:
        """
        智能截断响应体，避免大数据导致内存问题
        
        当响应数据量大时，只保留摘要信息：
        - total、records 数量
        - 前 N 条 records
        
        Returns:
            处理后的响应体（JSON 格式化）
        """
        import json
        
        # 获取配置
        config = self.truncate_config or {}
        max_records = config.get('max_records', 100)
        max_size_kb = config.get('max_size_kb', 100)
        
        # 检查大小
        size_kb = len(response_body) / 1024
        
        # 尝试解析 JSON
        try:
            data = json.loads(response_body)
            
            # 检查是否需要截断
            if size_kb > max_size_kb and isinstance(data, dict) and 'data' in data:
                inner_data = data['data']
                
                if isinstance(inner_data, dict) and 'records' in inner_data:
                    records = inner_data['records']
                    total = inner_data.get('total', len(records))
                    
                    if isinstance(records, list) and len(records) > max_records:
                        # 截断 records
                        truncated_records = records[:max_records]
                        
                        # 构建摘要响应
                        truncated_data = {
                            "code": data.get('code'),
                            "message": data.get('message'),
                            "data": {
                                "total": total,
                                "size": inner_data.get('size', 10),
                                "current": inner_data.get('current', 1),
                                "records_count": len(records),
                                "records": truncated_records,
                                "_truncated": True,
                                "_truncated_msg": f"数据量过大({len(records)}条，{size_kb:.1f}KB)，已截断只显示前{max_records}条"
                            }
                        }
                        
                        logger.warning(f"响应数据量过大({len(records)}条，{size_kb:.1f}KB)，已截断")
                        data = truncated_data
            
            # 统一格式化输出
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        except (json.JSONDecodeError, TypeError):
            # 不是 JSON，原样返回
            return response_body

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