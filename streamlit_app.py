import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import numpy as np

# --- 頁面配置 ---
st.set_page_config(page_title="台股操盤決策系統 Pro", layout="wide", page_icon="📈")

# --- 股票代號對照表（可手動新增）---
SYMBOL_MAP = {
    "主動統一升級50": "00936", "元大高股息": "0056", "國泰永續高股息": "00878",
    "群益台灣精選高息": "00919", "光寶科": "2301", "台達電": "2308",
    "鴻海": "2317", "台積電": "2330", "金像電": "2368", "廣達": "2382",
    "奇鋐": "3017", "欣興": "3037", "緯創": "3231", "群創": "3481", "緯穎": "6669",
    "聯發科": "2454", "日月光": "3711", "聯電": "2303", "南亞科": "2408",
    "華碩": "2357", "宏碁": "2353", "研華": "2395", "信驊": "5274",
    "緯穎": "6669", "英業達": "2356", "仁寶": "2324", "和碩": "4938"
}

# =============================================
# 數據獲取函式
# =============================================

@st.cache_data(ttl=1800)
def get_market_data():
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
        except Exception:
            market_res[name] = {"price": 0.0, "change": 0.0}
    return market_res

@st.cache_data(ttl=1800)
def get_stock_history(sid, period="3mo"):
    """取得個股歷史數據並計算技術指標"""
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period=period)
        if df.empty:
            return None

        # --- 技術指標計算 ---
        # 均線
        df['MA5']  = df['Close'].rolling(5).mean()
        df['MA10'] = df['Close'].rolling(10).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()

        # RSI (14日)
        delta = df['Close'].diff()
        gain  = delta.clip(lower=0)
        loss  = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD']        = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist']   = df['MACD'] - df['MACD_Signal']

        # KD (隨機指標, 9日)
        low9  = df['Low'].rolling(9).min()
        high9 = df['High'].rolling(9).max()
        rsv   = (df['Close'] - low9) / (high9 - low9 + 1e-9) * 100
        df['K'] = rsv.ewm(com=2, adjust=False).mean()
        df['D'] = df['K'].ewm(com=2, adjust=False).mean()

        # 布林通道 (20日, 2倍標準差)
        df['BB_Mid']   = df['Close'].rolling(20).mean()
        df['BB_Std']   = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
        df['BB_Lower'] = df['BB_Mid'] - 2 * df['BB_Std']

        # 成交量均線
        df['Vol_MA5'] = df['Volume'].rolling(5).mean()

        return df
    except Exception:
        return None

@st.cache_data(ttl=1800)
def get_institutional_data(stock_id):
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=14)).strftime('%Y-%m-%d')
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
                    df['buy']  = pd.to_numeric(df['buy'],  errors='coerce').fillna(0)
                    df['sell'] = pd.to_numeric(df['sell'], errors='coerce').fillna(0)
                    recent = df.tail(9)
                    net   = recent['buy'].sum() - recent['sell'].sum()
                    by_type = df.groupby('name').apply(lambda x: x['buy'].sum() - x['sell'].sum())
                    return {
                        "status": "買超" if net > 0 else "賣超",
                        "net": int(net),
                        "by_type": by_type.to_dict()
                    }
    except Exception:
        pass
    return {"status": "無數據", "net": 0, "by_type": {}}

