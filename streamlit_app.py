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
#MainMenu{visibility:hidden;}
header[data-testid="stHeader"]{display:none!important;}
footer{display:none!important;}
div[data-testid="stToolbar"]{display:none!important;}
div[data-testid="stDecoration"]{display:none!important;}
.viewerBadge_container__1QSob{display:none!important;}
button[kind="header"]{display:none!important;}
[data-testid="collapsedControl"]{top:8px!important;}

.stApp{background:#0d1117;}
.block-container{padding:0.6rem 0.8rem 2rem!important;max-width:100%!important;}

.hero-box{background:linear-gradient(135deg,#1a1f2e,#0f3460);border:1px solid #30363d;border-radius:12px;padding:12px 16px;margin-bottom:8px;}
.hero-title{font-size:1.3rem;font-weight:800;color:#e6edf3;margin:0;}
.hero-sub{color:#8b949e;font-size:0.72rem;margin-top:2px;}

div[data-testid="metric-container"]{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 10px;}
div[data-testid="metric-container"] label{color:#8b949e!important;font-size:0.68rem!important;font-weight:600!important;text-transform:uppercase;}
div[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#e6edf3!important;font-size:1.15rem!important;font-weight:700!important;}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] svg{display:none;}

div[data-testid="stTabs"]>div:first-child button{font-size:1rem!important;font-weight:700!important;padding:9px 16px!important;}
div[data-testid="stTabs"] div[data-testid="stTabs"]>div:first-child button{font-size:0.82rem!important;font-weight:600!important;padding:7px 10px!important;}
div[data-testid="stExpander"]>details{background:#161b22!important;border:1px solid #30363d!important;border-radius:10px!important;margin-bottom:6px!important;}
div[data-testid="stExpander"]>details>summary{font-size:0.95rem!important;font-weight:600!important;color:#e6edf3!important;padding:11px 14px!important;}

.badge{display:block;border-radius:7px;padding:8px 12px;font-size:0.85rem;font-weight:600;margin:6px 0;}
.bg-sell{background:#3d1a1a;color:#f85149;border:1px solid #da3633;}
.bg-flat{background:#3d2e00;color:#e3b341;border:1px solid #9e6a03;}
.bg-hold{background:#1a4731;color:#3fb950;border:1px solid #238636;}
.bg-watch{background:#1a2233;color:#79c0ff;border:1px solid #1f6feb;}

.pgrid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin:8px 0;}
.pbox{background:#21262d;border-radius:7px;padding:7px 8px;text-align:center;}
.pbox .pl{font-size:0.6rem;color:#8b949e;text-transform:uppercase;display:block;}
.pbox .pv{font-size:0.92rem;font-weight:700;color:#e6edf3;display:block;}
.pbox .pd{font-size:0.68rem;display:block;}
.atr-box{background:#1a2233;border:1px solid #1f6feb;border-radius:7px;padding:8px 12px;margin:6px 0;font-size:0.8rem;color:#79c0ff;}
.sbar{background:#21262d;border-radius:6px;padding:7px 10px;margin:6px 0;font-family:monospace;font-size:0.82rem;}

/* AI 分析區塊 */
.ai-box{background:linear-gradient(135deg,#0d1f12,#0a1628);border:1px solid #238636;border-radius:10px;padding:12px 14px;margin:8px 0;}
.ai-title{font-size:0.8rem;color:#3fb950;font-weight:600;margin-bottom:6px;}
.ai-content{font-size:0.88rem;color:#c9d1d9;line-height:1.6;white-space:pre-wrap;}
.ai-market-box{background:linear-gradient(135deg,#0f1a2e,#0d1117);border:1px solid #1f6feb;border-radius:10px;padding:14px 16px;margin:10px 0;}
.ai-market-title{font-size:0.82rem;color:#58a6ff;font-weight:600;margin-bottom:8px;}

.pick-card{background:#161b22;border:1px solid #30363d;border-left:4px solid #58a6ff;border-radius:10px;padding:12px 14px;margin-bottom:8px;}
.pick-name{font-size:1rem;font-weight:700;color:#e6edf3;}
.pick-tag{background:#21262d;color:#8b949e;border-radius:4px;padding:1px 6px;font-size:0.68rem;margin-left:4px;}
.pick-score{float:right;color:#58a6ff;font-weight:700;font-size:0.9rem;}
.pick-info{font-size:0.78rem;color:#8b949e;margin-top:4px;}
.pick-entry{color:#79c0ff;font-weight:600;font-size:0.88rem;margin-top:6px;}
.pick-atr{background:#1a2233;border-radius:5px;padding:4px 8px;font-size:0.75rem;color:#58a6ff;margin-top:4px;display:inline-block;}

.market-card{background:#161b22;border-radius:7px;padding:8px 12px;border-left:3px solid #58a6ff;font-size:0.8rem;color:#c9d1d9;}
hr{border-color:#21262d!important;margin:10px 0!important;}
section[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #21262d;}
</style>
""", unsafe_allow_html=True)
# =============================================
# AI 分析模組（支援 OpenAI / Gemini，自動偵測）
# =============================================
def get_ai_client():
    """取得 AI 客戶端，優先 OpenAI，備援 Gemini"""
    try:
        import openai
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return "openai", key
    except Exception:
        pass
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return "gemini", key
    except Exception:
        pass
    return None, None


def call_ai(prompt: str) -> str:
    """呼叫 AI API，回傳繁體中文分析文字"""
    provider, key = get_ai_client()
    if not provider:
        return None

    if provider == "openai":
        try:
            import openai
            client = openai.OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content":
                     "你是一位專業的台股技術分析師，熟悉台灣股市操作。"
                     "請用繁體中文，精簡扼要地回答，每點不超過2行，"
                     "語氣直接務實，不要廢話，不要免責聲明。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"[OpenAI 錯誤：{e}]"

    elif provider == "gemini":
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}",
                json={"contents": [{"parts": [{"text":
                    "你是台股技術分析師，請用繁體中文精簡回答，不要免責聲明。\n\n" + prompt
                }]}],
                "generationConfig": {"maxOutputTokens": 400, "temperature": 0.3}},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return f"[Gemini 錯誤：{resp.status_code}]"
        except Exception as e:
            return f"[Gemini 錯誤：{e}]"
    return None


def build_stock_prompt(s: dict) -> str:
    """建立個股分析 prompt"""
    atr  = s.get("atr")
    inst = s["inst"]
    sigs = s["signals"]

    sig_lines = "\n".join([f"  - {k}：{v[0]}（{'+1' if v[1]>0 else ('-1' if v[1]<0 else '0')}）"
                             for k, v in sigs.items()])
    atr_line = ""
    if atr:
        atr_line = (f"ATR(14)={atr['atr']:.1f}，ATR停損線={atr['sl']:.0f}（{atr['sl_pct']:+.1f}%），"
                    f"移動停利線={atr['trailing']:.0f}，停利1={atr['tp1']:.0f}，停利2={atr['tp2']:.0f}")

    return f"""請針對以下台股個股進行操作分析：

股票：{s['name']}（{s['sid']}.TW）
現價：{s['price']:.1f}　持有成本：{s['cost']:.1f}　損益：{s['pnl']:+.1f}%
技術評分：{s['score']:+d}/5
法人動態：{inst['status']}（淨量 {inst['net']:+,}）
{atr_line}

技術訊號：
{sig_lines}

請給我：
1. 📊 今日操作建議（一句話）
2. 🎯 進場/加碼價位（若適合）
3. 🛑 停損執行方式（結合ATR）
4. ⚠️ 最大風險點
5. 📅 預計持有天數與目標"""


def build_market_prompt(picks: list, market: dict) -> str:
    """建立今日市場總覽 prompt"""
    mkt_lines = "\n".join([f"  {k}：{v['price']:.0f if v['price']>1000 else v['price']:.2f}（{v['change']:+.2f}%）"
                             for k, v in market.items()])
    pick_lines = "\n".join([
        f"  {p['name']}：評分{p['score']:+d}，現價{p['price']:.0f}，RSI{p['rsi']:.0f}，"
        f"{'MACD翻紅' if p.get('macd_flip') else '均線突破' if p.get('breakout') else '技術強勢'}，"
        f"法人{p['inst']}"
        for p in picks[:5]
    ]) if picks else "  （今日無強訊號標的）"

    return f"""今日台股大盤與推薦標的總覽：

大盤指數：
{mkt_lines}

今日技術強勢個股（評分≥3）：
{pick_lines}

請給我：
1. 🌏 今日大盤氛圍判斷（多/空/中性）
2. 📈 今日適合操作的方向與族群
3. 🎯 最值得關注的1~2檔（從上述標的中挑）及理由
4. ⚠️ 今日最大風險提示
5. 💡 今日操作策略總結（一句話）"""
SYMBOL_MAP = {
    "光寶科": "2301", "台達電": "2308", "鴻海": "2317", "台積電": "2330",
    "金像電": "2368", "廣達": "2382", "奇鋐": "3017", "欣興": "3037",
    "緯創": "3231", "群創": "3481", "緯穎": "6669", "聯發科": "2454",
    "日月光": "3711", "聯電": "2303", "南亞科": "2408", "華碩": "2357",
    "宏碁": "2353", "研華": "2395", "信驊": "5274", "英業達": "2356",
    "仁寶": "2324", "和碩": "4938",
    "主動統一升級50": "00936", "元大高股息": "0056",
    "國泰永續高股息": "00878", "群益台灣精選高息": "00919",
}
ETF_SET = {"主動統一升級50", "元大高股息", "國泰永續高股息", "群益台灣精選高息"}

@st.cache_data(ttl=1800)
def get_market_data():
    tickers = {"費半": "^SOX", "納指": "^IXIC", "TSM ADR": "TSM", "台指": "^TWII"}
    res = {}
    for name, t in tickers.items():
        try:
            data = yf.download(t, period="5d", progress=False, auto_adjust=True)
            if not data.empty:
                close = data["Close"]
                if hasattr(close, "columns"): close = close.squeeze()
                close = close.dropna()
                if len(close) >= 2:
                    chg = (float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100
                    res[name] = {"price": float(close.iloc[-1]), "change": float(chg)}
                elif len(close) == 1: res[name] = {"price": float(close.iloc[-1]), "change": 0.0}
                else: res[name] = {"price": 0.0, "change": 0.0}
            else: res[name] = {"price": 0.0, "change": 0.0}
        except Exception: res[name] = {"price": 0.0, "change": 0.0}
    return res

@st.cache_data(ttl=1800)
def get_stock_history(sid, period="6mo"):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period=period)
        if df.empty: return None
        df["MA5"]  = df["Close"].rolling(5).mean()
        df["MA10"] = df["Close"].rolling(10).mean()
        df["MA20"] = df["Close"].rolling(20).mean()
        df["MA60"] = df["Close"].rolling(60).mean()
        df["TR"] = np.maximum(df["High"]-df["Low"], np.maximum(
            abs(df["High"]-df["Close"].shift(1)), abs(df["Low"]-df["Close"].shift(1))))
        df["ATR14"] = df["TR"].rolling(14).mean()
        delta = df["Close"].diff()
        gain, loss = delta.clip(lower=0), -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean().replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
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
        df["Trailing_Stop"] = df["Close"] - 2 * df["ATR14"]
        df["MA_Squeeze"] = (df[["MA5","MA10","MA20"]].max(axis=1) - df[["MA5","MA10","MA20"]].min(axis=1)) < df["ATR14"]
        return df
    except Exception: return None

@st.cache_data(ttl=3600)
def get_institutional_data(stock_id):
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
        resp = requests.get("https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockInstitutionalInvestors",
                    "data_id": stock_id, "start_date": start_date}, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 200 and data.get("data"):
                df = pd.DataFrame(data["data"])
                df["buy"]  = pd.to_numeric(df["buy"],  errors="coerce").fillna(0)
                df["sell"] = pd.to_numeric(df["sell"], errors="coerce").fillna(0)
                net = int(df.tail(9)["buy"].sum() - df.tail(9)["sell"].sum())
                by_type = df.groupby("name").apply(lambda x: x["buy"].sum()-x["sell"].sum()).to_dict()
                return {"status": "買超" if net>0 else "賣超", "net": net, "by_type": by_type, "src": "finmind"}
    except Exception: pass
    try:
        df = yf.Ticker(f"{stock_id}.TW").history(period="10d")
        if not df.empty and len(df) >= 3:
            r = df.tail(5)
            net_est = int(r[r["Close"]>r["Open"]]["Volume"].sum() - r[r["Close"]<=r["Open"]]["Volume"].sum())
            return {"status": "買超(估)" if net_est>0 else "賣超(估)", "net": net_est, "by_type": {}, "src": "yf_vol"}
    except Exception: pass
    return {"status": "無數據", "net": 0, "by_type": {}, "src": "none"}
def compute_signal_score(df):
    if df is None or len(df) < 20: return 0, {}
    latest, prev = df.iloc[-1], df.iloc[-2]
    signals, score = {}, 0
    close = float(latest["Close"])
    ma20 = latest.get("MA20")
    if pd.notna(ma20):
        ma20 = float(ma20)
        if close > ma20: signals["均線"] = (f"站上20MA({ma20:.0f})", +1); score += 1
        else:            signals["均線"] = (f"跌破20MA({ma20:.0f})", -1); score -= 1
    rsi = latest.get("RSI")
    if pd.notna(rsi):
        rsi = float(rsi)
        if rsi < 30:   signals["RSI"] = (f"RSI {rsi:.0f} 超賣", +1); score += 1
        elif rsi > 70: signals["RSI"] = (f"RSI {rsi:.0f} 超買", -1); score -= 1
        else:          signals["RSI"] = (f"RSI {rsi:.0f}", 0)
    mh = latest.get("MACD_Hist"); mhp = prev.get("MACD_Hist")
    if pd.notna(mh) and pd.notna(mhp):
        mh, mhp = float(mh), float(mhp)
        if mh > 0 and mhp <= 0:   signals["MACD"] = ("MACD柱翻紅 ★", +1); score += 1
        elif mh < 0 and mhp >= 0: signals["MACD"] = ("MACD柱翻綠", -1); score -= 1
        elif mh > 0:               signals["MACD"] = ("MACD柱擴大", +1); score += 1
        else:                      signals["MACD"] = ("MACD柱收縮", -1); score -= 1
    k = latest.get("K"); d = latest.get("D")
    kp = prev.get("K"); dp = prev.get("D")
    if pd.notna(k) and pd.notna(d) and pd.notna(kp) and pd.notna(dp):
        k, d, kp, dp = float(k), float(d), float(kp), float(dp)
        if k > d and kp <= dp and k < 80: signals["KD"] = (f"KD黃金交叉 K={k:.0f}", +1); score += 1
        elif k < d and kp >= dp and k > 20: signals["KD"] = (f"KD死亡交叉 K={k:.0f}", -1); score -= 1
        elif k < 20: signals["KD"] = (f"KD超賣 K={k:.0f}", +1); score += 1
        elif k > 80: signals["KD"] = (f"KD超買 K={k:.0f}", -1); score -= 1
    bbu = latest.get("BB_Upper"); bbl = latest.get("BB_Lower")
    if pd.notna(bbu) and pd.notna(bbl):
        bbu, bbl = float(bbu), float(bbl)
        if close < bbl:   signals["布林"] = ("觸布林下緣", +1); score += 1
        elif close > bbu: signals["布林"] = ("突布林上緣", -1); score -= 1
        else:
            bb_pct = (close-bbl)/(bbu-bbl)*100 if (bbu-bbl)>0 else 50
            signals["布林"] = (f"布林帶內 {bb_pct:.0f}%", 0)
    vol = latest.get("Volume"); vma = latest.get("Vol_MA5")
    if pd.notna(vol) and pd.notna(vma) and float(vma) > 0:
        vr = float(vol)/float(vma)
        if vr > 1.5 and close > float(prev["Close"]): signals["量能"] = (f"放量上漲 {vr:.1f}x", +1); score += 1
        elif vr > 1.5: signals["量能"] = (f"放量下跌 {vr:.1f}x", -1); score -= 1
        else:          signals["量能"] = (f"量能正常 {vr:.1f}x", 0)
    return max(-5, min(5, score)), signals

def calc_atr_stops(df, cost):
    latest = df.iloc[-1]
    atr = latest.get("ATR14")
    if not pd.notna(atr) or float(atr) == 0 or cost == 0: return None
    atr = float(atr); price = float(latest["Close"])
    sl_atr  = round(cost - 2.0 * atr, 1)
    tp1_atr = round(cost + 2.5 * atr, 1)
    tp2_atr = round(cost + 4.0 * atr, 1)
    trailing = round(float(df["Close"].tail(20).max()) - 2.0 * atr, 1)
    return {"atr": atr, "sl": sl_atr, "tp1": tp1_atr, "tp2": tp2_atr, "trailing": trailing,
            "sl_pct": round((sl_atr-cost)/cost*100,1),
            "tp1_pct": round((tp1_atr-cost)/cost*100,1),
            "tp2_pct": round((tp2_atr-cost)/cost*100,1)}

def classify(score, pnl, inst_status, df, cost):
    latest = df.iloc[-1]; prev = df.iloc[-2]
    atr_data = calc_atr_stops(df, cost) if cost > 0 else None
    price = float(latest["Close"]); is_sell_inst = "賣超" in inst_status
    k = latest.get("K"); d = latest.get("D"); kp = prev.get("K"); dp = prev.get("D")
    mh = latest.get("MACD_Hist"); mhp = prev.get("MACD_Hist")
    kd_golden = (pd.notna(k) and pd.notna(d) and pd.notna(kp) and pd.notna(dp) and float(k)>float(d) and float(kp)<=float(dp))
    macd_flip = (pd.notna(mh) and pd.notna(mhp) and float(mh)>0 and float(mhp)<=0)
    add_signal_ok = kd_golden or macd_flip
    sl_line = atr_data["sl"] if atr_data else (cost*0.90 if cost>0 else 0)
    sl_pct  = atr_data["sl_pct"] if atr_data else -10.0
    if cost > 0 and price <= sl_line:
        return "sell", "🛑 ATR停損出清", "bg-sell", f"現價({price:.0f})≤ATR停損線({sl_line:.0f}/{sl_pct:.1f}%)"
    if score <= -3 and is_sell_inst:
        return "sell", "🚨 技術+法人雙殺出清", "bg-sell", "評分-3且法人賣超"
    if pnl > 20 and score <= -2:
        ts = atr_data["trailing"] if atr_data else None
        return "sell", f"💰 移動停利出場 (+{pnl:.1f}%)", "bg-sell", f"獲利>{pnl:.0f}%且技術轉弱，Trailing Stop:{ts:.0f if ts else 'N/A'}"
    if score <= -2:
        return "sell", "📵 停損空手", "bg-sell", "技術評分≤-2，空手等訊號"
    if cost > 0 and sl_line < price < cost and pnl >= sl_pct and score >= 0:
        if add_signal_ok:
            sig = "KD黃金交叉" if kd_golden else "MACD柱翻紅"
            return "flat", f"✅ 佈局機會（{sig}確認）", "bg-flat", f"回踩支撐+{sig}，可小量加碼"
        return "flat", "⏳ 等待加碼確認訊號", "bg-flat", "無KD交叉/MACD翻紅，暫觀察"
    ts_line = atr_data["trailing"] if atr_data else None
    if pnl > 10 and score >= 1:
        ts_note = f"（移動停利:{ts_line:.0f}）" if ts_line else ""
        return "hold", f"🚀 讓利潤奔跑 (+{pnl:.1f}%){ts_note}", "bg-hold", "技術健康，守移動停利線"
    if score >= 1 or (pnl >= 0 and score >= 0):
        return "hold", "✅ 續抱", "bg-hold", "技術向上，持有"
    return "flat", "👁 觀察等待", "bg-watch", "訊號中性，守20MA"

def score_bar(score):
    bar = ""
    for i in range(-5, 6):
        if i == 0: bar += "│"
        elif score > 0 and 0 < i <= score: bar += "🟩"
        elif score < 0 and score <= i < 0: bar += "🟥"
        else: bar += "⬜"
    return bar
def collect_summary(sname, sid, cost):
    df = get_stock_history(sid); inst = get_institutional_data(sid)
    if df is None or df.empty: return None
    latest = df.iloc[-1]; price = float(latest["Close"])
    pnl = (price-cost)/cost*100 if cost > 0 else 0
    score, signals = compute_signal_score(df)
    cat, title, badge, reason = classify(score, pnl, inst["status"], df, cost)
    atr_data = calc_atr_stops(df, cost) if cost > 0 else None
    return {"name": sname, "sid": sid, "cost": cost, "price": price, "pnl": pnl,
            "score": score, "cat": cat, "title": title, "badge": badge, "reason": reason,
            "inst": inst, "signals": signals, "df": df, "atr": atr_data}


def render_detail(s):
    cost = s["cost"]; price = s["price"]; score = s["score"]; inst = s["inst"]; atr = s["atr"]
    st.markdown(f'<div class="badge {s["badge"]}">{s["title"]}<br><small style="font-weight:400;opacity:0.85">{s["reason"]}</small></div>', unsafe_allow_html=True)
    if atr:
        ts_info = f"　移動停利：<b>{atr['trailing']:.0f}</b>" if s["pnl"] > 5 else ""
        st.markdown(f'<div class="atr-box">📐 ATR(14)={atr["atr"]:.1f}　波動/日={atr["atr"]/price*100:.1f}%{ts_info}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sbar">空 {score_bar(score)} 多　評分 <b>{score:+d}/5</b></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("現價", f"{price:.1f}")
    c2.metric("損益", f"{s['pnl']:+.1f}%", delta=f"{price-cost:+.0f}" if cost>0 else "")
    inst_lbl = inst["status"] + ("⁺" if inst["src"]=="yf_vol" else "")
    c3.metric("法人", inst_lbl, delta=f"{inst['net']:+,}" if inst["net"]!=0 else "")
    if cost > 0 and atr:
        sl = atr["sl"]; tp1 = atr["tp1"]; tp2 = atr["tp2"]; ts = atr["trailing"]
        c_sl  = "#f85149" if price>sl  else "#3fb950"
        c_tp1 = "#3fb950" if price<tp1 else "#e3b341"
        c_tp2 = "#3fb950" if price<tp2 else "#58a6ff"
        html = '<div class="pgrid-4">'
        for lbl, val, diff, color in [
            (f"ATR停損\n{atr['sl_pct']:+.0f}%", sl,  price-sl,  c_sl),
            ("移動停利\n(近高-2ATR)",             ts,  price-ts,  "#e3b341"),
            (f"停利1\n{atr['tp1_pct']:+.0f}%",  tp1, price-tp1, c_tp1),
            (f"停利2\n{atr['tp2_pct']:+.0f}%",  tp2, price-tp2, c_tp2),
        ]:
            html += f'<div class="pbox"><span class="pl">{lbl}</span><span class="pv">{val:.0f}</span><span class="pd" style="color:{color}">{diff:+.0f}</span></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    with st.expander("📐 技術明細"):
        for ind, (msg, v) in s["signals"].items():
            st.write(f"{'🟢' if v>0 else ('🔴' if v<0 else '🟡')} **{ind}**：{msg}")
        l = s["df"].iloc[-1]
        rows = [
            ("ATR14",    f"{float(l['ATR14']):.2f}"   if pd.notna(l.get("ATR14"))     else "N/A"),
            ("RSI",      f"{float(l['RSI']):.1f}"     if pd.notna(l.get("RSI"))       else "N/A"),
            ("K/D",      f"{float(l['K']):.0f}/{float(l['D']):.0f}" if pd.notna(l.get("K")) else "N/A"),
            ("MACD柱",   f"{float(l['MACD_Hist']):.3f}" if pd.notna(l.get("MACD_Hist")) else "N/A"),
            ("20MA",     f"{float(l['MA20']):.0f}"    if pd.notna(l.get("MA20"))      else "N/A"),
            ("布林上/下", f"{float(l['BB_Upper']):.0f}/{float(l['BB_Lower']):.0f}" if pd.notna(l.get("BB_Upper")) else "N/A"),
        ]
        st.table(pd.DataFrame(rows, columns=["指標","值"]))
    with st.expander("🏦 法人籌碼"):
        note = "（備援：量能方向）" if inst["src"]=="yf_vol" else ""
        st.caption(f"來源：{inst['src']} {note}")
        if inst["by_type"]:
            for nt, nv in inst["by_type"].items():
                st.write(f"{'🟢' if nv>0 else '🔴'} **{nt}**：{int(nv):+,} 股")
        else:
            st.write(f"整體：**{inst['status']}**　淨量：{inst['net']:+,}")

    # ── AI 個股分析 ──
    provider, _ = get_ai_client()
    if provider:
        ai_key = f"ai_stock_{s['name']}_{s['price']:.0f}"
        if ai_key not in st.session_state:
            st.session_state[ai_key] = None
        col_btn, col_hint = st.columns([2, 3])
        with col_btn:
            if st.button(f"🤖 AI 分析 {s['name']}", key=f"btn_{ai_key}", use_container_width=True):
                with st.spinner("AI 分析中..."):
                    st.session_state[ai_key] = call_ai(build_stock_prompt(s))
        if st.session_state[ai_key]:
            st.markdown(f"""
            <div class="ai-box">
              <div class="ai-title">🤖 AI 綜合建議</div>
              <div class="ai-content">{st.session_state[ai_key]}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.caption("💡 設定 OPENAI_API_KEY 或 GEMINI_API_KEY 即可啟用 AI 個股分析")
@st.cache_data(ttl=3600)
def scan_picks():
    picks = []
    for sname, sid in SYMBOL_MAP.items():
        if sname in ETF_SET: continue
        try:
            df = get_stock_history(sid); inst = get_institutional_data(sid)
            if df is None or len(df) < 25: continue
            score, signals = compute_signal_score(df)
            if score < 3: continue
            latest = df.iloc[-1]; prev = df.iloc[-2]
            price = float(latest["Close"])
            rsi   = float(latest.get("RSI", 50)) if pd.notna(latest.get("RSI")) else 50
            ma20  = float(latest.get("MA20", 0)) if pd.notna(latest.get("MA20")) else 0
            vol   = float(latest.get("Volume", 0))
            vma   = float(latest.get("Vol_MA5", 1)) if float(latest.get("Vol_MA5", 1))>0 else 1
            vol_r = vol/vma
            mh    = float(latest.get("MACD_Hist", 0)) if pd.notna(latest.get("MACD_Hist")) else 0
            mhp   = float(prev.get("MACD_Hist", 0))   if pd.notna(prev.get("MACD_Hist"))   else 0
            squeeze = bool(latest.get("MA_Squeeze", False))
            atr   = float(latest.get("ATR14", 0)) if pd.notna(latest.get("ATR14")) else 0
            if rsi > 70 or rsi < 25: continue
            if ma20 > 0 and price < ma20: continue
            if vol_r < 1.2: continue
            macd_flip = (mh > 0 and mhp <= 0); breakout = squeeze; trigger = macd_flip or breakout
            atr_sl = round(price - 2*atr, 1) if atr > 0 else None
            df60 = df.tail(60); avg_chg = df60["Close"].pct_change().mean()*100
            if avg_chg > 0.05:
                est_d = int(10/avg_chg); payback = f"~{est_d}T({max(1,round(est_d/5))}w)"
            else: payback = "趨勢確認中"
            entry = round(float(ma20)*1.001, 1) if ma20>0 else round(price*0.99, 1)
            good  = [msg for _, (msg, v) in signals.items() if v>0]
            picks.append({"name": sname, "sid": sid, "price": price, "score": score,
                          "inst": inst["status"], "rsi": rsi, "vol_r": vol_r,
                          "entry": entry, "payback": payback, "reasons": good,
                          "atr_sl": atr_sl, "atr": atr,
                          "trigger": trigger, "macd_flip": macd_flip, "breakout": breakout})
        except Exception: continue
    picks.sort(key=lambda x: (int(x["trigger"]), x["score"], 1 if "買超" in x["inst"] else 0, x["vol_r"]), reverse=True)
    return picks[:8]

# ── 主 UI ──
now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
market  = get_market_data()
provider, _ = get_ai_client()
ai_available = provider is not None

ai_tag = "  🤖 AI" if ai_available else ""
ai_sub = "  |  AI分析已啟用" if ai_available else "  |  AI未設定"
st.markdown(f"""
<div class="hero-box">
  <div class="hero-title">📈 台股操盤 Pro{ai_tag}</div>
  <div class="hero-sub">{now_str}  |  ATR動態停損 · RSI · MACD · KD{ai_sub}</div>
</div>""", unsafe_allow_html=True)

with st.expander("🌐 大盤概況", expanded=False):
    if market:
        cols = st.columns(4)
        for i, (name, val) in enumerate(market.items()):
            chg = val["change"]
            cols[i].metric(name, f"{val['price']:.0f}" if val["price"]>1000 else f"{val['price']:.2f}",
                          f"{chg:+.2f}%", delta_color="normal" if chg>=0 else "inverse")
    tsm_chg = market.get("TSM ADR", {}).get("change", 0)
    sox_chg = market.get("費半",    {}).get("change", 0)
    if   tsm_chg > 1 and sox_chg > 1:   st.markdown('<div class="market-card" style="border-color:#3fb950">🔥 ADR+費半同步大漲</div>', unsafe_allow_html=True)
    elif tsm_chg < -1 and sox_chg < -1: st.markdown('<div class="market-card" style="border-color:#f85149">🚨 ADR+費半同步重挫</div>', unsafe_allow_html=True)
    elif tsm_chg > 1:  st.markdown('<div class="market-card" style="border-color:#3fb950">🎯 TSM ADR強勢</div>', unsafe_allow_html=True)
    elif tsm_chg < -1: st.markdown('<div class="market-card" style="border-color:#e3b341">⚠️ TSM ADR走弱</div>', unsafe_allow_html=True)
    else: st.markdown('<div class="market-card">📊 大盤平盤整理</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ 設定")
    uploaded_file = st.file_uploader("📂 匯入 CSV（未實現損益）", type="csv")
    st.markdown("---")
    st.markdown("### 🔍 單股查詢")
    manual_name = st.text_input("股票名稱", placeholder="台積電、鴻海...")
    manual_cost = st.number_input("持有成本", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    st.markdown("---")
    if ai_available:
        st.markdown(f"### 🤖 AI({provider.upper()}) ✅")
        st.caption("AI 分析已啟用")
    else:
        st.markdown("### 🤖 AI 分析")
        st.caption("設定 API Key 即可啟用")
        with st.expander("設定說明"):
            st.markdown(
                "**Streamlit Cloud Secrets 設定：**\n\n"
                "1. App 右下角 Manage app\n"
                "2. Settings → Secrets\n"
                "3. 貼入：\n"
                "   OPENAI_API_KEY = \"sk-...\"\n"
                "   或\n"
                "   GEMINI_API_KEY = \"AIza...\"\n"
                "4. 儲存後 App 自動重啟"
            )
    st.caption("⚠️ 僅供參考，投資需自負盈虧")
# ── 收集持股 ──
summaries = []
if uploaded_file:
    try:
        df_csv = pd.read_csv(uploaded_file)
        df_csv.columns = df_csv.columns.str.strip()
        if "成交均價" in df_csv.columns and "股票名稱" in df_csv.columns:
            df_csv["成交均價"] = pd.to_numeric(df_csv["成交均價"].astype(str).str.replace(",",""), errors="coerce")
            valid = [(str(r["股票名稱"]).strip(), r["成交均價"])
                     for _, r in df_csv.iterrows()
                     if str(r.get("股票名稱","")).strip() in SYMBOL_MAP]
            if valid:
                prog = st.progress(0, text="分析中...")
                for idx, (sn, cv) in enumerate(valid):
                    s = collect_summary(sn, SYMBOL_MAP[sn], float(cv))
                    if s: summaries.append(s)
                    prog.progress((idx+1)/len(valid), text=f"分析 {sn}...")
                prog.empty()
            else:
                st.warning("CSV 中股票名稱不在對照表內")
        else:
            st.error("CSV 需包含【股票名稱】與【成交均價】欄位")
    except Exception as e:
        st.error(f"CSV 讀取錯誤：{e}")
elif manual_name:
    if manual_name in SYMBOL_MAP:
        with st.spinner(f"分析 {manual_name}..."):
            s = collect_summary(manual_name, SYMBOL_MAP[manual_name], float(manual_cost))
        if s: summaries.append(s)
    else:
        st.sidebar.error(f"找不到 {manual_name}")

# ── 主標籤 ──
tab_hold, tab_pick = st.tabs(["📂 持有股", "🌟 推薦入手股"])

with tab_hold:
    if not summaries:
        st.markdown("""
        <div style="text-align:center;padding:50px 10px;color:#8b949e;">
          <div style="font-size:2.5rem">📂</div>
          <div style="font-size:0.92rem;margin-top:8px">左上角 >> 上傳 CSV 或輸入股票名稱</div>
        </div>""", unsafe_allow_html=True)
    else:
        sell_list = [s for s in summaries if s["cat"]=="sell"]
        flat_list = [s for s in summaries if s["cat"]=="flat"]
        hold_list = [s for s in summaries if s["cat"]=="hold"]
        sub1, sub2, sub3 = st.tabs([
            f"🛑 停損/出清 ({len(sell_list)})",
            f"⚖️ 佈局候機 ({len(flat_list)})",
            f"💎 續抱 ({len(hold_list)})",
        ])
        def render_list(lst, tab):
            with tab:
                if not lst: st.success("此類別目前無持股 👍"); return
                for s in sorted(lst, key=lambda x: x["pnl"]):
                    icon = "▼" if s["pnl"] < 0 else "▲"
                    with st.expander(f"{s['name']}  {s['price']:.0f}  {icon}{abs(s['pnl']):.1f}%", expanded=False):
                        render_detail(s)
        render_list(sell_list, sub1)
        render_list(flat_list, sub2)
        render_list(hold_list, sub3)

with tab_pick:
    st.markdown("""<div style="font-size:0.75rem;color:#8b949e;margin-bottom:6px;">
    篩選：評分>=3 · 站上20MA · RSI 25~70 · 量能>1.2x · 優先MACD翻紅/均線突破 · 排除ETF</div>""",
    unsafe_allow_html=True)
    with st.spinner("掃描中..."):
        picks = scan_picks()

    # AI 今日市場總覽
    if ai_available:
        ai_mkt_key = f"ai_market_{now_str}"
        if ai_mkt_key not in st.session_state:
            st.session_state[ai_mkt_key] = None
        if st.button("🤖 AI 今日市場總覽", use_container_width=True):
            with st.spinner("AI 分析今日市場..."):
                st.session_state[ai_mkt_key] = call_ai(build_market_prompt(picks, market))
        if st.session_state[ai_mkt_key]:
            st.markdown(f"""
            <div class="ai-market-box">
              <div class="ai-market-title">🤖 AI 今日市場總覽</div>
              <div class="ai-content">{st.session_state[ai_mkt_key]}</div>
            </div>""", unsafe_allow_html=True)

    if not picks:
        st.info("今日暫無強訊號標的（評分>=3+量能確認）")
        st.caption("市場可能整理中，等待入場時機")
    for p in picks:
        inst_icon = "🟢" if "買超" in p["inst"] else ("🔴" if "賣超" in p["inst"] else "⚪")
        trigger_badge = " 🔥MACD翻紅" if p["macd_flip"] else (" 💥均線突破" if p["breakout"] else "")
        atr_note = f"ATR停損:{p['atr_sl']}" if p["atr_sl"] else ""
        st.markdown(f"""
        <div class="pick-card">
          <div>
            <span class="pick-name">{p['name']}</span>
            <span class="pick-tag">{p['sid']}.TW</span>
            <span class="pick-score">評分 {p['score']:+d}/5</span>
          </div>
          <div class="pick-info">現價 {p['price']:.1f}  {inst_icon} {p['inst']}  RSI {p['rsi']:.0f}  量{p['vol_r']:.1f}x{trigger_badge}</div>
          <div class="pick-entry">📍 建議入手：{p['entry']}</div>
          <div class="pick-atr">{atr_note}  ⏱ +10%：{p['payback']}</div>
        </div>""", unsafe_allow_html=True)
        if p["reasons"]: st.caption("✅ " + "  ".join(p["reasons"][:3]))
        st.markdown("")

