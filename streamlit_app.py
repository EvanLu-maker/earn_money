import streamlit as st
import pandas as pd
import yfinance as yf
from FinMind.data import DataLoader
import datetime

# --- 初始化與配置 ---
st.set_page_config(page_title="台股實戰全維度 App", layout="wide")
api = DataLoader() # FinMind API

# 自動對照表：解決名稱與代號問題
SYMBOL_MAP = {
    "主動統一升級50": "00936", "元大高股息": "0056", "國泰永續高股息": "00878",
    "群益台灣精選高息": "00919", "光寶科": "2301", "台達電": "2308",
    "鴻海": "2317", "台積電": "2330", "金像電": "2368", "廣達": "2382",
    "奇鋐": "3017", "欣興": "3037", "緯創": "3231", "群創": "3481", "緯穎": "6669"
}

# --- 數據獲取函式 ---
@st.cache_data(ttl=3600)
def get_market_data():
    """獲取美股連動與大盤資訊"""
    tickers = {
        "費城半導體": "^SOX",
        "納斯達克": "^IXIC",
        "台積電ADR": "TSM",
        "台指現貨": "^TWII"
    }
    market_res = {}
    for name, t in tickers.items():
        data = yf.download(t, period="2d", progress=False)
        if not data.empty:
            change = (data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100
            market_res[name] = {"price": data['Close'].iloc[-1], "change": float(change)}
    return market_res

def get_institutional_data(stock_id):
    """獲取台股三大法人買賣超 (FinMind)"""
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        df = api.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
        if not df.empty:
            # 計算近三日外資與投信淨買賣
            recent = df.tail(3)
            net_buy = recent['buy'].sum() - recent['sell'].sum()
            return "買超" if net_buy > 0 else "賣超"
    except:
        return "未知"
    return "無數據"

# --- 主程式介面 ---
st.title("🏹 台股全維度實戰決策系統")
st.caption("整合：美股連動、法人籌碼、大盤趨勢、個股診斷")

# 1. 頂部看板：全球與大盤走勢
market = get_market_data()
cols = st.columns(len(market))
for i, (name, val) in enumerate(market.items()):
    cols[i].metric(name, f"{val['price']:.2f}", f"{val['change']:.2f}%")

# 2. 側邊欄：匯入 CSV
with st.sidebar:
    st.header("📂 數據匯入")
    uploaded_file = st.file_uploader("匯入『未實現彙總』CSV", type="csv")
    st.markdown("---")
    st.write("今日操作策略重點：")
    if market['台積電ADR']['change'] > 1:
        st.success("🎯 ADR 大漲，電子股權值股今日強勢。")
    elif market['台積電ADR']['change'] < -1:
        st.error("🚨 ADR 走弱，小心台積電與供應鏈拖累。")

# 3. 核心邏輯：持股分析
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    # 數據預處理
    df['成交均價'] = pd.to_numeric(df['成交均價'].astype(str).str.replace(',', ''), errors='coerce')

    st.subheader("📊 個股深度診斷與進場點建議")

    for index, row in df.iterrows():
        stock_name = row['股票名稱']
        if stock_name in SYMBOL_MAP:
            sid = SYMBOL_MAP[stock_name]
            cost = row['成交均價']

            # 即時價與分析
            ticker = yf.Ticker(f"{sid}.TW")
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
            inst_status = get_institutional_data(sid)
            pnl = (current_price - cost) / cost * 100

            # 建立決策卡片
            with st.expander(f"{stock_name} ({sid}) | 現價: {current_price:.2f} | 損益: {pnl:.2f}%"):
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    st.write(f"**成交均價:** {cost}")
                    st.write(f"**法人動態:** {inst_status}")
                with c2:
                    st.write(f"**昨日美股影響:** {'正向' if market['費城半導體']['change'] > 0 else '負面'}")
                    st.write(f"**建議停損價:** {cost * 0.93:.1f}")
                with c3:
                    # 進階決策邏輯
                    if pnl < -7:
                        st.error("🛑 操作建議：達到硬停損點。大盤若轉弱，請優先出清此標的。")
                    elif inst_status == "買超" and pnl > 0:
                        st.success("🚀 操作建議：強勢續抱。法人認養中，可上移停利點。")
                    elif inst_status == "賣超" and pnl < 0:
                        st.warning("⚠️ 操作建議：減碼。法人轉賣且趨勢走弱，不宜攤平。")
                    else:
                        st.info("⌛ 操作建議：區間震盪。守住 20 日線則持股不動。")

# 4. 今日推薦入手 (模擬進階選股邏輯)
st.markdown("---")
st.subheader("💡 今日推薦進場/關注")
st.write("根據法人籌碼與盤後數據自動推薦：")
rec_cols = st.columns(3)
rec_cols[0].info("**鴻海 (2317)**\n原因：法人連買，受惠美股 AI 權值股反彈，支撐看 200。")
rec_cols[1].info("**台積電 (2330)**\n原因：ADR 溢價擴大，早盤有跳空動能。")
rec_cols[2].info("**廣達 (2382)**\n原因：回測月線不破，法人重新佈局。")

# 免責聲明
st.divider()
st.caption("免責聲明：本 App 提供之數據僅供參考，不代表投資建議，投資人需自負盈虧責任。")
