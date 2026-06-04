import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import numpy as np

st.set_page_config(
    page_title="台股操盤 Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed"
)

# ── 隱藏 Streamlit 預設 UI 元素 ──
st.markdown("""
<style>
/* 隱藏頂部工具列、頁尾、右下角按鈕 */
#MainMenu { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }
.viewerBadge_container__1QSob { display: none !important; }
button[kind="header"] { display: none !important; }
[data-testid="collapsedControl"] { top: 8px !important; }

/* ── 全域 ── */
.stApp { background: #0d1117; }
.block-container { padding: 0.6rem 0.8rem 2rem !important; max-width: 100% !important; }

/* ── Hero ── */
.hero-box {
    background: linear-gradient(135deg,#1a1f2e,#0f3460);
    border:1px solid #30363d; border-radius:12px;
    padding:12px 16px; margin-bottom:10px;
}
.hero-title { font-size:1.3rem; font-weight:800; color:#e6edf3; margin:0; }
.hero-sub   { color:#8b949e; font-size:0.75rem; margin-top:2px; }

/* ── 大盤折疊 expander ── */
details summary { font-size:0.85rem !important; color:#8b949e !important; }
details[open] summary { color:#e6edf3 !important; }

/* ── Metric ── */
div[data-testid="metric-container"] {
    background:#161b22; border:1px solid #30363d;
    border-radius:8px; padding:8px 10px;
}
div[data-testid="metric-container"] label {
    color:#8b949e !important; font-size:0.7rem !important; font-weight:600 !important;
    text-transform:uppercase;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color:#e6edf3 !important; font-size:1.2rem !important; font-weight:700 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] svg { display:none; }

/* ── 主標籤 ── */
div[data-testid="stTabs"] > div:first-child button {
    font-size:1rem !important; font-weight:700 !important;
    padding:9px 18px !important;
}

/* ── 子標籤 ── */
div[data-testid="stTabs"] div[data-testid="stTabs"] > div:first-child button {
    font-size:0.85rem !important; font-weight:600 !important;
    padding:7px 12px !important;
}

/* ── 個股 expander ── */
div[data-testid="stExpander"] > details {
    background:#161b22 !important;
    border:1px solid #30363d !important;
    border-radius:10px !important;
    margin-bottom:6px !important;
}
div[data-testid="stExpander"] > details > summary {
    font-size:1rem !important; font-weight:600 !important;
    color:#e6edf3 !important; padding:12px 14px !important;
}

/* ── badge ── */
.badge {
    display:inline-block; border-radius:6px;
    padding:6px 12px; font-size:0.85rem; font-weight:600;
    margin:6px 0; width:100%; box-sizing:border-box;
}
.bg-sell  { background:#3d1a1a; color:#f85149; border:1px solid #da3633; }
.bg-flat  { background:#3d2e00; color:#e3b341; border:1px solid #9e6a03; }
.bg-hold  { background:#1a4731; color:#3fb950; border:1px solid #238636; }
.bg-watch { background:#1a2233; color:#79c0ff; border:1px solid #1f6feb; }

/* ── 停損停利格 ── */
.pgrid { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:6px; margin:8px 0; }
.pbox  { background:#21262d; border-radius:7px; padding:7px 8px; text-align:center; }
.pbox .pl { font-size:0.62rem; color:#8b949e; text-transform:uppercase; display:block; }
.pbox .pv { font-size:0.95rem; font-weight:700; color:#e6edf3; display:block; }
.pbox .pd { font-size:0.7rem; display:block; }

/* ── 評分條 ── */
.sbar { background:#21262d; border-radius:6px; padding:7px 10px; margin:6px 0; font-family:monospace; font-size:0.85rem; }

/* ── 推薦卡 ── */
.pick-card {
    background:#161b22; border:1px solid #30363d;
    border-left:4px solid #58a6ff; border-radius:10px;
    padding:12px 14px; margin-bottom:8px;
}
.pick-name    { font-size:1.05rem; font-weight:700; color:#e6edf3; }
.pick-tag     { background:#21262d; color:#8b949e; border-radius:4px; padding:1px 6px; font-size:0.7rem; margin-left:4px; }
.pick-score   { float:right; color:#58a6ff; font-weight:700; font-size:0.95rem; }
.pick-why     { font-size:0.78rem; color:#8b949e; margin-top:4px; line-height:1.5; }
.pick-entry   { color:#79c0ff; font-weight:600; font-size:0.92rem; margin-top:6px; }
.pick-payback { font-size:0.75rem; color:#8b949e; }

/* ── 大盤 氛圍 ── */
.market-card { background:#161b22; border-radius:7px; padding:8px 12px; border-left:3px solid #58a6ff; font-size:0.8rem; color:#c9d1d9; }

hr { border-color:#21262d !important; margin:10px 0 !important; }
section[data-testid="stSidebar"] { background:#0d1117 !important; border-right:1px solid #21262d; }
</style>
""", unsafe_allow_html=True)
# =============================================
# 股票代號對照表（ETF 另外標記，推薦時排除）
# =============================================
SYMBOL_MAP = {
    "光寶科": "2301", "台達電": "2308", "鴻海": "2317", "台積電": "2330",
    "金像電": "2368", "廣達": "2382", "奇鋐": "3017", "欣興": "3037",
    "緯創": "3231", "群創": "3481", "緯穎": "6669", "聯發科": "2454",
    "日月光": "3711", "聯電": "2303", "南亞科": "2408", "華碩": "2357",
    "宏碁": "2353", "研華": "2395", "信驊": "5274", "英業達": "2356",
    "仁寶": "2324", "和碩": "4938",
    # ETF（持股用，推薦排除）
    "主動統一升級50": "00936", "元大高股息": "0056",
    "國泰永續高股息": "00878", "群益台灣精選高息": "00919",
}
ETF_SET = {"主動統一升級50", "元大高股息", "國泰永續高股息", "群益台灣精選高息"}

