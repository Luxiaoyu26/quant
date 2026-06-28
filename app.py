import os

for key in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
]:
    os.environ.pop(key, None)

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data_loader import clear_data_cache, load_csv_data, load_price_data
from core.indicators import add_moving_averages, add_rsi, add_bollinger_bands, add_macd
from core.backtester import run_backtest
from strategies.rule_based import ma_cross_strategy, rsi_mean_reversion_strategy, bollinger_strategy
from strategies.ml_strategy import ml_direction_strategy
from selection.main_wave_selector import run_main_wave_candidate_selection
from stock_pools.sector_map import STOCK_SECTOR_MAP


def _parse_stock_pool(raw_text: str) -> list[str]:
    normalized = raw_text.replace(",", "\n").replace("，", "\n")
    symbols = []
    for value in normalized.splitlines():
        symbol = value.strip()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


def render_main_wave_page() -> None:
    st.title("主升浪候选股 Top20")
    st.caption("规则型候选池：动量因子 · 板块因子 · 量价因子 · 风险过滤")

    today = pd.Timestamp.today().normalize()
    default_pool = "\n".join(STOCK_SECTOR_MAP.keys())
    with st.sidebar:
        st.header("候选池设置")
        pool_text = st.text_area(
            "股票池",
            value=default_pool,
            height=220,
            help="支持英文/中文逗号或换行分隔。",
            key="main_wave_pool",
        )
        wave_start = st.date_input(
            "开始日期",
            value=today - pd.Timedelta(days=180),
            key="main_wave_start",
        )
        wave_end = st.date_input("结束日期", value=today, key="main_wave_end")
        specify_date = st.checkbox("指定选择日期", value=False, key="main_wave_use_date")
        wave_select_date = (
            st.date_input("选择日期", value=wave_end, key="main_wave_select_date")
            if specify_date
            else None
        )
        wave_top_n = st.number_input(
            "Top N", min_value=1, max_value=100, value=20, step=1, key="main_wave_top_n"
        )
        wave_adjust_label = st.selectbox(
            "复权方式",
            ["前复权 qfq", "不复权", "后复权 hfq"],
            key="main_wave_adjust",
        )
        wave_adjust = {
            "前复权 qfq": "qfq",
            "不复权": "",
            "后复权 hfq": "hfq",
        }[wave_adjust_label]
        wave_source = st.selectbox(
            "数据源", ["自动", "东方财富", "新浪"], key="main_wave_source"
        )
        wave_use_cache = st.checkbox(
            "启用本地行情缓存", value=True, key="main_wave_cache"
        )
        wave_disable_proxy = st.checkbox(
            "忽略系统代理环境变量", value=True, key="main_wave_proxy"
        )
        generate = st.button("生成候选池", type="primary", key="main_wave_generate")

    st.markdown(
        """
**当前 V2 主升浪评分重点关注：**

1. 个股 20 日 / 60 日动量；
2. 是否接近 20 日 / 60 日新高；
3. 均线趋势结构；
4. 放量突破迹象；
5. 板块强度；
6. 风险惩罚。
        """
    )
    st.info("候选池仅用于研究，不构成投资建议。建议至少选择约 90 个交易日的数据。")
    if not generate:
        st.write("设置股票池和日期后，点击“生成候选池”。")
        return

    symbols = _parse_stock_pool(pool_text)
    if not symbols:
        st.warning("股票池为空，请至少输入一个 A 股代码。")
        return
    if pd.to_datetime(wave_start) > pd.to_datetime(wave_end):
        st.warning("开始日期不能晚于结束日期。")
        return

    try:
        with st.spinner(f"正在计算 {len(symbols)} 只股票的候选排名……"):
            result = run_main_wave_candidate_selection(
                symbols=symbols,
                start=str(wave_start),
                end=str(wave_end),
                select_date=str(wave_select_date) if wave_select_date else None,
                top_n=int(wave_top_n),
                adjust=wave_adjust,
                source=wave_source,
                use_cache=wave_use_cache,
                disable_proxy=wave_disable_proxy,
            )
    except Exception as exc:
        st.error(f"候选池生成失败：{exc}")
        return

    errors = result.attrs.get("errors", [])
    if errors:
        st.warning(f"有 {len(errors)} 只股票处理失败，其他股票已继续计算。")
        with st.expander("查看失败明细"):
            for error in errors:
                st.write(f"- {error}")

    if result.empty:
        st.warning("没有股票通过当前风险过滤条件，请检查日期范围、数据源或股票池。")
        return

    st.subheader(f"候选结果 Top {len(result)}")
    st.dataframe(result, use_container_width=True, hide_index=True)
    st.download_button(
        "下载候选池 CSV",
        result.to_csv(index=False).encode("utf-8-sig"),
        file_name="main_wave_candidates.csv",
        mime="text/csv",
    )

