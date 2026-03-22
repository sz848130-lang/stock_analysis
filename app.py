import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="股票量化分析", layout="wide")
st.title("📈 股票量化分析工具")

st.sidebar.header("手动分析设置")
symbol = st.sidebar.text_input("股票代码（例如 002413）", value="002413")
days = st.sidebar.slider("分析天数", 30, 365, 120)

@st.cache_data(ttl=3600)
def get_stock_data(code, days):
    # 自动添加市场后缀
    if code.startswith('6'):
        ticker = f"{code}.SS"   # 上海
    else:
        ticker = f"{code}.SZ"   # 深圳
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return None
        # 计算均线
        df["MA5"] = df["Close"].rolling(5).mean()
        df["MA20"] = df["Close"].rolling(20).mean()
        df["信号"] = 0
        df.loc[df["MA5"] > df["MA20"], "信号"] = 1
        df.loc[df["MA5"] < df["MA20"], "信号"] = -1
        df["持仓变化"] = df["信号"].diff()
        return df
    except Exception as e:
        st.error(f"获取数据失败：{e}")
        return None

if st.sidebar.button("开始分析"):
    with st.spinner("获取数据中..."):
        df = get_stock_data(symbol, days)
        if df is not None:
            st.success("分析完成！")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最新收盘价", f"{df['Close'].iloc[-1]:.2f}")
            with col2:
                st.metric("MA5", f"{df['MA5'].iloc[-1]:.2f}")
            with col3:
                st.metric("MA20", f"{df['MA20'].iloc[-1]:.2f}")
            latest_signal = "买入" if df["信号"].iloc[-1] == 1 else ("卖出" if df["信号"].iloc[-1] == -1 else "观望")
            st.info(f"当前信号：{latest_signal}")

            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="K线"
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df["MA5"], mode='lines', name="MA5", line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], mode='lines', name="MA20", line=dict(color='blue')))
            fig.update_layout(title=f"{symbol} 日K线图", xaxis_title="日期", yaxis_title="价格", height=600)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("最新20日数据")
            st.dataframe(df[['Open','High','Low','Close','MA5','MA20']].tail(20))
        else:
            st.error("未获取到数据，请检查股票代码是否正确。")

st.markdown("---")
st.markdown("### 使用说明")
st.markdown("1. 输入6位股票代码（如002413）")
st.markdown("2. 选择分析天数，点击“开始分析”")
st.markdown("3. 系统显示K线图、移动平均线、买卖信号")