# =============================================
# 技術面綜合評分
# =============================================
def compute_signal_score(df, cost):
    """回傳 (score -5~+5, signals dict)"""
    if df is None or len(df) < 20:
        return 0, {}

    latest  = df.iloc[-1]
    prev    = df.iloc[-2]
    signals = {}
    score   = 0

    # 1. 均線多空排列
    ma5, ma20, ma60 = latest.get('MA5'), latest.get('MA20'), latest.get('MA60')
    close = latest['Close']
    if pd.notna(ma5) and pd.notna(ma20):
        if close > ma20:
            signals['均線'] = ('✅ 站上20MA，短線偏多', 1)
            score += 1
        else:
            signals['均線'] = ('❌ 跌破20MA，短線偏空', -1)
            score -= 1

    # 2. RSI
    rsi = latest.get('RSI')
    if pd.notna(rsi):
        if rsi < 30:
            signals['RSI'] = (f'🟢 RSI={rsi:.1f} 超賣區，反彈機率高', 2)
            score += 2
        elif rsi > 70:
            signals['RSI'] = (f'🔴 RSI={rsi:.1f} 超買區，留意回檔', -1)
            score -= 1
        elif 40 <= rsi <= 60:
            signals['RSI'] = (f'🟡 RSI={rsi:.1f} 中性區間', 0)

    # 3. MACD 黃金/死亡交叉
    macd_h     = latest.get('MACD_Hist')
    macd_h_pre = prev.get('MACD_Hist')
    if pd.notna(macd_h) and pd.notna(macd_h_pre):
        if macd_h > 0 and macd_h_pre <= 0:
            signals['MACD'] = ('🟢 MACD 黃金交叉，動能翻多', 2)
            score += 2
        elif macd_h < 0 and macd_h_pre >= 0:
            signals['MACD'] = ('🔴 MACD 死亡交叉，動能翻空', -2)
            score -= 2
        elif macd_h > 0:
            signals['MACD'] = ('✅ MACD 紅柱擴張，多方佔優', 1)
            score += 1
        else:
            signals['MACD'] = ('❌ MACD 綠柱擴張，空方佔優', -1)
            score -= 1

    # 4. KD 交叉
    k, d = latest.get('K'), latest.get('D')
    k_pre, d_pre = prev.get('K'), prev.get('D')
    if pd.notna(k) and pd.notna(d):
        if k > d and k_pre <= d_pre and k < 80:
            signals['KD'] = (f'🟢 KD 黃金交叉 (K={k:.1f})', 1)
            score += 1
        elif k < d and k_pre >= d_pre and k > 20:
            signals['KD'] = (f'🔴 KD 死亡交叉 (K={k:.1f})', -1)
            score -= 1
        elif k < 20:
            signals['KD'] = (f'🟢 KD 超賣區 K={k:.1f}，注意反彈', 1)
            score += 1
        elif k > 80:
            signals['KD'] = (f'🔴 KD 超買區 K={k:.1f}，留意賣壓', -1)
            score -= 1

    # 5. 布林通道
    bbu = latest.get('BB_Upper')
    bbl = latest.get('BB_Lower')
    if pd.notna(bbu) and pd.notna(bbl):
        bb_pct = (close - bbl) / (bbu - bbl) * 100 if (bbu - bbl) > 0 else 50
        if close < bbl:
            signals['布林'] = (f'🟢 跌破布林下軌 ({close:.1f}<{bbl:.1f})，超跌反彈區', 1)
            score += 1
        elif close > bbu:
            signals['布林'] = (f'🔴 突破布林上軌 ({close:.1f}>{bbu:.1f})，短線過熱', -1)
            score -= 1
        else:
            signals['布林'] = (f'🟡 布林帶內 {bb_pct:.0f}% 位置', 0)

    # 6. 量能
    vol    = latest.get('Volume')
    vol_ma = latest.get('Vol_MA5')
    if pd.notna(vol) and pd.notna(vol_ma) and vol_ma > 0:
        vol_ratio = vol / vol_ma
        if vol_ratio > 1.5 and close > prev['Close']:
            signals['量能'] = (f'🟢 價漲量增 ({vol_ratio:.1f}x均量)，主力進場訊號', 1)
            score += 1
        elif vol_ratio > 1.5 and close < prev['Close']:
            signals['量能'] = (f'🔴 價跌量增 ({vol_ratio:.1f}x均量)，賣壓沉重', -1)
            score -= 1
        else:
            signals['量能'] = (f'🟡 量能正常 ({vol_ratio:.1f}x均量)', 0)

    return max(-5, min(5, score)), signals

def score_to_action(score, pnl, inst_status):
    """根據綜合評分產生操作建議"""
    net_status = inst_status.get('status', '無數據')

    if pnl < -7:
        return "🛑 硬停損：損益已達 -7%，無論技術面，請優先出清保護本金。", "error"

    if score >= 3 and net_status == "買超":
        return "🚀 強力做多：技術面強勢 + 法人買超，可加碼或續抱，停利點上移至成本 +15%。", "success"
    elif score >= 2:
        return "✅ 偏多續抱：技術面偏多，續抱為主，停損守成本 -7%。", "success"
    elif score <= -3 and net_status == "賣超":
        return "🚨 強力出清：技術面轉弱 + 法人賣超雙重確認，建議立即減碼或出清。", "error"
    elif score <= -2:
        return "⚠️ 減碼觀望：技術面偏空，建議減碼至半倉，等待訊號好轉再加回。", "warning"
    elif pnl > 10 and score < 0:
        return "💰 獲利了結：已有不錯獲利且技術面轉弱，建議先出一半鎖利。", "warning"
    else:
        return "⌛ 區間持有：訊號中性，守住20日均線，無明顯操作需求。", "info"

