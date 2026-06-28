# 主升浪候选股 Top20 设计

## 目标与边界

在不改变现有单股回测流程的前提下，增加规则型 A 股候选池。第一版只使用动量、量价、板块强度和风险过滤，不训练模型、不读取新闻、不连接 QMT、不下单。

## 模块

- `stock_pools/sector_map.py`：标准化股票代码并返回静态板块。
- `factors/momentum_factors.py`：从单股 OHLCV 计算收益、均线、新高和突破特征。
- `factors/volume_price_factors.py`：计算成交量均线、量比、上涨日量能和波动率。
- `factors/sector_factors.py`：在选股日期的股票截面上聚合板块强度。
- `factors/risk_filters.py`：保留全部行并记录过滤结果和原因。
- `selection/main_wave_selector.py`：负责加载多只股票、跳过失败项、取最近特征截面、评分和 Top N。

## 数据流

每只股票通过现有 `load_price_data` 获取缓存或网络行情；因子函数不下载数据。选择器取 `select_date`（未指定时使用 `end`）当日或之前最近一条记录，组成截面，加入板块强度并过滤。只对通过过滤的股票计算百分位评分和最终分。

下载失败的股票不会终止流程，错误信息保存在返回 DataFrame 的 `attrs["errors"]` 中供页面提示。若没有可用候选，返回带标准列的空 DataFrame。

## 页面接入

`app.py` 在侧边栏最顶部增加页面选择。主升浪页面由 `render_main_wave_page()` 独立渲染，完成后调用 `st.stop()`；单股回测路径继续执行现有代码，不整体缩进、不重构。

## 测试

单元测试覆盖代码板块映射、动量、量价、板块聚合、过滤和评分。选股器测试使用 monkeypatch 模拟行情，验证单股失败可跳过、默认股票池可产生候选。最终运行全量测试、编译检查和 Streamlit 双页面启动探测。
