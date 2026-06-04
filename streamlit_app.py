import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import datetime
import numpy as np
import io
import csv as csv_module

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
div[data-testid="stTabs"]>div:first-child button{font-size:1rem!important;font-weight:700!important;padding:9px 16px!important;}
div[data-testid="stTabs"] div[data-testid="stTabs"]>div:first-child button{font-size:0.82rem!important;font-weight:600!important;padding:7px 10px!important;}
div[data-testid="stExpander"]>details{background:#161b22!important;border:1px solid #30363d!important;border-radius:10px!important;margin-bottom:6px!important;}
div[data-testid="stExpander"]>details>summary{font-size:0.95rem!important;font-weight:600!important;color:#e6edf3!important;padding:11px 14px!important;}
.badge{display:block;border-radius:7px;padding:8px 12px;font-size:0.85rem;font-weight:600;margin:6px 0;}
.bg-sell{background:#3d1a1a;color:#f85149;border:1px solid #da3633;}
.bg-flat{background:#3d2e00;color:#e3b341;border:1px solid #9e6a03;}
.bg-hold{background:#1a4731;color:#3fb950;border:1px solid #238636;}
.pgrid-5{display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:5px;margin:8px 0;}
.pgrid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin:8px 0;}
.pbox{background:#21262d;border-radius:7px;padding:7px 8px;text-align:center;}
.pbox .pl{font-size:0.6rem;color:#8b949e;text-transform:uppercase;display:block;}
.pbox .pv{font-size:0.88rem;font-weight:700;color:#e6edf3;display:block;}
.atr-box{background:#1a2233;border:1px solid #1f6feb;border-radius:7px;padding:8px 12px;margin:6px 0;font-size:0.8rem;color:#79c0ff;}
.sbar{background:#21262d;border-radius:6px;padding:7px 10px;margin:6px 0;font-family:monospace;font-size:0.78rem;color:#c9d1d9;}
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
# AI 模組
# =============================================
def get_ai_client():
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key: return "openai", key
    except Exception: pass
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key: return "gemini", key
    except Exception: pass
    return None, None

def call_ai(prompt):
    provider, key = get_ai_client()
    if not provider: return "❌ 尚未設定 API Key，請在 Streamlit Secrets 設定 GEMINI_API_KEY（AIza...開頭）"
    if provider == "openai":
        try:
            import openai
            client = openai.OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":"你是台股技術分析師。用繁體中文，精簡直接，不要免責聲明。"},
                    {"role":"user","content":prompt}
                ], max_tokens=500, temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception as e: return "OpenAI錯誤: "+str(e)
    elif provider == "gemini":
        models = ["gemini-2.0-flash","gemini-1.5-flash","gemini-flash-latest"]
        for model in models:
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent"
                headers = {"Content-Type":"application/json","X-goog-api-key":key}
                body = {"contents":[{"parts":[{"text":prompt}]}]}
                resp = requests.post(url,json=body,headers=headers,timeout=20)
                data = resp.json()
                if "candidates" in data:
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                elif "error" in data:
                    msg = data["error"].get("message","")
                    if "quota" in msg.lower() or "RESOURCE_EXHAUSTED" in msg: continue
                    return "Gemini錯誤("+model+"): "+msg
            except Exception: continue
        return "Gemini: 所有模型配額已滿，請稍後再試"
    return None

def build_stock_prompt(s):
    lines = [
        "股票："+s.get("name","")+" ("+s.get("ticker","")+")",
        "市價："+str(round(s.get("csv_price",0),1))+"，成本："+str(round(s.get("cost",0),1))+"，損益："+str(round(s.get("pnl_pct",0),1))+"%",
        "技術評分："+str(s.get("score",0))+"，RSI："+str(round(s.get("rsi",0),1)),
        "MACD柱："+str(round(s.get("macd_hist",0),3))+"，KD K："+str(round(s.get("k_val",0),1))+" D："+str(round(s.get("d_val",0),1)),
        "ATR停損線："+str(round(s.get("stop_price",0),1))+"，20MA："+str(round(s.get("ma20",0),1))+"（"+("上方" if s.get("above_ma20") else "下方")+"）",
        "目前分類："+s.get("category",""),
        "","請分三段回答（每段2行內）：",
        "1.【現況】技術面現況","2.【操作】賣出/攤平/續抱，具體理由","3.【風險】需關注的訊號",
    ]
    return "\n".join(lines)

def build_pick_prompt(p):
    lines = [
        "股票："+p.get("name","")+" ("+p.get("ticker","")+")",
        "現價："+str(round(p.get("price",0),1))+"，建議入手："+str(p.get("entry",0)),
        "技術評分：+"+str(p.get("score",0))+"，RSI："+str(round(p.get("rsi",0),1))+"，量比："+str(round(p.get("vol_ratio",0),1))+"x",
        "信號："+("MACD剛翻正 " if p.get("macd_flip") else "")+("均線糾結突破 " if p.get("squeeze_break") else "一般技術強勢"),
        "","請分三段回答（每段2行內）：",
        "1.【公司簡介】做什麼、產業、市場熱度","2.【推薦原因】技術面哪裡強、符合哪個題材","3.【操作策略】入手時機、停損停利",
    ]
    return "\n".join(lines)

def build_market_prompt(picks, market):
    lines = [
        "今日市場：費半"+market.get("sox","?")+" "+market.get("sox_chg","")+"，納指"+market.get("ndx","?")+" "+market.get("ndx_chg",""),
        "TSM ADR："+market.get("tsm","?")+" "+market.get("tsm_chg","")+"，台指："+market.get("twii","?")+" "+market.get("twii_chg",""),
        "","今日技術面推薦：",
    ]
    for p in picks[:6]:
        lines.append("- "+p.get("name","")+" 評分+"+str(p.get("score",0))+" 現價"+str(round(p.get("price",0),1))+" RSI"+str(round(p.get("rsi",0),0)))
    lines += ["","請給出今日大盤簡評與操作方向，不超過150字。"]
    return "\n".join(lines)


# =============================================
# 名稱對照 & CSV 解析
# =============================================
NAME_TO_TICKER = {
    "台積電":"2330","鴻海":"2317","聯發科":"2454","廣達":"2382",
    "緯創":"3231","技嘉":"2376","華碩":"2357","瑞昱":"2379",
    "聯詠":"3034","群聯":"8299","矽力-KY":"6415","世芯-KY":"3661",
    "創意":"3443","力積電":"6770","南亞科":"2408","旺宏":"2337",
    "欣興":"3037","台光電":"2383","健鼎":"3044","大立光":"3008",
    "信驊":"5274","祥碩":"5269","金像電":"2368","台達電":"2308",
    "群創":"3481","友達":"2409","奇鋐":"3017","建準":"2421",
    "力旺":"3529","智原":"3035","神盾":"6462","鴻準":"2354",
    "緯穎":"6669","英業達":"2356","仁寶":"2324","光寶科":"2301",
    "玉晶光":"3406","臻鼎-KY":"4958","新應材":"3715","敦泰":"3545",
    "元大高股息":"0056","國泰永續高股息":"00878",
    "群益台灣精選高息":"00919","主動統一升級50":"00936",
    "元大台灣50":"0050","富邦台50":"006208",
    "國泰台灣5G+":"00881","中信關鍵半導體":"00891",
}

ETF_LIST = ["0050","0056","00878","00919","00936","006208","00881",
            "00891","00896","00900","00905","00907","00908"]

def clean_num(s):
    if s is None: return 0.0
    s = str(s).strip().replace(",","").replace("%","").replace("+","").replace("(","").replace(")","")
    try: return float(s)
    except: return 0.0

def name_to_ticker(name):
    name = str(name).strip()
    if name in NAME_TO_TICKER: return NAME_TO_TICKER[name]
    for k,v in NAME_TO_TICKER.items():
        if k in name or name in k: return v
    return None

def parse_broker_csv(raw_bytes):
    """
    券商CSV格式（固定欄位）：
    col0=名稱 col1=股數 col2=總損益 col3=交易別 col4=成交均價(成本)
    col5=市價(現價) col6=現值 col7=付出成本 col8=預估損益 col9=報酬率 col10=幣別
    """
    text = None
    for enc in ["utf-8-sig","utf-8","big5","cp950"]:
        try: text = raw_bytes.decode(enc); break
        except: pass
    if text is None: return None, "無法解碼檔案"

    results = []
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line: continue
        reader = csv_module.reader(io.StringIO(line))
        try: cols = next(reader)
        except: continue
        if len(cols) < 3: continue
        first = cols[0].strip().strip('"').strip()
        if first in ["股票名稱","總預估損益","總預估現值","總融資現金"]: continue
        if not first or first.startswith("總") or first.startswith("合計"): continue
        ticker_code = name_to_ticker(first)
        if ticker_code is None: continue
        try:
            shares = clean_num(cols[1]) if len(cols) > 1 else 1      # 股數（原始股數）
            total_pnl = clean_num(cols[2]) if len(cols) > 2 else 0    # 總損益$
            cost = clean_num(cols[4]) if len(cols) > 4 else 0          # 成交均價=成本
            csv_price = clean_num(cols[5]) if len(cols) > 5 else cost  # 市價=現價（用CSV）
            pnl_pct = clean_num(cols[9]) if len(cols) > 9 else 0       # 報酬率%
            if cost <= 0: continue
            results.append({
                "ticker": ticker_code, "name": first,
                "cost": cost,
                "shares": shares,           # 保留原始股數
                "csv_price": csv_price,     # CSV市價（顯示用）
                "total_pnl": total_pnl,     # 損益金額
                "pnl_pct": pnl_pct,         # CSV報酬率（顯示用）
            })
        except: continue

    if not results: return None, "未能解析到有效持股（可能名稱對照表缺少你的股票）"
    return pd.DataFrame(results), None


# =============================================
# 市場數據 & 技術指標
# =============================================
@st.cache_data(ttl=1800)
def get_market_data():
    tickers = {"sox":"^SOX","ndx":"^IXIC","tsm":"TSM","twii":"^TWII"}
    result = {}
    for k,sym in tickers.items():
        try:
            data = yf.download(sym,period="2d",interval="1d",progress=False,auto_adjust=True)
            if data.empty: result[k]=(0.0,0.0); continue
            close = data["Close"]
            if hasattr(close,"squeeze"): close=close.squeeze()
            close=close.dropna()
            if len(close)<2: result[k]=(float(close.iloc[-1]) if len(close)==1 else 0.0,0.0); continue
            latest=float(close.iloc[-1]); prev=float(close.iloc[-2])
            result[k]=(latest,(latest-prev)/prev*100 if prev!=0 else 0.0)
        except: result[k]=(0.0,0.0)
    return result

@st.cache_data(ttl=900)
def get_ohlcv(ticker, period="3mo"):
    try:
        data = yf.download(ticker,period=period,interval="1d",progress=False,auto_adjust=True)
        if data.empty: return None
        def sq(c):
            x=data[c]
            if hasattr(x,"squeeze"): x=x.squeeze()
            return x
        df = pd.DataFrame({"Open":sq("Open"),"High":sq("High"),"Low":sq("Low"),"Close":sq("Close"),"Volume":sq("Volume")}).dropna()
        return df
    except: return None

def compute_indicators(ticker):
    df = get_ohlcv(ticker)
    if df is None or len(df)<26: return None
    try:
        close=df["Close"]; high=df["High"]; low=df["Low"]; volume=df["Volume"]
        delta=close.diff()
        gain=delta.clip(lower=0).rolling(14).mean()
        loss=(-delta.clip(upper=0)).rolling(14).mean()
        rsi=100-100/(1+gain/loss.replace(0,np.nan))
        ema12=close.ewm(span=12).mean(); ema26=close.ewm(span=26).mean()
        macd_hist=(ema12-ema26)-(ema12-ema26).ewm(span=9).mean()
        rsv=(close-low.rolling(14).min())/(high.rolling(14).max()-low.rolling(14).min()+1e-9)*100
        k_val=rsv.ewm(com=2).mean(); d_val=k_val.ewm(com=2).mean()
        ma20=close.rolling(20).mean(); ma5=close.rolling(5).mean(); ma10=close.rolling(10).mean()
        tr=pd.concat([(high-low),(high-close.shift(1)).abs(),(low-close.shift(1)).abs()],axis=1).max(axis=1)
        atr14=tr.rolling(14).mean()
        vol_avg20=volume.rolling(20).mean()
        vol_ratio=float(volume.iloc[-1]/vol_avg20.iloc[-1]) if float(vol_avg20.iloc[-1])!=0 else 1.0
        price=float(close.iloc[-1]); atr_val=float(atr14.iloc[-1]); ma20_val=float(ma20.iloc[-1])
        ma5_v=float(ma5.iloc[-1]); ma10_v=float(ma10.iloc[-1])
        rsi_val=float(rsi.iloc[-1]); macd_h=float(macd_hist.iloc[-1])
        macd_h_prev=float(macd_hist.iloc[-2]) if len(macd_hist)>=2 else macd_h
        k=float(k_val.iloc[-1]); d=float(d_val.iloc[-1])
        k_prev=float(k_val.iloc[-2]) if len(k_val)>=2 else k
        d_prev=float(d_val.iloc[-2]) if len(d_val)>=2 else d
        recent_high=float(close.rolling(20).max().iloc[-1])
        squeeze=abs(ma5_v-ma20_val)/ma20_val<0.03 and abs(ma10_v-ma20_val)/ma20_val<0.02
        return {
            "price":price,"atr":atr_val,"ma20":ma20_val,
            "rsi":rsi_val,"macd_hist":macd_h,"macd_hist_prev":macd_h_prev,
            "k_val":k,"d_val":d,"k_prev":k_prev,"d_prev":d_prev,
            "vol_ratio":vol_ratio,"recent_high":recent_high,
            "squeeze":squeeze,"above_ma20":price>ma20_val,
        }
    except: return None

def get_institutional(ticker):
    try:
        stk=yf.Ticker(ticker); hist=stk.history(period="5d")
        if hist.empty: return None,"無數據"
        vol=hist["Volume"].iloc[-1]; cp=float(hist["Close"].iloc[-1])
        est=vol*cp*0.15/1e8
        if est>2: note="估法人買超 "+str(round(est,1))+"億"
        elif est>0.5: note="法人小幅參與 "+str(round(est,1))+"億"
        else: note="法人動向不明顯"
        return est,note
    except: return None,"無法取得"

def calc_score(ind):
    score=0
    if ind["rsi"]>50: score+=1
    if ind["rsi"]>60: score+=1
    if ind["rsi"]<40: score-=1
    if ind["rsi"]<30: score-=1
    if ind["macd_hist"]>0: score+=1
    if ind["macd_hist"]>0 and ind["macd_hist"]>ind["macd_hist_prev"]: score+=1
    if ind["macd_hist"]<0 and ind["macd_hist"]<ind["macd_hist_prev"]: score-=1
    if ind["macd_hist"]<0 and ind["macd_hist_prev"]>=0: score-=2
    if ind["k_val"]>ind["d_val"] and ind["k_prev"]<=ind["d_prev"]: score+=1
    if ind["k_val"]<ind["d_val"] and ind["k_prev"]>=ind["d_prev"]: score-=1
    if ind["k_val"]>70: score+=1
    if ind["k_val"]<30: score-=1
    if ind["price"]>ind["ma20"]: score+=1
    else: score-=1
    if ind["vol_ratio"]>1.5: score+=1
    return score

def classify_holding(ind, csv_price, cost):
    """用 CSV市價 判斷是否觸及停損，技術面用 yfinance"""
    atr=ind["atr"]
    pnl_pct=(csv_price-cost)/cost*100 if cost>0 else 0
    atr_stop=cost-2*atr
    trail_stop=ind["recent_high"]-2*atr
    score=calc_score(ind)
    kd_up=ind["k_val"]>ind["d_val"] and ind["k_prev"]<=ind["d_prev"]
    macd_flip=ind["macd_hist"]>0 and ind["macd_hist_prev"]<=0
    # 停損判斷：用CSV市價對比停損線
    if csv_price<=atr_stop or (csv_price<=trail_stop and pnl_pct>10) or score<=-2: cat="sell"
    elif pnl_pct>0 and ind["above_ma20"] and score>=1: cat="hold"
    elif (kd_up or macd_flip) and ind["above_ma20"] and pnl_pct>-15: cat="flat"
    elif score>=1 and ind["above_ma20"]: cat="hold"
    else: cat="flat"
    return {"category":cat,"pnl_pct":pnl_pct,"atr_stop":atr_stop,"trail_stop":trail_stop,"score":score}


# =============================================
# 日K線圖
# =============================================
def render_kline_chart(ticker, name):
    df = get_ohlcv(ticker, period="3mo")
    if df is None or df.empty:
        st.caption("無法取得K線資料")
        return
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name="K線",
            increasing_line_color="#3fb950", increasing_fillcolor="#3fb950",
            decreasing_line_color="#f85149", decreasing_fillcolor="#f85149",
        ))
        ma20 = df["Close"].rolling(20).mean()
        ma5 = df["Close"].rolling(5).mean()
        fig.add_trace(go.Scatter(x=df.index,y=ma20,mode="lines",name="20MA",line=dict(color="#58a6ff",width=1.5)))
        fig.add_trace(go.Scatter(x=df.index,y=ma5,mode="lines",name="5MA",line=dict(color="#e3b341",width=1,dash="dot")))
        fig.update_layout(
            paper_bgcolor="#0d1117",plot_bgcolor="#0d1117",
            font=dict(color="#8b949e",size=11),
            margin=dict(l=0,r=0,t=28,b=0),height=260,
            xaxis=dict(gridcolor="#21262d",showgrid=True,rangeslider_visible=False),
            yaxis=dict(gridcolor="#21262d",showgrid=True,side="right"),
            legend=dict(orientation="h",y=1.02,x=0,font=dict(size=10)),
            title=dict(text=name+" 近3月日K",font=dict(size=12,color="#e6edf3"),x=0.01),
        )
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    except ImportError:
        st.caption("plotly 安裝中，請稍後重試")
    except Exception as e:
        st.caption("圖表錯誤: "+str(e))

# =============================================
# 推薦標的
# =============================================
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
    ("玉晶光","3406.TW"),("臻鼎-KY","4958.TW"),("敦泰","3545.TW"),("晶相光","3531.TW"),
    ("新應材","3715.TW"),("帆宣","6196.TW"),("川湖","2059.TW"),("穎崴","6515.TW"),
    ("譜瑞-KY","4966.TW"),("富鼎","8261.TW"),("立積","4968.TW"),("宏碁","2353.TW"),
]

ETF_LIST_SCAN = ["0050","0056","00878","00919","00936","006208","00881","00891","00896","00900"]

def scan_recommendations(held_tickers):
    picks_hi=[]; picks_lo=[]
    for name,ticker in SCAN_TICKERS:
        code=ticker.replace(".TW","")
        if code in ETF_LIST_SCAN: continue
        if ticker in held_tickers or code in held_tickers: continue
        ind=compute_indicators(ticker)
        if not ind: continue
        score=calc_score(ind)
        if score<2: continue
        rsi=ind["rsi"]
        if rsi<20 or rsi>75: continue
        if not ind["above_ma20"]: continue
        macd_flip=ind["macd_hist"]>0 and ind["macd_hist_prev"]<=0
        squeeze_break=ind["squeeze"] and ind["price"]>ind["ma20"]
        priority=macd_flip or squeeze_break
        price=ind["price"]; atr=ind["atr"]
        entry=round(price*0.98,1); stop=round(price-2*atr,1)
        target=round(price*1.10,1)
        risk=price-stop; reward=target-price
        rr=round(reward/risk,1) if risk>0 else 0
        item={
            "name":name,"ticker":ticker,"price":price,"score":score,"rsi":rsi,
            "macd_hist":ind["macd_hist"],"macd_hist_prev":ind["macd_hist_prev"],
            "k_val":ind["k_val"],"d_val":ind["d_val"],
            "atr":atr,"ma20":ind["ma20"],"above_ma20":True,"vol_ratio":ind["vol_ratio"],
            "entry":entry,"stop":stop,"target":target,"rr":rr,"days_to_profit":20,
            "priority":priority,"macd_flip":macd_flip,"squeeze_break":squeeze_break,
        }
        if score>=3 and ind["vol_ratio"]>=1.2: picks_hi.append(item)
        else: picks_lo.append(item)
    picks_hi.sort(key=lambda x:(int(x["priority"]),x["score"],x["rsi"]),reverse=True)
    picks_lo.sort(key=lambda x:(int(x["priority"]),x["score"]),reverse=True)
    result=picks_hi[:8]
    if len(result)<5: result+=picks_lo[:5-len(result)]
    return result


# =============================================
# 主介面
# =============================================
ai_provider,ai_key=get_ai_client()
ai_enabled=ai_provider is not None
ai_badge="AI已連線" if ai_enabled else "需設定API Key"
ai_color="3fb950" if ai_enabled else "e3b341"

st.markdown(
    '<div class="hero-box"><div class="hero-title">📈 台股操盤 Pro &nbsp;<span style="font-size:0.7rem;color:#'+ai_color+';">'+ai_badge+'</span></div>'
    +'<div class="hero-sub">'+datetime.datetime.now().strftime("%Y/%m/%d %H:%M")+' 更新</div></div>',
    unsafe_allow_html=True
)

if not ai_enabled:
    with st.expander("🔑 如何設定 AI Key",expanded=False):
        st.markdown("1. 進入 Streamlit Cloud → App → **Manage app** → **Settings** → **Secrets**")
        st.markdown("2. 貼上（需要 **AIza** 開頭的 Gemini Key）：")
        st.code('GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXX"',language="toml")
        st.markdown("3. 免費取得：https://aistudio.google.com/app/apikey")

mkt=get_market_data()
sox_v,sox_c=mkt.get("sox",(0.0,0.0)); ndx_v,ndx_c=mkt.get("ndx",(0.0,0.0))
tsm_v,tsm_c=mkt.get("tsm",(0.0,0.0)); twii_v,twii_c=mkt.get("twii",(0.0,0.0))
mkt_data_for_ai={
    "sox":str(round(sox_v,0)),"sox_chg":("+" if sox_c>=0 else "")+str(round(sox_c,2))+"%",
    "ndx":str(round(ndx_v,0)),"ndx_chg":("+" if ndx_c>=0 else "")+str(round(ndx_c,2))+"%",
    "tsm":str(round(tsm_v,2)),"tsm_chg":("+" if tsm_c>=0 else "")+str(round(tsm_c,2))+"%",
    "twii":str(round(twii_v,0)),"twii_chg":("+" if twii_c>=0 else "")+str(round(twii_c,2))+"%",
}

def fmt_d(chg):
    arrow="↑" if chg>=0 else "↓"
    color="#3fb950" if chg>=0 else "#f85149"
    return '<span style="color:'+color+';font-size:0.8rem;">'+arrow+" "+str(abs(round(chg,2)))+"%</span>"

with st.expander("📊 今日大盤指標",expanded=False):
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown("**費半**\n### "+str(int(sox_v))+"\n"+fmt_d(sox_c),unsafe_allow_html=True)
    with c2: st.markdown("**納指**\n### "+str(int(ndx_v))+"\n"+fmt_d(ndx_c),unsafe_allow_html=True)
    with c3: st.markdown("**TSM ADR**\n### "+str(round(tsm_v,2))+"\n"+fmt_d(tsm_c),unsafe_allow_html=True)
    with c4: st.markdown("**台指**\n### "+str(int(twii_v))+"\n"+fmt_d(twii_c),unsafe_allow_html=True)

with st.expander("📂 匯入持股 CSV",expanded=True):
    st.caption("支援券商匯出格式（名稱,股數,損益,交易別,成交均價,市價,...）")
    uploaded=st.file_uploader("選擇 CSV 檔案",type=["csv","txt"],label_visibility="collapsed")

if uploaded is not None:
    raw=uploaded.read()
    df_parsed,err=parse_broker_csv(raw)
    if err:
        st.error("❌ "+err)
        try:
            preview=raw.decode("utf-8-sig","ignore")[:400]
            st.code(preview,language="text")
        except: pass
    else:
        st.session_state["holdings"]=df_parsed.to_dict("records")
        names=df_parsed["name"].tolist()
        st.success("✅ 已載入 "+str(len(df_parsed))+" 筆持股："+", ".join(names))

holdings=st.session_state.get("holdings",[])


tab_hold,tab_pick=st.tabs(["📂 持有股","🌟 推薦入手股"])

with tab_hold:
    if not holdings:
        st.info("尚未匯入持股，請展開上方「📂 匯入持股 CSV」上傳檔案。")
    else:
        sell_list,flat_list,hold_list=[],[],[]
        for h in holdings:
            raw_t=str(h["ticker"]).strip()
            ticker=raw_t if raw_t.endswith(".TW") else raw_t+".TW"
            name=str(h.get("name",raw_t))
            cost=float(h.get("cost",0))
            shares=float(h.get("shares",1))
            csv_price=float(h.get("csv_price",cost))  # CSV市價
            total_pnl=float(h.get("total_pnl",0))
            csv_pnl_pct=float(h.get("pnl_pct",0))     # CSV報酬率%
            code=raw_t.replace(".TW","")

            if code in ETF_LIST:
                hold_list.append({
                    "name":name,"ticker":ticker,"cost":cost,"shares":shares,
                    "csv_price":csv_price,"pnl_pct":csv_pnl_pct,"score":0,"category":"hold",
                    "atr_stop":0,"trail_stop":0,"inst_note":"ETF",
                    "rsi":50,"macd_hist":0,"k_val":50,"d_val":50,
                    "atr":0,"ma20":0,"above_ma20":True,"stop_price":0,
                    "total_pnl":total_pnl,"is_etf":True,
                })
                continue

            ind=compute_indicators(ticker)
            if not ind:
                flat_list.append({
                    "name":name,"ticker":ticker,"cost":cost,"shares":shares,
                    "csv_price":csv_price,"pnl_pct":csv_pnl_pct,"score":0,"category":"flat",
                    "atr_stop":0,"trail_stop":0,"inst_note":"資料不足",
                    "rsi":0,"macd_hist":0,"k_val":0,"d_val":0,
                    "atr":0,"ma20":0,"above_ma20":False,"stop_price":0,
                    "total_pnl":total_pnl,"is_etf":False,
                })
                continue

            cls=classify_holding(ind,csv_price,cost)
            _,inst_note=get_institutional(ticker)
            sd={
                "name":name,"ticker":ticker,"cost":cost,"shares":shares,
                "csv_price":csv_price,        # 顯示用：CSV市價
                "pnl_pct":csv_pnl_pct,        # 顯示用：CSV報酬率
                "score":cls["score"],"category":cls["category"],
                "atr_stop":cls["atr_stop"],"trail_stop":cls["trail_stop"],
                "inst_note":inst_note,
                "rsi":ind["rsi"],"macd_hist":ind["macd_hist"],
                "k_val":ind["k_val"],"d_val":ind["d_val"],
                "atr":ind["atr"],"ma20":ind["ma20"],
                "above_ma20":ind["above_ma20"],"stop_price":cls["atr_stop"],
                "total_pnl":total_pnl,"is_etf":False,
            }
            if cls["category"]=="sell": sell_list.append(sd)
            elif cls["category"]=="flat": flat_list.append(sd)
            else: hold_list.append(sd)

        sub1,sub2,sub3=st.tabs([
            "🛑 賣出/停損 ("+str(len(sell_list))+")",
            "⚖️ 攤平 ("+str(len(flat_list))+")",
            "💎 續抱 ("+str(len(hold_list))+")"
        ])

        def render_card(s,tab_key=""):
            pnl=s["pnl_pct"]
            pnl_color="#3fb950" if pnl>=0 else "#f85149"
            cat=s["category"]; is_etf=s.get("is_etf",False)
            badge_class="bg-sell" if cat=="sell" else ("bg-flat" if cat=="flat" else "bg-hold")
            cat_label="賣出/停損" if cat=="sell" else ("攤平" if cat=="flat" else ("ETF長抱" if is_etf else "續抱"))
            score_str=("+" if s["score"]>=0 else "")+str(s["score"])
            pnl_amt=s.get("total_pnl",0)
            pnl_amt_str=("+" if pnl_amt>=0 else "")+"{:,.0f}".format(pnl_amt)
            # 顯示：市價(CSV) | 成本 | 股數 | 損益% | 損益$
            display_price=s["csv_price"]
            label=s["name"]+"  "+str(round(display_price,1))+"  "+("+" if pnl>=0 else "")+str(round(pnl,2))+"%"

            with st.expander(label,expanded=False):
                st.markdown('<div class="badge '+badge_class+'">建議：'+cat_label+('' if is_etf else ' | 評分 '+score_str)+'</div>',unsafe_allow_html=True)
                if is_etf:
                    st.caption("ETF不做技術分析，建議依自身策略操作")
                    st.markdown(
                        '<div class="pgrid-4">'
                        +'<div class="pbox"><span class="pl">市價(CSV)</span><span class="pv">'+str(round(display_price,2))+'</span></div>'
                        +'<div class="pbox"><span class="pl">成本</span><span class="pv">'+str(round(s["cost"],2))+'</span></div>'
                        +'<div class="pbox"><span class="pl">損益%</span><span class="pv" style="color:'+pnl_color+';">'+("+" if pnl>=0 else "")+str(round(pnl,2))+"%</span></div>"
                        +'<div class="pbox"><span class="pl">損益$</span><span class="pv" style="color:'+pnl_color+';">'+pnl_amt_str+'</span></div>'
                        +'</div>',unsafe_allow_html=True
                    )
                else:
                    above_lbl="✅上方" if s["above_ma20"] else "❌下方"
                    st.markdown(
                        '<div class="pgrid-5">'
                        +'<div class="pbox"><span class="pl">市價(CSV)</span><span class="pv">'+str(round(display_price,1))+'</span></div>'
                        +'<div class="pbox"><span class="pl">成本</span><span class="pv">'+str(round(s["cost"],1))+'</span></div>'
                        +'<div class="pbox"><span class="pl">股數</span><span class="pv">'+"{:,.0f}".format(s["shares"])+'</span></div>'
                        +'<div class="pbox"><span class="pl">損益%</span><span class="pv" style="color:'+pnl_color+';">'+("+" if pnl>=0 else "")+str(round(pnl,2))+"%</span></div>"
                        +'<div class="pbox"><span class="pl">損益$</span><span class="pv" style="color:'+pnl_color+';">'+pnl_amt_str+'</span></div>'
                        +'</div>'
                        +'<div class="atr-box">🛡️ ATR停損：<b>'+str(round(s["atr_stop"],1))+'</b> | 追蹤停利：<b>'+str(round(s["trail_stop"],1))+'</b></div>'
                        +'<div class="sbar">RSI:'+str(round(s["rsi"],1))+" | MACD:"+str(round(s["macd_hist"],3))+" | K:"+str(round(s["k_val"],1))+" D:"+str(round(s["d_val"],1))+" | 20MA:"+str(round(s["ma20"],1))+" "+above_lbl+"</div>"
                        +'<div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">法人：'+s["inst_note"]+'</div>',
                        unsafe_allow_html=True
                    )
                    render_kline_chart(s["ticker"],s["name"])
                    if ai_enabled:
                        if st.button("🤖 AI分析",key="ai_h_"+s["ticker"]+"_"+tab_key):
                            with st.spinner("AI分析中..."):
                                result=call_ai(build_stock_prompt(s))
                            if result:
                                st.markdown('<div class="ai-box"><div class="ai-title">AI分析</div><div class="ai-content">'+result+'</div></div>',unsafe_allow_html=True)
                    else:
                        st.caption("未設定API Key，無法使用AI分析")

        with sub1:
            if sell_list:
                for s in sell_list: render_card(s,"sell")
            else: st.success("✅ 目前無需賣出/停損的持股")
        with sub2:
            if flat_list:
                for s in flat_list: render_card(s,"flat")
            else: st.success("✅ 目前無需攤平的持股")
        with sub3:
            if hold_list:
                for s in hold_list: render_card(s,"hold")
            else: st.info("目前無續抱標的")


with tab_pick:
    held_tickers=[]
    for h in holdings:
        t=str(h["ticker"]).strip()
        held_tickers+=[t,t+".TW",t.replace(".TW","")]

    st.caption("依技術評分排序，⭐MACD翻正/均線突破優先，至少5個")

    if st.button("🔄 掃描推薦標的",type="primary"):
        with st.spinner("掃描中，約需30~60秒..."):
            picks=scan_recommendations(held_tickers)
            st.session_state["picks"]=picks
            st.session_state["pick_reasons"]={}

    picks=st.session_state.get("picks",[])
    pick_reasons=st.session_state.get("pick_reasons",{})

    if picks:
        if ai_enabled:
            col_a1,col_a2=st.columns(2)
            with col_a1:
                if st.button("🤖 AI今日市場總覽"):
                    with st.spinner("AI分析市場..."):
                        result=call_ai(build_market_prompt(picks,mkt_data_for_ai))
                    if result:
                        st.markdown('<div class="ai-market-box"><div class="ai-market-title">AI今日市場總覽</div><div class="ai-content">'+result+'</div></div>',unsafe_allow_html=True)
            with col_a2:
                if st.button("🤖 一鍵分析所有推薦"):
                    for p in picks:
                        with st.spinner("分析 "+p["name"]+"..."):
                            r=call_ai(build_pick_prompt(p))
                            if r: pick_reasons[p["ticker"]]=r
                    st.session_state["pick_reasons"]=pick_reasons
                    st.rerun()

        st.markdown("---")
        for p in picks:
            pt_tag="🚀 MACD剛翻正" if p.get("macd_flip") else ("💥 均線突破" if p.get("squeeze_break") else "")
            lbl=("⭐ " if p["priority"] else "")+p["name"]+"  "+p["ticker"]+"  評分+"+str(p["score"])+"  RSI"+str(round(p["rsi"],0))

            with st.expander(lbl,expanded=bool(p["priority"])):
                pt_html='<span style="background:#0d3d1a;color:#3fb950;border-radius:4px;padding:2px 8px;font-size:0.72rem;">'+pt_tag+"</span>" if pt_tag else ""
                st.markdown(
                    '<div class="pick-card">'
                    +'<span class="pick-name">'+p["name"]+'</span>'
                    +'<span class="pick-tag">'+p["ticker"]+'</span>'
                    +'<span class="pick-score">評分 +'+str(p["score"])+'</span>'
                    +pt_html
                    +'<div class="pick-info">現價 '+str(round(p["price"],1))+" | RSI "+str(round(p["rsi"],0))+" | 量比 "+str(round(p["vol_ratio"],1))+"x | 20MA "+str(round(p["ma20"],1))+"</div>"
                    +'<div class="pick-entry">📍 建議入手：'+str(p["entry"])+'</div>'
                    +'<div class="pick-atr">🛡️ 停損：'+str(p["stop"])+" | 目標："+str(p["target"])+" (+10%) | 風報比 "+str(p["rr"])+"</div>"
                    +'</div>',unsafe_allow_html=True
                )
                render_kline_chart(p["ticker"],p["name"])
                reason=pick_reasons.get(p["ticker"],"")
                if reason:
                    st.markdown('<div class="ai-box"><div class="ai-title">AI分析（公司介紹+推薦原因）</div><div class="ai-content">'+reason+'</div></div>',unsafe_allow_html=True)
                elif ai_enabled:
                    if st.button("🤖 AI分析 "+p["name"],key="ai_p_"+p["ticker"]):
                        with st.spinner("AI分析中..."):
                            r=call_ai(build_pick_prompt(p))
                        if r:
                            pick_reasons[p["ticker"]]=r
                            st.session_state["pick_reasons"]=pick_reasons
                            st.markdown('<div class="ai-box"><div class="ai-title">AI分析</div><div class="ai-content">'+r+'</div></div>',unsafe_allow_html=True)
                else:
                    st.caption("未設定API Key（需 AIza...開頭的 Gemini Key）")
    else:
        st.info("點擊上方「🔄 掃描推薦標的」開始掃描")

