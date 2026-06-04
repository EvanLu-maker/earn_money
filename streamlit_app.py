import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import numpy as np

# =============================================
# 頁面配置 & 自訂 CSS
# =============================================
st.set_page_config(
    page_title="台股操盤 Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background: #0d1117; }
.hero-box {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid #30363d; border-radius: 16px;
    padding: 24px 32px; margin-bottom: 20px;
}
.hero-title { font-size: 2rem; font-weight: 800; color: #e6edf3; margin: 0; letter-spacing: -0.5px; }
.hero-sub { color: #8b949e; font-size: 0.85rem; margin-top: 4px; }
div[data-testid="metric-container"] {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 16px 20px; transition: border-color 0.2s;
}
div[data-testid="metric-container"]:hover { border-color: #58a6ff; }
div[data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.5px; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
.stock-card { background: #161b22; border: 1px solid #30363d; border-radius: 14px; padding: 20px 24px; margin-bottom: 16px; }
.stock-card-title { font-size: 1.15rem; font-weight: 700; color: #e6edf3; margin-bottom: 4px; }
.stock-tag { display: inline-block; background: #21262d; color: #8b949e; border-radius: 6px; padding: 2px 8px; font-size: 0.75rem; margin-left: 6px; }
.score-bar-wrap { background: #21262d; border-radius: 8px; padding: 10px 14px; margin: 10px 0; font-family: monospace; font-size: 1rem; letter-spacing: 2px; }
.badge-buy  { background:#1a4731; color:#3fb950; border:1px solid #238636; border-radius:8px; padding:10px 14px; font-weight:600; }
.badge-sell { background:#3d1a1a; color:#f85149; border:1px solid #da3633; border-radius:8px; padding:10px 14px; font-weight:600; }
.badge-warn { background:#3d2e00; color:#e3b341; border:1px solid #9e6a03; border-radius:8px; padding:10px 14px; font-weight:600; }
.badge-hold { background:#1c2128; color:#8b949e; border:1px solid #30363d; border-radius:8px; padding:10px 14px; font-weight:600; }
.price-grid { display:flex; gap:10px; flex-wrap:wrap; margin:12px 0; }
.price-box { flex:1; min-width:120px; background:#21262d; border-radius:10px; padding:10px 14px; text-align:center; }
.price-box .label { font-size:0.7rem; color:#8b949e; text-transform:uppercase; letter-spacing:0.5px; }
.price-box .value { font-size:1.15rem; font-weight:700; color:#e6edf3; margin-top:2px; }
.price-box .diff  { font-size:0.75rem; margin-top:2px; }
section[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #21262d; }
section[data-testid="stSidebar"] .stMarkdown h3 { color: #58a6ff; }
.market-card { background: #161b22; border-radius: 10px; padding: 12px 14px; border-left: 3px solid #58a6ff; font-size: 0.85rem; color: #c9d1d9; }
.pwa-hint { background: linear-gradient(90deg, #1a1f2e, #16213e); border: 1px solid #1f6feb; border-radius: 10px; padding: 12px 16px; color: #79c0ff; font-size: 0.83rem; margin-top: 16px; }
.block-container { padding-top: 1.5rem !important; }
hr { border-color: #21262d !important; margin: 20px 0 !important; }
details { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 10px !important; padding: 4px !important; }
.action-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; }
.action-urgent { border-left: 4px solid #f85149; }
.action-watch  { border-left: 4px solid #e3b341; }
.action-hold   { border-left: 4px solid #3fb950; }
.action-pick   { border-left: 4px solid #58a6ff; }
</style>
""", unsafe_allow_html=True)
# =============================================
# 股票代號對照表
# =============================================
SYMBOL_MAP = {
    "主動統一升級50": "00936", "元大高股息": "0056", "國泰永續高股息": "00878",
    "群益台灣精選高息": "00919", "光寶科": "2301", "台達電": "2308",
    "鴻海": "2317", "台積電": "2330", "金像電": "2368", "廣達": "2382",
    "奇鋐": "3017", "欣興": "3037", "緯創": "3231", "群創": "3481", "緯穎": "6669",
    "聯發科": "2454", "日月光": "3711", "聯電": "2303", "南亞科": "2408",
    "華碩": "2357", "宏碁": "2353", "研華": "2395", "信驊": "5274",
    "英業達": "2356", "仁寶": "2324", "和碩": "4938"
}

# =============================================
# 數據函式
# =============================================
@st.cache_data(ttl=1800)
def get_market_data():
    tickers = {"費城半導體": "^SOX", "納斯達克": "^IXIC", "台積電ADR": "TSM", "台指現貨": "^TWII"}
    res = {}
    for name, t in tickers.items():
        try:
            data = yf.download(t, period="5d", progress=False, auto_adjust=True)
            if not data.empty:
                close = data["Close"]
                if hasattr(close, "columns"):
                    close = close.squeeze()
                close = close.dropna()
                if len(close) >= 2:
                    chg = (float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100
                    res[name] = {"price": float(close.iloc[-1]), "change": float(chg)}
                elif len(close) == 1:
                    res[name] = {"price": float(close.iloc[-1]), "change": 0.0}
                else:
                    res[name] = {"price": 0.0, "change": 0.0}
            else:
                res[name] = {"price": 0.0, "change": 0.0}
        except Exception:
            res[name] = {"price": 0.0, "change": 0.0}
    return res

@st.cache_data(ttl=1800)
def get_stock_history(sid, period="3mo"):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period=period)
        if df.empty:
            return None
        df["MA5"]  = df["Close"].rolling(5).mean()
        df["MA10"] = df["Close"].rolling(10).mean()
        df["MA20"] = df["Close"].rolling(20).mean()
        df["MA60"] = df["Close"].rolling(60).mean()
        delta = df["Close"].diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean().replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"]        = ema12 - ema26
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]
        low9  = df["Low"].rolling(9).min()
        high9 = df["High"].rolling(9).max()
        rsv   = (df["Close"] - low9) / (high9 - low9 + 1e-9) * 100
        df["K"] = rsv.ewm(com=2, adjust=False).mean()
        df["D"] = df["K"].ewm(com=2, adjust=False).mean()
        df["BB_MA"]    = df["Close"].rolling(20).mean()
        df["BB_Std"]   = df["Close"].rolling(20).std()
        df["BB_Upper"] = df["BB_MA"] + 2 * df["BB_Std"]
        df["BB_Lower"] = df["BB_MA"] - 2 * df["BB_Std"]
        df["Vol_MA5"]  = df["Volume"].rolling(5).mean()
        return df
    except Exception:
        return None

@st.cache_data(ttl=1800)
def get_institutional_data(stock_id):
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        resp = requests.get("https://api.finmindtrade.com/api/v4/data", params={
            "dataset": "TaiwanStockInstitutionalInvestors",
            "data_id": stock_id,
            "start_date": start_date,
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 200 and data.get("data"):
                df = pd.DataFrame(data["data"])
                df["buy"]  = pd.to_numeric(df["buy"],  errors="coerce").fillna(0)
                df["sell"] = pd.to_numeric(df["sell"], errors="coerce").fillna(0)
                recent = df.tail(9)
                net = recent["buy"].sum() - recent["sell"].sum()
                by_type = df.groupby("name").apply(
                    lambda x: x["buy"].sum() - x["sell"].sum()
                ).to_dict()
                return {"status": "買超" if net > 0 else "賣超", "net": int(net), "by_type": by_type}
    except Exception:
        pass
    return {"status": "無數據", "net": 0, "by_type": {}}
def compute_signal_score(df, cost):
    if df is None or len(df) < 20:
        return 0, {}
    latest, prev = df.iloc[-1], df.iloc[-2]
    signals, score = {}, 0
    close = float(latest["Close"])
    ma20 = latest.get("MA20")
    if pd.notna(ma20):
        if close > float(ma20):
            signals["均線"] = (f"🟢 收在20MA({float(ma20):.1f})上方", +1); score += 1
        else:
            signals["均線"] = (f"🔴 跌破20MA({float(ma20):.1f})", -1); score -= 1
    rsi = latest.get("RSI")
    if pd.notna(rsi):
        rsi = float(rsi)
        if rsi < 30:
            signals["RSI"] = (f"🟢 RSI {rsi:.0f} — 超賣反彈機會", +1); score += 1
        elif rsi > 70:
            signals["RSI"] = (f"🔴 RSI {rsi:.0f} — 超買注意", -1); score -= 1
        else:
            signals["RSI"] = (f"🟡 RSI {rsi:.0f} — 中性", 0)
    mh  = latest.get("MACD_Hist")
    mhp = prev.get("MACD_Hist")
    if pd.notna(mh) and pd.notna(mhp):
        mh, mhp = float(mh), float(mhp)
        if mh > 0 and mhp <= 0:
            signals["MACD"] = ("🟢 MACD柱翻正，多頭啟動", +1); score += 1
        elif mh < 0 and mhp >= 0:
            signals["MACD"] = ("🔴 MACD柱翻負，空頭啟動", -1); score -= 1
        elif mh > 0:
            signals["MACD"] = (f"🟢 MACD柱擴大 {mh:.3f}", +1); score += 1
        else:
            signals["MACD"] = (f"🔴 MACD柱收縮 {mh:.3f}", -1); score -= 1
    k  = latest.get("K"); d  = latest.get("D")
    kp = prev.get("K");   dp = prev.get("D")
    if pd.notna(k) and pd.notna(d):
        k, d, kp, dp = float(k), float(d), float(kp), float(dp)
        if k > d and kp <= dp and k < 80:
            signals["KD"] = (f"🟢 KD黃金交叉 K={k:.0f}", +1); score += 1
        elif k < d and kp >= dp and k > 20:
            signals["KD"] = (f"🔴 KD死亡交叉 K={k:.0f}", -1); score -= 1
        elif k < 20:
            signals["KD"] = (f"🟢 KD超賣區 K={k:.0f}", +1); score += 1
        elif k > 80:
            signals["KD"] = (f"🔴 KD超買區 K={k:.0f}", -1); score -= 1
    bbu = latest.get("BB_Upper"); bbl = latest.get("BB_Lower")
    if pd.notna(bbu) and pd.notna(bbl):
        bbu, bbl = float(bbu), float(bbl)
        if close < bbl:
            signals["布林"] = ("🟢 觸及布林下緣，超賣反彈", +1); score += 1
        elif close > bbu:
            signals["布林"] = ("🔴 突破布林上緣，超買警示", -1); score -= 1
        else:
            bb_pct = (close - bbl) / (bbu - bbl) * 100
            signals["布林"] = (f"🟡 布林帶內 {bb_pct:.0f}% 位置", 0)
    vol = latest.get("Volume"); vma = latest.get("Vol_MA5")
    if pd.notna(vol) and pd.notna(vma) and float(vma) > 0:
        vr = float(vol) / float(vma)
        prev_close = float(prev["Close"])
        if vr > 1.5 and close > prev_close:
            signals["量能"] = (f"🟢 放量上漲 {vr:.1f}x", +1); score += 1
        elif vr > 1.5 and close < prev_close:
            signals["量能"] = (f"🔴 放量下跌 {vr:.1f}x", -1); score -= 1
        else:
            signals["量能"] = (f"🟡 量能正常 {vr:.1f}x", 0)
    return max(-5, min(5, score)), signals

def score_to_action(score, pnl, inst):
    s = inst.get("status", "無數據")
    if pnl < -7:
        return "🛑 硬停損：-7% 已觸及，請立即出清保護本金", "sell"
    if score >= 3 and s == "買超":
        return "🚀 強力做多：技術+法人雙重確認，可加碼，停利上移至+15%", "buy"
    elif score >= 2:
        return "✅ 偏多續抱：技術面健康，持有，停損守-7%", "buy"
    elif score <= -3 and s == "賣超":
        return "🚨 強力出清：技術+法人雙殺，建議出清", "sell"
    elif score <= -2:
        return "⚠️ 減碼觀望：技術偏空，減碼至半倉等待訊號", "warn"
    elif pnl > 10 and score < 0:
        return "💰 部分獲利了結：有獲利且技術轉弱，先出一半鎖利", "warn"
    else:
        return "⌛ 區間持有：訊號中性，守住20MA，靜待下一個訊號", "hold"

def render_score_bar(score):
    bar = ""
    for i in range(-5, 6):
        if i == 0: bar += "│"
        elif score > 0 and 0 < i <= score: bar += "🟩"
        elif score < 0 and score <= i < 0: bar += "🟥"
        else: bar += "⬜"
    return bar
# =============================================
# UI 主體
# =============================================
now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
st.markdown(f"""
<div class="hero-box">
  <div class="hero-title">📈 台股操盤決策系統 Pro</div>
  <div class="hero-sub">更新時間 {now_str}　｜　RSI · MACD · KD · 布林通道 · 法人籌碼 · 大盤連動</div>
</div>
""", unsafe_allow_html=True)

market = get_market_data()
if market:
    cols = st.columns(len(market))
    for i, (name, val) in enumerate(market.items()):
        chg = val["change"]
        clr = "normal" if chg >= 0 else "inverse"
        cols[i].metric(name, f"{val['price']:.2f}", f"{chg:+.2f}%", delta_color=clr)

st.divider()

with st.sidebar:
    st.markdown("### ⚙️ 操作設定")
    uploaded_file = st.file_uploader("📂 匯入未實現彙總 CSV", type="csv")
    st.markdown("---")
    st.markdown("### 🔍 單股即時查詢")
    manual_name = st.text_input("股票名稱", placeholder="例：台積電、鴻海")
    manual_cost = st.number_input("持有成本價", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    st.markdown("---")
    st.markdown("### 🌐 大盤氛圍")
    tsm_chg = market.get("台積電ADR", {}).get("change", 0)
    sox_chg = market.get("費城半導體", {}).get("change", 0)
    if tsm_chg > 1 and sox_chg > 1:
        st.markdown('<div class="market-card" style="border-color:#3fb950">🔥 ADR+費半同步大漲，今日電子股強勢</div>', unsafe_allow_html=True)
    elif tsm_chg < -1 and sox_chg < -1:
        st.markdown('<div class="market-card" style="border-color:#f85149">🚨 ADR+費半同步重挫，今日謹慎操作</div>', unsafe_allow_html=True)
    elif tsm_chg > 1:
        st.markdown('<div class="market-card" style="border-color:#3fb950">🎯 台積電ADR強勢，台積族群關注</div>', unsafe_allow_html=True)
    elif tsm_chg < -1:
        st.markdown('<div class="market-card" style="border-color:#e3b341">⚠️ 台積電ADR走弱，供應鏈留意賣壓</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-card">📊 大盤平盤整理，今日個股表現為主</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="pwa-hint">
    📱 <b>加到手機主畫面</b><br>
    iPhone：Safari → 分享 → 加入主畫面<br>
    Android：Chrome → 選單 → 加到主畫面
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.caption("⚠️ 本系統僅供輔助參考，投資人需自負盈虧責任")
# =============================================
# 個股渲染
# =============================================
def render_stock(sname, sid, cost):
    with st.spinner(f"載入 {sname} 數據中..."):
        df   = get_stock_history(sid)
        inst = get_institutional_data(sid)
    if df is None or df.empty:
        st.error(f"⚠️ {sname}：無法取得數據"); return
    latest = df.iloc[-1]
    price  = float(latest["Close"])
    pnl    = (price - cost) / cost * 100 if cost > 0 else 0
    score, signals = compute_signal_score(df, cost)
    action_msg, action_type = score_to_action(score, pnl, inst)
    pnl_color = "#3fb950" if pnl >= 0 else "#f85149"
    st.markdown(f"""
    <div class="stock-card">
      <div class="stock-card-title">
        {sname} <span class="stock-tag">{sid}.TW</span>
        <span style="float:right;color:{pnl_color};font-size:1rem;">
          {"▲" if pnl >= 0 else "▼"} {pnl:+.2f}%
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("現價",     f"{price:.2f}")
    m2.metric("持有損益", f"{pnl:+.2f}%", delta=f"{price-cost:+.2f}" if cost > 0 else "")
    m3.metric("技術評分", f"{score:+d} / 5", delta="偏多" if score > 0 else ("偏空" if score < 0 else "中性"))
    m4.metric("法人動態", inst["status"], delta=f"{inst['net']:+,}" if inst["net"] != 0 else "")
    bar = render_score_bar(score)
    st.markdown(f'<div class="score-bar-wrap">空 {bar} 多　｜　技術評分 <b>{score:+d}</b></div>', unsafe_allow_html=True)
    badge_map = {"buy": "badge-buy", "sell": "badge-sell", "warn": "badge-warn", "hold": "badge-hold"}
    st.markdown(f'<div class="{badge_map[action_type]}">{action_msg}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if cost > 0:
        sl5, sl7, tp10, tp15 = cost*0.95, cost*0.93, cost*1.10, cost*1.15
        sl5d  = price - sl5;  sl7d  = price - sl7
        tp10d = price - tp10; tp15d = price - tp15
        sl5c  = "#f85149" if price > sl5  else "#3fb950"
        sl7c  = "#f85149" if price > sl7  else "#3fb950"
        tp10c = "#3fb950" if price < tp10 else "#e3b341"
        tp15c = "#3fb950" if price < tp15 else "#e3b341"
        st.markdown(f"""
        <div class="price-grid">
          <div class="price-box"><div class="label">軟停損 -5%</div><div class="value">{sl5:.1f}</div><div class="diff" style="color:{sl5c}">{sl5d:+.1f}</div></div>
          <div class="price-box"><div class="label">硬停損 -7%</div><div class="value">{sl7:.1f}</div><div class="diff" style="color:{sl7c}">{sl7d:+.1f}</div></div>
          <div class="price-box"><div class="label">停利1 +10%</div><div class="value">{tp10:.1f}</div><div class="diff" style="color:{tp10c}">{tp10d:+.1f}</div></div>
          <div class="price-box"><div class="label">停利2 +15%</div><div class="value">{tp15:.1f}</div><div class="diff" style="color:{tp15c}">{tp15d:+.1f}</div></div>
        </div>
        """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("📐 技術指標明細"):
            for ind, (msg, _) in signals.items():
                st.write(f"**{ind}：** {msg}")
            l = df.iloc[-1]
            rows = [
                ("RSI(14)", f"{float(l['RSI']):.1f}"       if pd.notna(l.get("RSI"))       else "N/A"),
                ("K值",     f"{float(l['K']):.1f}"          if pd.notna(l.get("K"))          else "N/A"),
                ("D值",     f"{float(l['D']):.1f}"          if pd.notna(l.get("D"))          else "N/A"),
                ("MACD柱",  f"{float(l['MACD_Hist']):.3f}"  if pd.notna(l.get("MACD_Hist")) else "N/A"),
                ("20MA",    f"{float(l['MA20']):.1f}"       if pd.notna(l.get("MA20"))       else "N/A"),
                ("60MA",    f"{float(l['MA60']):.1f}"       if pd.notna(l.get("MA60"))       else "N/A"),
                ("布林上",  f"{float(l['BB_Upper']):.1f}"   if pd.notna(l.get("BB_Upper"))   else "N/A"),
                ("布林下",  f"{float(l['BB_Lower']):.1f}"   if pd.notna(l.get("BB_Lower"))   else "N/A"),
            ]
            st.table(pd.DataFrame(rows, columns=["指標", "數值"]))
    with c2:
        with st.expander("🏦 法人籌碼明細"):
            if inst["by_type"]:
                for nt, nv in inst["by_type"].items():
                    icon = "🟢" if nv > 0 else "🔴"
                    st.write(f"{icon} **{nt}**：{int(nv):+,} 股")
            else:
                st.caption("無法取得法人資料（API限制）")
    st.divider()
# =============================================
# 批次分析輔助
# =============================================
def collect_stock_summary(sname, sid, cost):
    df   = get_stock_history(sid)
    inst = get_institutional_data(sid)
    if df is None or df.empty:
        return None
    latest = df.iloc[-1]
    price  = float(latest["Close"])
    pnl    = (price - cost) / cost * 100 if cost > 0 else 0
    score, signals = compute_signal_score(df, cost)
    action_msg, action_type = score_to_action(score, pnl, inst)
    ma20 = latest.get("MA20"); rsi = latest.get("RSI")
    return {
        "name": sname, "sid": sid, "cost": cost,
        "price": price, "pnl": pnl,
        "score": score, "action_type": action_type, "action_msg": action_msg,
        "inst_status": inst["status"], "inst_net": inst["net"],
        "ma20": float(ma20) if pd.notna(ma20) else None,
        "rsi":  float(rsi)  if pd.notna(rsi)  else None,
        "signals": signals,
    }

@st.cache_data(ttl=3600)
def scan_recommended_picks():
    picks = []
    for sname, sid in SYMBOL_MAP.items():
        try:
            df   = get_stock_history(sid)
            inst = get_institutional_data(sid)
            if df is None or df.empty:
                continue
            latest = df.iloc[-1]
            price  = float(latest["Close"])
            score, signals = compute_signal_score(df, 0)
            if score < 2:
                continue
            df60 = df.tail(60)
            avg_daily_chg = df60["Close"].pct_change().mean() * 100
            if avg_daily_chg > 0.05:
                est_days  = int(10 / avg_daily_chg)
                est_weeks = max(1, round(est_days / 5))
                payback   = f"約 {est_days} 個交易日（{est_weeks} 週）"
            else:
                payback = "趨勢偏弱，不易估算"
            ma20 = latest.get("MA20")
            entry = float(ma20) if pd.notna(ma20) and float(ma20) < price else round(price * 0.99, 1)
            reasons = [msg.lstrip("🟢 ") for _, (msg, v) in signals.items() if v > 0]
            picks.append({
                "name": sname, "sid": sid, "price": price, "score": score,
                "inst": inst["status"], "entry": round(entry, 1),
                "payback": payback, "reasons": reasons,
            })
        except Exception:
            continue
    picks.sort(key=lambda x: (x["score"], 1 if x["inst"] == "買超" else 0), reverse=True)
    return picks[:8]
# =============================================
# 主程式執行
# =============================================
if uploaded_file:
    try:
        df_csv = pd.read_csv(uploaded_file)
        df_csv.columns = df_csv.columns.str.strip()
        if "成交均價" in df_csv.columns and "股票名稱" in df_csv.columns:
            df_csv["成交均價"] = pd.to_numeric(
                df_csv["成交均價"].astype(str).str.replace(",", ""), errors="coerce"
            )
            valid_rows = [
                (str(r.get("股票名稱", "")).strip(), r["成交均價"])
                for _, r in df_csv.iterrows()
                if str(r.get("股票名稱", "")).strip() in SYMBOL_MAP
            ]
            if not valid_rows:
                st.warning("CSV 中股票名稱不在對照表內，請用下方單股查詢。")
            else:
                summaries = []
                prog = st.progress(0, text="分析持股中...")
                for idx, (sn, cost_val) in enumerate(valid_rows):
                    s = collect_stock_summary(sn, SYMBOL_MAP[sn], float(cost_val))
                    if s:
                        summaries.append(s)
                    prog.progress((idx + 1) / len(valid_rows), text=f"分析 {sn}...")
                prog.empty()

                tab1, tab2, tab3, tab4 = st.tabs([
                    "🚨 今日該注意處理",
                    "👁 今日觀察",
                    "💎 今日續抱",
                    "🌟 今日推薦可入手標的",
                ])

                urgent  = [s for s in summaries if s["action_type"] in ("sell", "warn")]
                watch   = [s for s in summaries if s["action_type"] == "hold" and s["score"] < 0]
                hold_ok = [s for s in summaries if s["action_type"] in ("buy", "hold") and s["score"] >= 0]

                with tab1:
                    if not urgent:
                        st.success("✅ 今日無需緊急處理的持股，持股健康！")
                    for s in sorted(urgent, key=lambda x: x["pnl"]):
                        pnl_color = "#f85149" if s["pnl"] < 0 else "#e3b341"
                        st.markdown(f"""
                        <div class="action-card action-urgent">
                          <b>{s['name']}</b>
                          <span class="stock-tag">{s['sid']}.TW</span>
                          <span style="float:right;color:{pnl_color};font-weight:700">{s['pnl']:+.2f}%</span><br>
                          <span style="color:#8b949e;font-size:0.85rem">現價 {s['price']:.1f}　評分 {s['score']:+d}　法人 {s['inst_status']}</span><br>
                          <span style="color:#f85149;font-size:0.9rem;margin-top:6px;display:block">{s['action_msg']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        reasons_bad = [msg for _, (msg, v) in s["signals"].items() if v < 0]
                        if reasons_bad:
                            st.caption("⚠️ 弱勢訊號：" + "、".join(reasons_bad[:3]))

                with tab2:
                    if not watch:
                        st.info("📋 目前無需特別觀察的持股。")
                    for s in sorted(watch, key=lambda x: x["score"]):
                        st.markdown(f"""
                        <div class="action-card action-watch">
                          <b>{s['name']}</b>
                          <span class="stock-tag">{s['sid']}.TW</span>
                          <span style="float:right;color:#e3b341;font-weight:700">{s['pnl']:+.2f}%</span><br>
                          <span style="color:#8b949e;font-size:0.85rem">現價 {s['price']:.1f}　評分 {s['score']:+d}　法人 {s['inst_status']}</span><br>
                          <span style="color:#e3b341;font-size:0.9rem;margin-top:6px;display:block">{s['action_msg']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        mixed = [msg for _, (msg, v) in s["signals"].items() if v != 0]
                        if mixed:
                            st.caption("📍 " + "、".join(mixed[:3]))

                with tab3:
                    if not hold_ok:
                        st.info("目前無明確續抱訊號。")
                    for s in sorted(hold_ok, key=lambda x: -x["score"]):
                        st.markdown(f"""
                        <div class="action-card action-hold">
                          <b>{s['name']}</b>
                          <span class="stock-tag">{s['sid']}.TW</span>
                          <span style="float:right;color:#3fb950;font-weight:700">{s['pnl']:+.2f}%</span><br>
                          <span style="color:#8b949e;font-size:0.85rem">現價 {s['price']:.1f}　評分 {s['score']:+d}　法人 {s['inst_status']}</span><br>
                          <span style="color:#3fb950;font-size:0.9rem;margin-top:6px;display:block">{s['action_msg']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        good = [msg for _, (msg, v) in s["signals"].items() if v > 0]
                        if good:
                            st.caption("✅ 多頭訊號：" + "、".join(good[:3]))

                with tab4:
                    st.caption("掃描對照表所有股票，找出技術+籌碼最佳入場點")
                    with st.spinner("掃描推薦標的中..."):
                        picks = scan_recommended_picks()
                    if not picks:
                        st.info("今日暫無符合條件的推薦標的（評分 ≥2）")
                    for p in picks:
                        inst_badge = "🟢 法人買超" if p["inst"] == "買超" else ("🔴 法人賣超" if p["inst"] == "賣超" else "⚪ 法人無數據")
                        st.markdown(f"""
                        <div class="action-card action-pick">
                          <b>{p['name']}</b>
                          <span class="stock-tag">{p['sid']}.TW</span>
                          <span style="float:right;color:#58a6ff;font-weight:700">評分 {p['score']:+d}</span><br>
                          <span style="color:#8b949e;font-size:0.85rem">現價 {p['price']:.1f}　{inst_badge}</span><br>
                          <span style="color:#79c0ff;font-size:0.9rem;margin-top:6px;display:block">
                            📍 入手價：<b>{p['entry']}</b>　⏱ 約多久到+10%：{p['payback']}
                          </span>
                        </div>
                        """, unsafe_allow_html=True)
                        if p["reasons"]:
                            st.caption("📊 入手理由：" + "、".join(p["reasons"][:4]))
                        st.markdown("")

                st.divider()
                st.subheader("📋 完整持股明細")
                for s in summaries:
                    render_stock(s["name"], s["sid"], s["cost"])
        else:
            st.error("CSV 需包含『股票名稱』與『成交均價』欄位。")
    except Exception as e:
        st.error(f"CSV 讀取錯誤：{e}")

if manual_name:
    if manual_name in SYMBOL_MAP:
        st.subheader(f"🔍 {manual_name} 即時分析")
        render_stock(manual_name, SYMBOL_MAP[manual_name], float(manual_cost))
    else:
        st.sidebar.error(f"找不到『{manual_name}』，請確認名稱")

if not uploaded_file and not manual_name:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#8b949e;">
      <div style="font-size:3rem;">📊</div>
      <div style="font-size:1.1rem;margin-top:12px;">請在左側上傳 CSV 或輸入股票名稱開始分析</div>
    </div>
    """, unsafe_allow_html=True)

