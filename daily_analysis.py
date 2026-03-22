import akshare as ak
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

# 股票列表（按你要求）
STOCKS = [
    "002413", "002639", "603601", "600010", "002340",
    "002165", "002506", "515180", "159611"
]

def analyze_stock(code):
    """返回分析结果字典"""
    try:
        end = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - pd.Timedelta(days=120)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=code, start_date=start, end_date=end, adjust="qfq")
        if df.empty:
            return None
        df.columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]
        df["日期"] = pd.to_datetime(df["日期"])
        df.set_index("日期", inplace=True)
        df["MA5"] = df["收盘"].rolling(5).mean()
        df["MA20"] = df["收盘"].rolling(20).mean()
        latest = df.iloc[-1]
        signal = "买入" if latest["MA5"] > latest["MA20"] else ("卖出" if latest["MA5"] < latest["MA20"] else "观望")
        return {
            "代码": code,
            "日期": latest.name.strftime("%Y-%m-%d"),
            "收盘价": round(latest["收盘"], 2),
            "MA5": round(latest["MA5"], 2),
            "MA20": round(latest["MA20"], 2),
            "信号": signal,
            "涨跌幅": round(latest["涨跌幅"], 2)
        }
    except:
        return None

def send_email(results):
    """发送邮件"""
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PWD")
    receivers = ["623819670@qq.com", "sz848130@gmail.com"]  # 你的邮箱
    subject = f"股票每日分析 {datetime.now().strftime('%Y-%m-%d')}"
    # 构建表格
    df = pd.DataFrame(results)
    html = df.to_html(index=False)
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receivers, msg.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败：{e}")

def main():
    results = []
    for code in STOCKS:
        print(f"分析 {code}...")
        res = analyze_stock(code)
        if res:
            results.append(res)
    if results:
        send_email(results)
    else:
        print("没有获取到数据")

if __name__ == "__main__":
    main()