# =============================================
# 數據函式
# =============================================
@st.cache_data(ttl=1800)
def get_market_data():
    tickers = {"費半": "^SOX", "納指": "^IXIC", "TSM ADR": "TSM", "台指": "^TWII"}
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

@st.cache_data(ttl=3600)
def get_institutional_data(stock_id):
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        resp = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockInstitutionalInvestors",
                    "data_id": stock_id, "start_date": start_date},
            timeout=8
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 200 and data.get("data"):
                df = pd.DataFrame(data["data"])
                df["buy"]  = pd.to_numeric(df["buy"],  errors="coerce").fillna(0)
                df["sell"] = pd.to_numeric(df["sell"], errors="coerce").fillna(0)
                recent = df.tail(9)
                net = int(recent["buy"].sum() - recent["sell"].sum())
                by_type = df.groupby("name").apply(
                    lambda x: x["buy"].sum() - x["sell"].sum()
                ).to_dict()
                return {"status": "買超" if net > 0 else "賣超", "net": net, "by_type": by_type, "src": "finmind"}
    except Exception:
        pass
    try:
        df = yf.Ticker(f"{stock_id}.TW").history(period="10d")
        if not df.empty and len(df) >= 3:
            recent = df.tail(5)
            up_vol   = recent[recent["Close"] > recent["Open"]]["Volume"].sum()
            down_vol = recent[recent["Close"] <= recent["Open"]]["Volume"].sum()
            net_est  = int(up_vol - down_vol)
            return {"status": "買超(估)" if net_est > 0 else "賣超(估)", "net": net_est, "by_type": {}, "src": "yf_vol"}
    except Exception:
        pass
    return {"status": "無數據", "net": 0, "by_type": {}, "src": "none"}
