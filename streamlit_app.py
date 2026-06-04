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
[data-testid="collapsedControl"]{display:none!important;}
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
.upload-box{background:#161b22;border:2px dashed #30363d;border-radius:10px;padding:12px 16px;margin-bottom:10px;}
.upload-title{font-size:0.85rem;color:#8b949e;font-weight:600;margin-bottom:6px;}
</style>
""", unsafe_allow_html=True)

# =============================================
# AI 分析模組（支援 OpenAI / Gemini，自動偵測）
# =============================================
def get_ai_client():
    try:
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
                    {"role": "system", "content": "你是一位專業的台股技術分析師。請用繁體中文，精簡扼要地回答，語氣直接務實，不要廢話，不要免責聲明。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI 錯誤: {e}"
    elif provider == "gemini":
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            body = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=body, timeout=15)
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            return f"Gemini 錯誤: {e}"
    return None

def build_stock_prompt(s: dict) -> str:
    lines = [
        f"股票：{s.get('name','')} ({s.get('ticker','')})",
        f"現價：{s.get('price',0):.1f}，成本：{s.get('cost',0):.1f}，損益：{s.get('pnl_pct',0):.1f}%",
        f"技術評分：{s.get('score',0)}",
        f"RSI14：{s.get('rsi',0):.1f}",
        f"MACD柱：{s.get('macd_hist',0):.3f}",
        f"KD K值：{s.get('k_val',0):.1f}，D值：{s.get('d_val',0):.1f}",
        f"ATR14：{s.get('atr',0):.2f}，動態停損線：{s.get('stop_price',0):.1f}",
        f"最高追蹤停利線：{s.get('trail_stop',0):.1f}",
        f"20MA：{s.get('ma20',0):.1f}，收盤在20MA{'上方' if s.get('above_ma20') else '下方'}",
        f"法人動向：{s.get('inst_note','')}",
        f"目前分類：{s.get('category','')}",
    ]
    prompt = "\n".join(lines)
    prompt += "\n\n請針對以上數據，給出3~5點操作建議（賣出/攤平/續抱/觀察），並說明理由。"
    return prompt

def build_market_prompt(picks: list, market: dict) -> str:
    m = market
    lines = [
        f"今日市場：費半{m.get('sox','')} {m.get('sox_chg','')}，納指{m.get('ndx','')} {m.get('ndx_chg','')}",
        f"TSM ADR：{m.get('tsm','')} {m.get('tsm_chg','')}，台指期：{m.get('twii','')} {m.get('twii_chg','')}",
        "\n今日推薦標的（技術評分高）：",
    ]
    for p in picks[:5]:
        lines.append(f"- {p.get('name','')} 評分{p.get('score',0)} 現價{p.get('price',0):.1f} RSI{p.get('rsi',0):.0f}")
    lines.append("\n請給出今日大盤簡評與操作策略方向，不超過150字。")
    return "\n".join(lines)


# =============================================
# 市場數據
# =============================================
@st.cache_data(ttl=1800)
def get_market_data():
    tickers = {"sox": "^SOX", "ndx": "^IXIC", "tsm": "TSM", "twii": "^TWII"}
    result = {}
    for k, sym in tickers.items():
        try:
            data = yf.download(sym, period="2d", interval="1d", progress=False, auto_adjust=True)
            if data.empty:
                result[k] = (0.0, 0.0)
                continue
            close = data["Close"]
            if hasattr(close, "squeeze"):
                close = close.squeeze()
            close = close.dropna()
            if len(close) < 2:
                result[k] = (float(close.iloc[-1]) if len(close) == 1 else 0.0, 0.0)
                continue
            latest = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            chg = (latest - prev) / prev * 100 if prev != 0 else 0.0
            result[k] = (latest, chg)
        except Exception:
            result[k] = (0.0, 0.0)
    return result

# =============================================
# 技術指標計算
# =============================================
def compute_indicators(ticker: str):
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if data.empty:
            return None
        close = data["Close"]
        if hasattr(close, "squeeze"):
            close = close.squeeze()
        close = close.dropna()
        high = data["High"]
        if hasattr(high, "squeeze"):
            high = high.squeeze()
        low = data["Low"]
        if hasattr(low, "squeeze"):
            low = low.squeeze()
        volume = data["Volume"]
        if hasattr(volume, "squeeze"):
            volume = volume.squeeze()

        if len(close) < 26:
            return None

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)

        # MACD
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_hist = macd_line - signal_line

        # KD
        low14 = low.rolling(14).min()
        high14 = high.rolling(14).max()
        rsv = (close - low14) / (high14 - low14 + 1e-9) * 100
        k_val = rsv.ewm(com=2).mean()
        d_val = k_val.ewm(com=2).mean()

        # 20MA
        ma20 = close.rolling(20).mean()

        # ATR
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()

        # Volume ratio
        vol_avg20 = volume.rolling(20).mean()
        vol_ratio = volume.iloc[-1] / vol_avg20.iloc[-1] if vol_avg20.iloc[-1] != 0 else 1.0

        price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2]) if len(close) >= 2 else price
        atr_val = float(atr14.iloc[-1])
        ma20_val = float(ma20.iloc[-1])
        rsi_val = float(rsi.iloc[-1])
        macd_h = float(macd_hist.iloc[-1])
        macd_h_prev = float(macd_hist.iloc[-2]) if len(macd_hist) >= 2 else macd_h
        k = float(k_val.iloc[-1])
        d = float(d_val.iloc[-1])
        k_prev = float(k_val.iloc[-2]) if len(k_val) >= 2 else k
        d_prev = float(d_val.iloc[-2]) if len(d_val) >= 2 else d

        # Recent high for trailing stop
        recent_high = float(close.rolling(20).max().iloc[-1])

        # MA squeeze breakout: 5MA, 10MA, 20MA close together then spread
        ma5 = float(close.rolling(5).mean().iloc[-1])
        ma10 = float(close.rolling(10).mean().iloc[-1])
        squeeze = abs(ma5 - ma20_val) / ma20_val < 0.03 and abs(ma10 - ma20_val) / ma20_val < 0.02

        return {
            "price": price,
            "prev_price": prev_price,
            "atr": atr_val,
            "ma20": ma20_val,
            "rsi": rsi_val,
            "macd_hist": macd_h,
            "macd_hist_prev": macd_h_prev,
            "k_val": k,
            "d_val": d,
            "k_prev": k_prev,
            "d_prev": d_prev,
            "vol_ratio": float(vol_ratio),
            "recent_high": recent_high,
            "squeeze": squeeze,
            "ma5": ma5,
            "ma10": ma10,
            "above_ma20": price > ma20_val,
        }
    except Exception:
        return None


# =============================================
# 法人動向估算
# =============================================
def get_institutional(ticker: str):
    try:
        stk = yf.Ticker(ticker)
        hist = stk.history(period="5d")
        if hist.empty:
            return None, "無數據"
        vol = hist["Volume"].iloc[-1]
        close = float(hist["Close"].iloc[-1])
        est_inst = vol * close * 0.15 / 1e8
        if est_inst > 2:
            note = f"估法人買超 {est_inst:.1f}億(估)"
        elif est_inst > 0.5:
            note = f"法人小幅參與 {est_inst:.1f}億(估)"
        else:
            note = "法人動向不明顯(估)"
        return est_inst, note
    except Exception:
        return None, "無法取得"

# =============================================
# 評分計算
# =============================================
def calc_score(ind: dict) -> int:
    score = 0
    rsi = ind["rsi"]
    macd_h = ind["macd_hist"]
    macd_h_prev = ind["macd_hist_prev"]
    k = ind["k_val"]
    d = ind["d_val"]
    k_prev = ind["k_prev"]
    d_prev = ind["d_prev"]
    price = ind["price"]
    ma20 = ind["ma20"]
    vol_ratio = ind["vol_ratio"]

    if rsi > 50: score += 1
    if rsi > 60: score += 1
    if rsi < 40: score -= 1
    if rsi < 30: score -= 1

    if macd_h > 0: score += 1
    if macd_h > macd_h_prev and macd_h > 0: score += 1
    if macd_h < 0 and macd_h < macd_h_prev: score -= 1
    if macd_h < 0 and macd_h_prev >= 0: score -= 2

    kd_cross_up = k > d and k_prev <= d_prev
    kd_cross_down = k < d and k_prev >= d_prev
    if kd_cross_up: score += 1
    if kd_cross_down: score -= 1
    if k > 70: score += 1
    if k < 30: score -= 1

    if price > ma20: score += 1
    else: score -= 1

    if vol_ratio > 1.5: score += 1
    elif vol_ratio > 1.2: score += 0

    return score

# =============================================
# 持有股分類
# =============================================
def classify_holding(ind: dict, cost: float) -> dict:
    price = ind["price"]
    atr = ind["atr"]
    pnl_pct = (price - cost) / cost * 100 if cost > 0 else 0

    # ATR 動態停損線
    atr_stop = cost - 2 * atr
    # 追蹤停利線
    trail_stop = ind["recent_high"] - 2 * atr

    score = calc_score(ind)

    macd_h = ind["macd_hist"]
    macd_h_prev = ind["macd_hist_prev"]
    k = ind["k_val"]
    d = ind["d_val"]
    k_prev = ind["k_prev"]
    d_prev = ind["d_prev"]
    above_ma20 = ind["above_ma20"]

    kd_cross_up = k > d and k_prev <= d_prev
    macd_flip_red = macd_h > 0 and macd_h_prev <= 0

    # 停損條件
    stop_triggered = price <= atr_stop
    trail_triggered = price <= trail_stop and pnl_pct > 10

    if stop_triggered or trail_triggered or score <= -2:
        cat = "sell"
    elif pnl_pct > 0 and above_ma20 and score >= 1:
        # 獲利中，技術良好 → 續抱
        cat = "hold"
    elif (kd_cross_up or macd_flip_red) and above_ma20 and pnl_pct > -15:
        # 有訊號回踩，且未深套 → 可考慮攤平
        cat = "flat"
    elif score >= 1 and above_ma20:
        cat = "hold"
    else:
        cat = "flat"

    return {
        "category": cat,
        "pnl_pct": pnl_pct,
        "atr_stop": atr_stop,
        "trail_stop": trail_stop,
        "score": score,
    }


# =============================================
# 推薦標的掃描
# =============================================
ETF_LIST = ["0050","0056","00878","00919","00936","006208","00881","00891","00896","00900"]

SCAN_TICKERS = [
    ("台積電","2330.TW"),("鴻海","2317.TW"),("聯發科","2454.TW"),("廣達","2382.TW"),
    ("緯創","3231.TW"),("技嘉","2376.TW"),("華碩","2357.TW"),("瑞昱","2379.TW"),
    ("聯詠","3034.TW"),("群聯","8299.TW"),("矽力-KY","6415.TW"),("世芯-KY","3661.TW"),
    ("創意","3443.TW"),("力積電","6770.TW"),("南亞科","2408.TW"),("旺宏","2337.TW"),
    ("欣興","3037.TW"),("臻鼎-KY","4958.TW"),("台光電","2383.TW"),("健鼎","3044.TW"),
    ("大立光","3008.TW"),("玉晶光","3406.TW"),("信驊","5274.TW"),("祥碩","5269.TW"),
    ("金像電","2368.TW"),("台達電","2308.TW"),("群創","3481.TW"),("友達","2409.TW"),
    ("奇鋐","3017.TW"),("建準","2421.TW"),("鈺創","5351.TW"),("威剛","3260.TW"),
    ("精成科","6510.TW"),("晶豐明源","6598.TW"),("力旺","3529.TW"),("智原","3035.TW"),
    ("金麗科","3228.TW"),("神盾","6462.TW"),("晶相光","3531.TW"),("鴻準","2354.TW"),
]

def scan_recommendations(held_tickers: list) -> list:
    picks = []
    for name, ticker in SCAN_TICKERS:
        code = ticker.replace(".TW","")
        if code in ETF_LIST or ticker in ETF_LIST:
            continue
        if ticker in held_tickers or code in held_tickers:
            continue
        ind = compute_indicators(ticker)
        if not ind:
            continue
        score = calc_score(ind)
        if score < 3:
            continue
        rsi = ind["rsi"]
        if rsi < 25 or rsi > 70:
            continue
        if not ind["above_ma20"]:
            continue
        if ind["vol_ratio"] < 1.2:
            continue
        # 優先篩選：MACD剛翻正 或 均線糾結突破
        macd_flip = ind["macd_hist"] > 0 and ind["macd_hist_prev"] <= 0
        squeeze_break = ind["squeeze"] and ind["price"] > ind["ma20"]
        priority = macd_flip or squeeze_break

        price = ind["price"]
        atr = ind["atr"]
        entry = round(price * 0.98, 1)
        stop = round(price - 2 * atr, 1)
        target = round(price * 1.10, 1)
        risk = price - stop
        reward = target - price
        rr = reward / risk if risk > 0 else 0

        # 回本預估（假設日均漲幅0.5%）
        if price > 0:
            days_to_profit = round(10 / 0.5) if rr > 1 else 99
        else:
            days_to_profit = 99

        picks.append({
            "name": name,
            "ticker": ticker,
            "price": price,
            "score": score,
            "rsi": rsi,
            "macd_hist": ind["macd_hist"],
            "k_val": ind["k_val"],
            "d_val": ind["d_val"],
            "atr": atr,
            "ma20": ind["ma20"],
            "above_ma20": ind["above_ma20"],
            "vol_ratio": ind["vol_ratio"],
            "entry": entry,
            "stop": stop,
            "target": target,
            "rr": rr,
            "days_to_profit": days_to_profit,
            "priority": priority,
            "macd_flip": macd_flip,
            "squeeze_break": squeeze_break,
            "inst_note": "",
        })

    picks.sort(key=lambda x: (x["priority"], x["score"], x["rsi"]), reverse=True)
    return picks[:8]


# =============================================
# 主介面
# =============================================
# AI 狀態
ai_provider, ai_key = get_ai_client()
ai_enabled = ai_provider is not None
ai_badge = "🤖 AI已連線" if ai_enabled else "🔑 AI未設定"

st.markdown(f"""
<div class="hero-box">
  <div class="hero-title">📈 台股操盤 Pro &nbsp;<span style="font-size:0.7rem;color:#{'3fb950' if ai_enabled else 'e3b341'};">{ai_badge}</span></div>
  <div class="hero-sub">{datetime.datetime.now().strftime('%Y/%m/%d %H:%M')} 更新</div>
</div>
""", unsafe_allow_html=True)

# =============================================
# 市場指標（折疊）
# =============================================
with st.expander("📊 今日大盤指標", expanded=False):
    mkt = get_market_data()
    c1, c2, c3, c4 = st.columns(4)
    def fmt_delta(chg):
        arrow = "↑" if chg >= 0 else "↓"
        color = "#3fb950" if chg >= 0 else "#f85149"
        return f'<span style="color:{color};font-size:0.8rem;">{arrow} {abs(chg):.2f}%</span>'

    sox_v, sox_c = mkt.get("sox", (0.0, 0.0))
    ndx_v, ndx_c = mkt.get("ndx", (0.0, 0.0))
    tsm_v, tsm_c = mkt.get("tsm", (0.0, 0.0))
    twii_v, twii_c = mkt.get("twii", (0.0, 0.0))

    with c1:
        st.markdown(f"**費半**\n### {sox_v:,.0f}\n{fmt_delta(sox_c)}", unsafe_allow_html=True)
    with c2:
        st.markdown(f"**納指**\n### {ndx_v:,.0f}\n{fmt_delta(ndx_c)}", unsafe_allow_html=True)
    with c3:
        st.markdown(f"**TSM ADR**\n### {tsm_v:.2f}\n{fmt_delta(tsm_c)}", unsafe_allow_html=True)
    with c4:
        st.markdown(f"**台指**\n### {twii_v:,.0f}\n{fmt_delta(twii_c)}", unsafe_allow_html=True)

    mkt_data_for_ai = {
        "sox": f"{sox_v:,.0f}", "sox_chg": f"{sox_c:+.2f}%",
        "ndx": f"{ndx_v:,.0f}", "ndx_chg": f"{ndx_c:+.2f}%",
        "tsm": f"{tsm_v:.2f}", "tsm_chg": f"{tsm_c:+.2f}%",
        "twii": f"{twii_v:,.0f}", "twii_chg": f"{twii_c:+.2f}%",
    }
else:
    mkt_data_for_ai = {}

# =============================================
# 匯入 CSV（直接在主介面，不用 sidebar）
# =============================================
with st.expander("📂 匯入持股 CSV", expanded=True):
    st.markdown('<div class="upload-title">請上傳持股 CSV（欄位：股票代號, 名稱, 成本價, 持有張數）</div>', unsafe_allow_html=True)
    st.caption("CSV 格式範例：2330, 台積電, 1000, 2")
    uploaded = st.file_uploader("選擇 CSV 檔案", type=["csv"], label_visibility="collapsed")

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded, header=None)
        df.columns = ["ticker","name","cost","shares"][:len(df.columns)]
        df["ticker"] = df["ticker"].astype(str).str.strip()
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0)
        df["shares"] = pd.to_numeric(df["shares"], errors="coerce").fillna(0)
        st.session_state["holdings"] = df.to_dict("records")
        st.success(f"✅ 已載入 {len(df)} 筆持股")
    except Exception as e:
        st.error(f"CSV 解析失敗：{e}")

holdings = st.session_state.get("holdings", [])


# =============================================
# 主標籤頁
# =============================================
tab_hold, tab_pick = st.tabs(["📂 持有股", "🌟 推薦入手股"])

# =============================================
# 持有股標籤
# =============================================
with tab_hold:
    if not holdings:
        st.info("尚未匯入持股，請展開上方「📂 匯入持股 CSV」上傳檔案。")
    else:
        sell_list, flat_list, hold_list = [], [], []

        for h in holdings:
            raw_ticker = str(h["ticker"]).strip()
            ticker = raw_ticker if raw_ticker.endswith(".TW") else raw_ticker + ".TW"
            name = h.get("name", raw_ticker)
            cost = float(h.get("cost", 0))
            shares = float(h.get("shares", 0))

            ind = compute_indicators(ticker)
            if not ind:
                flat_list.append({"name": name, "ticker": ticker, "cost": cost, "shares": shares,
                                   "price": 0, "pnl_pct": 0, "score": 0, "category": "flat",
                                   "atr_stop": 0, "trail_stop": 0, "inst_note": "無法取得", "ind": None})
                continue

            cls = classify_holding(ind, cost)
            inst_val, inst_note = get_institutional(ticker)
            price = ind["price"]
            score = cls["score"]

            stock_data = {
                "name": name, "ticker": ticker, "cost": cost, "shares": shares,
                "price": price, "pnl_pct": cls["pnl_pct"], "score": score,
                "category": cls["category"], "atr_stop": cls["atr_stop"],
                "trail_stop": cls["trail_stop"], "inst_note": inst_note,
                "rsi": ind["rsi"], "macd_hist": ind["macd_hist"],
                "k_val": ind["k_val"], "d_val": ind["d_val"],
                "atr": ind["atr"], "ma20": ind["ma20"],
                "above_ma20": ind["above_ma20"], "stop_price": cls["atr_stop"],
                "ind": ind,
            }
            if cls["category"] == "sell":
                sell_list.append(stock_data)
            elif cls["category"] == "flat":
                flat_list.append(stock_data)
            else:
                hold_list.append(stock_data)

        sub1, sub2, sub3 = st.tabs([
            f"🛑 賣出/停損 ({len(sell_list)})",
            f"⚖️ 攤平 ({len(flat_list)})",
            f"💎 續抱 ({len(hold_list)})"
        ])

        def render_stock_card(s, tab_key=""):
            pnl = s["pnl_pct"]
            pnl_color = "#3fb950" if pnl >= 0 else "#f85149"
            cat = s["category"]
            badge_class = "bg-sell" if cat == "sell" else ("bg-flat" if cat == "flat" else "bg-hold")
            cat_label = "賣出/停損" if cat == "sell" else ("攤平" if cat == "flat" else "續抱")

            label = f"{s['name']}  {s['price']:.1f}  {pnl:+.2f}%"
            with st.expander(label, expanded=False):
                st.markdown(f'<div class="badge {badge_class}">建議：{cat_label} ｜ 評分 {s["score"]:+d}</div>', unsafe_allow_html=True)
                st.markdown(f"""
<div class="pgrid-4">
  <div class="pbox"><span class="pl">現價</span><span class="pv">{s['price']:.1f}</span></div>
  <div class="pbox"><span class="pl">成本</span><span class="pv">{s['cost']:.1f}</span></div>
  <div class="pbox"><span class="pl">損益</span><span class="pv" style="color:{pnl_color};">{pnl:+.1f}%</span></div>
  <div class="pbox"><span class="pl">張數</span><span class="pv">{s['shares']:.0f}</span></div>
</div>
<div class="atr-box">
  🛡️ ATR停損線：<b>{s['atr_stop']:.1f}</b> ｜ 追蹤停利線：<b>{s['trail_stop']:.1f}</b>
</div>
<div class="sbar">
  RSI: {s['rsi']:.1f} ｜ MACD柱: {s['macd_hist']:.3f} ｜ K: {s['k_val']:.1f} D: {s['d_val']:.1f}
  ｜ 20MA: {s['ma20']:.1f} ({'✅上方' if s['above_ma20'] else '❌下方'})
</div>
<div style="font-size:0.78rem;color:#8b949e;margin-top:4px;">📋 法人：{s['inst_note']}</div>
""", unsafe_allow_html=True)
                if ai_enabled:
                    btn_key = f"ai_{s['ticker']}_{tab_key}"
                    if st.button(f"🤖 AI 分析 {s['name']}", key=btn_key):
                        with st.spinner("AI 分析中..."):
                            prompt = build_stock_prompt(s)
                            result = call_ai(prompt)
                        if result:
                            st.markdown(f'<div class="ai-box"><div class="ai-title">🤖 AI 分析結果</div><div class="ai-content">{result}</div></div>', unsafe_allow_html=True)
                        else:
                            st.warning("AI 回傳空值，請重試")
                else:
                    st.caption("🔑 設定 API Key 後可啟用 AI 分析（見下方說明）")

        with sub1:
            if sell_list:
                for s in sell_list:
                    render_stock_card(s, "sell")
            else:
                st.success("✅ 目前無需賣出/停損的持股")

        with sub2:
            if flat_list:
                for s in flat_list:
                    render_stock_card(s, "flat")
            else:
                st.success("✅ 目前無需攤平的持股")

        with sub3:
            if hold_list:
                for s in hold_list:
                    render_stock_card(s, "hold")
            else:
                st.info("目前無續抱標的")


# =============================================
# 推薦入手股標籤
# =============================================
with tab_pick:
    held_tickers = []
    for h in holdings:
        t = str(h["ticker"]).strip()
        held_tickers.append(t)
        held_tickers.append(t + ".TW")
        held_tickers.append(t.replace(".TW",""))

    st.caption("依技術評分排序（評分>=3），優先顯示 MACD翻正 或 均線糾結突破 標的")

    if st.button("🔄 掃描推薦標的", type="primary"):
        with st.spinner("掃描中，約需 30~60 秒..."):
            picks = scan_recommendations(held_tickers)
            st.session_state["picks"] = picks

    picks = st.session_state.get("picks", [])

    if picks:
        if ai_enabled:
            if st.button("🤖 AI 今日市場總覽"):
                with st.spinner("AI 分析市場..."):
                    prompt = build_market_prompt(picks, mkt_data_for_ai if mkt_data_for_ai else {})
                    result = call_ai(prompt)
                if result:
                    st.markdown(f'<div class="ai-market-box"><div class="ai-market-title">AI 今日市場總覽</div><div class="ai-content">{result}</div></div>', unsafe_allow_html=True)
        else:
            st.caption("設定 API Key 後可啟用 AI 市場總覽（見下方說明）")

        for p in picks:
            priority_tag = ""
            if p.get("macd_flip"):
                priority_tag = "MACD翻正"
            elif p.get("squeeze_break"):
                priority_tag = "均線突破"

            label_prefix = "⭐ " if p["priority"] else ""
            with st.expander(
                label_prefix + p["name"] + "  " + p["ticker"] + "  評分 +" + str(p["score"]),
                expanded=p["priority"]
            ):
                priority_html = ""
                if priority_tag:
                    priority_html = '<span style="background:#0d3d1a;color:#3fb950;border-radius:4px;padding:2px 7px;font-size:0.72rem;margin-left:6px;">' + priority_tag + "</span>"
                st.markdown(
                    '<div class="pick-card">'
                    + '<span class="pick-name">' + p["name"] + "</span>"
                    + '<span class="pick-tag">' + p["ticker"] + "</span>"
                    + '<span class="pick-score">評分 +' + str(p["score"]) + "</span>"
                    + priority_html
                    + '<div class="pick-info">現價 ' + f"{p['price']:.1f}" + " | RSI " + f"{p['rsi']:.0f}" + " | 成交量比 " + f"{p['vol_ratio']:.1f}" + "x | 20MA " + f"{p['ma20']:.1f}" + "</div>"
                    + '<div class="pick-entry">📍 建議入手：' + f"{p['entry']:.1f}" + "</div>"
                    + '<div class="pick-atr">🛡️ 停損：' + f"{p['stop']:.1f}" + "（-2ATR） | 目標：" + f"{p['target']:.1f}" + "（+10%） | 風報比 " + f"{p['rr']:.1f}" + "</div>"
                    + '<div style="font-size:0.78rem;color:#8b949e;margin-top:5px;">🕐 預計到達目標：約 ' + str(p["days_to_profit"]) + " 個交易日（估）</div>"
                    + "</div>",
                    unsafe_allow_html=True
                )

                if ai_enabled:
                    if st.button("🤖 AI 分析 " + p["name"], key="ai_pick_" + p["ticker"]):
                        with st.spinner("AI 分析中..."):
                            prompt = build_stock_prompt({**p, "cost": p["price"], "pnl_pct": 0, "stop_price": p["stop"], "trail_stop": p["stop"], "inst_note": ""})
                            result = call_ai(prompt)
                        if result:
                            st.markdown('<div class="ai-box"><div class="ai-title">AI 分析結果</div><div class="ai-content">' + result + "</div></div>", unsafe_allow_html=True)
    else:
        st.info("點擊上方「🔄 掃描推薦標的」按鈕開始掃描")


# =============================================
# AI 設定說明（若未設定 API Key）
# =============================================
if not ai_enabled:
    with st.expander("🔑 如何啟用 AI 分析功能", expanded=False):
        st.markdown("**步驟：**")
        st.markdown("1. 進入 Streamlit Cloud → 你的 App → **Manage app**（右下角）")
        st.markdown("2. 點 **Settings** → **Secrets**")
        st.markdown("3. 貼上以下任一 API Key（擇一即可）")
        st.markdown("**使用 OpenAI（GPT-4o-mini）：**")
        st.code('OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"', language="toml")
        st.markdown("**或使用 Gemini（免費）：**")
        st.code('GEMINI_API_KEY = "AIzaxxxxxxxxxxxxxxxxxxxxxxxx"', language="toml")
        st.markdown("4. 點 **Save** → App 自動重新啟動")
        st.markdown("5. 重啟後出現 **AI已連線** 即成功")
        st.markdown("**取得 API Key：**")
        st.markdown("- OpenAI：https://platform.openai.com/api-keys")
        st.markdown("- Gemini（免費）：https://aistudio.google.com/app/apikey")