st.set_page_config(page_title="Quant Trading Platform", layout="wide")

page_name = st.sidebar.radio("页面", ["单股回测", "主升浪候选池"])
if page_name == "主升浪候选池":
    render_main_wave_page()
    st.stop()

st.title("A股量化交易平台 MVP+")
st.caption("A股数据 · K线技术指标 · 策略回测 · 真实交易规则近似 · 机器学习方向预测")

with st.sidebar:
    st.header("基础设置")
    market = st.selectbox("市场", ["A股", "美股/港股"], index=0)
    use_cache = st.checkbox(
        "启用本地行情缓存",
        value=True,
        help="第一次下载后保存到 data_cache/，之后同样参数会直接读本地缓存，避免重复请求网络。",
    )
    if st.button("清空本地行情缓存"):
        deleted_count = clear_data_cache()
        st.success(f"已清空缓存文件：{deleted_count} 个")

    disable_proxy = st.checkbox(
        "忽略系统代理环境变量",
        value=True,
        help="下载行情前忽略 HTTP_PROXY、HTTPS_PROXY 和 ALL_PROXY，减少代理配置导致的连接失败。",
    )
    data_source = "auto"
    uploaded_file = None
    adjust = "qfq"

    if market == "A股":
        symbol = st.text_input("股票代码", value="600519", help="A股示例：600519 贵州茅台；000001 平安银行；300750 宁德时代；也支持 600519.SH / 000001.SZ")
        source_label = st.selectbox(
            "A股数据源",
            ["自动", "东方财富", "新浪", "本地CSV"],
            index=0,
        )
        data_source = {
            "自动": "auto",
            "东方财富": "eastmoney",
            "新浪": "sina",
            "本地CSV": "local_csv",
        }[source_label]
        if data_source == "local_csv":
            uploaded_file = st.file_uploader(
                "上传本地行情 CSV",
                type=["csv"],
                help="CSV 需包含 Date、Open、High、Low、Close、Volume 字段，字段名大小写均可。",
            )
        adjust_label = st.selectbox("复权方式", ["前复权 qfq", "不复权", "后复权 hfq"], index=0)
        adjust = {"前复权 qfq": "qfq", "不复权": "", "后复权 hfq": "hfq"}[adjust_label]
        default_fee = 0.0003
        default_slippage = 0.0002
        default_sell_tax = 0.0005
    else:
        symbol = st.text_input("股票代码", value="AAPL", help="美股示例：AAPL, MSFT, TSLA；港股示例可能需要 .HK 后缀")
        adjust = "none"
        data_source = "yfinance"
        disable_proxy = True
        default_fee = 0.001
        default_slippage = 0.0005
        default_sell_tax = 0.0

    start = st.date_input("开始日期", value=pd.to_datetime("2020-01-01"))
    end = st.date_input("结束日期", value=pd.to_datetime("2025-01-01"))
    initial_cash = st.number_input("初始资金", min_value=1000.0, value=100000.0, step=10000.0)
    fee_rate = st.number_input("佣金/双边费率", min_value=0.0, value=default_fee, step=0.0001, format="%.4f")
    slippage_rate = st.number_input("滑点率", min_value=0.0, value=default_slippage, step=0.0001, format="%.4f")
    sell_tax_rate = st.number_input("卖出印花税/单边税率", min_value=0.0, value=default_sell_tax, step=0.0001, format="%.4f", help="A股默认按卖出单边 0.05% 近似；可按你的券商实际费率调整。")

    st.header("A股真实规则近似")
    if market == "A股":
        lot_size = st.number_input("最小交易单位/一手", min_value=1, value=100, step=100, help="A股普通股票通常买入至少 100 股，卖出可卖持仓。这里为简化按买入整数手处理。")
        min_commission = st.number_input("最低佣金", min_value=0.0, value=5.0, step=1.0)
        enable_t1 = st.checkbox("启用 T+1 卖出限制", value=True)
        enable_limit_filter = st.checkbox("启用涨跌停无法成交近似", value=True)
        limit_rate = st.selectbox("涨跌停幅度近似", [0.10, 0.20, 0.05], index=0, format_func=lambda x: f"{x:.0%}", help="主板常见 10%，创业板/科创板常见 20%，ST 常见 5%。这里只做日线近似。")
    else:
        lot_size = 1
        min_commission = 0.0
        enable_t1 = False
        enable_limit_filter = False
        limit_rate = 0.10

    trade_price_label = st.selectbox("成交价格", ["次日开盘价 Open", "次日收盘价 Close"], index=0, help="策略信号已经 shift 一天，默认用次日开盘价撮合，更接近实盘。")
    trade_price_col = "Open" if trade_price_label.startswith("次日开盘") else "Close"

    st.header("策略选择")
    strategy_name = st.selectbox(
        "策略",
        ["双均线策略", "RSI均值回归策略", "布林带策略", "机器学习方向预测策略"],
    )

    params = {}
    if strategy_name == "双均线策略":
        params["fast"] = st.slider("短期均线", 2, 60, 5)
        params["slow"] = st.slider("长期均线", 5, 200, 20)
    elif strategy_name == "RSI均值回归策略":
        params["window"] = st.slider("RSI窗口", 5, 40, 14)
        params["buy_threshold"] = st.slider("买入阈值：RSI低于", 5, 45, 30)
        params["sell_threshold"] = st.slider("卖出阈值：RSI高于", 55, 95, 70)
    elif strategy_name == "布林带策略":
        params["window"] = st.slider("布林带窗口", 5, 80, 20)
        params["num_std"] = st.slider("标准差倍数", 1.0, 4.0, 2.0, step=0.1)
    else:
        params["train_ratio"] = st.slider("训练集比例", 0.5, 0.85, 0.7, step=0.05)
        params["probability_threshold"] = st.slider("上涨概率买入阈值", 0.50, 0.80, 0.55, step=0.01)
        params["n_estimators"] = st.slider("随机森林树数量", 50, 500, 200, step=50)