def compute_signal_score(df):
    if df is None or len(df) < 20:
        return 0, {}
    latest, prev = df.iloc[-1], df.iloc[-2]
    signals, score = {}, 0
    close = float(latest["Close"])

    ma20 = latest.get("MA20")
    if pd.notna(ma20):
        ma20 = float(ma20)
        if close > ma20:
            signals["均線"] = (f"收在20MA({ma20:.0f})上方", +1); score += 1
        else:
            signals["均線"] = (f"跌破20MA({ma20:.0f})", -1); score -= 1

    rsi = latest.get("RSI")
    if pd.notna(rsi):
        rsi = float(rsi)
        if rsi < 30:
            signals["RSI"] = (f"RSI {rsi:.0f} 超賣", +1); score += 1
        elif rsi > 70:
            signals["RSI"] = (f"RSI {rsi:.0f} 超買", -1); score -= 1
        else:
            signals["RSI"] = (f"RSI {rsi:.0f} 中性", 0)

    mh  = latest.get("MACD_Hist"); mhp = prev.get("MACD_Hist")
    if pd.notna(mh) and pd.notna(mhp):
        mh, mhp = float(mh), float(mhp)
        if mh > 0 and mhp <= 0:
            signals["MACD"] = ("MACD 翻正", +1); score += 1
        elif mh < 0 and mhp >= 0:
            signals["MACD"] = ("MACD 翻負", -1); score -= 1
        elif mh > 0:
            signals["MACD"] = ("MACD 擴大", +1); score += 1
        else:
            signals["MACD"] = ("MACD 收縮", -1); score -= 1

    k  = latest.get("K"); d  = latest.get("D")
    kp = prev.get("K");   dp = prev.get("D")
    if pd.notna(k) and pd.notna(d) and pd.notna(kp) and pd.notna(dp):
        k, d, kp, dp = float(k), float(d), float(kp), float(dp)
        if k > d and kp <= dp and k < 80:
            signals["KD"] = (f"KD黃金交叉 K={k:.0f}", +1); score += 1
        elif k < d and kp >= dp and k > 20:
            signals["KD"] = (f"KD死亡交叉 K={k:.0f}", -1); score -= 1
        elif k < 20:
            signals["KD"] = (f"KD超賣 K={k:.0f}", +1); score += 1
        elif k > 80:
            signals["KD"] = (f"KD超買 K={k:.0f}", -1); score -= 1

    bbu = latest.get("BB_Upper"); bbl = latest.get("BB_Lower")
    if pd.notna(bbu) and pd.notna(bbl):
        bbu, bbl = float(bbu), float(bbl)
        if close < bbl:
            signals["布林"] = ("觸布林下緣 超賣", +1); score += 1
        elif close > bbu:
            signals["布林"] = ("突布林上緣 超買", -1); score -= 1
        else:
            bb_pct = (close - bbl) / (bbu - bbl) * 100 if (bbu - bbl) > 0 else 50
            signals["布林"] = (f"布林帶內 {bb_pct:.0f}%", 0)

    vol = latest.get("Volume"); vma = latest.get("Vol_MA5")
    if pd.notna(vol) and pd.notna(vma) and float(vma) > 0:
        vr = float(vol) / float(vma)
        prev_close = float(prev["Close"])
        if vr > 1.5 and close > prev_close:
            signals["量能"] = (f"放量上漲 {vr:.1f}x", +1); score += 1
        elif vr > 1.5 and close < prev_close:
            signals["量能"] = (f"放量下跌 {vr:.1f}x", -1); score -= 1
        else:
            signals["量能"] = (f"量能正常 {vr:.1f}x", 0)

    return max(-5, min(5, score)), signals


