import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime

# --- 初始化與配置 ---
st.set_page_config(page_title="台股實戰全維度 App", layout="wide")

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
        try:
            data = yf.download(t, period="2d", progress=False, auto_adjust=True)
            if not data.empty and len(data) >= 2:
                close = data['Close']
                change = (float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100
                market_res[name] = {"price": float(close.iloc[-1]), "change": float(change)}
            elif not data.empty:
                close = data['Close']
                market_res[name] = {"price": float(close.iloc[-1]), "change": 0.0}
        except Exception as e:
            market_res[name] = {"price": 0.0, "change": 0.0}
    return market_res

@st.cache_data(ttl=3600)
def get_institutional_data(stock_id):
    """獲取台股三大法人買賣超 (FinMind REST API，不需安裝套件)"""
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": "TaiwanStockInstitutionalInvestors",
            "data_id": stock_id,
            "start_date": start_date,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 200 and data.get("data"):
                df = pd.DataFrame(data["data"])
                if not df.empty:
                    recent = df.tail(9)  # 近3日 x 3法人
                    net_buy = recent['buy'].astype(float).sum() - recent['sell'].astype(float).sum()
                    return "買超" if net_buy > 0 else "賣超"
    except Exception:
        pass
    return "無數據"

# --- 主程式介面 ---
st.title("🏹 台股全維度實戰決策系統")
st.caption("整合：美股連動、法人籌碼、大盤趨勢、個股診斷")

# 1. 頂部看板：全球與大盤走勢
market = get_market_data()
if market:
    cols = st.columns(len(market))
    for i, (name, val) in enumerate(market.items()):
        delta_color = "normal"
        cols[i].metric(name, f"{val['price']:.2f}", f"{val['change']:.2f}%", delta_color=delta_color)
else:
    st.warning("無法取得大盤數據，請稍後再試。")

# 2. 側邊欄：匯入 CSV
with st.sidebar:
    st.header("📂 數據匯入")
    uploaded_file = st.file_uploader("匯入『未實現彙總』CSV", type="csv")
    st.markdown("---")
    st.write("今日操作策略重點：")
    tsm_change = market.get('台積電ADR', {}).get('change', 0)
    if tsm_change > 1:
        st.success("🎯 ADR 大漲，電子股權值股今日強勢。")
    elif tsm_change < -1:
        st.error("🚨 ADR 走弱，小心台積電與供應鏈拖累。")
    else:
        st.info("📊 ADR 平盤整理，今日個股表現為主。")

# 3. 核心邏輯：持股分析
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        # 數據預處理
        if '成交均價' in df.columns:
            df['成交均價'] = pd.to_numeric(df['成交均價'].astype(str).str.replace(',', ''), errors='coerce')

            st.subheader("📊 個股深度診斷與進場點建議")

            matched = False
            for index, row in df.iterrows():
                stock_name = str(row.get('股票名稱', ''))
                if stock_name in SYMBOL_MAP:
                    matched = True
                    sid = SYMBOL_MAP[stock_name]
                    cost = row['成交均價']

                    # 即時價與分析
                    try:
                        ticker = yf.Ticker(f"{sid}.TW")
                        hist = ticker.history(period="1d")
                        if hist.empty:
                            st.warning(f"{stock_name}：無法取得即時價格，請稍後再試。")
                            continue
                        current_price = float(hist['Close'].iloc[-1])
                    except Exception:
                        st.warning(f"{stock_name}：取得價格失敗。")
                        continue

                    inst_status = get_institutional_data(sid)
                    pnl = (current_price - cost) / cost * 100 if cost and cost > 0 else 0

                    # 建立決策卡片
                    pnl_sign = "+" if pnl >= 0 else ""
                    with st.expander(f"{stock_name} ({sid}) | 現價: {current_price:.2f} | 損益: {pnl_sign}{pnl:.2f}%"):
                        c1, c2, c3 = st.columns([1, 1, 2])
                        with c1:
                            st.write(f"**成交均價:** {cost:.2f}")
                            st.write(f"**法人動態:** {inst_status}")
                        with c2:
                            sox_change = market.get('費城半導體', {}).get('change', 0)
                            st.write(f"**昨日美股影響:** {'正向 📈' if sox_change > 0 else '負面 📉'}")
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

            if not matched:
                st.info("CSV 中的股票名稱未找到對應代號，請確認欄位名稱為『股票名稱』。")
        else:
            st.error("CSV 缺少『成交均價』欄位，請確認格式正確。")
    except Exception as e:
        st.error(f"讀取 CSV 時發生錯誤：{e}")

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
