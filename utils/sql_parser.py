"""SQL INSERT语句解析器"""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


def detect_encoding(file_path: str) -> str:
    """
    检测文件编码
    
    尝试顺序：utf-8-sig (BOM) -> utf-8 -> gbk -> gb2312 -> gb18030 -> latin-1
    """
    # 先检查 BOM
    try:
        with open(file_path, 'rb') as f:
            bom = f.read(3)
            if bom == b'\xef\xbb\xbf':
                return 'utf-8-sig'
    except:
        pass
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
            return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'


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

        支持两种格式：
        1. 简化格式（8字段）：
           INSERT INTO table (data_source_id, type, code, name, field, agg_type, filter_condition, component_code) VALUES
           (123, 'filter', 'orgId', '组织', 'org_id', NULL, 'in', 'tree-select');

        2. 完整格式（26字段）：
           INSERT INTO `db`.`table` (`id`, `data_source_id`, `type`, `code`, ...) VALUES (1, 76, 'filter', 'bizType', ...);

        Args:
            sql: INSERT INTO ... VALUES ...

        Returns:
            字段配置列表
        """
        fields = []

        logger.info(f"开始解析 SQL，内容长度: {len(sql)} 字符")

        # 找到所有 INSERT ... VALUES (...) 语句
        # 使用逐字符解析，正确处理嵌套括号和引号
        i = 0
        while i < len(sql):
            # 找到 INSERT 关键字
            insert_pos = sql.upper().find('INSERT', i)
            if insert_pos == -1:
                break

            # 找到 VALUES 关键字
            values_pos = sql.upper().find('VALUES', insert_pos)
            if values_pos == -1:
                break

            # 找到 VALUES 后面的左括号
            paren_start = sql.find('(', values_pos)
            if paren_start == -1:
                break

            # 找到匹配的右括号（考虑嵌套和引号）
            paren_end = self._find_matching_paren(sql, paren_start)
            if paren_end == -1:
                break

            # 提取 VALUES 中的内容
            values_str = sql[paren_start + 1:paren_end]

            # 解析字段值
            values = self._parse_values(values_str)

            if len(values) >= 4:
                # 根据字段数量判断格式
                if len(values) == 8:
                    # 简化格式
                    field = DataSourceField(
                        data_source_id=int(values[0]),
                        type=values[1],
                        code=values[2],
                        name=values[3],
                        field=values[4] if values[4] else None,
                        agg_type=values[5] if values[5] else None,
                        filter_condition=values[6] if values[6] else None,
                        component_code=values[7] if values[7] else None
                    )
                else:
                    # 完整格式（26字段）
                    # 字段顺序：id, data_source_id, type, code, decimal_places, code_alias, field, ...
                    # 索引：     0    1               2     3     4               5           6      ...
                    field = DataSourceField(
                        data_source_id=int(values[1]),  # 第2个字段
                        type=values[2],                  # 第3个字段
                        code=values[3],                  # 第4个字段
                        name=values[10] if len(values) > 10 and values[10] else values[3],  # name 在第11位
                        field=values[6] if len(values) > 6 and values[6] else None,
                        agg_type=values[8] if len(values) > 8 and values[8] else None,
                        filter_condition=values[24] if len(values) > 24 and values[24] else None,
                        component_code=values[12] if len(values) > 12 and values[12] else None
                    )

                fields.append(field)
                logger.debug(f"解析字段: data_source_id={field.data_source_id}, type={field.type}, code={field.code}")

            i = paren_end + 1

        logger.info(f"解析SQL完成，共 {len(fields)} 个字段配置")
        return fields

    def _find_matching_paren(self, sql: str, start: int) -> int:
        """
        找到匹配的右括号位置

        Args:
            sql: SQL 字符串
            start: 左括号位置

        Returns:
            匹配的右括号位置，未找到返回 -1
        """
        depth = 0
        in_string = False
        string_char = None
        i = start

        while i < len(sql):
            char = sql[i]

            if in_string:
                if char == string_char:
                    # 检查是否是转义引号
                    if i + 1 < len(sql) and sql[i + 1] == string_char:
                        i += 1
                    else:
                        in_string = False
            else:
                if char in ("'", '"'):
                    in_string = True
                    string_char = char
                elif char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        return i

            i += 1

        return -1

    def _parse_values(self, values_str: str) -> List[Optional[str]]:
        """
        解析 VALUES 中的字段值

        处理：NULL, 数字, 字符串(单引号), JSON字符串

        Args:
            values_str: "29240, 76, 'filter', 'bizType', NULL, ..."

        Returns:
            ['29240', '76', 'filter', 'bizType', None, ...]
        """
        result = []
        current = ""
        in_string = False
        string_char = None
        last_was_string_end = False  # 标记上一个字符是否是字符串结束
        i = 0

        while i < len(values_str):
            char = values_str[i]

            if in_string:
                if char == string_char:
                    # 检查是否是转义引号 ''
                    if i + 1 < len(values_str) and values_str[i + 1] == string_char:
                        current += char
                        i += 1
                    else:
                        in_string = False
                        last_was_string_end = True
                        # 字符串值直接添加到结果，不等到逗号
                        result.append(current)
                        current = ""
                else:
                    current += char
            else:
                if char in ("'", '"'):
                    in_string = True
                    string_char = char
                    current = ""
                    last_was_string_end = False
                elif char == ',':
                    # 分隔符
                    if not last_was_string_end:
                        # 只有当上一个不是字符串结束时才处理 current
                        value = current.strip()
                        if value.upper() == 'NULL':
                            result.append(None)
                        elif value:
                            result.append(value)
                        else:
                            result.append(None)
                    # 重置状态
                    current = ""
                    last_was_string_end = False
                elif char not in (' ', '\t', '\n', '\r'):
                    current += char
                    last_was_string_end = False

            i += 1

        # 处理最后一个值
        if not last_was_string_end:
            value = current.strip()
            if value.upper() == 'NULL':
                result.append(None)
            elif value:
                result.append(value)

        return result

    def parse_sql_file(self, file_path: str) -> List[DataSourceField]:
        """
        解析SQL文件

        Args:
            file_path: SQL文件路径

        Returns:
            字段配置列表
        """
        # 自动检测文件编码
        encoding = detect_encoding(file_path)
        logger.info(f"检测到文件编码: {encoding}")
        
        with open(file_path, 'r', encoding=encoding) as f:
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