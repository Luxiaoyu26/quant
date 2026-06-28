# A股量化交易平台 MVP

一个基于 Streamlit 的本地量化研究平台，面向 A 股策略学习、技术指标分析和逐日撮合式回测，同时支持美股/港股行情。项目目前专注研究与回测，并通过 Broker 抽象为后续模拟交易和 QMT 接入预留边界。

## 当前功能

- A 股行情：自动、东方财富、新浪、本地 CSV
- 美股/港股行情：yfinance
- 本地 CSV 行情缓存与缓存清理
- 系统代理环境变量处理
- K 线、成交量、均线、RSI、MACD、布林带
- 策略回测、交易明细、每日持仓和绩效指标
- 独立 OHLCV 数据质量检查工具
- Paper Broker 与安全的 QMT 接口桩

## 当前策略

- 双均线策略
- RSI 均值回归策略
- 布林带策略
- 机器学习方向预测策略

## 当前回测规则

- T+1 卖出限制
- 100 股整数手
- 双边佣金
- 最低佣金
- 卖出印花税
- 滑点
- 涨跌停过滤
- 停牌/无成交量过滤

## 项目结构

```text
quant_platform/
├── app.py                     # Streamlit 页面入口
├── requirements.txt          # Python 依赖
├── configs/default.yaml      # 默认配置预留
├── brokers/                  # 模拟交易与未来实盘接口
│   ├── base_broker.py
│   ├── paper_broker.py
│   └── qmt_broker_stub.py
├── core/                     # 数据、指标、回测和通用工具
│   ├── data_loader.py
│   ├── indicators.py
│   ├── backtester.py
│   ├── data_quality.py
│   └── metrics.py
├── strategies/               # 规则与机器学习策略
├── data_cache/               # 本地行情缓存
├── outputs/                  # 导出结果预留目录
├── docs/                     # 路线图与 QMT 接入规划
└── tests/                    # 单元测试
```

## 安装方法

建议使用 Python 3.10 或更高版本，并创建独立虚拟环境：

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 运行方法

在项目根目录执行：

```bash
streamlit run app.py
```

## 使用示例

1. 在侧边栏选择“A股”。
2. 输入股票代码并选择行情数据源、日期范围和复权方式。
3. 选择策略并调整参数。
4. 查看 K 线、绩效指标、交易明细和每日持仓。
5. 首次网络下载后会写入 `data_cache/`，相同参数可直接命中本地缓存。

A 股股票代码示例：

| 代码 | 名称 |
| --- | --- |
| 600519 | 贵州茅台 |
| 000001 | 平安银行 |
| 300750 | 宁德时代 |
| 601318 | 中国平安 |

也支持 `600519.SH`、`000001.SZ`、`sh600519` 等格式。

## 测试

```bash
python -m pytest -v
```

## 后续规划

- 多股票组合回测
- 因子选股
- 参数优化
- 模拟交易
- QMT 接口
- 风控系统

详细路线见 [docs/roadmap.md](docs/roadmap.md)，QMT 边界见 [docs/qmt_integration_plan.md](docs/qmt_integration_plan.md)。

## 风险提示

- 本项目仅用于学习和研究。
- 本项目不构成任何投资建议。
- 回测收益不代表未来收益。
- 当前 QMT 模块只是接口桩，不连接账户，也不执行真实交易。

## License

本项目采用 [MIT License](LICENSE)。
