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
.block-container{padding:0.5rem 0.6rem 4rem!important;max-width:100%!important;}
.hero-box{background:linear-gradient(135deg,#1a1f2e,#0f3460);border:1px solid #30363d;border-radius:10px;padding:10px 14px;margin-bottom:8px;}
.hero-title{font-size:1.1rem;font-weight:800;color:#e6edf3;margin:0;}
.hero-sub{color:#8b949e;font-size:0.68rem;margin-top:2px;}
div[data-testid="stTabs"]>div:first-child button{font-size:0.85rem!important;font-weight:700!important;padding:7px 10px!important;}
div[data-testid="stExpander"]>details{background:#161b22!important;border:1px solid #30363d!important;border-radius:10px!important;margin-bottom:6px!important;}
div[data-testid="stExpander"]>details>summary{font-size:0.88rem!important;font-weight:600!important;color:#e6edf3!important;padding:9px 12px!important;}
.badge{display:block;border-radius:7px;padding:7px 10px;font-size:0.8rem;font-weight:600;margin:5px 0;}
.bg-sell{background:#3d1a1a;color:#f85149;border:1px solid #da3633;}
.bg-flat{background:#3d2e00;color:#e3b341;border:1px solid #9e6a03;}
.bg-hold{background:#1a4731;color:#3fb950;border:1px solid #238636;}
.bg-strong{background:#0d2a1f;color:#56d364;border:1px solid #238636;}
.bg-add{background:#0a2040;color:#79c0ff;border:1px solid #1f6feb;}
.bg-watch{background:#2a2000;color:#e3b341;border:1px solid #9e6a03;}
.bg-reduce{background:#2a1500;color:#ffa657;border:1px solid #d1242f;}
.bg-stop{background:#3d1a1a;color:#f85149;border:1px solid #da3633;}
.bg-nodata{background:#1c1c1c;color:#8b949e;border:1px solid #484f58;}
.bg-etf{background:#1a3040;color:#7ee787;border:1px solid #3fb950;}
.pbox{background:#21262d;border-radius:6px;padding:5px 4px;text-align:center;}
.pbox .pl{font-size:0.58rem;color:#8b949e;text-transform:uppercase;display:block;margin-bottom:1px;}
.pbox .pv{font-size:0.85rem;font-weight:700;color:#e6edf3;display:block;}
.atr-box{background:#1a2233;border:1px solid #1f6feb;border-radius:6px;padding:6px 10px;margin:5px 0;font-size:0.75rem;color:#79c0ff;}
.sbar{background:#21262d;border-radius:5px;padding:6px 8px;margin:5px 0;font-family:monospace;font-size:0.72rem;color:#c9d1d9;word-break:break-all;}
.ai-box{background:linear-gradient(135deg,#0d1f12,#0a1628);border:1px solid #238636;border-radius:8px;padding:7px 10px;margin:5px 0;}
.ai-title{font-size:0.78rem;color:#3fb950;font-weight:600;margin-bottom:3px;}
.ai-content{font-size:0.82rem;color:#c9d1d9;line-height:1.4;white-space:pre-wrap;word-break:break-word;}
.pick-card{background:#161b22;border:1px solid #30363d;border-left:3px solid #58a6ff;border-radius:9px;padding:10px 12px;margin-bottom:7px;}
.pick-name{font-size:0.95rem;font-weight:700;color:#e6edf3;}
.pick-tag{background:#21262d;color:#8b949e;border-radius:4px;padding:1px 5px;font-size:0.65rem;margin-left:3px;}
.pick-score{float:right;color:#58a6ff;font-weight:700;font-size:0.85rem;}
.pick-info{font-size:0.75rem;color:#8b949e;margin-top:3px;}
.pick-entry{color:#79c0ff;font-weight:600;font-size:0.82rem;margin-top:5px;}
.pick-atr{background:#1a2233;border-radius:4px;padding:3px 7px;font-size:0.7rem;color:#58a6ff;margin-top:3px;display:inline-block;}
</style>
""", unsafe_allow_html=True)

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
    if not provider: return "未設定 API Key"
    if provider == "claude":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(model="claude-opus-4-5", max_tokens=4096,
                system="台股技術分析師。繁體中文，條列式，精簡，每點不超過2行，不要免責聲明。",
                messages=[{"role":"user","content":prompt}])
            return msg.content[0].text.strip()
        except Exception as e: return "Claude錯誤:"+str(e)
    elif provider == "openai":
        try:
            import openai
            resp = openai.OpenAI(api_key=key).chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"台股分析師，繁體中文，條列式，精簡"},
                          {"role":"user","content":prompt}], max_tokens=4096, temperature=0.3)
            return resp.choices[0].message.content.strip()
        except Exception as e: return "OpenAI錯誤:"+str(e)
    elif provider == "gemini":
        headers = {"Content-Type":"application/json"}
        if key.startswith("AQ."): headers["x-goog-api-key"] = key
        payload = {"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":8192,"temperature":0.3}}
        last_err = ""
        for model in ["gemini-2.5-flash","gemini-2.0-flash","gemini-2.0-flash-lite"]:
            try:
                url = "https://generativelanguage.googleapis.com/v1beta/models/"+model+":generateContent"
                if not key.startswith("AQ."): url += "?key="+key
                r = requests.post(url, headers=headers, json=payload, timeout=30)
                if r.status_code == 200: return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                elif r.status_code == 429: last_err = "配額超限"; continue
                else: last_err = model+":"+str(r.status_code); continue
            except Exception as e: last_err = str(e); continue
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
    "群創":"3481.TW","友達":"2409.TW","遠傳":"4904.TW","台灣大":"3045.TW","中華電":"2412.TW",
    "國泰金":"2882.TW","富邦金":"2881.TW","中信金":"2891.TW","兆豐金":"2886.TW",
    "玉山金":"2884.TW","台塑":"1301.TW","南亞":"1303.TW","台化":"1326.TW",
    "台塑化":"6505.TW","中鋼":"2002.TW","長榮":"2603.TW","陽明":"2609.TW",
    "萬海":"2615.TW","華航":"2610.TW","長榮航空":"2618.TW",
    "可成":"2474.TW","巨大":"9921.TW","正新":"2105.TW","世芯-KY":"3661.TW",
    "力積電":"6770.TW","南亞科":"2408.TW","華邦電":"2344.TW","旺宏":"2337.TW",
    "緯穎":"6669.TW","英業達":"2356.TW","技嘉":"2376.TW","微星":"2377.TW","健鼎":"3044.TW",
    "主動統一升級50":"00957.TW","元大高股息":"0056.TW","國泰永續高股息":"00878.TW",
    "群益台灣精選高息":"00919.TW","元大台灣50":"0050.TW","富邦台50":"006208.TW",
    "永豐台灣ESG":"00888.TW","中信關鍵半導體":"00891.TW",
}
ETF_LIST = {"00957.TW","0056.TW","00878.TW","00919.TW","0050.TW","006208.TW","00888.TW","00891.TW"}
SECTOR_GROUPS={"AI半導體":["台積電","聯發科","日月光投控","矽力-KY","世界","聯電","力積電","群聯","瑞昱"],"PCB電路板":["欣興","金像電","臻鼎-KY","健鼎","耀華","台光電","南電","燿華"],"面板顯示":["群創","友達","彩晶"],"電源管理":["台達電","光寶科"],"組裝代工":["鴻海","廣達","緯創","英業達","仁寶","和碩"]}
NON_CORE=["群創","友達","金像電","欣興","彩晶"]
DEFENSIVE_STOCKS={"中華電","遠傳","台灣大","中鋼","台塑化","台塑","南亞","長榮","陽明","萬海"}
GROWTH_STOCKS={"台積電","聯發科","鴻海","廣達","緯創","台達電","技嘉","微星","緯穎","日月光投控","奇鋐","雙鴻","矽力-KY","祥碩","信驊","世芯-KY","聯詠","群聯","瑞昱"}
RECOMMEND_POOL = [
    ("台積電","2330.TW"),("聯發科","2454.TW"),("鴻海","2317.TW"),("台達電","2308.TW"),
    ("廣達","2382.TW"),("緯創","3231.TW"),("日月光投控","3711.TW"),("聯詠","3034.TW"),
    ("矽力-KY","6415.TW"),("祥碩","5269.TW"),("信驊","5274.TW"),("神盾","6462.TW"),
    ("奇鋐","3017.TW"),("雙鴻","3324.TW"),("世芯-KY","3661.TW"),("玉晶光","3406.TW"),
    ("大立光","3008.TW"),("欣興","3037.TW"),("金像電","2368.TW"),("健鼎","3044.TW"),
    ("長榮","2603.TW"),("陽明","2609.TW"),("台塑化","6505.TW"),("中鋼","2002.TW"),
    ("力積電","6770.TW"),("南亞科","2408.TW"),("華邦電","2344.TW"),("旺宏","2337.TW"),
    ("緯穎","6669.TW"),("技嘉","2376.TW"),("微星","2377.TW"),("英業達","2356.TW"),
    ("群聯","8299.TW"),("瑞昱","2379.TW"),("遠傳","4904.TW"),("台灣大","3045.TW"),("中華電","2412.TW"),
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
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        return df if len(df) >= 5 else None
    except: return None

def get_current_price(ticker):
    try:
        p = yf.Ticker(ticker).fast_info.last_price
        if p and p > 0: return round(float(p), 2)
    except: pass
    df = fetch_stock(ticker, "5d")
    if df is not None and len(df) > 0: return round(float(df["Close"].iloc[-1]), 2)
    return None

def calc_indicators(df):
    if df is None or len(df)<20: return {}
    c=df["Close"].values.flatten().astype(float); v=df["Volume"].values.flatten().astype(float)
    delta=np.diff(c); gain=np.where(delta>0,delta,0); loss=np.where(delta<0,-delta,0)
    ag=np.convolve(gain,np.ones(14)/14,mode='valid'); al=np.convolve(loss,np.ones(14)/14,mode='valid')
    rsi=100-100/(1+ag[-1]/(al[-1]+1e-9))
    def ema(x,n):
        e=np.zeros(len(x)); e[n-1]=np.mean(x[:n])
        for i in range(n,len(x)): e[i]=x[i]*2/(n+1)+e[i-1]*(1-2/(n+1))
        return e
    e12=ema(c,12); e26=ema(c,26); macd=e12-e26; sig=ema(macd[25:],9); hist=macd[25:]-sig
    n=9
    lows=[min(df["Low"].values.flatten()[max(0,i-n+1):i+1]) for i in range(len(c))]
    highs=[max(df["High"].values.flatten()[max(0,i-n+1):i+1]) for i in range(len(c))]
    rsv=[(c[i]-lows[i])/(highs[i]-lows[i]+1e-9)*100 for i in range(len(c))]
    K=50.0; D=50.0
    for r in rsv: K=K*2/3+r/3; D=D*2/3+K/3
    ma20=np.mean(c[-20:])
    tr=[max(df["High"].values.flatten()[i]-df["Low"].values.flatten()[i],
            abs(df["High"].values.flatten()[i]-c[i-1]) if i>0 else 0,
            abs(df["Low"].values.flatten()[i]-c[i-1]) if i>0 else 0) for i in range(len(c))]
    atr=np.mean(tr[-14:]) if len(tr)>=14 else np.mean(tr)
    avg_v=np.mean(v[-20:]) if len(v)>=20 else np.mean(v)
    inst=round((v[-1]-avg_v)*c[-1]/1e8,1)
    return {"rsi":round(rsi,1),"macd":round(hist[-1],3) if len(hist)>0 else 0,
            "macd_cross":bool(hist[-1]>0) if len(hist)>0 else False,
            "k":round(K,1),"d":round(D,1),"ma20":round(ma20,1),"above_ma20":bool(c[-1]>ma20),
            "atr":round(atr,2),"inst":inst,"price":round(float(c[-1]),2),"bearish_day":bool(float(df["Open"].iloc[-1])>float(c[-1])),"open_price":round(float(df["Open"].iloc[-1]),2)}

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
    for name,t in {"台指":"^TWII","納指":"^IXIC","TSM":"TSM"}.items():
        try:
            info=yf.Ticker(t).fast_info
            res[name]={"price":round(info.last_price,2),"change_pct":round((info.last_price-info.previous_close)/info.previous_close*100,2)}
        except: res[name]={"price":0,"change_pct":0}
    return res

def parse_csv(f):
    try: content=f.read().decode("utf-8-sig")
    except: content=f.read().decode("big5",errors="ignore")
    stocks=[]
    for row in csv_module.reader(io.StringIO(content)):
        if len(row)<5: continue
        name=row[0].strip().strip('"')
        if name in ["股票名稱","名稱",""] or name.startswith("#"): continue
        try: shares=float(str(row[1]).replace(",","").strip().strip('"'))
        except: continue
        try: cost=float(str(row[4]).replace(",","").strip().strip('"'))
        except: continue
        if shares>0 and cost>0: stocks.append({"name":name,"shares":shares,"cost":cost})
    return stocks

def analyze_portfolio(stocks):
    results=[]
    for s in stocks:
        ticker=get_ticker(s["name"]); ind={}; price=None
        is_etf=ticker in ETF_LIST if ticker else False
        if ticker:
            price=get_current_price(ticker)
            if not is_etf:
                df=fetch_stock(ticker)
                if df is not None and len(df)>=20:
                    ind=calc_indicators(df)
                    if ind and "price" in ind: price=ind["price"]
        if not price or price<=0: price=s["cost"]
        pnl_pct=(price-s["cost"])/s["cost"]*100 if s["cost"]>0 else 0
        pnl_amt=(price-s["cost"])*s["shares"]
        results.append({**s,"ticker":ticker,"price":price,"ind":ind,
                        "pnl_pct":pnl_pct,"pnl_amt":pnl_amt,"score":score_stock(ind),
                        "is_etf":is_etf,"price_ok":(price!=s["cost"])})
    # Compute position percentages
    total_val=sum(r["price"]*r["shares"] for r in results if r.get("price_ok"))
    for r in results:
        r["pos_pct"]=round(r["price"]*r["shares"]/total_val*100,1) if total_val>0 else 0
        sector=""
        for sg,names in SECTOR_GROUPS.items():
            if r["name"] in names: sector=sg; break
        sector_total=sum(x["price"]*x["shares"] for x in results if x.get("price_ok") and any(x["name"] in n for n in [SECTOR_GROUPS.get(sector,[])]))
        r["sector_heavy"]=sector!="" and total_val>0 and sector_total/total_val>0.45
        r["is_noncore"]=r["name"] in NON_CORE
    return results

def classify(r):
    if not r.get("price_ok"): return "nodata"
    if r.get("is_etf"): return "etf"
    sc=r.get("score",0); pnl=r.get("pnl_pct",0)
    pos=r.get("pos_pct",0); heavy=r.get("sector_heavy",False)
    noncore=r.get("is_noncore",False)
    above_ma=r.get("ind",{}).get("above_ma20",False) if r.get("ind") else False
    if sc<=0 and pnl<-15: return "stop"
    if pnl<-20: return "stop"
    if sc<=1: return "reduce"
    if noncore and pnl>10 and sc<3: return "reduce"
    if pos>20 and sc<3: return "reduce"
    if heavy and sc<3: return "reduce"
    if sc>=4 and pnl>-5 and pos<=20 and not heavy and above_ma: return "add"
    if sc>=3 and pnl>-10 and above_ma: return "strong"
    return "watch"
def get_key_levels(r):
    price=r.get("price",0); cost=r.get("cost",0)
    ind=r.get("ind",{}) or {}
    ma20=ind.get("ma20",0); atr=ind.get("atr",0)
    if ma20>0:
        op_stop=round(max(ma20*0.97, cost*0.90),1)
        defend=round(max(ma20*0.99, cost*0.95),1)
    else:
        op_stop=round(cost*0.90,1)
        defend=round(cost*0.95,1)
    turn_strong=round(cost,1) if price<cost else round(cost*1.05,1)
    sys_stop=round(price-atr*2,1) if atr>0 and price>0 else op_stop
    return {"defend":defend,"turn_strong":turn_strong,"op_stop":op_stop,"sys_stop":sys_stop}

def generate_market_headline(mkt, holdings_names=[]):
    tw=mkt.get("台指",{}).get("change_pct",0)
    nas=mkt.get("納指",{}).get("change_pct",0)
    tsm=mkt.get("TSM",{}).get("change_pct",0)
    if tsm<=-3: headline="台積電ADR重挫，AI持股今日先守不追"
    elif nas<=-1.5: headline="美股科技股轉弱，成長股今日偏觀望"
    elif tw<=-1: headline="台股走弱，今日以控風險為主"
    elif tw>=1 and nas>=1: headline="台美同步走強，強勢股觀察轉強價"
    elif tsm>=2: headline="台積電ADR走強，半導體族群有支撐"
    else: headline="盤勢訊號普通，依個股支撐與部位操作"
    focus_map={"鴻海":"鴻海看300","緯創":"緯創看176","台積電":"台積電跟ADR","欣興":"欣興守970","金像電":"金像電只觀察","群創":"群創反彈先處理","台達電":"台達電看大盤"}
    focus=[focus_map[n] for n in holdings_names if n in focus_map]
    return headline, "；".join(focus[:3])
def get_recommendations(mkt=None):
    # Market weakness filter: if TWI drops > 1%, no buy signal, show as watch only
    mkt_weak = False
    if mkt:
        tw_chg = mkt.get("台指",{}).get("change_pct",0)
        tsm_chg = mkt.get("TSM",{}).get("change_pct",0)
        if tw_chg <= -1 or tsm_chg <= -3: mkt_weak = True
    buy_picks=[]; watch_picks=[]; def_picks=[]
    for name,ticker in RECOMMEND_POOL:
        if ticker in ETF_LIST: continue
        df=fetch_stock(ticker,"2mo")
        if df is None or len(df)<20: continue
        ind=calc_indicators(df)
        if not ind: continue
        sc=score_stock(ind)
        if sc<2: continue
        is_def = name in DEFENSIVE_STOCKS
        is_growth = name in GROWTH_STOCKS
        bearish = ind.get("bearish_day",False)
        above_ma = ind.get("above_ma20",False)
        # Bearish day (open > close today) deducts 1 point for buy consideration
        buy_sc = sc - (1 if bearish else 0)
        entry = {"name":name,"ticker":ticker,"ind":ind,"score":sc,"buy_score":buy_sc,
                 "is_def":is_def,"is_growth":is_growth,"bearish":bearish,"mkt_weak":mkt_weak}
        if is_def:
            if sc>=2: def_picks.append(entry)
        elif mkt_weak or bearish or not above_ma:
            if sc>=3: watch_picks.append(entry)
        else:
            if buy_sc>=3: buy_picks.append(entry)
            elif sc>=2: watch_picks.append(entry)
    buy_picks.sort(key=lambda x:-x["buy_score"])
    watch_picks.sort(key=lambda x:-x["score"])
    def_picks.sort(key=lambda x:-x["score"])
    return buy_picks[:5], watch_picks[:5], def_picks[:3]
def show_kline(ticker,height=260):
    df=fetch_stock(ticker)
    if df is not None and len(df)>5:
        try:
            import plotly.graph_objects as go
            fig=go.Figure(data=[go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],increasing_line_color="#3fb950",decreasing_line_color="#f85149")])
            fig.update_layout(height=height,paper_bgcolor="#0d1117",plot_bgcolor="#0d1117",font_color="#c9d1d9",xaxis_rangeslider_visible=False,margin=dict(l=0,r=0,t=15,b=0))
            st.plotly_chart(fig,use_container_width=True)
        except: st.info("需安裝 plotly")

def prow(items):
    for lbl,val,color in items:
        st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 12px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;"><span style="color:#8b949e;font-size:0.78rem;">'+str(lbl)+'</span><span style="color:'+str(color)+';font-size:1rem;font-weight:700;">'+str(val)+'</span></div>',unsafe_allow_html=True)
def render_pick_card(p):
    ind=p["ind"]; sc=p["score"]; name=p["name"]; ticker=p["ticker"]
    price=ind.get("price",0); entry=round(ind.get("ma20",price)*0.99,1)
    inst_val=ind.get("inst",0)
    inst_txt=("法人買超 "+str(inst_val)+"億") if inst_val>0 else ("法人小幅參與 "+str(abs(inst_val))+"億")
    bearish=p.get("bearish",False); mkt_weak=p.get("mkt_weak",False)
    is_def=p.get("is_def",False); is_growth=p.get("is_growth",False)
    buy_sc=p.get("buy_score",sc)
    # Type badge and action label
    if is_def:
        type_label="🛡️ 防禦/穩定"; type_color="#6e7681"; action="觀察配置"
        reason="防禦型：高配息穩定，非短線攻擊標的"
    elif mkt_weak and not is_def:
        type_label="⚠️ 盤勢轉弱"; type_color="#e3b341"; action="僅觀察，不追價"
        reason="大盤走弱，即便技術分高，今日先觀察支撐，不追進"
    elif bearish:
        type_label="🟠 盤中轉弱"; type_color="#f0883e"; action="等止跌確認"
        reason="今日開高走低（賣壓重），扣1分，等收盤確認止跌後再評估"
    else:
        type_label="✅ 買進候選"; type_color="#3fb950"; action="可考慮分批進場"
        reason="技術面偏多，站上MA20，法人/KD/MACD同向"
    signals=[]
    if ind.get("above_ma20"): signals.append("✅MA20")
    if ind.get("macd_cross"): signals.append("📈MACD")
    if ind.get("k",50)<80 and ind.get("k",50)>ind.get("d",50): signals.append("🔁KD")
    if inst_val>0: signals.append("🏦法人")
    if bearish: signals.append("🔻開高走低")
    sig_str=" ".join(signals) if signals else "—"
    prow([("現價",str(price),"#e6edf3"),("評分",str(sc)+" → 買"+str(buy_sc) if bearish else "分數 +"+str(sc),"#79c0ff")])
    prow([("參考入手",str(entry),"#3fb950"),("法人",inst_txt,"#8b949e")])
    st.markdown('<div style="background:#21262d;border-left:3px solid '+type_color+';padding:6px 10px;border-radius:4px;margin:4px 0;">'
        +'<span style="color:'+type_color+';font-weight:700;font-size:0.8rem;">'+type_label+'</span>'
        +' <span style="color:#8b949e;font-size:0.75rem;">'+action+'</span><br>'
        +'<span style="color:#c9d1d9;font-size:0.72rem;">'+reason+'</span><br>'
        +'<span style="color:#8b949e;font-size:0.7rem;">'+sig_str+'</span>'
        +'</div>',unsafe_allow_html=True)
    ai_key="ai_pick_"+ticker
    c1,c2=st.columns(2)
    with c1:
        if st.button("📊 K線",key="kp_"+ticker):
            st.session_state["skp_"+ticker]=not st.session_state.get("skp_"+ticker,False)
    with c2:
        if st.button("🤖 AI分析",key="ap_"+ticker):
            with st.spinner("分析中..."):
                prompt=("[推薦股] "+name+"("+ticker+") | 現價"+str(price)+" | RSI"+str(round(ind.get("rsi",0),0))+" MACD"+str(round(ind.get("macd",0),2))+" K"+str(round(ind.get("k",0),0))+" 20MA"+str(round(ind.get("ma20",0),0))+" | "+inst_txt+" | 盤中:"+("開高走低" if bearish else "正常")+"\n你是台股分析師，數據已給你，禁止重複報價，今天日期是 "+str(datetime.date.today())+"，繁體中文，請完整輸出，每個段落獨立換行：\n【結論】一句話說明操作建議（買進/觀察/防禦）\n【走勢】技術面偏多或偏空，關鍵支撐壓力\n【理由】進場依據或等待條件\n【新聞】只引用近3個月內真實新聞，寫明月份，嚴禁捏造")
                st.session_state[ai_key]=call_ai(prompt)
    if st.session_state.get("skp_"+ticker): show_kline(ticker)
    if ai_key in st.session_state:
        with st.expander("🤖 AI分析（"+name+"）",expanded=True):
            raw=str(st.session_state[ai_key]).replace("<","&lt;").replace(">","&gt;")
            _colors={"結論":"#f0883e","走勢":"#79c0ff","理由":"#e3b341","新聞":"#7ee787"}
            import re
            parts=re.split(r'(【[^】]+】)',raw)
            html=""
            cur_color="#c9d1d9"; cur_tag=""
            for part in parts:
                m=re.match(r'【([^】]+)】',part)
                if m:
                    cur_tag=m.group(1); cur_color=_colors.get(cur_tag,"#c9d1d9")
                    html+='<div style="color:'+cur_color+';font-weight:700;margin-top:8px;">【'+cur_tag+'】</div>'
                elif part.strip():
                    html+='<div style="border-left:2px solid '+cur_color+';padding-left:8px;margin-bottom:4px;color:#c9d1d9;font-size:0.82rem;">'+part.strip()+'</div>'
            st.markdown(html,unsafe_allow_html=True)
def render_stock_card(r):
    name=r["name"]; price=r["price"]; cost=r["cost"]; shares=r["shares"]
    pnl_pct=r["pnl_pct"]; pnl_amt=r["pnl_amt"]; ind=r["ind"]; sc=r["score"]
    ticker=r.get("ticker",""); price_ok=r.get("price_ok",False); is_etf=r.get("is_etf",False)
    pnl_color="#3fb950" if pnl_pct>=0 else "#f85149"
    pnl_sign="+" if pnl_pct>=0 else ""
    cl=classify(r)
    badge_map={"stop":("bg-stop","🔴 停損/出場"),"reduce":("bg-reduce","🟠 反彈減碼"),"watch":("bg-watch","⚠️ 觀望等待"),"strong":("bg-strong","💎 強勢續抱"),"add":("bg-add","➕ 條件加碼"),"etf":("bg-etf","💚 ETF長期持有"),"nodata":("bg-nodata","⚙️ 資料不足")}
    badge_cls,badge_txt=badge_map.get(cl,("bg-watch","⚠️ 觀望等待"))
    if cl=="nodata": badge_txt+=" — 現價異常，請重新抓取"
    if r.get("pos_pct",0)>20 and cl not in ("stop","nodata","etf"): badge_txt+=" ⚠️單檔過重"
    if r.get("sector_heavy",False) and cl not in ("stop","nodata","etf"): badge_txt+=" ⚠️族群過重"
    if not price_ok:
        col_r1,col_r2=st.columns([3,1])
        with col_r1: prow([("現價", "⚙️ 資料不足", "#8b949e")])
        with col_r2:
            if st.button("🔄",key="retry_"+name,help="重新抓取現價"):
                new_p=get_current_price(ticker)
                if new_p and new_p>0:
                    r["price"]=new_p; r["price_ok"]=True
                    r["pnl_pct"]=(new_p-cost)/cost*100 if cost>0 else 0
                    r["pnl_amt"]=(new_p-cost)*shares
                    st.rerun()
    else:
        prow([("現價", str(price), "#e6edf3")])
    prow([("成本", str(cost), "#8b949e")])
    if price_ok:
        prow([("損益", pnl_sign+str(int(pnl_amt))+" ("+pnl_sign+str(round(pnl_pct,1))+"%)", pnl_color)])
    else:
        prow([("損益", "取得中", "#8b949e")])
    prow([("評分", ("+"+str(sc) if sc>0 else str(sc)), "#58a6ff")])
    if ind:
        atr_stop=round(price-ind.get("atr",0)*2,1); trail_stop=round(price*0.95,1)
        kl=get_key_levels(r)
        st.markdown('<div class="atr-box">🛡 操作停損 <b>'+str(kl["op_stop"])+'</b>｜防守 <b>'+str(kl["defend"])+'</b>｜轉強 <b>'+str(kl["turn_strong"])+'</b></div>',unsafe_allow_html=True)
        ma_icon="✅" if ind.get("above_ma20") else "❌"; ma_dir="上方" if ind.get("above_ma20") else "下方"
        st.markdown('<div class="sbar">RSI:'+str(ind.get("rsi","-"))+' MACD:'+str(round(ind.get("macd",0),3))+' K:'+str(ind.get("k","-"))+'/D:'+str(ind.get("d","-"))+' MA20:'+str(ind.get("ma20","-"))+' '+ma_icon+ma_dir+'</div>',unsafe_allow_html=True)
        inst=ind.get("inst",0)
        st.markdown('<div style="font-size:0.68rem;color:#8b949e;margin:3px 0;">'+("法人買超 "+str(inst)+"億" if inst>0 else "法人小幅參與 "+str(abs(inst))+"億")+'</div>',unsafe_allow_html=True)
    elif is_etf: st.markdown('<div class="sbar">ETF — 依配息策略持有</div>',unsafe_allow_html=True)
    ai_key="aih_"+name
    c1,c2=st.columns(2)
    with c1:
        if ticker and st.button("📈 K線",key="kh_"+name):
            st.session_state["skh_"+name]=not st.session_state.get("skh_"+name,False)
    with c2:
        if st.button("🤖 AI分析",key="ah_"+name):
            with st.spinner("分析中..."):
                rsi_v=str(ind.get("rsi","-")); macd_v=str(round(ind.get("macd",0),3))
                k_v=str(ind.get("k","-")); d_v=str(ind.get("d","-")); ma_v=str(ind.get("ma20","-")); atr_v=str(round(ind.get("atr",0),2))
                inst_disp=("法人買超"+str(round(inst,1))+"億") if inst>0 else "法人小幅參與"
                prompt=("[持股] "+name+"("+str(ticker)+") | 現價"+str(price)+" 成本"+str(cost)+" 損益"+str(round(pnl_pct,1))+"% | RSI "+rsi_v+" K "+k_v+" | "+inst_disp+"\n你是台股分析師，數據已給你，禁止重複報價，今天日期是 "+str(datetime.date.today())+"，繁體中文，請完整輸出，每個段落獨立換行：\n【結論】一句話說明現在操作建議\n【走勢】技術面偏多或偏空，關鍵支撐壓力\n【理由】為何適合或不適合現在操作\n【新聞】只引用近3個月內真實新聞，寫明月份，嚴禁捏造"+(" (ETF:配息/績效分析)" if is_etf else ""))
                st.session_state[ai_key]=call_ai(prompt)
    if st.session_state.get(ai_key):
        with st.expander("🤖 AI分析（"+name+"）", expanded=True):
            _txt=st.session_state[ai_key]
            import re as _re
            _parts=_re.split(r'(【[^】]+】)',_txt)
            _colors={"結論":"#f0883e","走勢":"#79c0ff","理由":"#e3b341","新聞":"#7ee787","ETF":"#7ee787"}
            _cur_color="#c9d1d9"
            for _p in _parts:
                if _p.startswith("【") and _p.endswith("】"):
                    _key=_p[1:-1]
                    _cur_color=_colors.get(_key,"#c9d1d9")
                    st.markdown(f'<span style="color:{_cur_color};font-weight:700;font-size:0.95rem;">{_p}</span>',unsafe_allow_html=True)
                elif _p.strip():
                    st.markdown(f'<div style="color:#c9d1d9;font-size:0.88rem;line-height:1.6;margin:4px 0 12px 0;padding-left:8px;border-left:2px solid {_cur_color};">{_p.strip()}</div>',unsafe_allow_html=True)
    if st.session_state.get("skh_"+name) and ticker: show_kline(ticker)

def main():
    provider,_=get_ai_client()
    ai_label={"claude":"● Claude","openai":"● OpenAI","gemini":"● Gemini"}.get(provider,"需設定AI Key")
    now_str=datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    mkt=get_market_data()
    portfolio=st.session_state.get("portfolio",[])
    holdings_names=[s["name"] for s in portfolio]
    headline, focus_str = generate_market_headline(mkt, holdings_names)
    # Hero header
    focus_html=('<div style="font-size:0.72rem;color:#79c0ff;margin-top:2px;">'+focus_str+'</div>') if focus_str else ''
    st.markdown('<div class="hero-box"><div class="hero-title">'+headline+'<span style="font-size:0.65rem;color:#3fb950;margin-left:6px;">'+ai_label+'</span></div>'+focus_html+'<div class="hero-sub">'+now_str+'</div></div>',unsafe_allow_html=True)
    # Compact market strip
    tw_c=mkt.get("台指",{}).get("change_pct",0); nas_c=mkt.get("納指",{}).get("change_pct",0); tsm_c=mkt.get("TSM",{}).get("change_pct",0)
    def _mc(v): return ("#3fb950" if v>=0 else "#f85149")
    def _ms(v): return ("+" if v>=0 else "")+str(v)+"%"
    st.markdown('<div style="display:flex;gap:10px;padding:4px 0;font-size:0.72rem;flex-wrap:wrap;">'
        +'<span style="color:#8b949e;">台指</span><span style="color:'+_mc(tw_c)+';">'+str(int(mkt.get("台指",{}).get("price",0)))+' '+_ms(tw_c)+'</span>'
        +'<span style="color:#8b949e;">｜納指</span><span style="color:'+_mc(nas_c)+';">'+str(int(mkt.get("納指",{}).get("price",0)))+' '+_ms(nas_c)+'</span>'
        +'<span style="color:#8b949e;">｜TSM ADR</span><span style="color:'+_mc(tsm_c)+';">'+str(round(mkt.get("TSM",{}).get("price",0),1))+' '+_ms(tsm_c)+'</span>'
        +'</div>',unsafe_allow_html=True)
    # All-in-one tab bar: 匯入 | 持有股 | 推薦
    # CSV upload - always visible above tabs
    with st.expander("⬆️ 匯入持股 CSV", expanded=(not portfolio)):
        st.caption("券商匯出 CSV | 只讀名稱/股數/成交均價 | 市價即時抓")
        uploaded=st.file_uploader("上傳持股CSV",type=["csv","txt"],label_visibility="collapsed",key="csv_upload")
        if uploaded:
            stocks=parse_csv(uploaded)
            if stocks:
                st.session_state["portfolio"]=stocks
                portfolio=stocks
                st.caption("✅ 已載入 "+str(len(stocks))+" 筆持股："+", ".join([s["name"] for s in stocks]))
            else: st.error("❌ 解析失敗，請確認格式：名稱,股數,,,成本")
    tab1,tab2=st.tabs(["📁 持有股("+str(len(portfolio))+"筆)","⭐ 推薦"])
    with tab1:
        if not portfolio: st.info("請先匯入持股 CSV")
        else:
            results=analyze_portfolio(portfolio)
            stop_l=[r for r in results if classify(r)=="stop"]
            reduce_l=[r for r in results if classify(r)=="reduce"]
            watch_l=[r for r in results if classify(r)=="watch"]
            strong_l=[r for r in results if classify(r)=="strong"]
            add_l=[r for r in results if classify(r)=="add"]
            etf_l=[r for r in results if classify(r)=="etf"]
            nodata_l=[r for r in results if classify(r)=="nodata"]
            total_pnl=sum(r["pnl_amt"] for r in results if r.get("price_ok"))
            total_cost=sum(r["cost"]*r["shares"] for r in results if r.get("price_ok"))
            total_pnl_pct=total_pnl/total_cost*100 if total_cost>0 else 0
            pnl_col="#3fb950" if total_pnl>=0 else "#f85149"
            prow([("總損益",(("+" if total_pnl>=0 else "")+str(int(total_pnl))+"元（"+("+" if total_pnl_pct>=0 else "")+str(round(total_pnl_pct,1))+"%）"),pnl_col)])
            tabs=st.tabs(["🔴 停損("+str(len(stop_l))+")","🟠 減碼("+str(len(reduce_l))+")","⚠️ 觀望("+str(len(watch_l))+")","💎 續抱("+str(len(strong_l))+")","➕ 加碼("+str(len(add_l))+")","💚 ETF("+str(len(etf_l))+")","⚙️ 資料("+str(len(nodata_l))+")"])
            for ti,(tab,group) in enumerate(zip(tabs,[stop_l,reduce_l,watch_l,strong_l,add_l,etf_l,nodata_l])):
                with tab:
                    if not group: st.caption("本區無持股")
                    for r in group:
                        pnl_s="+" if r["pnl_pct"]>=0 else ""
                        pnl_t=(pnl_s+str(round(r["pnl_pct"],1))+"%") if r.get("price_ok") else "⚙️"
                        with st.expander(r["name"]+"  "+str(r["price"])+"  "+pnl_t,expanded=False):
                            render_stock_card(r)
    with tab2:
        st.caption("依技術評分排序 | 盤勢轉弱時不顯示買進訊號")
        with st.spinner("掃描推薦中..."):
            buy_picks,watch_picks,def_picks=get_recommendations(mkt)
        if not buy_picks and not watch_picks and not def_picks:
            st.info("目前無符合條件推薦股（評分≥2）")
        else:
            if buy_picks:
                st.markdown('<div style="color:#3fb950;font-weight:700;font-size:0.85rem;margin:4px 0;">✅ 買進候選</div>',unsafe_allow_html=True)
                for p in buy_picks:
                    with st.expander(p["name"]+"  "+p["ticker"]+"  +"+str(p["buy_score"])+"分",expanded=False):
                        render_pick_card(p)
            if watch_picks:
                st.markdown('<div style="color:#e3b341;font-weight:700;font-size:0.85rem;margin:4px 0;">⚠️ 觀察/等確認</div>',unsafe_allow_html=True)
                for p in watch_picks:
                    with st.expander(p["name"]+"  "+p["ticker"]+"  +"+str(p["score"])+"分",expanded=False):
                        render_pick_card(p)
            if def_picks:
                st.markdown('<div style="color:#6e7681;font-weight:700;font-size:0.85rem;margin:4px 0;">🛡️ 防禦/穩定型</div>',unsafe_allow_html=True)
                for p in def_picks:
                    with st.expander(p["name"]+"  "+p["ticker"]+"  +"+str(p["score"])+"分",expanded=False):
                        render_pick_card(p)
if __name__ == "__main__":
    main()