# =============================================
# UI 介面
# =============================================

# --- 頂部大盤看板 ---
st.title("📈 台股操盤決策系統 Pro")
st.caption(f"更新時間：{datetime.datetime.now().strftime('%Y/%m/%d %H:%M')} ｜ 整合技術指標 + 法人籌碼 + 大盤連動")

market = get_market_data()
if market:
    cols = st.columns(len(market))
    for i, (name, val) in enumerate(market.items()):
        color = "normal" if val['change'] == 0 else ("normal" if val['change'] > 0 else "inverse")
        cols[i].metric(name, f"{val['price']:.2f}", f"{val['change']:+.2f}%", delta_color=color)

st.divider()

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 操作設定")
    uploaded_file = st.file_uploader("📂 匯入『未實現彙總』CSV", type="csv")

    st.markdown("---")
    st.subheader("🔍 單股查詢")
    manual_name = st.text_input("輸入股票名稱（需在對照表內）", placeholder="例：台積電")
    manual_cost = st.number_input("持有成本價", min_value=0.0, value=0.0, step=0.5)

    st.markdown("---")
    st.subheader("🌐 大盤氛圍")
    tsm_chg = market.get('台積電ADR', {}).get('change', 0)
    sox_chg = market.get('費城半導體', {}).get('change', 0)
    if tsm_chg > 1 and sox_chg > 1:
        st.success("🔥 ADR + 費半同步大漲，今日電子股偏強。")
    elif tsm_chg > 1:
        st.success("🎯 台積電ADR強勢，今早可關注台積電族群。")
    elif tsm_chg < -1 and sox_chg < -1:
        st.error("🚨 ADR + 費半同步重挫，今日電子股偏弱，謹慎操作。")
    elif tsm_chg < -1:
        st.warning("⚠️ 台積電ADR走弱，供應鏈留意賣壓。")
    else:
        st.info("📊 大盤 ADR 平盤，今日以個股表現為主。")

    st.markdown("---")
    st.caption("免責聲明：本系統僅供輔助參考，投資人需自負盈虧責任。")

# =============================================
# 個股分析核心
# =============================================
def render_stock_analysis(stock_name, sid, cost):
    """渲染單一個股的完整分析卡片"""
    st.markdown(f"### 🔎 {stock_name}（{sid}）")

    with st.spinner(f"正在抓取 {stock_name} 數據..."):
        df_hist = get_stock_history(sid)
        inst    = get_institutional_data(sid)

    if df_hist is None or df_hist.empty:
        st.error(f"{stock_name}：無法取得歷史數據。")
        return

    latest        = df_hist.iloc[-1]
    current_price = float(latest['Close'])
    pnl           = (current_price - cost) / cost * 100 if cost > 0 else 0
    score, signals = compute_signal_score(df_hist, cost)
    action_msg, action_type = score_to_action(score, pnl, inst)

    # --- 評分長條視覺化 ---
    score_bar = ""
    for i in range(-5, 6):
        if i == 0:
            score_bar += "｜"
        elif i <= score and score > 0:
            score_bar += "🟩"
        elif i >= score and score < 0:
            score_bar += "🟥"
        else:
            score_bar += "⬜"

    # --- 主要數據列 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("現價", f"{current_price:.2f}")
    col2.metric("持有損益", f"{pnl:+.2f}%", delta=f"{current_price - cost:+.2f}" if cost > 0 else "")
    col3.metric("技術評分", f"{score:+d} / 5", delta="偏多" if score > 0 else ("偏空" if score < 0 else "中性"))
    col4.metric("法人動態", inst['status'], delta=f"淨{inst['net']:+,}股" if inst['net'] != 0 else "")

    st.markdown(f"**評分進度條：** 空 {score_bar} 多")

    # --- 操作建議 ---
    if action_type == "success":
        st.success(action_msg)
    elif action_type == "error":
        st.error(action_msg)
    elif action_type == "warning":
        st.warning(action_msg)
    else:
        st.info(action_msg)

    # --- 停損停利價格表 ---
    if cost > 0:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("硬停損 -7%",  f"{cost * 0.93:.1f}", delta=f"{cost * 0.93 - current_price:+.1f}", delta_color="inverse")
        c2.metric("軟停損 -5%",  f"{cost * 0.95:.1f}", delta=f"{cost * 0.95 - current_price:+.1f}", delta_color="inverse")
        c3.metric("停利1 +10%", f"{cost * 1.10:.1f}", delta=f"{cost * 1.10 - current_price:+.1f}")
        c4.metric("停利2 +15%", f"{cost * 1.15:.1f}", delta=f"{cost * 1.15 - current_price:+.1f}")

    # --- 技術指標明細 ---
    with st.expander("📐 技術指標明細"):
        if signals:
            for indicator, (msg, _) in signals.items():
                st.write(f"**{indicator}：** {msg}")
        else:
            st.write("數據不足，無法計算指標。")

        l = df_hist.iloc[-1]
        tbl = {
            "指標": ["RSI(14)", "K值", "D值", "MACD柱", "20MA", "60MA", "布林上軌", "布林下軌"],
            "數值": [
                f"{l.get('RSI', float('nan')):.1f}" if pd.notna(l.get('RSI')) else "N/A",
                f"{l.get('K', float('nan')):.1f}"   if pd.notna(l.get('K'))   else "N/A",
                f"{l.get('D', float('nan')):.1f}"   if pd.notna(l.get('D'))   else "N/A",
                f"{l.get('MACD_Hist', float('nan')):.3f}" if pd.notna(l.get('MACD_Hist')) else "N/A",
                f"{l.get('MA20', float('nan')):.1f}" if pd.notna(l.get('MA20')) else "N/A",
                f"{l.get('MA60', float('nan')):.1f}" if pd.notna(l.get('MA60')) else "N/A",
                f"{l.get('BB_Upper', float('nan')):.1f}" if pd.notna(l.get('BB_Upper')) else "N/A",
                f"{l.get('BB_Lower', float('nan')):.1f}" if pd.notna(l.get('BB_Lower')) else "N/A",
            ]
        }
        st.table(pd.DataFrame(tbl))

    # --- 法人籌碼明細 ---
    with st.expander("🏦 法人籌碼明細"):
        if inst['by_type']:
            for name_t, net_val in inst['by_type'].items():
                icon = "🟢" if net_val > 0 else "🔴"
                st.write(f"{icon} **{name_t}**：淨{int(net_val):+,} 股")
        else:
            st.write("無法取得法人資料（FinMind API 限制）。")

    st.divider()

