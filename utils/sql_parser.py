"""SQL INSERT语句解析器"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DataSourceField:
    """数据源字段配置"""
    data_source_id: int
    type: str  # filter, index_info, dimension, orders
    code: str
    name: str
    field: Optional[str] = None
    agg_type: Optional[str] = None  # sum, avg, max, min, count
    filter_condition: Optional[str] = None  # in, geq, gtr, leq, lss
    component_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "data_source_id": self.data_source_id,
            "type": self.type,
            "code": self.code,
            "name": self.name,
            "field": self.field,
            "agg_type": self.agg_type,
            "filter_condition": self.filter_condition,
            "component_code": self.component_code
        }


class SQLParser:
    """SQL INSERT语句解析器"""

    # 字段列顺序（对应INSERT语句中的列顺序）
    FIELD_COLUMNS = [
        'data_source_id', 'type', 'code', 'name', 'field',
        'agg_type', 'filter_condition', 'component_code'
    ]

    def __init__(self):
        pass

    def parse_insert_statement(self, sql: str) -> List[DataSourceField]:
        """
        解析INSERT语句，提取字段配置

        Args:
            sql: INSERT INTO ... VALUES ...

        Returns:
            字段配置列表
        """
        fields = []

        # 提取数据源ID（从第一条记录获取）
        ds_id_match = re.search(r'\((\d+),\s*[\'"]filter[\'"]', sql)
        if not ds_id_match:
            ds_id_match = re.search(r'\((\d+),\s*[\'"]index_info[\'"]', sql)

        data_source_id = int(ds_id_match.group(1)) if ds_id_match else 0

        # 匹配 VALUES 后面的每一行数据
        # 格式: (123, 'filter', 'orgId', '组织', 'org_id', NULL, 'in', 'tree-select')
        value_pattern = r"\((\d+),\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*(?:'([^']+)'|NULL),\s*(?:'([^']+)'|NULL),\s*(?:'([^']+)'|NULL),\s*(?:'([^']+)'|NULL)\)"

        matches = re.findall(value_pattern, sql)

        for match in matches:
            field = DataSourceField(
                data_source_id=int(match[0]),
                type=match[1],
                code=match[2],
                name=match[3],
                field=match[4] if match[4] else None,
                agg_type=match[5] if match[5] else None,
                filter_condition=match[6] if match[6] else None,
                component_code=match[7] if match[7] else None
            )
            fields.append(field)

        logger.info(f"解析SQL完成，共 {len(fields)} 个字段配置")
        return fields

    def parse_sql_file(self, file_path: str) -> List[DataSourceField]:
        """
        解析SQL文件

        Args:
            file_path: SQL文件路径

        Returns:
            字段配置列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        return self.parse_insert_statement(sql_content)

    def parse_sql_directory(self, dir_path: str) -> Dict[int, List[DataSourceField]]:
        """
        解析目录下所有SQL文件

        Args:
            dir_path: SQL文件目录

        Returns:
            {data_source_id: [字段配置列表]}
        """
        result = {}
        dir_path = Path(dir_path)

        for sql_file in dir_path.glob("*.sql"):
            logger.info(f"解析文件: {sql_file}")
            fields = self.parse_sql_file(str(sql_file))

            # 按data_source_id分组
            for field in fields:
                if field.data_source_id not in result:
                    result[field.data_source_id] = []
                result[field.data_source_id].append(field)

        return result

    def get_fields_by_type(self, fields: List[DataSourceField], field_type: str) -> List[DataSourceField]:
        """
        按类型筛选字段

        Args:
            fields: 字段列表
            field_type: filter/index_info/dimension/orders

        Returns:
            筛选后的字段列表
        """
        return [f for f in fields if f.type == field_type]


class DataSourceConfig:
    """数据源配置（解析后的结构化配置）"""

    def __init__(self, fields: List[DataSourceField]):
        self.all_fields = fields
        self.widget_id = fields[0].data_source_id if fields else 0

        # 按类型分组
        self.filters = [f for f in fields if f.type == 'filter']
        self.index_info = [f for f in fields if f.type == 'index_info']
        self.dimensions = [f for f in fields if f.type == 'dimension']
        self.orders = [f for f in fields if f.type == 'orders']

    def get_filter_codes(self) -> List[str]:
        """获取所有过滤字段编码"""
        return [f.code for f in self.filters]

    def get_index_codes(self) -> List[str]:
        """获取所有指标字段编码"""
        return [f.code for f in self.index_info]

    def get_dimension_codes(self) -> List[str]:
        """获取所有维度字段编码"""
        return [f.code for f in self.dimensions]

    def get_order_codes(self) -> List[str]:
        """获取所有排序字段编码"""
        return [f.code for f in self.orders]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "widget_id": self.widget_id,
            "filters": [f.to_dict() for f in self.filters],
            "index_info": [f.to_dict() for f in self.index_info],
            "dimensions": [f.to_dict() for f in self.dimensions],
            "orders": [f.to_dict() for f in self.orders]
        }