def pct(x):
    return f"{x:.2%}"


def num(x):
    return f"{x:,.2f}"


def plot_price(df: pd.DataFrame, title: str):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="K线",
    ))
    for col in ["MA5", "MA10", "MA20", "MA60"]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines", name=col))
    if {"BB_UPPER", "BB_MID", "BB_LOWER"}.issubset(df.columns):
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_UPPER"], mode="lines", name="BB Upper"))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_MID"], mode="lines", name="BB Mid"))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_LOWER"], mode="lines", name="BB Lower"))

    buy_points = df[(df.get("Trade", 0) > 0)] if "Trade" in df.columns else pd.DataFrame()
    sell_points = df[(df.get("Trade", 0) < 0)] if "Trade" in df.columns else pd.DataFrame()
    if not buy_points.empty:
        fig.add_trace(go.Scatter(x=buy_points.index, y=buy_points["Close"], mode="markers", name="买入", marker=dict(symbol="triangle-up", size=10)))
    if not sell_points.empty:
        fig.add_trace(go.Scatter(x=sell_points.index, y=sell_points["Close"], mode="markers", name="卖出", marker=dict(symbol="triangle-down", size=10)))

    fig.update_layout(title=title, xaxis_title="日期", yaxis_title="价格", height=650, xaxis_rangeslider_visible=False)
    return fig