# =============================================
# 執行分析
# =============================================

# 1. CSV 持股批次分析
if uploaded_file:
    try:
        df_csv = pd.read_csv(uploaded_file)
        df_csv.columns = df_csv.columns.str.strip()

        if '成交均價' in df_csv.columns and '股票名稱' in df_csv.columns:
            df_csv['成交均價'] = pd.to_numeric(
                df_csv['成交均價'].astype(str).str.replace(',', ''), errors='coerce'
            )
            st.subheader("📋 持股批次分析")

            matched = False
            for _, row in df_csv.iterrows():
                sname = str(row.get('股票名稱', '')).strip()
                if sname in SYMBOL_MAP:
                    matched = True
                    render_stock_analysis(sname, SYMBOL_MAP[sname], float(row['成交均價']))

            if not matched:
                st.warning("CSV 中的股票名稱皆不在對照表內。請確認欄位名稱為『股票名稱』，或在側邊欄使用單股查詢。")
        else:
            st.error("CSV 格式錯誤，需包含『股票名稱』與『成交均價』欄位。")
    except Exception as e:
        st.error(f"讀取 CSV 時發生錯誤：{e}")

# 2. 單股查詢
if manual_name and manual_name in SYMBOL_MAP:
    st.subheader(f"🔍 單股查詢：{manual_name}")
    render_stock_analysis(manual_name, SYMBOL_MAP[manual_name], manual_cost)
elif manual_name and manual_name not in SYMBOL_MAP:
    st.sidebar.warning(f"『{manual_name}』不在對照表中，請確認名稱。")

# 若都沒輸入，顯示使用說明
if not uploaded_file and not manual_name:
    st.info("👈 請在左側側邊欄：\n1. 上傳『未實現彙總』CSV 進行批次分析，或\n2. 輸入單一股票名稱進行即時查詢。")
    st.markdown("""
    ### 🧭 系統功能說明
    | 功能 | 說明 |
    |------|------|
    | **大盤看板** | 即時費半、納指、台積電ADR、台指漲跌幅 |
    | **技術評分** | RSI + MACD + KD + 布林通道 + 均線 + 量能，-5到+5分 |
    | **停損停利** | 自動計算 -5% / -7% 停損，+10% / +15% 停利價格 |
    | **法人籌碼** | 外資、投信、自營商三大法人近兩週買賣超 |
    | **操作建議** | 綜合所有維度自動產生：強做多 / 做多 / 觀望 / 減碼 / 出清 |
    """)
