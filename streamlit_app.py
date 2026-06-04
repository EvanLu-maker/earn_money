import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import numpy as np
import io

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
.pgrid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin:8px 0;}
.pbox{background:#21262d;border-radius:7px;padding:7px 8px;text-align:center;}
.pbox .pl{font-size:0.6rem;color:#8b949e;text-transform:uppercase;display:block;}
.pbox .pv{font-size:0.92rem;font-weight:700;color:#e6edf3;display:block;}
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
hr{border-color:#21262d!important;margin:10px 0!important;}
</style>
""", unsafe_allow_html=True)

# =============================================
# AI 模組 - Gemini Key 內建（可在 Streamlit Secrets 覆蓋）
# =============================================
HARDCODED_GEMINI_KEY = "AIzaSyArdjlQ5Wm6ZWtlatjq_OUM7PreYfIIK-o"

def get_ai_client():
    # 優先用 Streamlit Secrets，否則用內建 key
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
    # 內建 fallback key
    if HARDCODED_GEMINI_KEY:
        return "gemini", HARDCODED_GEMINI_KEY
    return None, None

def call_ai(prompt):
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
                    {"role": "system", "content": "你是台股技術分析師。用繁體中文，精簡直接回答，不要免責聲明。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return "OpenAI錯誤: " + str(e)
    elif provider == "gemini":
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + key
            headers = {"Content-Type": "application/json"}
            body = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=body, headers=headers, timeout=20)
            data = resp.json()
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            elif "error" in data:
                return "Gemini錯誤: " + data["error"].get("message","未知錯誤")
            return "Gemini回傳格式異常"
        except Exception as e:
            return "Gemini錯誤: " + str(e)
    return None

def build_stock_prompt(s):
    lines = [
        "股票：" + s.get("name","") + " (" + s.get("ticker","") + ")",
        "現價：" + str(round(s.get("price",0),1)) + "，成本：" + str(round(s.get("cost",0),1)) + "，損益：" + str(round(s.get("pnl_pct",0),1)) + "%",
        "技術評分：" + str(s.get("score",0)),
        "RSI14：" + str(round(s.get("rsi",0),1)),
        "MACD柱：" + str(round(s.get("macd_hist",0),3)),
        "KD K：" + str(round(s.get("k_val",0),1)) + " D：" + str(round(s.get("d_val",0),1)),
        "ATR14：" + str(round(s.get("atr",0),2)) + "，動態停損：" + str(round(s.get("stop_price",0),1)),
        "20MA：" + str(round(s.get("ma20",0),1)) + "，收盤在20MA" + ("上方" if s.get("above_ma20") else "下方"),
        "法人動向：" + s.get("inst_note",""),
        "目前分類：" + s.get("category",""),
        "",
        "請針對以上數據，給出3~5點操作建議（賣出/攤平/續抱/觀察），說明理由。",
    ]
    return "\n".join(lines)

def build_market_prompt(picks, market):
    lines = [
        "今日市場：費半" + market.get("sox","?") + " " + market.get("sox_chg","") + "，納指" + market.get("ndx","?") + " " + market.get("ndx_chg",""),
        "TSM ADR：" + market.get("tsm","?") + " " + market.get("tsm_chg","") + "，台指：" + market.get("twii","?") + " " + market.get("twii_chg",""),
        "", "今日推薦標的：",
    ]
    for p in picks[:5]:
        lines.append("- " + p.get("name","") + " 評分" + str(p.get("score",0)) + " 現價" + str(round(p.get("price",0),1)) + " RSI" + str(round(p.get("rsi",0),0)))
    lines.append("")
    lines.append("請給出今日大盤簡評與操作策略方向，不超過150字。")
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
# 技術指標
# =============================================
def compute_indicators(ticker):
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

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)

        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        macd_hist = macd_line - signal_line

        low14 = low.rolling(14).min()
        high14 = high.rolling(14).max()
        rsv = (close - low14) / (high14 - low14 + 1e-9) * 100
        k_val = rsv.ewm(com=2).mean()
        d_val = k_val.ewm(com=2).mean()

        ma20 = close.rolling(20).mean()
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()

        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs()
        ], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()

        vol_avg20 = volume.rolling(20).mean()
        vol_ratio = volume.iloc[-1] / vol_avg20.iloc[-1] if vol_avg20.iloc[-1] != 0 else 1.0

        price = float(close.iloc[-1])
        atr_val = float(atr14.iloc[-1])
        ma20_val = float(ma20.iloc[-1])
        ma5_val = float(ma5.iloc[-1])
        ma10_val = float(ma10.iloc[-1])
        rsi_val = float(rsi.iloc[-1])
        macd_h = float(macd_hist.iloc[-1])
        macd_h_prev = float(macd_hist.iloc[-2]) if len(macd_hist) >= 2 else macd_h
        k = float(k_val.iloc[-1])
        d = float(d_val.iloc[-1])
        k_prev = float(k_val.iloc[-2]) if len(k_val) >= 2 else k
        d_prev = float(d_val.iloc[-2]) if len(d_val) >= 2 else d
        recent_high = float(close.rolling(20).max().iloc[-1])
        squeeze = abs(ma5_val - ma20_val) / ma20_val < 0.03 and abs(ma10_val - ma20_val) / ma20_val < 0.02

        return {
            "price": price, "atr": atr_val, "ma20": ma20_val,
            "ma5": ma5_val, "ma10": ma10_val, "rsi": rsi_val,
            "macd_hist": macd_h, "macd_hist_prev": macd_h_prev,
            "k_val": k, "d_val": d, "k_prev": k_prev, "d_prev": d_prev,
            "vol_ratio": float(vol_ratio), "recent_high": recent_high,
            "squeeze": squeeze, "above_ma20": price > ma20_val,
        }
    except Exception:
        return None


# =============================================
# 法人估算
# =============================================
def get_institutional(ticker):
    try:
        stk = yf.Ticker(ticker)
        hist = stk.history(period="5d")
        if hist.empty:
            return None, "無數據"
        vol = hist["Volume"].iloc[-1]
        close_p = float(hist["Close"].iloc[-1])
        est = vol * close_p * 0.15 / 1e8
        if est > 2:
            note = "估法人買超 " + str(round(est,1)) + "億(估)"
        elif est > 0.5:
            note = "法人小幅參與 " + str(round(est,1)) + "億(估)"
        else:
            note = "法人動向不明顯(估)"
        return est, note
    except Exception:
        return None, "無法取得"

# =============================================
# 評分
# =============================================
def calc_score(ind):
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
    if macd_h > 0 and macd_h > macd_h_prev: score += 1
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
    return score

# =============================================
# 持有股分類
# =============================================
def classify_holding(ind, cost):
    price = ind["price"]
    atr = ind["atr"]
    pnl_pct = (price - cost) / cost * 100 if cost > 0 else 0
    atr_stop = cost - 2 * atr
    trail_stop = ind["recent_high"] - 2 * atr
    score = calc_score(ind)

    k = ind["k_val"]
    d = ind["d_val"]
    k_prev = ind["k_prev"]
    d_prev = ind["d_prev"]
    macd_h = ind["macd_hist"]
    macd_h_prev = ind["macd_hist_prev"]
    above_ma20 = ind["above_ma20"]

    kd_cross_up = k > d and k_prev <= d_prev
    macd_flip_red = macd_h > 0 and macd_h_prev <= 0
    stop_triggered = price <= atr_stop
    trail_triggered = price <= trail_stop and pnl_pct > 10

    if stop_triggered or trail_triggered or score <= -2:
        cat = "sell"
    elif pnl_pct > 0 and above_ma20 and score >= 1:
        cat = "hold"
    elif (kd_cross_up or macd_flip_red) and above_ma20 and pnl_pct > -15:
        cat = "flat"
    elif score >= 1 and above_ma20:
        cat = "hold"
    else:
        cat = "flat"

    return {"category": cat, "pnl_pct": pnl_pct, "atr_stop": atr_stop, "trail_stop": trail_stop, "score": score}


# =============================================
# 推薦標的掃描
# =============================================
ETF_LIST = ["0050","0056","00878","00919","00936","006208","00881","00891","00896","00900"]

SCAN_TICKERS = [
    ("台積電","2330.TW"),("鴻海","2317.TW"),("聯發科","2454.TW"),("廣達","2382.TW"),
    ("緯創","3231.TW"),("技嘉","2376.TW"),("華碩","2357.TW"),("瑞昱","2379.TW"),
    ("聯詠","3034.TW"),("群聯","8299.TW"),("矽力-KY","6415.TW"),("世芯-KY","3661.TW"),
    ("創意","3443.TW"),("力積電","6770.TW"),("南亞科","2408.TW"),("旺宏","2337.TW"),
    ("欣興","3037.TW"),("台光電","2383.TW"),("健鼎","3044.TW"),("大立光","3008.TW"),
    ("信驊","5274.TW"),("祥碩","5269.TW"),("金像電","2368.TW"),("台達電","2308.TW"),
    ("群創","3481.TW"),("友達","2409.TW"),("奇鋐","3017.TW"),("建準","2421.TW"),
    ("力旺","3529.TW"),("智原","3035.TW"),("神盾","6462.TW"),("鴻準","2354.TW"),
    ("緯穎","6669.TW"),("英業達","2356.TW"),("仁寶","2324.TW"),("光寶科","2301.TW"),
    ("敦泰","3545.TW"),("晶相光","3531.TW"),("玉晶光","3406.TW"),("臻鼎-KY","4958.TW"),
]

def scan_recommendations(held_tickers):
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
        rr = round(reward / risk, 1) if risk > 0 else 0

        picks.append({
            "name": name, "ticker": ticker, "price": price,
            "score": score, "rsi": rsi,
            "macd_hist": ind["macd_hist"], "macd_hist_prev": ind["macd_hist_prev"],
            "k_val": ind["k_val"], "d_val": ind["d_val"],
            "atr": atr, "ma20": ind["ma20"], "above_ma20": True,
            "vol_ratio": ind["vol_ratio"],
            "entry": entry, "stop": stop, "target": target, "rr": rr,
            "days_to_profit": 20,
            "priority": priority, "macd_flip": macd_flip, "squeeze_break": squeeze_break,
            "inst_note": "",
        })

    picks.sort(key=lambda x: (int(x["priority"]), x["score"]), reverse=True)
    return picks[:8]


# =============================================
# CSV 解析 - 寬鬆版，支援多種格式
# =============================================
def parse_holdings_csv(raw_bytes):
    """
    支援格式：
    - 逗號/Tab/空白分隔
    - 有無表頭
    - BIG5 / UTF-8 / UTF-8-BOM 編碼
    - 欄位順序：代號, 名稱, 成本, 張數（至少需要代號+成本）
    """
    errors = []
    # 嘗試多種編碼
    for enc in ["utf-8-sig", "utf-8", "big5", "cp950", "latin1"]:
        try:
            text = raw_bytes.decode(enc)
            break
        except Exception:
            text = None
    if text is None:
        return None, "無法解碼檔案，請確認編碼為 UTF-8 或 BIG5"

    # 嘗試多種分隔符
    for sep in [",", "\t", "\s+", ";"]:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, header=None, engine="python", dtype=str)
            df = df.dropna(how="all")
            if df.shape[1] < 2:
                continue
            # 移除可能的表頭行（第一欄非數字就是表頭）
            first_val = str(df.iloc[0, 0]).strip()
            if not first_val.replace(".","").isdigit():
                df = df.iloc[1:].reset_index(drop=True)
            if df.empty:
                continue
            # 指派欄位
            cols = list(df.columns)
            result = pd.DataFrame()
            result["ticker"] = df.iloc[:, 0].astype(str).str.strip().str.replace(" ","")
            if df.shape[1] >= 4:
                result["name"] = df.iloc[:, 1].astype(str).str.strip()
                result["cost"] = pd.to_numeric(df.iloc[:, 2], errors="coerce").fillna(0)
                result["shares"] = pd.to_numeric(df.iloc[:, 3], errors="coerce").fillna(1)
            elif df.shape[1] == 3:
                result["name"] = df.iloc[:, 1].astype(str).str.strip()
                result["cost"] = pd.to_numeric(df.iloc[:, 2], errors="coerce").fillna(0)
                result["shares"] = 1
            elif df.shape[1] == 2:
                result["name"] = result["ticker"]
                result["cost"] = pd.to_numeric(df.iloc[:, 1], errors="coerce").fillna(0)
                result["shares"] = 1
            # 過濾無效行
            result = result[result["cost"] > 0]
            if result.empty:
                continue
            return result, None
        except Exception as ex:
            errors.append(str(ex))
            continue

    return None, "解析失敗，請確認格式為：代號, 名稱, 成本價, 張數\n錯誤：" + " / ".join(errors[:2])


# =============================================
# 主介面
# =============================================
ai_provider, ai_key = get_ai_client()
ai_enabled = ai_provider is not None
ai_badge = "AI已連線" if ai_enabled else "AI未設定"
ai_color = "3fb950" if ai_enabled else "e3b341"

st.markdown(
    '<div class="hero-box">'
    + '<div class="hero-title">📈 台股操盤 Pro &nbsp;<span style="font-size:0.7rem;color:#' + ai_color + ';">' + ai_badge + '</span></div>'
    + '<div class="hero-sub">' + datetime.datetime.now().strftime("%Y/%m/%d %H:%M") + ' 更新</div>'
    + '</div>',
    unsafe_allow_html=True
)

# 市場數據（先取，不在 expander 內部）
mkt = get_market_data()
sox_v, sox_c = mkt.get("sox", (0.0, 0.0))
ndx_v, ndx_c = mkt.get("ndx", (0.0, 0.0))
tsm_v, tsm_c = mkt.get("tsm", (0.0, 0.0))
twii_v, twii_c = mkt.get("twii", (0.0, 0.0))
mkt_data_for_ai = {
    "sox": str(round(sox_v,0)), "sox_chg": ("+" if sox_c >= 0 else "") + str(round(sox_c,2)) + "%",
    "ndx": str(round(ndx_v,0)), "ndx_chg": ("+" if ndx_c >= 0 else "") + str(round(ndx_c,2)) + "%",
    "tsm": str(round(tsm_v,2)), "tsm_chg": ("+" if tsm_c >= 0 else "") + str(round(tsm_c,2)) + "%",
    "twii": str(round(twii_v,0)), "twii_chg": ("+" if twii_c >= 0 else "") + str(round(twii_c,2)) + "%",
}

def fmt_delta(chg):
    arrow = "↑" if chg >= 0 else "↓"
    color = "#3fb950" if chg >= 0 else "#f85149"
    return '<span style="color:' + color + ';font-size:0.8rem;">' + arrow + " " + str(abs(round(chg,2))) + "%" + "</span>"

with st.expander("📊 今日大盤指標", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**費半**\n### " + str(int(sox_v)) + "\n" + fmt_delta(sox_c), unsafe_allow_html=True)
    with c2:
        st.markdown("**納指**\n### " + str(int(ndx_v)) + "\n" + fmt_delta(ndx_c), unsafe_allow_html=True)
    with c3:
        st.markdown("**TSM ADR**\n### " + str(round(tsm_v,2)) + "\n" + fmt_delta(tsm_c), unsafe_allow_html=True)
    with c4:
        st.markdown("**台指**\n### " + str(int(twii_v)) + "\n" + fmt_delta(twii_c), unsafe_allow_html=True)

# =============================================
# 匯入 CSV
# =============================================
with st.expander("📂 匯入持股 CSV", expanded=True):
    st.caption("支援格式：代號,名稱,成本,張數（逗號/Tab分隔，UTF-8 或 BIG5 編碼）")
    st.caption("最少只需兩欄：代號, 成本價")
    uploaded = st.file_uploader("選擇 CSV 檔案", type=["csv","txt"], label_visibility="collapsed")

if uploaded is not None:
    raw = uploaded.read()
    df_parsed, err = parse_holdings_csv(raw)
    if err:
        st.error("❌ CSV解析失敗：" + err)
        st.info("格式範例（逗號分隔，可無表頭）：\n2330, 台積電, 1000, 2\n2317, 鴻海, 200, 5")
    else:
        st.session_state["holdings"] = df_parsed.to_dict("records")
        st.success("✅ 已載入 " + str(len(df_parsed)) + " 筆持股：" + "、".join(df_parsed["name"].tolist()[:5]))

holdings = st.session_state.get("holdings", [])


# =============================================
# 主標籤頁
# =============================================
tab_hold, tab_pick = st.tabs(["📂 持有股", "🌟 推薦入手股"])

with tab_hold:
    if not holdings:
        st.info("尚未匯入持股，請展開上方「📂 匯入持股 CSV」上傳檔案。")
    else:
        sell_list, flat_list, hold_list = [], [], []

        for h in holdings:
            raw_ticker = str(h["ticker"]).strip()
            ticker = raw_ticker if raw_ticker.endswith(".TW") else raw_ticker + ".TW"
            name = str(h.get("name", raw_ticker))
            cost = float(h.get("cost", 0))
            shares = float(h.get("shares", 1))

            ind = compute_indicators(ticker)
            if not ind:
                flat_list.append({
                    "name": name, "ticker": ticker, "cost": cost, "shares": shares,
                    "price": 0, "pnl_pct": 0, "score": 0, "category": "flat",
                    "atr_stop": 0, "trail_stop": 0, "inst_note": "無法取得",
                    "rsi": 0, "macd_hist": 0, "k_val": 0, "d_val": 0,
                    "atr": 0, "ma20": 0, "above_ma20": False, "stop_price": 0,
                })
                continue

            cls = classify_holding(ind, cost)
            _, inst_note = get_institutional(ticker)

            stock_data = {
                "name": name, "ticker": ticker, "cost": cost, "shares": shares,
                "price": ind["price"], "pnl_pct": cls["pnl_pct"], "score": cls["score"],
                "category": cls["category"], "atr_stop": cls["atr_stop"],
                "trail_stop": cls["trail_stop"], "inst_note": inst_note,
                "rsi": ind["rsi"], "macd_hist": ind["macd_hist"],
                "k_val": ind["k_val"], "d_val": ind["d_val"],
                "atr": ind["atr"], "ma20": ind["ma20"],
                "above_ma20": ind["above_ma20"], "stop_price": cls["atr_stop"],
            }
            if cls["category"] == "sell":
                sell_list.append(stock_data)
            elif cls["category"] == "flat":
                flat_list.append(stock_data)
            else:
                hold_list.append(stock_data)

        sub1, sub2, sub3 = st.tabs([
            "🛑 賣出/停損 (" + str(len(sell_list)) + ")",
            "⚖️ 攤平 (" + str(len(flat_list)) + ")",
            "💎 續抱 (" + str(len(hold_list)) + ")"
        ])

        def render_stock_card(s, tab_key=""):
            pnl = s["pnl_pct"]
            pnl_color = "#3fb950" if pnl >= 0 else "#f85149"
            cat = s["category"]
            badge_class = "bg-sell" if cat == "sell" else ("bg-flat" if cat == "flat" else "bg-hold")
            cat_label = "賣出/停損" if cat == "sell" else ("攤平" if cat == "flat" else "續抱")
            score_str = ("+" if s["score"] >= 0 else "") + str(s["score"])
            label = s["name"] + "  " + str(round(s["price"],1)) + "  " + ("+" if pnl >= 0 else "") + str(round(pnl,2)) + "%"

            with st.expander(label, expanded=False):
                st.markdown(
                    '<div class="badge ' + badge_class + '">建議：' + cat_label + ' | 評分 ' + score_str + "</div>",
                    unsafe_allow_html=True
                )
                above_lbl = "✅上方" if s["above_ma20"] else "❌下方"
                st.markdown(
                    '<div class="pgrid-4">'
                    + '<div class="pbox"><span class="pl">現價</span><span class="pv">' + str(round(s["price"],1)) + "</span></div>"
                    + '<div class="pbox"><span class="pl">成本</span><span class="pv">' + str(round(s["cost"],1)) + "</span></div>"
                    + '<div class="pbox"><span class="pl">損益</span><span class="pv" style="color:' + pnl_color + ';">' + ("+" if pnl >= 0 else "") + str(round(pnl,1)) + "%</span></div>"
                    + '<div class="pbox"><span class="pl">張數</span><span class="pv">' + str(int(s["shares"])) + "</span></div>"
                    + "</div>"
                    + '<div class="atr-box">🛡️ ATR停損：<b>' + str(round(s["atr_stop"],1)) + "</b> | 追蹤停利：<b>" + str(round(s["trail_stop"],1)) + "</b></div>"
                    + '<div class="sbar">RSI: ' + str(round(s["rsi"],1)) + " | MACD: " + str(round(s["macd_hist"],3)) + " | K: " + str(round(s["k_val"],1)) + " D: " + str(round(s["d_val"],1)) + " | 20MA: " + str(round(s["ma20"],1)) + " " + above_lbl + "</div>"
                    + '<div style="font-size:0.78rem;color:#8b949e;margin-top:4px;">法人：' + s["inst_note"] + "</div>",
                    unsafe_allow_html=True
                )
                if ai_enabled:
                    if st.button("🤖 AI 分析 " + s["name"], key="ai_h_" + s["ticker"] + "_" + tab_key):
                        with st.spinner("AI 分析中..."):
                            result = call_ai(build_stock_prompt(s))
                        if result:
                            st.markdown('<div class="ai-box"><div class="ai-title">AI 分析結果</div><div class="ai-content">' + result + "</div></div>", unsafe_allow_html=True)
                else:
                    st.caption("AI未連線")

        with sub1:
            if sell_list:
                for s in sell_list: render_stock_card(s, "sell")
            else:
                st.success("✅ 目前無需賣出/停損的持股")
        with sub2:
            if flat_list:
                for s in flat_list: render_stock_card(s, "flat")
            else:
                st.success("✅ 目前無需攤平的持股")
        with sub3:
            if hold_list:
                for s in hold_list: render_stock_card(s, "hold")
            else:
                st.info("目前無續抱標的")


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
                    result = call_ai(build_market_prompt(picks, mkt_data_for_ai))
                if result:
                    st.markdown('<div class="ai-market-box"><div class="ai-market-title">AI 今日市場總覽</div><div class="ai-content">' + result + "</div></div>", unsafe_allow_html=True)

        for p in picks:
            priority_tag = "MACD翻正" if p.get("macd_flip") else ("均線突破" if p.get("squeeze_break") else "")
            label_prefix = "⭐ " if p["priority"] else ""
            exp_label = label_prefix + p["name"] + "  " + p["ticker"] + "  評分 +" + str(p["score"])

            with st.expander(exp_label, expanded=bool(p["priority"])):
                pt_html = ""
                if priority_tag:
                    pt_html = '<span style="background:#0d3d1a;color:#3fb950;border-radius:4px;padding:2px 7px;font-size:0.72rem;margin-left:6px;">' + priority_tag + "</span>"
                st.markdown(
                    '<div class="pick-card">'
                    + '<span class="pick-name">' + p["name"] + "</span>"
                    + '<span class="pick-tag">' + p["ticker"] + "</span>"
                    + '<span class="pick-score">評分 +' + str(p["score"]) + "</span>"
                    + pt_html
                    + '<div class="pick-info">現價 ' + str(round(p["price"],1)) + " | RSI " + str(round(p["rsi"],0)) + " | 量比 " + str(round(p["vol_ratio"],1)) + "x | 20MA " + str(round(p["ma20"],1)) + "</div>"
                    + '<div class="pick-entry">📍 建議入手：' + str(p["entry"]) + "</div>"
                    + '<div class="pick-atr">🛡️ 停損：' + str(p["stop"]) + " | 目標：" + str(p["target"]) + " | 風報比 " + str(p["rr"]) + "</div>"
                    + '<div style="font-size:0.78rem;color:#8b949e;margin-top:5px;">🕐 預計到達目標：約 ' + str(p["days_to_profit"]) + " 個交易日（估）</div>"
                    + "</div>",
                    unsafe_allow_html=True
                )
                if ai_enabled:
                    if st.button("🤖 AI 分析 " + p["name"], key="ai_p_" + p["ticker"]):
                        with st.spinner("AI 分析中..."):
                            sp = {**p, "cost": p["price"], "pnl_pct": 0, "stop_price": p["stop"], "trail_stop": p["stop"], "inst_note": ""}
                            result = call_ai(build_stock_prompt(sp))
                        if result:
                            st.markdown('<div class="ai-box"><div class="ai-title">AI 分析結果</div><div class="ai-content">' + result + "</div></div>", unsafe_allow_html=True)
    else:
        st.info("點擊上方「🔄 掃描推薦標的」按鈕開始掃描")

