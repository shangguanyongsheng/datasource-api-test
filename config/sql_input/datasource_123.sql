-- 数据源ID: 123
-- 数据源名称: 融资统计测试数据源
-- 说明: 用户提供的INSERT语句，测试框架自动解析字段配置

INSERT INTO rpt_data_source_field (data_source_id, type, code, name, field, agg_type, filter_condition, component_code) VALUES
(123, 'filter', 'orgId', '组织', 'org_id', NULL, 'in', 'tree-select'),
(123, 'filter', 'year', '年度', 'year', NULL, 'geq', 'date'),
(123, 'filter', 'status', '状态', 'status', NULL, 'in', 'select'),
(123, 'index_info', 'amount', '金额', 'amount', 'sum', NULL, NULL),
(123, 'index_info', 'balance', '余额', 'balance', 'sum', NULL, NULL),
(123, 'index_info', 'count', '笔数', 'id', 'count', NULL, NULL),
(123, 'dimension', 'orgId', '组织', 'org_id', NULL, NULL, NULL),
(123, 'dimension', 'month', '月份', 'month', NULL, NULL, NULL),
(123, 'dimension', 'year', '年度', 'year', NULL, NULL, NULL),
(123, 'orders', 'amount', '金额', 'amount', NULL, NULL, NULL),
(123, 'orders', 'year', '年度', 'year', NULL, NULL, NULL);