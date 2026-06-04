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

st.markdown("""
<style>
/* ── 全域底色 ── */
.stApp { background: #0d1117; }
.block-container { padding: 0.5rem 0.8rem 2rem !important; max-width: 100% !important; }

/* ── Hero ── */
.hero-box {
    background: linear-gradient(135deg,#1a1f2e,#0f3460);
    border: 1px solid #30363d; border-radius: 14px;
    padding: 14px 18px; margin-bottom: 12px;
}
.hero-title { font-size: 1.4rem; font-weight: 800; color: #e6edf3; margin:0; }
.hero-sub   { color: #8b949e; font-size: 0.78rem; margin-top:3px; }

/* ── Metric 卡片 ── */
div[data-testid="metric-container"] {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 10px 12px;
}
div[data-testid="metric-container"] label {
    color: #8b949e !important; font-size: 0.72rem !important;
    font-weight: 600 !important; text-transform: uppercase;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e6edf3 !important; font-size: 1.35rem !important; font-weight: 700 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.82rem !important;
}

/* ── 主標籤（持有股/推薦） ── */
div[data-testid="stTabs"] > div:first-child button {
    font-size: 1.05rem !important; font-weight: 700 !important;
    padding: 10px 20px !important; border-radius: 10px 10px 0 0 !important;
}

/* ── 個股卡片 ── */
.scard {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;
    cursor: pointer;
}
.scard-name  { font-size: 1.1rem; font-weight: 700; color: #e6edf3; }
.scard-tag   { display:inline-block; background:#21262d; color:#8b949e; border-radius:5px; padding:1px 7px; font-size:0.72rem; margin-left:5px; }
.scard-sub   { font-size: 0.82rem; color: #8b949e; margin-top:4px; }
.scard-badge { display:inline-block; border-radius:6px; padding:4px 10px; font-size:0.82rem; font-weight:600; margin-top:6px; }
.bg-sell  { background:#3d1a1a; color:#f85149; border:1px solid #da3633; }
.bg-flat  { background:#3d2e00; color:#e3b341; border:1px solid #9e6a03; }
.bg-watch { background:#1a2233; color:#79c0ff; border:1px solid #1f6feb; }
.bg-hold  { background:#1a4731; color:#3fb950; border:1px solid #238636; }

/* ── 停損停利格 ── */
.pgrid { display:flex; gap:8px; flex-wrap:wrap; margin:10px 0; }
.pbox  { flex:1; min-width:80px; background:#21262d; border-radius:8px; padding:8px 10px; text-align:center; }
.pbox .pl { font-size:0.65rem; color:#8b949e; text-transform:uppercase; }
.pbox .pv { font-size:1.05rem; font-weight:700; color:#e6edf3; margin-top:1px; }
.pbox .pd { font-size:0.72rem; margin-top:1px; }

/* ── 評分條 ── */
.sbar { background:#21262d; border-radius:7px; padding:8px 12px; margin:8px 0; font-family:monospace; font-size:0.9rem; letter-spacing:1px; }

/* ── 操作badge ── */
.badge-buy  { background:#1a4731; color:#3fb950; border:1px solid #238636; border-radius:7px; padding:8px 12px; font-weight:600; font-size:0.9rem; }
.badge-sell { background:#3d1a1a; color:#f85149; border:1px solid #da3633; border-radius:7px; padding:8px 12px; font-weight:600; font-size:0.9rem; }
.badge-warn { background:#3d2e00; color:#e3b341; border:1px solid #9e6a03; border-radius:7px; padding:8px 12px; font-weight:600; font-size:0.9rem; }
.badge-hold { background:#1c2128; color:#8b949e; border:1px solid #30363d; border-radius:7px; padding:8px 12px; font-weight:600; font-size:0.9rem; }

/* ── 推薦卡 ── */
.pick-card {
    background:#161b22; border:1px solid #30363d;
    border-left:4px solid #58a6ff; border-radius:10px;
    padding:14px 16px; margin-bottom:10px;
}
.pick-name  { font-size:1.05rem; font-weight:700; color:#e6edf3; }
.pick-price { font-size:0.88rem; color:#8b949e; margin-top:3px; }
.pick-entry { font-size:1rem; color:#79c0ff; font-weight:600; margin-top:6px; }
.pick-payback { font-size:0.8rem; color:#8b949e; margin-top:3px; }

/* ── 側邊欄/大盤氛圍 ── */
section[data-testid="stSidebar"] { background:#0d1117 !important; border-right:1px solid #21262d; }
.market-card { background:#161b22; border-radius:8px; padding:10px 12px; border-left:3px solid #58a6ff; font-size:0.82rem; color:#c9d1d9; margin-bottom:8px; }
.pwa-hint { background:linear-gradient(90deg,#1a1f2e,#16213e); border:1px solid #1f6feb; border-radius:8px; padding:10px 14px; color:#79c0ff; font-size:0.8rem; margin-top:12px; }

hr { border-color:#21262d !important; margin:12px 0 !important; }
details { background:#161b22 !important; border:1px solid #30363d !important; border-radius:8px !important; padding:3px !important; }
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
    """法人籌碼：優先 FinMind，備援用 yfinance info 的 52w 相對位置估算"""
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

    # ── 備援：用 yfinance 近期走勢估算籌碼方向 ──
    try:
        df = yf.Ticker(f"{stock_id}.TW").history(period="10d")
        if not df.empty and len(df) >= 3:
            recent = df.tail(5)
            up_vol   = recent[recent["Close"] > recent["Open"]]["Volume"].sum()
            down_vol = recent[recent["Close"] <= recent["Open"]]["Volume"].sum()
            net_est  = int(up_vol - down_vol)
            status   = "買超(估)" if net_est > 0 else "賣超(估)"
            return {"status": status, "net": net_est, "by_type": {}, "src": "yf_vol"}
    except Exception:
        pass

    return {"status": "無數據", "net": 0, "by_type": {}, "src": "none"}
def compute_signal_score(df, cost):
    if df is None or len(df) < 20:
        return 0, {}
    latest, prev = df.iloc[-1], df.iloc[-2]
    signals, score = {}, 0
    close = float(latest["Close"])

    ma20 = latest.get("MA20")
    if pd.notna(ma20):
        if close > float(ma20):
            signals["均線"] = (f"收在20MA({float(ma20):.1f})上方", +1); score += 1
        else:
            signals["均線"] = (f"跌破20MA({float(ma20):.1f})", -1); score -= 1

    rsi = latest.get("RSI")
    if pd.notna(rsi):
        rsi = float(rsi)
        if rsi < 30:
            signals["RSI"] = (f"RSI {rsi:.0f} 超賣反彈機會", +1); score += 1
        elif rsi > 70:
            signals["RSI"] = (f"RSI {rsi:.0f} 超買注意", -1); score -= 1
        else:
            signals["RSI"] = (f"RSI {rsi:.0f} 中性", 0)

    mh  = latest.get("MACD_Hist"); mhp = prev.get("MACD_Hist")
    if pd.notna(mh) and pd.notna(mhp):
        mh, mhp = float(mh), float(mhp)
        if mh > 0 and mhp <= 0:
            signals["MACD"] = ("MACD柱翻正，多頭啟動", +1); score += 1
        elif mh < 0 and mhp >= 0:
            signals["MACD"] = ("MACD柱翻負，空頭啟動", -1); score -= 1
        elif mh > 0:
            signals["MACD"] = (f"MACD柱持續擴大 {mh:.3f}", +1); score += 1
        else:
            signals["MACD"] = (f"MACD柱持續收縮 {mh:.3f}", -1); score -= 1

    k  = latest.get("K"); d  = latest.get("D")
    kp = prev.get("K");   dp = prev.get("D")
    if pd.notna(k) and pd.notna(d) and pd.notna(kp) and pd.notna(dp):
        k, d, kp, dp = float(k), float(d), float(kp), float(dp)
        if k > d and kp <= dp and k < 80:
            signals["KD"] = (f"KD黃金交叉 K={k:.0f}", +1); score += 1
        elif k < d and kp >= dp and k > 20:
            signals["KD"] = (f"KD死亡交叉 K={k:.0f}", -1); score -= 1
        elif k < 20:
            signals["KD"] = (f"KD超賣區 K={k:.0f}", +1); score += 1
        elif k > 80:
            signals["KD"] = (f"KD超買區 K={k:.0f}", -1); score -= 1

    bbu = latest.get("BB_Upper"); bbl = latest.get("BB_Lower")
    if pd.notna(bbu) and pd.notna(bbl):
        bbu, bbl = float(bbu), float(bbl)
        if close < bbl:
            signals["布林"] = ("觸及布林下緣超賣反彈", +1); score += 1
        elif close > bbu:
            signals["布林"] = ("突破布林上緣超買警示", -1); score -= 1
        else:
            bb_pct = (close - bbl) / (bbu - bbl) * 100
            signals["布林"] = (f"布林帶內 {bb_pct:.0f}% 位置", 0)

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


def get_action(score, pnl, inst):
    """
    回傳 (分類, 主訊息, badge_class)
    分類: sell / flat / watch / hold
    """
    s = inst.get("status", "無數據")
    # 硬停損
    if pnl < -7:
        return "sell", "🛑 賣：-7%停損已觸及，立即出清", "badge-sell"
    # 強空
    if score <= -3 and "賣超" in s:
        return "sell", "🚨 賣：技術+法人雙殺，建議出清", "badge-sell"
    if score <= -2:
        return "flat", "⚠️ 攤平觀察：技術偏空，可小量攤平或等訊號", "badge-warn"
    # 有獲利但轉弱
    if pnl > 10 and score < 0:
        return "sell", "💰 賣：已獲利但技術轉弱，先出一半鎖利", "badge-sell"
    # 強多
    if score >= 3 and "買超" in s:
        return "hold", "🚀 續抱：技術+法人雙確認，可加碼", "badge-buy"
    if score >= 2:
        return "hold", "✅ 續抱：技術面健康，守住停損", "badge-buy"
    # 中性
    return "watch", "👁 觀察：訊號中性，守住20MA", "badge-hold"


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
    score, signals = compute_signal_score(df, cost)
    cat, msg, badge = get_action(score, pnl, inst)
    return {
        "name": sname, "sid": sid, "cost": cost,
        "price": price, "pnl": pnl,
        "score": score, "cat": cat, "msg": msg, "badge": badge,
        "inst": inst, "signals": signals, "df": df,
    }


def render_detail(s):
    """展開單股詳細資訊"""
    cost  = s["cost"]
    price = s["price"]
    score = s["score"]
    inst  = s["inst"]
    signals = s["signals"]
    df    = s["df"]

    bar = score_bar(score)
    st.markdown(f'<div class="sbar">空 {bar} 多　｜　評分 <b>{score:+d}</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="{s["badge"]}">{s["msg"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Metrics ──
    m1, m2, m3 = st.columns(3)
    m1.metric("現價", f"{price:.1f}")
    m2.metric("損益", f"{s['pnl']:+.2f}%", delta=f"{price-cost:+.1f}" if cost > 0 else "")
    inst_lbl = inst["status"]
    inst_d   = f"{inst['net']:+,}" if inst["net"] != 0 else ""
    if inst["src"] == "yf_vol":
        inst_lbl += "⁺"
    m3.metric("法人", inst_lbl, delta=inst_d)

    # ── 停損停利 ──
    if cost > 0:
        sl5, sl7, tp10, tp15 = cost*0.95, cost*0.93, cost*1.10, cost*1.15
        c1, c2, c3, c4 = st.columns(4)
        for col, label, target in [(c1,"軟停損",sl5),(c2,"硬停損",sl7),(c3,"停利1",tp10),(c4,"停利2",tp15)]:
            diff = price - target
            color = "#f85149" if (target < cost and price > target) else ("#3fb950" if price < target else "#e3b341")
            col.markdown(f"""
            <div class="pbox" style="background:#21262d;border-radius:8px;padding:8px;text-align:center;">
              <div class="pl">{label}</div>
              <div class="pv">{target:.1f}</div>
              <div class="pd" style="color:{color}">{diff:+.1f}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 技術指標 & 法人 ──
    with st.expander("📐 技術指標"):
        for ind, (msg, v) in signals.items():
            icon = "🟢" if v > 0 else ("🔴" if v < 0 else "🟡")
            st.write(f"{icon} **{ind}**：{msg}")
        l = df.iloc[-1]
        rows = [
            ("RSI", f"{float(l['RSI']):.1f}"       if pd.notna(l.get("RSI")) else "N/A"),
            ("K",   f"{float(l['K']):.1f}"          if pd.notna(l.get("K"))  else "N/A"),
            ("D",   f"{float(l['D']):.1f}"          if pd.notna(l.get("D"))  else "N/A"),
            ("MACD柱", f"{float(l['MACD_Hist']):.3f}" if pd.notna(l.get("MACD_Hist")) else "N/A"),
            ("20MA",  f"{float(l['MA20']):.1f}"     if pd.notna(l.get("MA20")) else "N/A"),
            ("布林上", f"{float(l['BB_Upper']):.1f}" if pd.notna(l.get("BB_Upper")) else "N/A"),
            ("布林下", f"{float(l['BB_Lower']):.1f}" if pd.notna(l.get("BB_Lower")) else "N/A"),
        ]
        st.table(pd.DataFrame(rows, columns=["指標","值"]))

    with st.expander("🏦 法人籌碼"):
        src_note = "（備援估算：近5日量能方向）" if inst["src"] == "yf_vol" else ""
        st.caption(f"資料來源：{inst['src']} {src_note}")
        if inst["by_type"]:
            for nt, nv in inst["by_type"].items():
                icon = "🟢" if nv > 0 else "🔴"
                st.write(f"{icon} **{nt}**：{int(nv):+,} 股")
        else:
            st.write(f"整體方向：**{inst['status']}**　淨量：{inst['net']:+,}")

    st.divider()
@st.cache_data(ttl=3600)
def scan_picks():
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
            avg_chg = df60["Close"].pct_change().mean() * 100
            if avg_chg > 0.05:
                est_d = int(10 / avg_chg)
                payback = f"約 {est_d} 交易日（{max(1,round(est_d/5))} 週）"
            else:
                payback = "趨勢偏弱不易估"
            ma20 = latest.get("MA20")
            entry = float(ma20) if pd.notna(ma20) and float(ma20) < price else round(price*0.99, 1)
            good = [msg for _, (msg, v) in signals.items() if v > 0]
            picks.append({
                "name": sname, "sid": sid, "price": price, "score": score,
                "inst": inst["status"], "entry": round(entry, 1),
                "payback": payback, "reasons": good,
            })
        except Exception:
            continue
    picks.sort(key=lambda x: (x["score"], 1 if "買超" in x["inst"] else 0), reverse=True)
    return picks[:10]


# =============================================
# 主 UI
# =============================================
now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
market  = get_market_data()

# Hero
st.markdown(f"""
<div class="hero-box">
  <div class="hero-title">📈 台股操盤 Pro</div>
  <div class="hero-sub">{now_str}　｜　RSI · MACD · KD · 布林 · 大盤連動</div>
</div>
""", unsafe_allow_html=True)

# 大盤四格
if market:
    cols = st.columns(4)
    for i, (name, val) in enumerate(market.items()):
        chg = val["change"]
        cols[i].metric(name, f"{val['price']:.0f}" if val['price'] > 1000 else f"{val['price']:.2f}",
                       f"{chg:+.2f}%", delta_color="normal" if chg >= 0 else "inverse")

st.divider()

# 側邊欄
with st.sidebar:
    st.markdown("### ⚙️ 設定")
    uploaded_file = st.file_uploader("📂 匯入 CSV（未實現損益）", type="csv")
    st.markdown("---")
    st.markdown("### 🔍 單股查詢")
    manual_name = st.text_input("股票名稱", placeholder="台積電、鴻海...")
    manual_cost = st.number_input("持有成本", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    st.markdown("---")
    tsm_chg = market.get("TSM ADR", {}).get("change", 0)
    sox_chg = market.get("費半", {}).get("change", 0)
    if tsm_chg > 1 and sox_chg > 1:
        st.markdown('<div class="market-card" style="border-color:#3fb950">🔥 ADR+費半同步大漲</div>', unsafe_allow_html=True)
    elif tsm_chg < -1 and sox_chg < -1:
        st.markdown('<div class="market-card" style="border-color:#f85149">🚨 ADR+費半同步重挫，謹慎</div>', unsafe_allow_html=True)
    elif tsm_chg > 1:
        st.markdown('<div class="market-card" style="border-color:#3fb950">🎯 TSM ADR強勢</div>', unsafe_allow_html=True)
    elif tsm_chg < -1:
        st.markdown('<div class="market-card" style="border-color:#e3b341">⚠️ TSM ADR走弱</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-card">📊 大盤平盤整理</div>', unsafe_allow_html=True)
    st.markdown("""<div class="pwa-hint">📱 加到主畫面：Safari→分享→加入主畫面</div>""", unsafe_allow_html=True)
    st.caption("⚠️ 僅供參考，投資需自負盈虧")
# =============================================
# CSV 批次 or 單股
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
                prog = st.progress(0, text="分析持股中...")
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
        s = collect_summary(manual_name, SYMBOL_MAP[manual_name], float(manual_cost))
        if s:
            summaries.append(s)
    else:
        st.sidebar.error(f"找不到『{manual_name}』")

# =============================================
# 主標籤：持有股 | 推薦入手股
# =============================================
if summaries or not (uploaded_file or manual_name):
    tab_hold, tab_pick = st.tabs(["📂 持有股", "🌟 推薦入手股"])
else:
    tab_hold, tab_pick = st.tabs(["📂 持有股", "🌟 推薦入手股"])

# ── 持有股標籤 ──
with tab_hold:
    if not summaries:
        st.markdown("""
        <div style="text-align:center;padding:50px 20px;color:#8b949e;">
          <div style="font-size:2.5rem;">📂</div>
          <div style="font-size:1rem;margin-top:10px;">請在左側上傳 CSV 或輸入股票名稱</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        sell_list  = [s for s in summaries if s["cat"] == "sell"]
        flat_list  = [s for s in summaries if s["cat"] == "flat"]
        watch_list = [s for s in summaries if s["cat"] == "watch"]
        hold_list  = [s for s in summaries if s["cat"] == "hold"]

        sub1, sub2, sub3 = st.tabs([
            f"🛑 賣出/停損 ({len(sell_list)})",
            f"⚠️ 攤平 ({len(flat_list)+len(watch_list)})",
            f"💎 續抱 ({len(hold_list)})",
        ])

        def render_card_list(lst, sub_tab):
            with sub_tab:
                if not lst:
                    st.info("此類別目前無持股")
                    return
                for s in sorted(lst, key=lambda x: x["pnl"]):
                    pnl_color = "#f85149" if s["pnl"] < 0 else "#3fb950"
                    cat_badge = {
                        "sell":  ("bg-sell",  "賣出"),
                        "flat":  ("bg-flat",  "攤平觀察"),
                        "watch": ("bg-watch", "觀察"),
                        "hold":  ("bg-hold",  "續抱"),
                    }.get(s["cat"], ("bg-watch","觀察"))
                    with st.expander(
                        f"{s['name']}　{s['price']:.1f}　{s['pnl']:+.2f}%",
                        expanded=False
                    ):
                        render_detail(s)

        render_card_list(sell_list,  sub1)
        render_card_list(flat_list + watch_list, sub2)
        render_card_list(hold_list,  sub3)

# ── 推薦入手股標籤 ──
with tab_pick:
    st.caption("依技術評分排序（評分≥2），⁺ 表示法人資料為備援估算")
    with st.spinner("掃描推薦標的中..."):
        picks = scan_picks()
    if not picks:
        st.info("今日暫無符合條件的推薦標的")
    for p in picks:
        inst_icon = "🟢" if "買超" in p["inst"] else ("🔴" if "賣超" in p["inst"] else "⚪")
        st.markdown(f"""
        <div class="pick-card">
          <div class="pick-name">{p['name']} <span class="scard-tag">{p['sid']}.TW</span>
            <span style="float:right;color:#58a6ff;font-weight:700">評分 {p['score']:+d}</span></div>
          <div class="pick-price">現價 {p['price']:.1f}　{inst_icon} {p['inst']}</div>
          <div class="pick-entry">📍 建議入手：{p['entry']}</div>
          <div class="pick-payback">⏱ 到+10%停利：{p['payback']}</div>
        </div>
        """, unsafe_allow_html=True)
        if p["reasons"]:
            st.caption("✅ " + "　".join(p["reasons"][:3]))
