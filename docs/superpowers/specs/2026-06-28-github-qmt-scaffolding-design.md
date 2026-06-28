# GitHub 工程化与 QMT 预留设计

## 范围

保持现有 Streamlit 页面、行情、策略和回测逻辑不变。本轮只增加工程化目录、独立工具模块、Broker 抽象、默认配置和项目文档。

## 模块边界

- `brokers/` 提供统一交易接口。`PaperBroker` 只做内存即时成交；`QMTBrokerStub` 不导入 QMT、不连接账户、不发送订单。
- `core/data_quality.py` 只检查 OHLCV 数据并返回结构化问题列表，不修改输入。
- `core/metrics.py` 提供独立、无状态的基础绩效函数，暂不替换 `backtester.py` 的现有计算。
- `configs/default.yaml` 记录默认参数，暂不强制 `app.py` 读取，避免改变页面行为。
- `docs/` 和 README 说明路线、风险和未来 QMT 接入边界。

## 安全与兼容

- `.gitignore` 忽略行情缓存和输出产物，但显式保留 `.gitkeep`。
- 不删除当前 `data_cache` 中已有 CSV。
- 所有新增 Python 模块不产生导入时副作用。
- QMT 桩的全部方法明确抛出 `NotImplementedError`。

## 测试

- `PaperBroker`：连接、买入、卖出、余额/持仓/订单/成交更新及非法交易。
- 数据质量：空表、缺列、索引、重复、缺失、非法价格、高低价和成交量。
- 指标：正常、空数据、零分母和常量收益。
- 全量测试、编译检查、YAML 解析和 Streamlit 无头启动。