def classify(score, pnl, inst_status):
    """
    分類邏輯（以技術面為主，損益為輔）：

    賣出：
      - 虧損 > 10%（嚴格停損，給足空間）
      - 技術 <= -3 且 法人賣超（雙重確認出清）
      - 已獲利 > 15% 且 技術 <= -2（鎖利出場）

    攤平：
      - 虧損 5~10% 之間 且 技術 >= 0（基本面/趨勢未壞，可考慮加碼降成本）
      - 技術 -1~-2（訊號偏空但未到出場，等待觀察）

    續抱：
      - 技術 >= 1（趨勢向上）
      - 或 損益 > 0 且 技術 >= 0（賺錢不賣，讓利潤奔跑）

    Returns: (cat, title, badge_class, reason)
    cat: "sell" / "flat" / "hold"
    """
    is_sell_inst = "賣超" in inst_status

    # ── 賣出條件 ──
    if pnl < -10:
        return "sell", "🛑 停損出清", "bg-sell", f"虧損已達 {pnl:.1f}%，超過-10%停損線"
    if score <= -3 and is_sell_inst:
        return "sell", "🚨 出清", "bg-sell", "技術+法人雙殺，建議出清"
    if pnl > 15 and score <= -2:
        return "sell", "💰 停利出場", "bg-sell", f"已獲利 {pnl:.1f}% 但技術轉弱，建議停利"

    # ── 攤平/等待條件 ──
    if -10 <= pnl < -5 and score >= 0:
        return "flat", "⚖️ 可考慮攤平", "bg-flat", f"虧 {pnl:.1f}% 但技術未壞，可小量攤平降成本"
    if score <= -2:
        return "flat", "⚠️ 等待訊號", "bg-flat", "技術偏空，暫不加碼，等技術好轉"

    # ── 續抱 ──
    if score >= 1 or (pnl >= 0 and score >= 0):
        if pnl > 10:
            return "hold", f"🚀 續抱（+{pnl:.1f}% 讓利潤奔跑）", "bg-hold", "技術健康，獲利中，守住停損讓利潤跑"
        return "hold", "✅ 續抱", "bg-hold", "技術向上，持有"

    # 其他（輕微偏空但損益還好）
    return "flat", "👁 觀察", "bg-watch", "訊號中性，守20MA等待方向"


def score_bar(score):
    bar = ""
    for i in range(-5, 6):
        if i == 0: bar += "│"
        elif score > 0 and 0 < i <= score: bar += "🟩"
        elif score < 0 and score <= i < 0: bar += "🟥"
        else: bar += "⬜"
    return bar
def collect_summary(sname, sid, cost):
    df   = get_stock_history(sid)
    inst = get_institutional_data(sid)
    if df is None or df.empty:
        return None
    latest = df.iloc[-1]
    price  = float(latest["Close"])
    pnl    = (price - cost) / cost * 100 if cost > 0 else 0
    score, signals = compute_signal_score(df)
    cat, title, badge, reason = classify(score, pnl, inst["status"])
    return {
        "name": sname, "sid": sid, "cost": cost,
        "price": price, "pnl": pnl,
        "score": score, "cat": cat, "title": title,
        "badge": badge, "reason": reason,
        "inst": inst, "signals": signals, "df": df,
    }


