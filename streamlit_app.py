import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import numpy as np
import io
import csv as csv_module

st.set_page_config(page_title="台股操盤 Pro",layout="wide",page_icon="📈",initial_sidebar_state="collapsed")

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
div[data-testid="stTabs"]>div:first-child button{font-size:1rem!important;font-weight:700!important;padding:9px 16px!important;}
div[data-testid="stExpander"]>details{background:#161b22!important;border:1px solid #30363d!important;border-radius:10px!important;margin-bottom:6px!important;}
div[data-testid="stExpander"]>details>summary{font-size:0.95rem!important;font-weight:600!important;color:#e6edf3!important;padding:11px 14px!important;}
.badge{display:block;border-radius:7px;padding:8px 12px;font-size:0.85rem;font-weight:600;margin:6px 0;}
.bg-sell{background:#3d1a1a;color:#f85149;border:1px solid #da3633;}
.bg-flat{background:#3d2e00;color:#e3b341;border:1px solid #9e6a03;}
.bg-hold{background:#1a4731;color:#3fb950;border:1px solid #238636;}
.pbox{background:#21262d;border-radius:7px;padding:7px 8px;text-align:center;}
.pbox .pl{font-size:0.6rem;color:#8b949e;text-transform:uppercase;display:block;}
.pbox .pv{font-size:0.88rem;font-weight:700;color:#e6edf3;display:block;}
.atr-box{background:#1a2233;border:1px solid #1f6feb;border-radius:7px;padding:8px 12px;margin:6px 0;font-size:0.8rem;color:#79c0ff;}
.sbar{background:#21262d;border-radius:6px;padding:7px 10px;margin:6px 0;font-family:monospace;font-size:0.78rem;color:#c9d1d9;}
.ai-box{background:linear-gradient(135deg,#0d1f12,#0a1628);border:1px solid #238636;border-radius:10px;padding:12px 14px;margin:8px 0;}
.ai-title{font-size:0.8rem;color:#3fb950;font-weight:600;margin-bottom:6px;}
.ai-content{font-size:0.88rem;color:#c9d1d9;line-height:1.6;white-space:pre-wrap;}
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

# AI 模組
def get_ai_client():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY","")
        if key and key.startswith("sk-ant"): return "claude", key
    except: pass
    try:
        key = st.secrets.get("OPENAI_API_KEY","")
        if key: return "openai", key
    except: pass
    try:
        key = st.secrets.get("GEMINI_API_KEY","")
        if key: return "gemini", key
    except: pass
    return None, None

def call_ai(prompt):
    provider, key = get_ai_client()
    if not provider:
        return "❌ 尚未設定 API Key，請在 Streamlit Secrets 設定 GEMINI_API_KEY"
    if provider == "claude":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(
                model="claude-opus-4-5", max_tokens=600,
                system="你是台股技術分析師。用繁體中文，精簡直接，條列式回答，不要免責聲明。",
                messages=[{"role":"user","content":prompt}]
            )
            return msg.content[0].text.strip()
        except Exception as e: return "Claude錯誤: "+str(e)
    elif provider == "openai":
        try:
            import openai
            client = openai.OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"你是台股技術分析師。用繁體中文，精簡直接，不要免責聲明。"},
                          {"role":"user","content":prompt}],
                max_tokens=600, temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception as e: return "OpenAI錯誤: "+str(e)
    elif provider == "gemini":
        # gemini-2.5-flash 已驗證可用，優先使用
        models = ["gemini-2.5-flash","gemini-2.0-flash","gemini-2.0-flash-lite"]
        headers = {"Content-Type":"application/json"}
        if key.startswith("AQ."):
            headers["x-goog-api-key"] = key
        payload = {"contents":[{"parts":[{"text":prompt}]}],
                   "generationConfig":{"maxOutputTokens":600,"temperature":0.3}}
        last_err = ""
        for model in models:
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent"
                if not key.startswith("AQ."):
                    url += "?key="+key
                r = requests.post(url, headers=headers, json=payload, timeout=25)
                if r.status_code == 200:
                    d = r.json()
                    return d["candidates"][0]["content"]["parts"][0]["text"].strip()
                elif r.status_code == 429:
                    last_err = model+": 配額超限，請稍後再試"
                    continue
                elif r.status_code == 404:
                    last_err = model+": 模型不存在"
                    continue
                else:
                    last_err = model+": "+str(r.status_code)+" "+r.text[:80]
                    continue
            except Exception as e:
                last_err = str(e); continue
        return "Gemini錯誤: "+last_err

NAME_TO_TICKER = {
    "台積電":"2330.TW","鴻海":"2317.TW","聯發科":"2454.TW","台達電":"2308.TW",
    "廣達":"2382.TW","緯創":"3231.TW","和碩":"4938.TW","仁寶":"2324.TW",
    "華碩":"2357.TW","宏碁":"2353.TW","聯電":"2303.TW","日月光投控":"3711.TW",
    "瑞昱":"2379.TW","聯詠":"3034.TW","矽力-KY":"6415.TW","祥碩":"5269.TW",
    "群聯":"8299.TW","智原":"3035.TW","創意":"3443.TW","新應材":"6643.TW",
    "玉晶光":"3406.TW","大立光":"3008.TW","嘉澤":"3533.TW","信驊":"5274.TW",
    "神盾":"6462.TW","力旺":"3529.TW","金像電":"2368.TW","欣興":"3037.TW",
    "奇鋐":"3017.TW","雙鴻":"3324.TW","建準":"2421.TW","超眾":"6230.TW",
    "群創":"3481.TW","友達":"2409.TW","台灣大":"4904.TW","中華電":"2412.TW",
    "國泰金":"2882.TW","富邦金":"2881.TW","中信金":"2891.TW","兆豐金":"2886.TW",
    "玉山金":"2884.TW","台塑":"1301.TW","南亞":"1303.TW","台化":"1326.TW",
    "台塑化":"6505.TW","中鋼":"2002.TW","長榮":"2603.TW","陽明":"2609.TW",
    "萬海":"2615.TW","華航":"2610.TW","長榮航空":"2618.TW",
    "可成":"2474.TW","巨大":"9921.TW","美利達":"9914.TW","正新":"2105.TW",
    "世芯-KY":"3661.TW","力積電":"6770.TW","南亞科":"2408.TW","華邦電":"2344.TW",
    "旺宏":"2337.TW","緯穎":"6669.TW","英業達":"2356.TW","技嘉":"2376.TW",
    "微星":"2377.TW","健鼎":"3044.TW","台光電":"2383.TW",
    # ETF
    "主動統一升級50":"00957.TW","元大高股息":"0056.TW","國泰永續高股息":"00878.TW",
    "群益台灣精選高息":"00919.TW","元大台灣50":"0050.TW","富邦台50":"006208.TW",
    "永豐台灣ESG":"00888.TW","中信關鍵半導體":"00891.TW",
}

# ETF 清單（不列入推薦，損益計算用成本）
ETF_LIST = {"00957.TW","0056.TW","00878.TW","00919.TW","0050.TW","006208.TW","00888.TW","00891.TW"}

RECOMMEND_POOL = [
    ("台積電","2330.TW"),("聯發科","2454.TW"),("鴻海","2317.TW"),("台達電","2308.TW"),
    ("廣達","2382.TW"),("緯創","3231.TW"),("日月光投控","3711.TW"),("聯詠","3034.TW"),
    ("矽力-KY","6415.TW"),("祥碩","5269.TW"),("信驊","5274.TW"),("神盾","6462.TW"),
    ("奇鋐","3017.TW"),("雙鴻","3324.TW"),("世芯-KY","3661.TW"),("玉晶光","3406.TW"),
    ("大立光","3008.TW"),("欣興","3037.TW"),("金像電","2368.TW"),("健鼎","3044.TW"),
    ("長榮","2603.TW"),("陽明","2609.TW"),("台塑化","6505.TW"),("中鋼","2002.TW"),
    ("力積電","6770.TW"),("南亞科","2408.TW"),("華邦電","2344.TW"),("旺宏","2337.TW"),
    ("緯穎","6669.TW"),("技嘉","2376.TW"),("微星","2377.TW"),("英業達","2356.TW"),
    ("群聯","8299.TW"),("瑞昱","2379.TW"),("智原","3035.TW"),("創意","3443.TW"),
    ("巨大","9921.TW"),("正新","2105.TW"),("台灣大","4904.TW"),("中華電","2412.TW"),
]

def get_ticker(name):
    if name in NAME_TO_TICKER: return NAME_TO_TICKER[name]
    for k,v in NAME_TO_TICKER.items():
        if k in name or name in k: return v
    return None

@st.cache_data(ttl=300)
def fetch_stock(ticker, period="3mo"):
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        if len(df) < 5: return None
        return df
    except: return None

def get_current_price(ticker):
    """專門取得即時現價，比 fetch_stock 更快"""
    try:
        tk = yf.Ticker(ticker)
        price = tk.fast_info.last_price
        if price and price > 0:
            return round(float(price), 2)
    except: pass
    # 備援：從歷史資料取最後收盤
    df = fetch_stock(ticker, "5d")
    if df is not None and len(df) > 0:
        return round(float(df["Close"].iloc[-1]), 2)
    return None

def calc_indicators(df):
    if df is None or len(df)<20: return {}
    c = df["Close"].values.flatten().astype(float)
    v = df["Volume"].values.flatten().astype(float)
    delta = np.diff(c); gain = np.where(delta>0,delta,0); loss = np.where(delta<0,-delta,0)
    ag = np.convolve(gain,np.ones(14)/14,mode='valid'); al = np.convolve(loss,np.ones(14)/14,mode='valid')
    rs = ag[-1]/(al[-1]+1e-9); rsi = 100-100/(1+rs)
    def ema(x,n):
        e=np.zeros(len(x)); e[n-1]=np.mean(x[:n])
        for i in range(n,len(x)): e[i]=x[i]*2/(n+1)+e[i-1]*(1-2/(n+1))
        return e
    e12=ema(c,12); e26=ema(c,26); macd=e12-e26; sig=ema(macd[25:],9); hist=macd[25:]-sig
    n=9; lows=[min(df["Low"].values.flatten()[max(0,i-n+1):i+1]) for i in range(len(c))]
    highs=[max(df["High"].values.flatten()[max(0,i-n+1):i+1]) for i in range(len(c))]
    rsv=[(c[i]-lows[i])/(highs[i]-lows[i]+1e-9)*100 for i in range(len(c))]
    K=50.0; D=50.0
    for r in rsv: K=K*2/3+r/3; D=D*2/3+K/3
    ma20=np.mean(c[-20:]) if len(c)>=20 else c[-1]
    tr=[max(df["High"].values.flatten()[i]-df["Low"].values.flatten()[i],
            abs(df["High"].values.flatten()[i]-c[i-1]) if i>0 else 0,
            abs(df["Low"].values.flatten()[i]-c[i-1]) if i>0 else 0) for i in range(len(c))]
    atr=np.mean(tr[-14:]) if len(tr)>=14 else np.mean(tr)
    avg_v=np.mean(v[-20:]) if len(v)>=20 else np.mean(v)
    inst_est=round((v[-1]-avg_v)*c[-1]/1e8,1) if len(v)>0 else 0
    return {"rsi":round(rsi,1),"macd":round(hist[-1],3) if len(hist)>0 else 0,
            "macd_cross":bool(hist[-1]>0) if len(hist)>0 else False,
            "k":round(K,1),"d":round(D,1),"ma20":round(ma20,1),
            "above_ma20":bool(c[-1]>ma20),"atr":round(atr,2),
            "inst":inst_est,"price":round(float(c[-1]),2)}

def score_stock(ind):
    if not ind: return 0
    s=0
    if 40<=ind["rsi"]<=70: s+=1
    if ind["macd_cross"]: s+=1
    if ind["k"]<80 and ind["k"]>ind["d"]: s+=1
    if ind["above_ma20"]: s+=1
    if ind["inst"]>0: s+=1
    return s

@st.cache_data(ttl=60)
def get_market_data():
    res={}
    tickers={"台指":"^TWII","納指":"^IXIC","TSM ADR":"TSM"}
    for name,t in tickers.items():
        try:
            tk=yf.Ticker(t); info=tk.fast_info
            res[name]={"price":round(info.last_price,2),"change_pct":round((info.last_price-info.previous_close)/info.previous_close*100,2)}
        except: res[name]={"price":0,"change_pct":0}
    return res

def parse_csv(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8-sig")
    except:
        content = uploaded_file.read().decode("big5", errors="ignore")
    reader = csv_module.reader(io.StringIO(content))
    rows = list(reader)
    stocks = []
    for row in rows:
        if len(row) < 5: continue
        name = row[0].strip().strip('"')
        if name in ["股票名稱","名稱",""] or name.startswith("#"): continue
        try: shares = float(str(row[1]).replace(",","").strip().strip('"'))
        except: continue
        try: cost = float(str(row[4]).replace(",","").strip().strip('"'))
        except: continue
        if shares <= 0 or cost <= 0: continue
        stocks.append({"name":name,"shares":shares,"cost":cost})
    return stocks

def analyze_portfolio(stocks):
    results = []
    for s in stocks:
        ticker = get_ticker(s["name"])
        ind = {}
        price = None
        is_etf = ticker in ETF_LIST if ticker else False

        if ticker:
            # 先嘗試即時現價
            price = get_current_price(ticker)
            # 再抓技術指標（ETF也抓，但分類不同）
            if not is_etf:
                df = fetch_stock(ticker)
                if df is not None and len(df) >= 20:
                    ind = calc_indicators(df)
                    if ind and "price" in ind:
                        price = ind["price"]

        # 如果還是抓不到現價，用成本（顯示時標註無法取得）
        if price is None or price <= 0:
            price = s["cost"]

        pnl_pct = (price - s["cost"]) / s["cost"] * 100 if s["cost"] > 0 else 0
        pnl_amt = (price - s["cost"]) * s["shares"]
        sc = score_stock(ind)

        results.append({**s, "ticker":ticker, "price":price, "ind":ind,
                        "pnl_pct":pnl_pct, "pnl_amt":pnl_amt, "score":sc,
                        "is_etf":is_etf, "price_ok": (price != s["cost"])})
    return results

def classify(r):
    # ETF 永遠顯示「續抱」不建議賣出
    if r.get("is_etf"): return "hold"
    # 現價=成本表示抓不到，不建議賣出
    if not r.get("price_ok"): return "flat"
    sc = r["score"]; pnl = r["pnl_pct"]
    if sc <= 0 and pnl < -15: return "sell"
    if sc >= 3 and pnl > -5: return "hold"
    return "flat"

@st.cache_data(ttl=600)
def get_recommendations():
    picks = []
    for name, ticker in RECOMMEND_POOL:
        if ticker in ETF_LIST: continue
        df = fetch_stock(ticker, "2mo")
        if df is None or len(df) < 20: continue
        ind = calc_indicators(df)
        if not ind: continue
        sc = score_stock(ind)
        if sc >= 3:
            picks.append({"name":name,"ticker":ticker,"ind":ind,"score":sc})
    picks.sort(key=lambda x: -x["score"])
    if len(picks) < 5:
        for name, ticker in RECOMMEND_POOL:
            if ticker in ETF_LIST: continue
            if any(p["ticker"]==ticker for p in picks): continue
            df = fetch_stock(ticker, "2mo")
            if df is None or len(df) < 20: continue
            ind = calc_indicators(df)
            if not ind: continue
            sc = score_stock(ind)
            if sc >= 2:
                picks.append({"name":name,"ticker":ticker,"ind":ind,"score":sc})
                picks.sort(key=lambda x: -x["score"])
            if len(picks) >= 5: break
    return picks[:10]

def show_kline(ticker, height=280):
    df = fetch_stock(ticker)
    if df is not None and len(df)>5:
        try:
            import plotly.graph_objects as go
            fig = go.Figure(data=[go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"],
                increasing_line_color="#3fb950", decreasing_line_color="#f85149"
            )])
            fig.update_layout(height=height, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                              font_color="#c9d1d9", xaxis_rangeslider_visible=False,
                              margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("需要安裝 plotly")

def render_pick_card(p):
    ind = p["ind"]; sc = p["score"]; name = p["name"]; ticker = p["ticker"]
    price = ind.get("price", 0)
    entry = round(ind.get("ma20", price) * 0.99, 1)
    atr_stop = round(price - ind.get("atr", 0) * 2, 1)
    trail_stop = round(price * 0.95, 1)
    inst_val = ind.get("inst", 0)
    inst_txt = "法人買超 "+str(inst_val)+"億" if inst_val > 0 else "法人小幅參與 "+str(abs(inst_val))+"億"
    score_txt = "評分 +"+str(sc)
    signals = []
    if ind.get("above_ma20"): signals.append("✅ 收在20MA("+str(ind.get("ma20",0))+")上方")
    if ind.get("macd_cross"): signals.append("MACD擴大 "+str(ind.get("macd",0)))
    if ind.get("k",50) < 80 and ind.get("k",50) > ind.get("d",50): signals.append("KD交叉 K:"+str(ind.get("k",0)))
    signal_str = "  ".join(signals)
    rsi_v = str(ind.get("rsi",0)); macd_v = str(ind.get("macd",0))
    k_v = str(ind.get("k",0)); d_v = str(ind.get("d",0)); ma20_v = str(ind.get("ma20",0))
    atr_v = str(ind.get("atr",0))

    card_html = ('<div class="pick-card">'
        '<span class="pick-name">'+name+'</span>'
        '<span class="pick-tag">'+ticker+'</span>'
        '<span class="pick-score">'+score_txt+'</span>'
        '<div class="pick-info">現價 '+str(price)+'</div>'
        '<div class="pick-entry">📍 建議入手：'+str(entry)+'</div>'
        '<div class="pick-atr">🛡 ATR停損：'+str(atr_stop)+' | 追蹤停利：'+str(trail_stop)+'</div>'
        '<div class="sbar">'+signal_str+'</div>'
        '<div style="font-size:0.72rem;color:#8b949e;">'+inst_txt+'</div>'
        '</div>')
    st.markdown(card_html, unsafe_allow_html=True)

    ai_key = "ai_pick_"+ticker
    col1, col2 = st.columns([1,3])
    with col1:
        if st.button("📊 日K線圖", key="kline_pick_"+ticker):
            st.session_state["show_kline_pick_"+ticker] = not st.session_state.get("show_kline_pick_"+ticker, False)
    with col2:
        if st.button("🤖 AI分析", key="aipick_"+ticker):
            with st.spinner("AI分析中..."):
                prompt = ("台股"+name+"("+ticker+")，現價"+str(price)+"，RSI:"+rsi_v+
                         "，MACD:"+macd_v+"，K:"+k_v+"/D:"+d_v+
                         "，20MA:"+ma20_v+"，ATR:"+atr_v+
                         "。請分析：①這家公司做什麼、產業熱度 ②技術面哪裡好、什麼題材 ③操作策略（進場點/停損/停利）")
                result = call_ai(prompt)
                st.session_state[ai_key] = result
    if st.session_state.get(ai_key):
        st.markdown('<div class="ai-box"><div class="ai-title">🤖 AI分析（'+name+'）</div><div class="ai-content">'+st.session_state[ai_key]+'</div></div>', unsafe_allow_html=True)
    if st.session_state.get("show_kline_pick_"+ticker):
        show_kline(ticker)

def render_stock_card(r):
    name=r["name"]; price=r["price"]; cost=r["cost"]; shares=r["shares"]
    pnl_pct=r["pnl_pct"]; pnl_amt=r["pnl_amt"]; ind=r["ind"]; sc=r["score"]
    ticker=r.get("ticker",""); price_ok=r.get("price_ok",False)
    is_etf=r.get("is_etf",False)
    cl = classify(r)
    badge_cls = {"sell":"bg-sell","flat":"bg-flat","hold":"bg-hold"}[cl]
    if cl=="sell": badge_txt = "建議：賣出/停損 | 評分 -5"
    elif cl=="flat":
        if not price_ok: badge_txt = "⚠️ 無法取得現價 | 手動確認"
        else: badge_txt = "觀望/攤平 | 評分 "+str(sc)
    else:
        if is_etf: badge_txt = "ETF 長期持有 | 依配息策略"
        else: badge_txt = "續抱/加碼 | 評分 +"+str(sc)
    pnl_color = "#3fb950" if pnl_pct >= 0 else "#f85149"
    pnl_sign = "+" if pnl_pct >= 0 else ""
    price_note = "" if price_ok else " ⚠️"

    st.markdown('<div class="badge '+badge_cls+'">'+badge_txt+'</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    with cols[0]: st.markdown('<div class="pbox"><span class="pl">現價</span><span class="pv">'+str(price)+price_note+'</span></div>', unsafe_allow_html=True)
    with cols[1]: st.markdown('<div class="pbox"><span class="pl">成本</span><span class="pv">'+str(cost)+'</span></div>', unsafe_allow_html=True)
    with cols[2]: st.markdown('<div class="pbox"><span class="pl">股數</span><span class="pv">'+str(int(shares))+'</span></div>', unsafe_allow_html=True)
    if price_ok:
        with cols[3]: st.markdown('<div class="pbox"><span class="pl">損益%</span><span class="pv" style="color:'+pnl_color+'">'+pnl_sign+str(round(pnl_pct,1))+'%</span></div>', unsafe_allow_html=True)
        with cols[4]: st.markdown('<div class="pbox"><span class="pl">損益$</span><span class="pv" style="color:'+pnl_color+'">'+pnl_sign+str(int(pnl_amt))+'</span></div>', unsafe_allow_html=True)
    else:
        with cols[3]: st.markdown('<div class="pbox"><span class="pl">損益%</span><span class="pv" style="color:#8b949e;">取得中</span></div>', unsafe_allow_html=True)
        with cols[4]: st.markdown('<div class="pbox"><span class="pl">損益$</span><span class="pv" style="color:#8b949e;">取得中</span></div>', unsafe_allow_html=True)

    if ind:
        atr_stop = round(price - ind.get("atr",0)*2, 1)
        trail_stop = round(price * 0.95, 1)
        st.markdown('<div class="atr-box">🛡 ATR停損：'+str(atr_stop)+' | 追蹤停利：'+str(trail_stop)+'</div>', unsafe_allow_html=True)
        ma_icon = "✅" if ind.get("above_ma20") else "❌"
        ma_dir = "上方" if ind.get("above_ma20") else "下方"
        rsi_v=str(ind.get("rsi","-")); macd_v=str(round(ind.get("macd",0),3))
        k_v=str(ind.get("k","-")); d_v=str(ind.get("d","-")); ma_v=str(ind.get("ma20","-"))
        st.markdown('<div class="sbar">RSI:'+rsi_v+' | MACD:'+macd_v+' | K:'+k_v+' D:'+d_v+' | 20MA:'+ma_v+' '+ma_icon+ma_dir+'</div>', unsafe_allow_html=True)
        inst=ind.get("inst",0)
        inst_txt="法人買超 "+str(inst)+"億" if inst>0 else "法人小幅參與 "+str(abs(inst))+"億"
        st.markdown('<div style="font-size:0.72rem;color:#8b949e;margin:4px 0;">'+inst_txt+'</div>', unsafe_allow_html=True)
    elif is_etf:
        st.markdown('<div class="sbar">ETF - 依配息策略持有，不顯示技術指標</div>', unsafe_allow_html=True)

    ai_key = "ai_hold_"+name
    col1, col2 = st.columns([1,1])
    with col1:
        if ticker and st.button("📈 日K線圖", key="kline_hold_"+name):
            st.session_state["show_kline_hold_"+name] = not st.session_state.get("show_kline_hold_"+name, False)
    with col2:
        if st.button("🤖 AI分析", key="aibtn_hold_"+name):
            with st.spinner("AI分析中..."):
                rsi_v=str(ind.get("rsi","-")); macd_v=str(round(ind.get("macd",0),3))
                k_v=str(ind.get("k","-")); d_v=str(ind.get("d","-"))
                ma_v=str(ind.get("ma20","-")); atr_v=str(round(ind.get("atr",0),2))
                prompt = ("台股"+name+"（"+str(ticker)+"），現價"+str(price)+
                         "元，成本"+str(cost)+"元，損益"+str(round(pnl_pct,1))+
                         "%，股數"+str(int(shares))+"股。")
                if ind:
                    prompt += ("RSI:"+rsi_v+"，MACD柱:"+macd_v+"，K:"+k_v+"/D:"+d_v+
                              "，20MA:"+ma_v+"，ATR:"+atr_v+"。")
                if is_etf:
                    prompt += "這是ETF，請從配息、持股分散度、長期績效角度分析建議。"
                else:
                    prompt += "請給出：①現在技術面狀況判斷 ②建議操作（賣/持/加碼）③具體停損停利點"
                result = call_ai(prompt)
                st.session_state[ai_key] = result
    if st.session_state.get(ai_key):
        st.markdown('<div class="ai-box"><div class="ai-title">🤖 AI分析</div><div class="ai-content">'+st.session_state[ai_key]+'</div></div>', unsafe_allow_html=True)
    if st.session_state.get("show_kline_hold_"+name) and ticker:
        show_kline(ticker)

def main():
    provider, _ = get_ai_client()
    ai_label = {"claude":"● Claude","openai":"● OpenAI","gemini":"● Gemini"}.get(provider,"需設定API Key")
    now_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    st.markdown('<div class="hero-box"><div class="hero-title">📊 台股操盤 Pro <span style="font-size:0.7rem;color:#3fb950;margin-left:8px;">'+ai_label+'</span></div><div class="hero-sub">即時行情 '+now_str+' 更新</div></div>', unsafe_allow_html=True)

    with st.expander("📊 今日大盤指標", expanded=False):
        mkt = get_market_data()
        cols = st.columns(len(mkt))
        for i,(mname,d) in enumerate(mkt.items()):
            color="#3fb950" if d["change_pct"]>=0 else "#f85149"
            sign="↑" if d["change_pct"]>=0 else "↓"
            pct=str(abs(round(d["change_pct"],2)))
            with cols[i]:
                st.markdown('<div style="background:#161b22;border-radius:8px;padding:10px;text-align:center;"><div style="color:#8b949e;font-size:0.72rem;">'+mname+'</div><div style="color:#e6edf3;font-size:1.4rem;font-weight:800;">'+str(round(d["price"],0))+'</div><div style="background:'+color+'22;color:'+color+';border-radius:4px;padding:2px 6px;font-size:0.75rem;font-weight:600;">'+sign+' '+pct+'%</div></div>', unsafe_allow_html=True)

    with st.expander("📁 匯入持股 CSV", expanded=True):
        st.markdown('<div style="font-size:0.75rem;color:#8b949e;margin-bottom:8px;">支援券商匯出格式 | 只讀：名稱、股數、成交均價 | 市價/損益全部即時抓</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["csv","txt"], label_visibility="collapsed")
        if uploaded:
            stocks = parse_csv(uploaded)
            if stocks:
                names = "、".join([s["name"] for s in stocks])
                st.success("✅ 已載入 "+str(len(stocks))+" 筆持股："+names)
                st.session_state["portfolio"] = stocks
            else:
                st.error("❌ 解析失敗，請確認 CSV 格式")

    portfolio = st.session_state.get("portfolio", [])
    tab1, tab2 = st.tabs(["📁 持有股", "⭐ 推薦入手股"])

    with tab1:
        if not portfolio:
            st.info("尚未匯入持股，請展開上方「📁 匯入持股 CSV」上傳檔案。")
        else:
            results = analyze_portfolio(portfolio)
            sell = [r for r in results if classify(r)=="sell"]
            flat = [r for r in results if classify(r)=="flat"]
            hold = [r for r in results if classify(r)=="hold"]
            total_pnl = sum(r["pnl_amt"] for r in results if r.get("price_ok"))
            total_cost = sum(r["cost"]*r["shares"] for r in results if r.get("price_ok"))
            total_pnl_pct = total_pnl/total_cost*100 if total_cost>0 else 0
            pnl_color = "#3fb950" if total_pnl>=0 else "#f85149"
            pnl_sign = "+" if total_pnl>=0 else ""
            pnl_amt_str = pnl_sign+str(int(total_pnl))
            pnl_pct_str = pnl_sign+str(round(total_pnl_pct,1))
            st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;"><span style="color:#8b949e;font-size:0.8rem;">📊 總損益（有即時現價的部位）</span><span style="color:'+pnl_color+';font-size:1.1rem;font-weight:700;">'+pnl_amt_str+' 元（'+pnl_pct_str+'%）</span></div>', unsafe_allow_html=True)

            t1,t2,t3 = st.tabs(["🔴 賣出/停損 ("+str(len(sell))+")", "⚖️ 攤平 ("+str(len(flat))+")", "💎 續抱 ("+str(len(hold))+")"])
            for tab_obj, group in [(t1,sell),(t2,flat),(t3,hold)]:
                with tab_obj:
                    for r in group:
                        pnl_sign2 = "+" if r["pnl_pct"]>=0 else ""
                        price_tag = str(r["price"]) if r.get("price_ok") else str(r["price"])+" ⚠️"
                        pnl_tag = pnl_sign2+str(round(r["pnl_pct"],2))+"%" if r.get("price_ok") else "---"
                        label = r["name"]+"  "+price_tag+"  "+pnl_tag
                        with st.expander(label, expanded=False):
                            render_stock_card(r)

    with tab2:
        st.markdown('<div style="color:#8b949e;font-size:0.75rem;margin-bottom:8px;">依技術評分排序（評分≥2）</div>', unsafe_allow_html=True)
        with st.spinner("掃描推薦標的..."):
            picks = get_recommendations()
        if picks:
            for p in picks:
                render_pick_card(p)
        else:
            st.info("目前無符合條件標的，請稍後再試")

if __name__ == "__main__":
    main()
