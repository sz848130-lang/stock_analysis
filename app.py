import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="股票量化分析", layout="wide")
st.title("📈 股票量化分析工具")

# 侧边栏输入
st.sidebar.header("手动分析设置")
symbol = st.sidebar.text_input("股票代码（例如 002413）", value="002413")
days = st.sidebar.slider("分析天数", 30, 365, 120)

@st.cache_data(ttl=3600, show_spinner=False)
def get_stock_data(code, days, retries=3):
    """获取股票数据，带重试机制"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    for attempt in range(retries):
        try:
            # 使用东方财富接口，更稳定
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
            # 简单信号
            df["信号"] = 0
            df.loc[df["MA5"] > df["MA20"], "信号"] = 1
            df.loc[df["MA5"] < df["MA20"], "信号"] = -1
            df["持仓变化"] = df["信号"].diff()
            return df
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # 等待2秒后重试
                continue
            else:
                st.error(f"数据获取失败（重试{retries}次后）：{str(e)}")
                return None
    return None

# 主界面按钮
if st.sidebar.button("开始分析"):
    with st.spinner("正在获取数据，请稍候..."):
        df = get_stock_data(symbol, days)
        if df is not None:
            st.success("分析完成！")
            # 关键指标
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最新收盘价", f"{df['收盘'].iloc[-1]:.2f}")
            with col2:
                st.metric("MA5", f"{df['MA5'].iloc[-1]:.2f}")
            with col3:
                st.metric("MA20", f"{df['MA20'].iloc[-1]:.2f}")
            # 当前信号
            latest_signal = "买入" if df["信号"].iloc[-1] == 1 else ("卖出" if df["信号"].iloc[-1] == -1 else "观望")
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
            
            # 显示最新数据表
            st.subheader("最新20日数据")
            st.dataframe(df.tail(20))
        else:
            st.error("未获取到数据，请检查股票代码是否正确，或稍后重试。")

# 使用说明
st.markdown("---")
st.markdown("### 使用说明")
st.markdown("1. 在左侧输入股票代码（深市6位，沪市6位，例如 600010）")
st.markdown("2. 选择分析天数，点击“开始分析”")
st.markdown("3. 系统会自动显示K线图、移动平均线、买卖信号")
st.markdown("4. 每日自动分析结果会通过邮件发送（需配置邮箱）")