def plot_volume(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="成交量"))
    fig.update_layout(title="成交量", xaxis_title="日期", yaxis_title="Volume", height=300)
    return fig


def plot_equity(bt: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bt.index, y=bt["Equity"], mode="lines", name="策略资金曲线"))
    fig.add_trace(go.Scatter(x=bt.index, y=bt["BuyHold_Equity"], mode="lines", name="买入并持有"))
    fig.update_layout(title="资金曲线对比", xaxis_title="日期", yaxis_title="资金", height=450)
    return fig


def plot_drawdown(bt: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bt.index, y=bt["Drawdown"], mode="lines", name="回撤"))
    fig.update_layout(title="最大回撤曲线", xaxis_title="日期", yaxis_title="Drawdown", height=300)
    return fig


try:
    if market == "A股" and data_source == "local_csv":
        if uploaded_file is None:
            st.info("请选择一个本地行情 CSV 文件。")
            st.stop()
        raw = load_csv_data(uploaded_file)
        raw = raw.loc[pd.to_datetime(start):pd.to_datetime(end)]
        if raw.empty:
            raise ValueError("本地 CSV 在所选日期范围内没有行情数据。")
    else:
        raw = load_price_data(
            symbol,
            str(start),
            str(end),
            market=market,
            adjust=adjust,
            source=data_source,
            disable_proxy=disable_proxy,
            use_cache=use_cache,
        )
    indicator_df = add_moving_averages(raw, windows=(5, 10, 20, 60))
    indicator_df = add_rsi(indicator_df)
    indicator_df = add_bollinger_bands(indicator_df)
    indicator_df = add_macd(indicator_df)

    ml_info = None
    if strategy_name == "双均线策略":
        strategy_df = ma_cross_strategy(raw, **params)
    elif strategy_name == "RSI均值回归策略":
        strategy_df = rsi_mean_reversion_strategy(raw, **params)
    elif strategy_name == "布林带策略":
        strategy_df = bollinger_strategy(raw, **params)
    else:
        strategy_df, ml_info = ml_direction_strategy(raw, **params)

    bt, trades, metrics = run_backtest(
        strategy_df,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        sell_tax_rate=sell_tax_rate,
        lot_size=int(lot_size),
        min_commission=float(min_commission),
        trade_price_col=trade_price_col,
        enable_t1=enable_t1,
        enable_limit_filter=enable_limit_filter,
        limit_rate=float(limit_rate),
    )
    display_df = indicator_df.join(strategy_df[[c for c in strategy_df.columns if c not in indicator_df.columns]], how="left")
    display_df = display_df.join(bt[["Trade", "Equity", "BuyHold_Equity", "Drawdown"]], how="left")

    st.subheader(f"{market} · {symbol.upper()} 回测结果")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最终资金", num(metrics["Final Equity"]))
    c2.metric("策略总收益", pct(metrics["Total Return"]))
    c3.metric("买入持有收益", pct(metrics["Buy & Hold Return"]))
    c4.metric("最大回撤", pct(metrics["Max Drawdown"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("年化收益", pct(metrics["Annual Return"]))
    c6.metric("夏普比率", f"{metrics['Sharpe Ratio']:.2f}")
    c7.metric("胜率", pct(metrics["Win Rate"]))
    c8.metric("交易次数", metrics["Trade Count"])

    c9, c10, c11, c12 = st.columns(4)
    c9.metric("持仓暴露", pct(metrics.get("Exposure", 0)))
    c10.metric("盈亏比", "∞" if metrics.get("Profit Factor") == float("inf") else f"{metrics.get('Profit Factor', 0):.2f}")
    c11.metric("总交易成本", num(metrics.get("Total Cost", 0)))
    c12.metric("平均持仓天数", f"{metrics.get('Average Holding Days', 0):.1f}")

    if ml_info:
        st.info(f"机器学习模型测试集准确率：{ml_info['test_accuracy']:.2%}；训练样本：{ml_info['train_size']}；测试样本：{ml_info['test_size']}。")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["行情与信号", "资金曲线", "技术指标", "交易明细", "每日持仓", "原始数据"])

    with tab1:
        st.plotly_chart(plot_price(display_df, f"{symbol.upper()} K线与交易信号"), use_container_width=True)
        st.plotly_chart(plot_volume(display_df), use_container_width=True)

    with tab2:
        st.plotly_chart(plot_equity(bt), use_container_width=True)
        st.plotly_chart(plot_drawdown(bt), use_container_width=True)

    with tab3:
        st.write("技术指标数据预览")
        cols = [c for c in ["Close", "MA5", "MA10", "MA20", "MA60", "RSI", "MACD", "MACD_SIGNAL", "MACD_HIST", "BB_UPPER", "BB_MID", "BB_LOWER"] if c in display_df.columns]
        st.dataframe(display_df[cols].tail(100), use_container_width=True)

    with tab4:
        st.write("交易明细包含成交价格、股数、手续费、印花税、单笔收益等字段。")
        if trades.empty:
            st.warning("当前参数下没有产生完整交易。")
        else:
            show_trades = trades.copy()
            for col in ["Return"]:
                if col in show_trades.columns:
                    show_trades[col] = show_trades[col].map(lambda x: f"{x:.2%}")
            st.dataframe(show_trades, use_container_width=True)
            st.download_button(
                "下载交易明细 CSV",
                trades.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{symbol.upper()}_trades.csv",
                mime="text/csv",
            )

    with tab5:
        st.write("每日持仓用于检查回测是否符合真实交易逻辑：现金、股数、市值、动作、无法成交原因。")
        holding_cols = [c for c in ["Close", "Cash", "Shares", "Market_Value", "Equity", "Actual_Position", "Action", "Reason", "Commission", "Sell_Tax", "Slippage_Cost"] if c in display_df.columns]
        st.dataframe(display_df[holding_cols].tail(300), use_container_width=True)
        st.download_button(
            "下载每日持仓 CSV",
            display_df[holding_cols].to_csv().encode("utf-8-sig"),
            file_name=f"{symbol.upper()}_daily_position.csv",
            mime="text/csv",
        )

    with tab6:
        st.dataframe(display_df.tail(300), use_container_width=True)
        st.download_button(
            "下载完整回测数据 CSV",
            display_df.to_csv().encode("utf-8-sig"),
            file_name=f"{symbol.upper()}_backtest.csv",
            mime="text/csv",
        )

    st.divider()
    st.markdown(
        """
### 这个平台目前的核心逻辑

- **K线**：展示每天的开盘价、最高价、最低价、收盘价。
- **成交量**：辅助判断价格变化背后是否有资金参与。
- **策略信号**：策略先生成 Signal，再 shift 一天形成 Position，避免使用未来信息。
- **A股数据**：使用 6 位股票代码，默认前复权价格，适合多数技术指标与回测。
- **回测**：逐日维护现金、股数、市值和资金曲线，而不是简单向量化收益。
- **A股交易规则近似**：支持 100 股整数手、T+1、最低佣金、涨跌停/停牌无法成交近似。
- **风险指标**：最大回撤衡量最糟糕的资金下跌幅度；夏普比率衡量单位波动下的收益。
        """
    )

except Exception as e:
    st.error(f"运行失败：{e}")
    st.markdown(
        """
可能原因：

1. 股票代码不存在或数据源暂时不可用；
2. 日期范围太短，指标或机器学习模型无法计算；
3. A股模式需要安装 `akshare`，且当前网络能访问数据源；
4. 美股/港股模式需要 `yfinance` 能访问网络；
5. 双均线策略中短均线必须小于长均线。
        """
    )
