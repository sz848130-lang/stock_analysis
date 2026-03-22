import streamlit as st
import akshare as ak

st.title("测试数据获取")
code = st.text_input("股票代码", "002413")
if st.button("测试"):
    try:
        df = ak.stock_zh_a_hist_em(symbol=code, start_date="20250101", end_date="20250323", adjust="qfq")
        st.write(df.head())
    except Exception as e:
        st.error(f"错误：{e}")
