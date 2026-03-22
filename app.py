import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="股票量化分析", layout="wide")
st.title("📈 股票量化分析工具")

st.sidebar.header("手动分析设置")
symbol = st.sidebar.text_input("股票代码（例如 002413）", value="002413")
days = st.sidebar.slider("分析天数", 30, 365, 120)

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(code, days, retries=3):
    """获取A股数据，带重试机制"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    for attempt in range(retries):
        try:
            df = ak.stock_zh_a_hist_em(
                symbol=code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            if df.empty:
                return None
            # 标准化列名
            df.columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]
            df["日期"] = pd.to_datetime(df["日期"])
            df.set_index("日期", inplace=True)
            # 计算均线
            df["MA5"] = df["收盘"].rolling(5).mean()
            df["MA20"] = df["收盘"].rolling(20).mean()
            # 信号
            df["信号"] = 0
            df.loc[df["MA5"] > df["MA20"], "信号"] = 1
            df.loc[df["MA5"] < df["MA20"], "信号"] = -1
            df["持仓变化"] = df["信号"].diff()
            return df
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # 重试前等待2秒
                continue
            else:
                st.error(f"获取数据失败（重试{retries}次后）：{e}")
                return None
    return None

if st.sidebar.button("开始分析"):
    with st.spinner("正在获取数据，请稍候..."):
        df = get_stock_data(symbol, days)
        if df is not None and not df.empty:
            # 获取最新数据
            latest = df.iloc[-1]
            try:
                close_val = float(latest["收盘"])
                ma5_val = float(latest["MA5"])
                ma20_val = float(latest["MA20"])
                signal_val = latest["信号"]
            except Exception as e:
                st.error(f"数据解析错误：{e}")
                st.stop()

            st.success("分析完成！")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最新收盘价", f"{close_val:.2f}")
            with col2:
                st.metric("MA5", f"{ma5_val:.2f}")
            with col3:
                st.metric("MA20", f"{ma20_val:.2f}")

            latest_signal = "买入" if signal_val == 1 else ("卖出" if signal_val == -1 else "观望")
            st.info(f"当前信号：{latest_signal}")

            # K线图
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["开盘"],
                high=df["最高"],
                low=df["最低"],
                close=df["收盘"],
                name="K线"
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df["MA5"], mode='lines', name="MA5", line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], mode='lines', name="MA20", line=dict(color='blue')))
            fig.update_layout(title=f"{symbol} 日K线图", xaxis_title="日期", yaxis_title="价格", height=600)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("最新20日数据")
            display_df = df[["开盘","最高","最低","收盘","MA5","MA20"]].tail(20)
            st.dataframe(display_df)
        else:
            st.error("未获取到数据，请检查股票代码是否正确，或稍后重试。")

st.markdown("---")
st.markdown("### 使用说明")
st.markdown("1. 输入6位股票代码（如002413）")
st.markdown("2. 选择分析天数，点击“开始分析”")
st.markdown("3. 系统显示K线图、移动平均线、买卖信号")