def render_detail(s):
    cost  = s["cost"]; price = s["price"]
    score = s["score"]; inst  = s["inst"]

    # 操作建議
    st.markdown(f'<div class="badge {s["badge"]}">{s["title"]}<br><small style="font-weight:400;opacity:0.85">{s["reason"]}</small></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 評分條
    st.markdown(f'<div class="sbar">空 {score_bar(score)} 多　評分 <b>{score:+d}/5</b></div>', unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("現價", f"{price:.1f}")
    c2.metric("損益", f"{s['pnl']:+.1f}%", delta=f"{price-cost:+.1f}" if cost > 0 else "")
    inst_lbl = inst["status"] + ("⁺" if inst["src"] == "yf_vol" else "")
    c3.metric("法人", inst_lbl, delta=f"{inst['net']:+,}" if inst["net"] != 0 else "")

    # 停損停利
    if cost > 0:
        sl10 = cost * 0.90   # -10% 硬停損
        sl5  = cost * 0.95   # -5% 軟停損
        tp10 = cost * 1.10   # +10% 停利1
        tp15 = cost * 1.15   # +15% 停利2
        items = [
            ("軟停損", sl5,  "#e3b341"),
            ("硬停損", sl10, "#f85149"),
            ("停利①",  tp10, "#3fb950"),
            ("停利②",  tp15, "#58a6ff"),
        ]
        html = '<div class="pgrid">'
        for lbl, target, color in items:
            diff = price - target
            diff_c = "#3fb950" if diff > 0 else "#f85149"
            if "停損" in lbl:
                diff_c = "#f85149" if price > target else "#3fb950"
            html += f'<div class="pbox"><span class="pl">{lbl}</span><span class="pv">{target:.0f}</span><span class="pd" style="color:{diff_c}">{diff:+.0f}</span></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # 技術指標
    with st.expander("📐 技術明細"):
        for ind, (msg, v) in s["signals"].items():
            icon = "🟢" if v > 0 else ("🔴" if v < 0 else "🟡")
            st.write(f"{icon} **{ind}**：{msg}")
        l = s["df"].iloc[-1]
        rows = [
            ("RSI",    f"{float(l['RSI']):.1f}"       if pd.notna(l.get("RSI")) else "N/A"),
            ("K/D",    f"{float(l['K']):.0f}/{float(l['D']):.0f}" if pd.notna(l.get("K")) else "N/A"),
            ("MACD柱", f"{float(l['MACD_Hist']):.3f}" if pd.notna(l.get("MACD_Hist")) else "N/A"),
            ("20MA",   f"{float(l['MA20']):.0f}"      if pd.notna(l.get("MA20")) else "N/A"),
            ("布林上", f"{float(l['BB_Upper']):.0f}"  if pd.notna(l.get("BB_Upper")) else "N/A"),
            ("布林下", f"{float(l['BB_Lower']):.0f}"  if pd.notna(l.get("BB_Lower")) else "N/A"),
        ]
        st.table(pd.DataFrame(rows, columns=["指標","值"]))

    # 法人
    with st.expander("🏦 法人籌碼"):
        note = "（備援：近5日量能方向）" if inst["src"] == "yf_vol" else ""
        st.caption(f"來源：{inst['src']} {note}")
        if inst["by_type"]:
            for nt, nv in inst["by_type"].items():
                st.write(f"{'🟢' if nv>0 else '🔴'} **{nt}**：{int(nv):+,} 股")
        else:
            st.write(f"整體：**{inst['status']}**　淨量：{inst['net']:+,}")
@st.cache_data(ttl=3600)
def scan_picks():
    """
    推薦邏輯（排除ETF，找真正有動能的個股）：
    條件：技術評分 >= 3（強烈訊號）
          且 近5日量能放大（放量啟動）
          且 RSI 不超買（< 75）
          且 收盤站上 20MA
    排序：評分高 > 法人買超 > 量能倍率
    """
    picks = []
    for sname, sid in SYMBOL_MAP.items():
        if sname in ETF_SET:
            continue  # 排除 ETF
        try:
            df   = get_stock_history(sid)
            inst = get_institutional_data(sid)
            if df is None or len(df) < 20:
                continue
            score, signals = compute_signal_score(df)
            if score < 3:  # 門檻拉高到 3，只推強訊號
                continue

            latest = df.iloc[-1]
            price  = float(latest["Close"])
            rsi    = float(latest.get("RSI", 50)) if pd.notna(latest.get("RSI")) else 50
            ma20   = float(latest.get("MA20", 0)) if pd.notna(latest.get("MA20")) else 0
            vol    = float(latest.get("Volume", 0)) if pd.notna(latest.get("Volume")) else 0
            vma    = float(latest.get("Vol_MA5", 1)) if pd.notna(latest.get("Vol_MA5")) else 1

            # 條件篩選
            if rsi > 75:
                continue  # 過熱不推
            if ma20 > 0 and price < ma20:
                continue  # 要站上 20MA
            vol_ratio = vol / vma if vma > 0 else 1

            # 估算入手價與回本時間
            df60 = df.tail(60)
            avg_chg = df60["Close"].pct_change().mean() * 100
            if avg_chg > 0.05:
                est_d = int(10 / avg_chg)
                payback = f"~{est_d}交易日（{max(1,round(est_d/5))}週）"
            else:
                payback = "需觀察趨勢"

            entry = round(float(ma20) * 1.002, 1) if ma20 > 0 else round(price * 0.99, 1)

            good_signals = [msg for _, (msg, v) in signals.items() if v > 0]

            picks.append({
                "name": sname, "sid": sid, "price": price, "score": score,
                "inst": inst["status"], "rsi": rsi,
                "vol_ratio": vol_ratio,
                "entry": entry, "payback": payback,
                "reasons": good_signals,
            })
        except Exception:
            continue

    # 排序：評分 > 法人買超 > 量能
    picks.sort(key=lambda x: (
        x["score"],
        1 if "買超" in x["inst"] else 0,
        x["vol_ratio"]
    ), reverse=True)
    return picks[:8]


# =============================================
# 主 UI
# =============================================
now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
market  = get_market_data()

# Hero
st.markdown(f"""
<div class="hero-box">
  <div class="hero-title">📈 台股操盤 Pro</div>
  <div class="hero-sub">{now_str}　｜　RSI · MACD · KD · 布林 · 大盤</div>
</div>
""", unsafe_allow_html=True)

# 大盤 — 折疊
with st.expander("🌐 大盤概況（點開查看）", expanded=False):
    if market:
        cols = st.columns(4)
        for i, (name, val) in enumerate(market.items()):
            chg = val["change"]
            cols[i].metric(
                name,
                f"{val['price']:.0f}" if val["price"] > 1000 else f"{val['price']:.2f}",
                f"{chg:+.2f}%",
                delta_color="normal" if chg >= 0 else "inverse"
            )
    tsm_chg = market.get("TSM ADR", {}).get("change", 0)
    sox_chg = market.get("費半",    {}).get("change", 0)
    if tsm_chg > 1 and sox_chg > 1:
        st.markdown('<div class="market-card" style="border-color:#3fb950">🔥 ADR+費半同步大漲，電子股強勢</div>', unsafe_allow_html=True)
    elif tsm_chg < -1 and sox_chg < -1:
        st.markdown('<div class="market-card" style="border-color:#f85149">🚨 ADR+費半同步重挫，謹慎操作</div>', unsafe_allow_html=True)
    elif tsm_chg > 1:
        st.markdown('<div class="market-card" style="border-color:#3fb950">🎯 TSM ADR強勢，台積族群關注</div>', unsafe_allow_html=True)
    elif tsm_chg < -1:
        st.markdown('<div class="market-card" style="border-color:#e3b341">⚠️ TSM ADR走弱，供應鏈留意</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-card">📊 大盤平盤整理</div>', unsafe_allow_html=True)

# 側邊欄
with st.sidebar:
    st.markdown("### ⚙️ 設定")
    uploaded_file = st.file_uploader("📂 匯入 CSV（未實現損益）", type="csv")
    st.markdown("---")
    st.markdown("### 🔍 單股查詢")
    manual_name = st.text_input("股票名稱", placeholder="台積電、鴻海...")
    manual_cost = st.number_input("持有成本", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    st.caption("⚠️ 僅供參考，投資需自負盈虧")
# =============================================
# 收集持股
# =============================================
summaries = []

if uploaded_file:
    try:
        df_csv = pd.read_csv(uploaded_file)
        df_csv.columns = df_csv.columns.str.strip()
        if "成交均價" in df_csv.columns and "股票名稱" in df_csv.columns:
            df_csv["成交均價"] = pd.to_numeric(
                df_csv["成交均價"].astype(str).str.replace(",", ""), errors="coerce"
            )
            valid = [(str(r["股票名稱"]).strip(), r["成交均價"])
                     for _, r in df_csv.iterrows()
                     if str(r.get("股票名稱","")).strip() in SYMBOL_MAP]
            if valid:
                prog = st.progress(0, text="分析中...")
                for idx, (sn, cv) in enumerate(valid):
                    s = collect_summary(sn, SYMBOL_MAP[sn], float(cv))
                    if s:
                        summaries.append(s)
                    prog.progress((idx+1)/len(valid), text=f"分析 {sn}...")
                prog.empty()
            else:
                st.warning("CSV 中股票名稱不在對照表內")
        else:
            st.error("CSV 需包含『股票名稱』與『成交均價』欄位")
    except Exception as e:
        st.error(f"CSV 讀取錯誤：{e}")

elif manual_name:
    if manual_name in SYMBOL_MAP:
        with st.spinner(f"分析 {manual_name}..."):
            s = collect_summary(manual_name, SYMBOL_MAP[manual_name], float(manual_cost))
        if s:
            summaries.append(s)
    else:
        st.sidebar.error(f"找不到『{manual_name}』")

# =============================================
# 主標籤
# =============================================
tab_hold, tab_pick = st.tabs(["📂 持有股", "🌟 推薦入手股"])

# ── 持有股 ──
with tab_hold:
    if not summaries:
        st.markdown("""
        <div style="text-align:center;padding:50px 10px;color:#8b949e;">
          <div style="font-size:2.5rem">📂</div>
          <div style="font-size:0.95rem;margin-top:8px">左上角 ≫ 上傳 CSV 或輸入股票名稱</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        sell_list = [s for s in summaries if s["cat"] == "sell"]
        flat_list = [s for s in summaries if s["cat"] == "flat"]
        hold_list = [s for s in summaries if s["cat"] == "hold"]

        sub1, sub2, sub3 = st.tabs([
            f"🛑 賣出 ({len(sell_list)})",
            f"⚖️ 攤平/等待 ({len(flat_list)})",
            f"💎 續抱 ({len(hold_list)})",
        ])

        def render_list(lst, tab):
            with tab:
                if not lst:
                    st.success("此類別目前無持股 👍")
                    return
                # 排序：賣出按損益升序（最慘的先看），其他按評分降序
                sorted_lst = sorted(lst, key=lambda x: x["pnl"])
                for s in sorted_lst:
                    pnl_color = "#f85149" if s["pnl"] < 0 else "#3fb950"
                    pnl_icon  = "▼" if s["pnl"] < 0 else "▲"
                    label = f"{s['name']}　{s['price']:.0f}　{pnl_icon}{abs(s['pnl']):.1f}%"
                    with st.expander(label, expanded=False):
                        render_detail(s)

        render_list(sell_list, sub1)
        render_list(flat_list, sub2)
        render_list(hold_list, sub3)

# ── 推薦入手股 ──
with tab_pick:
    st.markdown("""
    <div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">
    篩選條件：技術評分≥3 · 站上20MA · RSI&lt;75 · 排除ETF<br>
    ⁺ 法人資料為量能備援估算
    </div>
    """, unsafe_allow_html=True)
    with st.spinner("掃描中..."):
        picks = scan_picks()
    if not picks:
        st.info("今日暫無符合強訊號條件的推薦標的（評分需≥3）")
        st.caption("目前市場可能偏空或整理，等待更好入場時機")
    for p in picks:
        inst_icon = "🟢" if "買超" in p["inst"] else ("🔴" if "賣超" in p["inst"] else "⚪")
        rsi_note  = f"RSI {p['rsi']:.0f}"
        vol_note  = f"量{p['vol_ratio']:.1f}x" if p["vol_ratio"] > 1 else ""
        st.markdown(f"""
        <div class="pick-card">
          <div>
            <span class="pick-name">{p['name']}</span>
            <span class="pick-tag">{p['sid']}.TW</span>
            <span class="pick-score">評分 {p['score']:+d}/5</span>
          </div>
          <div class="pick-why">現價 {p['price']:.1f}　{inst_icon} {p['inst']}　{rsi_note}　{vol_note}</div>
          <div class="pick-entry">📍 建議入手：{p['entry']}</div>
          <div class="pick-payback">⏱ 到+10%停利：{p['payback']}</div>
        </div>
        """, unsafe_allow_html=True)
        if p["reasons"]:
            st.caption("✅ " + "　".join(p["reasons"][:3]))
        st.markdown("")
