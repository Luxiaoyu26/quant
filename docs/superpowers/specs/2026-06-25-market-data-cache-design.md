# 行情数据本地缓存设计

## 目标

在不改动策略、指标和回测逻辑的前提下，为 A 股及美股/港股网络行情增加参数级 CSV 缓存，并在 Streamlit 侧边栏提供启用和清空缓存控制。

## 设计

- 保留 `load_a_share_data` 和 `load_us_stock_data` 作为网络数据源函数。
- `load_price_data` 负责参数标准化、缓存键生成、缓存读取、市场分发和缓存写入。
- 缓存键由 `market/symbol/start/end/adjust/source` 的标准化值计算 MD5，并使用安全的可读前缀。
- 缓存 CSV 只保存标准化的 `Open, High, Low, Close, Volume`，`Date` 作为索引写入和恢复。
- 缓存读取失败时忽略坏缓存并继续网络下载；下载成功后覆盖缓存。
- 本地 CSV 通过 `load_csv_data` 单独加载，不进入行情缓存流程。
- `clear_data_cache` 仅删除指定缓存目录下的 CSV 文件并返回数量。

## Streamlit 接入

- 在任何网络库导入前清理代理环境变量。
- 所有市场分支均初始化 `adjust`、`data_source`、`disable_proxy` 和 `use_cache`。
- A 股提供自动、东方财富、新浪和本地 CSV；美股/港股使用 yfinance。
- 本地 CSV 模式使用上传文件，网络模式调用带缓存参数的 `load_price_data`。

## 验证

- 单元测试：缓存命中、禁用缓存、坏缓存回退、清空缓存、字段及日期索引标准化、本地 CSV。
- 静态检查：`py_compile` 与模块导入。
- 启动检查：短时运行 `streamlit run app.py`，确认服务成功启动且无即时导入异常。
