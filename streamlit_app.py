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
.hero-box{background:linear-gradient(135deg,#1a1f2e,#0f3460);border:1px solid #30363d;border-radius:8px;padding:6px 12px;margin-bottom:4px;}
.hero-title{font-size:0.95rem;font-weight:800;color:#e6edf3;margin:0;}
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
.bg-profit{background:#1f2a0a;color:#d2a679;border:1px solid #c9871f;}
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

def get_stock_news(name, ticker_num, max_items=4):
    """從 Google News RSS 抓取最近新聞標題，失敗回傳空字串"""
    try:
        import feedparser, urllib.parse
        query = urllib.parse.quote(name + " 股票")
        url = "https://news.google.com/rss/search?q=" + query + "&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            pub = entry.get("published","")[:16] if entry.get("published") else "近期"
            title = entry.get("title","").split(" - ")[0]
            items.append("• " + pub + " " + title)
        return "\n".join(items) if items else ""
    except:
        return ""

def get_ai_client():
    # 優先讀取用戶在 APP 內輸入的 API Key
    if st.session_state.get('user_api_key') and st.session_state.get('user_api_provider'):
        return st.session_state['user_api_provider'], st.session_state['user_api_key']
    # 其次讀取 Streamlit Cloud secrets
    try:
        key = st.secrets.get('ANTHROPIC_API_KEY','')
        if key and key.startswith('sk-ant'): return 'claude', key
    except: pass
    try:
        key = st.secrets.get('OPENAI_API_KEY','')
        if key: return 'openai', key
    except: pass
    try:
        key = st.secrets.get('GEMINI_API_KEY','')
        if key: return 'gemini', key
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
    "瑞昱":"2379.TW","聯詠":"3034.TW","矽力-KY":"6415.TWO","祥碩":"5269.TWO",
    "群聯":"8299.TW","智原":"3035.TWO","創意":"3443.TW","新應材":"4749.TWO",
    "玉晶光":"3406.TWO","大立光":"3008.TW","嘉澤":"3533.TWO","信驊":"5274.TWO",
    "神盾":"6462.TWO","力旺":"3529.TWO","金像電":"2368.TW","欣興":"3037.TW",
    "奇鋐":"3017.TWO","雙鴻":"3324.TWO","建準":"2421.TWO","超眾":"6230.TWO",
    "群創":"3481.TW","友達":"2409.TW","遠傳":"4904.TW","台灣大":"3045.TW","中華電":"2412.TW",
    "國泰金":"2882.TW","富邦金":"2881.TW","中信金":"2891.TW","兆豐金":"2886.TW",
    "玉山金":"2884.TW","台塑":"1301.TW","南亞":"1303.TW","台化":"1326.TW",
    "台塑化":"6505.TW","中鋼":"2002.TW","長榮":"2603.TW","陽明":"2609.TW",
    "萬海":"2615.TW","華航":"2610.TW","長榮航空":"2618.TW",
    "可成":"2474.TW","巨大":"9921.TW","正新":"2105.TW","世芯-KY":"3661.TWO",
    "力積電":"6770.TW","南亞科":"2408.TW","華邦電":"2344.TW","旺宏":"2337.TW",
    "緯穎":"6669.TW","英業達":"2356.TW","技嘉":"2376.TW","微星":"2377.TW","健鼎":"3044.TWO",
    "主動統一升級50":"00403A.TW","元大高股息":"0056.TW","國泰永續高股息":"00878.TW",
    "群益台灣精選高息":"00919.TW","元大台灣50":"0050.TW","富邦台50":"006208.TW",
    "永豐台灣ESG":"00888.TW","中信關鍵半導體":"00891.TW",
}
ETF_LIST = {"00403A.TW","0056.TW","00878.TW","00919.TW","0050.TW","006208.TW","00888.TW","00891.TW"}
SECTOR_GROUPS={"AI半導體":["台積電","聯發科","日月光投控","矽力-KY","世界","聯電","力積電","群聯","瑞昱"],"PCB電路板":["欣興","金像電","臻鼎-KY","健鼎","耀華","台光電","南電","燿華"],"面板顯示":["群創","友達","彩晶"],"電源管理":["台達電","光寶科"],"組裝代工":["鴻海","廣達","緯創","英業達","仁寶","和碩"]}
NON_CORE=["群創","友達","金像電","欣興","彩晶"]
DEFENSIVE_STOCKS={"中華電","遠傳","台灣大","中鋼","台塑化","台塑","南亞","長榮","陽明","萬海"}
GROWTH_STOCKS={"台積電","聯發科","鴻海","廣達","緯創","台達電","技嘉","微星","緯穎","日月光投控","奇鋐","雙鴻","矽力-KY","祥碩","信驊","世芯-KY","聯詠","群聯","瑞昱"}
# RECOMMEND_POOL: 台灣前150大市值，涵蓋各板塊，每週更新
# 板塊: AI半導體/電子/金融/航運/傳產/鋼鐵/電信/面板/生技/食品/航太/房建
RECOMMEND_POOL = [
    # --- AI / 半導體 ---
    ("台積電","2330"),("聯發科","2454"),("日月光投控","3711"),("聯電","2303"),
    ("力積電","6770"),("南亞科","2408"),("華邦電","2344"),("旺宏","2337"),
    ("矽力-KY","6415"),("祥碩","5269"),("信驊","5274"),("世芯-KY","3661"),
    ("瑞昱","2379"),("聯詠","3034"),("群聯","8299"),("智原","3035"),
    ("創意","3443"),("神盾","6462"),("力旺","3529"),("M31","6643"),
    # --- 伺服器 / AI 供應鏈 ---
    ("鴻海","2317"),("廣達","2382"),("緯創","3231"),("緯穎","6669"),
    ("英業達","2356"),("仁寶","2324"),("和碩","4938"),("技嘉","2376"),
    ("微星","2377"),("華碩","2357"),("宏碁","2353"),
    # --- 電源/散熱 ---
    ("台達電","2308"),("光寶科","2301"),("奇鋐","3017"),("雙鴻","3324"),
    ("建準","2421"),("超眾","6230"),
    # --- PCB / 載板 ---
    ("欣興","3037"),("金像電","2368"),("健鼎","3044"),("嘉澤","3533"),
    ("南電","8046"),("臻鼎-KY","4958"),("台光電","2383"),
    # --- 光學 / 鏡頭 ---
    ("大立光","3008"),("玉晶光","3406"),("先進光","3362"),
    # --- 面板 ---
    ("群創","3481"),("友達","2409"),
    # --- 記憶體模組 ---
    ("威剛","3260"),("宇瞻","8271"),
    # --- 金融 ---
    ("台灣金控","2892"),("國泰金","2882"),("富邦金","2881"),("中信金","2891"),
    ("兆豐金","2886"),("第一金","2892"),("玉山金","2884"),("元大金","2885"),
    ("永豐金","2890"),("合庫金","5880"),("開發金","2883"),("台新金","2887"),
    # --- 電信 ---
    ("中華電","2412"),("台灣大","3045"),("遠傳","4904"),
    # --- 航運 ---
    ("長榮","2603"),("陽明","2609"),("萬海","2615"),("台驊投控","2636"),
    ("慧洋-KY","2637"),("裕民","2606"),
    # --- 航空 ---
    ("華航","2610"),("長榮航空","2618"),
    # --- 石化 / 傳產 ---
    ("台塑","1301"),("南亞","1303"),("台化","1326"),("台塑化","6505"),
    ("奇美實業","3709"),("大連","1303"),
    # --- 鋼鐵 ---
    ("中鋼","2002"),("豐興","2015"),("東和鋼鐵","2006"),("燁輝","2023"),
    # --- 汽車零件 ---
    ("和泰車","2207"),("裕隆","2201"),("東陽","1319"),
    # --- 自行車 ---
    ("巨大","9921"),("美利達","9914"),
    # --- 食品飲料 ---
    ("統一","1216"),("統一超","2912"),("味全","1201"),("黑松","1234"),
    ("桂格","1227"),
    # --- 零售 / 百貨 ---
    ("全家","5903"),("遠東新","1402"),("潤泰全","2915"),
    # --- 生技醫療 ---
    ("台灣神隆","1789"),("生達","1720"),("杏輝","1734"),("東洋","4105"),
    ("晟德","4123"),("太景-KY","4157"),
    # --- 營建 ---
    ("國泰建設","2501"),("長虹","5534"),("興富發","2542"),("華固","2548"),
    # --- 電子通路 ---
    ("大聯大","3702"),("文曄","3036"),("聯強","2347"),
]

def get_ticker(name):
    name=name.strip()
    # 1. Exact match
    if name in NAME_TO_TICKER: return NAME_TO_TICKER[name]
    # 2. Fuzzy: prefer longer key match to avoid false positives
    best=None; best_len=0
    for k,v in NAME_TO_TICKER.items():
        if k in name or name in k:
            if len(k)>best_len: best=v; best_len=len(k)
    if best: return best
    # 3. Last resort: pure number in name → try as TW ticker (only if 4-6 digits standalone)
    import re as _re
    m=_re.search(r'(?<![\d])([0-9]{4,6}[A-Z]?)(?![\d])',name)
    if m:
        num=m.group(1)
        candidate=num+(".TW" if not num.endswith(".TW") else "")
        return candidate
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

@st.cache_data(ttl=86400)
def resolve_ticker(num):
    """Auto-detect .TW vs .TWO for a stock number. Returns resolved ticker or None."""
    if not num: return None
    # Already has suffix
    if num.endswith('.TW') or num.endswith('.TWO'): return num
    # Known OTC set (manually curated)
    _otc = {"6415","5269","5274","6462","3661","3017","3324","2421","6230","3044","3533",
            "3406","3529","3035","4749","8271","3362","3260","2637","4958","4123","4157"}
    if num in _otc: return num+".TWO"
    # Try .TW first (most stocks are listed)
    for suffix in (".TW",".TWO"):
        try:
            t = num+suffix
            df = yf.download(t, period="5d", interval="1d", progress=False, auto_adjust=True)
            if df is not None and not df.empty and len(df)>=1:
                return t
        except: pass
    return None


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

@st.cache_data(ttl=3600)
def get_us_overnight():
    res={}
    for name,t in {"SPY":"SPY","QQQ":"QQQ","DJI":"^DJI","NVDA":"NVDA","AMD":"AMD","SMH":"SMH","TSM_US":"TSM"}.items():
        try:
            df=yf.download(t,period="5d",interval="1d",progress=False,auto_adjust=True)
            if df is None or df.empty: continue
            if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            if len(df)<2: continue
            prev=float(df["Close"].iloc[-2]); last=float(df["Close"].iloc[-1])
            chg=round((last-prev)/prev*100,2)
            res[name]={"price":round(last,2),"change_pct":chg}
        except: res[name]={"price":0,"change_pct":0}
    return res

def generate_daily_brief(mkt, us, portfolio):
    sp=us.get("SPY",{}).get("change_pct",0); qq=us.get("QQQ",{}).get("change_pct",0)
    dj=us.get("DJI",{}).get("change_pct",0); nv=us.get("NVDA",{}).get("change_pct",0)
    am=us.get("AMD",{}).get("change_pct",0); sm=us.get("SMH",{}).get("change_pct",0)
    tsm=us.get("TSM_US",{}).get("change_pct",0)
    holdings=[s["name"] for s in portfolio]; hs=", ".join(holdings) if holdings else "尚未匯入持股"
    def s(v): return ("+"+str(v) if v>=0 else str(v))+"%"
    today=datetime.date.today().strftime("%m/%d")
    prompt=today+" 盤前：S&P500 "+s(sp)+" 道瓊 "+s(dj)+" QQQ "+s(qq)+" NVDA "+s(nv)+" AMD "+s(am)+" SMH "+s(sm)+" TSM ADR "+s(tsm)+" 台指昨日 "+s(mkt.get("台指",{}).get("change_pct",0))+" 持股："+hs+" 。請用繁體中文寫3-5句盤前操作總結，直接定調今日盤勢偏多偏空，點出哪個數據最影響持股，給出今日操作主軸（直接點名持股怎麼做），風格像老手操盤手，禁止免責聲明和廢話。"
    return call_ai(prompt)
def detect_csv_columns(f):
    """Read header row and return (headers, rows) for column mapping UI."""
    try: content=f.read().decode("utf-8-sig")
    except: content=f.read().decode("big5",errors="ignore")
    rows=[r for r in csv_module.reader(io.StringIO(content)) if any(c.strip() for c in r)]
    if not rows: return [],[],[]
    header=rows[0]
    data_rows=rows[1:] if len(rows)>1 else []
    return header,data_rows,content

def auto_guess_cols(header):
    """Guess column indices from header names. Returns dict or None if unclear."""
    NAME_KW=["名稱","股票名稱","股票","品名","有價證券名稱","商品名稱"]
    SHARES_KW=["股數","持有股數","庫存股數","數量","持股數","持有數量","實際庫存"]
    COST_KW=["均價","成本","成交均價","平均成本","均買價","每股成本","交易均價","現金成本","買進均價"]
    def find(kws):
        for kw in kws:
            for i,h in enumerate(header):
                if kw in h: return i
        return None
    ni=find(NAME_KW); si=find(SHARES_KW); ci=find(COST_KW)
    return {"name_col":ni,"shares_col":si,"cost_col":ci}

def parse_csv_with_map(content,col_map):
    """Parse CSV rows using given column mapping."""
    stocks=[]
    name_col=col_map["name_col"]; shares_col=col_map["shares_col"]; cost_col=col_map["cost_col"]
    needed=max(name_col,shares_col,cost_col)+1
    for row in csv_module.reader(io.StringIO(content)):
        if len(row)<needed: continue
        name=row[name_col].strip().strip('"')
        if not name or name in ["股票名稱","名稱","品名","有價證券名稱"] or name.startswith("#"): continue
        try: shares=float(str(row[shares_col]).replace(",","").strip().strip('"'))
        except: continue
        try: cost=float(str(row[cost_col]).replace(",","").strip().strip('"'))
        except: continue
        if shares>0 and cost>0: stocks.append({"name":name,"shares":shares,"cost":cost})
    return stocks

def parse_csv(f,col_map=None):
    """Legacy: parse with fixed cols (name=0,shares=1,cost=4) or given map."""
    try: content=f.read().decode("utf-8-sig")
    except: content=f.read().decode("big5",errors="ignore")
    if col_map:
        return parse_csv_with_map(content,col_map)
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
        ticker=get_ticker(s["name"]); ind={}; price=None; fetched=False
        # Auto-resolve .TW/.TWO if ticker has no suffix
        if ticker and not ticker.endswith(".TW") and not ticker.endswith(".TWO"):
            ticker = resolve_ticker(ticker) or ticker
        is_etf=ticker in ETF_LIST if ticker else False
        if ticker:
            price=get_current_price(ticker)
            if price and price>0: fetched=True
            if not is_etf:
                df=fetch_stock(ticker)
                if df is not None and len(df)>=20:
                    ind=calc_indicators(df)
                    if ind and "price" in ind:
                        price=ind["price"]; fetched=True
        if not price or price<=0: price=s["cost"]
        pnl_pct=(price-s["cost"])/s["cost"]*100 if s["cost"]>0 else 0
        pnl_amt=(price-s["cost"])*s["shares"]
        results.append({**s,"ticker":ticker,"price":price,"ind":ind,
                        "pnl_pct":pnl_pct,"pnl_amt":pnl_amt,"score":score_stock(ind),
                        "is_etf":is_etf,"price_ok":fetched})
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
    ind=r.get("ind",{}) or {}
    above_ma=ind.get("above_ma20",False)
    # 停損：技術面很爛（sc<=0）且虧損超過15%，或嚴重虧損跌破MA20
    if sc<=0 and pnl<-15: return "stop"
    if pnl<-20 and not above_ma: return "stop"
    # 減碼：技術面弱（sc<=1）且跌破MA20（不管損益），或部位過重技術差
    if sc<=1 and not above_ma: return "reduce"
    if pos>20 and sc<3 and not above_ma: return "reduce"
    if heavy and sc<3 and not above_ma: return "reduce"
    # 獲利了結：報酬率高且技術轉弱，或大幅獲利
    is_noncore=r.get("is_noncore",False)
    rsi=ind.get("rsi",50); macd=ind.get("macd",0); bearish=ind.get("bearish_day",False)
    tech_weak = (not above_ma) or (rsi>75 and macd<0) or (bearish and sc<4)
    if pnl>25 and tech_weak: return "profit"
    if pnl>15 and not above_ma: return "profit"
    if pnl>8 and (is_noncore or noncore) and sc<4: return "profit"
    # 加碼：技術非常強，站上MA20，部位不重，損益合理
    if sc>=4 and pos<=20 and not heavy and above_ma and pnl>-5: return "add"
    # 續抱：技術面OK（sc>=3且站上MA20），損益不論正負都可以續抱
    if sc>=3 and above_ma: return "strong"
    # 觀望：技術面普通（sc=2），或sc>=3但在MA20下方，等待轉機
    if sc>=2 and above_ma and pnl>-10: return "watch"
    return "reduce"
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

def get_profit_action(r):
    pnl=r.get("pnl_pct",0); name=r.get("name",""); ind=r.get("ind",{}) or {}
    above_ma=ind.get("above_ma20",False); rsi=ind.get("rsi",50)
    macd=ind.get("macd",0); bearish=ind.get("bearish_day",False)
    sc=r.get("score",0); price=r.get("price",0); is_noncore=r.get("is_noncore",False)
    # Determine stock type for trailing stop multiplier
    ticker=r.get("ticker","")
    if ticker in ETF_LIST: stop_mult=0.97
    elif name in GROWTH_STOCKS: stop_mult=0.93
    elif is_noncore: stop_mult=0.91
    else: stop_mult=0.95
    # Trailing stop: use MA20 as support reference if available
    ma20=ind.get("ma20",0)
    if ma20>0 and ma20>price*0.85:
        trail_stop=round(max(price*stop_mult, ma20*0.99),1)
    else:
        trail_stop=round(price*stop_mult,1)
    # Determine action and message
    tech_weak=(not above_ma) or (rsi>75 and macd<0) or (bearish and sc<4)
    if pnl>25 and tech_weak:
        action="🔴 強烈建議獲利了結"; emoji="🔴"
        msg="已大幅獲利，技術面轉弱，建議分批出場，不要等回到成本才後悔。"
    elif pnl>15 and not above_ma:
        action="⚡️ 建議部分獲利了結"; emoji="⚡️"
        msg="獲利%d%%，跌破MA20支撐，建議先減碼保護獲利，守住再看。" % int(pnl)
    elif pnl>25:
        action="🛡 續抱但設追蹤停利"; emoji="🛡"
        msg="大幅獲利且技術仍強，不追高，跌破 %.1f 可分批出場。" % trail_stop
    elif pnl>15:
        action="🛡 設停利保護獲利"; emoji="🛡"
        msg="獲利%.0f%%，建議設追蹤停利 %.1f，不急出但守好獲利。" % (pnl, trail_stop)
    elif is_noncore and pnl>8:
        action="💰 題材股可分批出場"; emoji="💰"
        msg="題材/非核心股，有獲利趁強先處理，不攤平，反彈可分批出。"
    else:
        action="💰 可分批出場"; emoji="💰"
        msg="已有獲利，高風險股建議反彈處理，設停利 %.1f。" % trail_stop
    return {"action":action,"emoji":emoji,"msg":msg,"trail_stop":trail_stop,"stop_mult":stop_mult}

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
def calc_indicators_ext(df):
    """Extended indicators: prev-day values for crossover detection, volume ratio, close location."""
    if df is None or len(df)<21: return {}
    ind = calc_indicators(df)
    if not ind: return {}
    c = df["Close"].values.flatten().astype(float)
    v = df["Volume"].values.flatten().astype(float)
    hi = df["High"].values.flatten().astype(float)
    lo = df["Low"].values.flatten().astype(float)
    ma20_prev = float(np.mean(c[-21:-1]))
    prev_close = float(c[-2])
    # MA20 breakout: today above, yesterday below
    ind["ma20_breakout"] = bool(c[-1] > ind["ma20"] and prev_close < ma20_prev)
    # KD crossover today (K>D today, K<=D yesterday)
    # Recalc KD for prev day
    n=9
    lows=[min(df["Low"].values.flatten()[max(0,i-n+1):i+1]) for i in range(len(c)-1)]
    highs=[max(df["High"].values.flatten()[max(0,i-n+1):i+1]) for i in range(len(c)-1)]
    rsv_p=[(c[i]-lows[i])/(highs[i]-lows[i]+1e-9)*100 for i in range(len(c)-1)]
    Kp=50.0; Dp=50.0
    for r2 in rsv_p: Kp=Kp*2/3+r2/3; Dp=Dp*2/3+Kp/3
    ind["kd_cross"] = bool(ind["k"] > ind["d"] and Kp <= Dp)
    # MACD histogram flip (neg->pos or DIF cross signal)
    def ema_fn(x,n2):
        e=np.zeros(len(x)); e[n2-1]=np.mean(x[:n2])
        for i in range(n2,len(x)): e[i]=x[i]*2/(n2+1)+e[i-1]*(1-2/(n2+1))
        return e
    e12=ema_fn(c,12); e26=ema_fn(c,26); macd_line=e12-e26
    sig9=ema_fn(macd_line[25:],9); hist=macd_line[25:]-sig9
    ind["macd_flip"] = bool(len(hist)>=2 and hist[-1]>0 and hist[-2]<=0)
    # Volume ratio: today vs 20-day avg
    avg_v = float(np.mean(v[-21:-1])) if len(v)>=21 else float(np.mean(v[:-1]))
    vol_ratio = float(v[-1]/avg_v) if avg_v>0 else 1.0
    ind["vol_ratio"] = round(vol_ratio, 2)
    # Close location: (close-low)/(high-low) today
    day_range = float(hi[-1] - lo[-1])
    ind["close_loc"] = round((c[-1]-lo[-1])/day_range, 2) if day_range>0 else 0.5
    # Today gain%
    ind["today_gain"] = round((c[-1]-c[-2])/c[-2]*100, 2) if c[-2]>0 else 0
    # Distance from MA20 in %
    ind["dist_ma20"] = round((c[-1]-ind["ma20"])/ind["ma20"]*100, 1) if ind["ma20"]>0 else 0
    # ATR-based support
    atr = ind.get("atr", 0)
    ind["support"] = round(ind["ma20"]*0.99, 1) if ind["ma20"]>0 else round(c[-1]*0.97,1)
    ind["stop_price"] = round(ind["ma20"]*0.97, 1) if ind["ma20"]>0 else round(c[-1]*0.95,1)
    return ind

def get_signal_grade(ind):
    """Grade a stock into: ready/pullback/watch/none based on anti-fake-breakout rules."""
    if not ind: return "none", []
    ma_break = ind.get("ma20_breakout", False)
    kd_cross = ind.get("kd_cross", False)
    macd_flip = ind.get("macd_flip", False)
    rsi = ind.get("rsi", 50)
    vol_ratio = ind.get("vol_ratio", 1.0)
    close_loc = ind.get("close_loc", 0.5)
    today_gain = ind.get("today_gain", 0)
    dist_ma20 = ind.get("dist_ma20", 0)
    above_ma = ind.get("above_ma20", False)
    signals = []
    # Count fresh signals
    if ma_break: signals.append("MA20突破")
    if kd_cross: signals.append("KD黃金交叉")
    if macd_flip: signals.append("MACD翻正")
    n_signals = len(signals)
    # Anti-fake-breakout filters
    rsi_ok = 45 <= rsi <= 65
    vol_ok = 1.2 <= vol_ratio <= 2.5
    close_ok = close_loc >= 0.55
    gain_ok = today_gain <= 7.0
    gain_big = today_gain > 5.0
    dist_far = dist_ma20 > 4.0
    # Must have at least 1 fresh signal or above MA with KD/MACD
    has_signal = n_signals >= 1 or (above_ma and (kd_cross or macd_flip))
    if not has_signal: return "none", signals
    if not rsi_ok: return "none", signals
    # Classify
    if n_signals >= 1 and vol_ok and close_ok and not gain_big and not dist_far:
        return "ready", signals    # 明日可入手
    elif gain_big or dist_far:
        return "pullback", signals  # 等回測
    else:
        return "watch", signals     # 技術待確認

def get_recommendations(mkt=None):
    mkt_weak = False
    if mkt:
        tw_chg = mkt.get("台指",{}).get("change_pct",0)
        tsm_chg = mkt.get("TSM",{}).get("change_pct",0)
        if tw_chg <= -1.5 or tsm_chg <= -3: mkt_weak = True
    ready_picks=[]; pullback_picks=[]; watch_picks=[]
    for name,num in RECOMMEND_POOL:
        ticker = resolve_ticker(num)
        if not ticker: continue
        if ticker in ETF_LIST: continue
        df=fetch_stock(ticker,"3mo")
        if df is None or len(df)<21: continue
        ind=calc_indicators_ext(df)
        if not ind: continue
        grade, signals = get_signal_grade(ind)
        if grade == "none": continue
        is_def = name in DEFENSIVE_STOCKS
        price = ind.get("price",0)
        support = ind.get("support", round(price*0.97,1))
        stop = ind.get("stop_price", round(price*0.95,1))
        dist_support = round((price - support)/price*100, 1) if price>0 else 0
        risk_pct = round((price - stop)/price*100, 1) if price>0 else 5.0
        # Entry price zone
        if grade == "ready":
            entry_low = round(price*0.995, 1)
            entry_high = round(price*1.008, 1)
            entry_msg = "現價附近分批，停損 "+str(stop)
        elif grade == "pullback":
            entry_low = round(support*0.995, 1)
            entry_high = round(support*1.01, 1)
            entry_msg = "等回 "+str(support)+" 附近再進，今日漲幅"+str(ind.get("today_gain",0))+"%已大"
        else:
            entry_low = round(support, 1)
            entry_high = round(ind.get("ma20",price)*1.005, 1)
            entry_msg = "等突破確認收盤，勿追"
        ep = {"condition": grade, "entry_low": entry_low, "entry_high": entry_high,
              "entry_msg": entry_msg, "support": support, "stop": stop, "risk_pct": risk_pct}
        entry = {"name":name,"ticker":ticker,"ind":ind,"score":len(signals),"buy_score":len(signals),
                 "is_def":is_def,"is_growth":name in GROWTH_STOCKS,"bearish":ind.get("bearish_day",False),
                 "mkt_weak":mkt_weak,"ep":ep,"signals":signals,
                 "vol_ratio":ind.get("vol_ratio",1),"today_gain":ind.get("today_gain",0),
                 "close_loc":ind.get("close_loc",0.5)}
        if grade=="ready" and not mkt_weak:
            ready_picks.append(entry)
        elif grade=="pullback":
            pullback_picks.append(entry)
        else:
            watch_picks.append(entry)
    # Sort: more signals first, then by volume ratio
    ready_picks.sort(key=lambda x:(-x["score"],-x["vol_ratio"]))
    pullback_picks.sort(key=lambda x:-x["score"])
    watch_picks.sort(key=lambda x:-x["score"])
    return ready_picks[:6], pullback_picks[:5], watch_picks[:4]

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
    price=ind.get("price",0); ma20=ind.get("ma20",price)
    inst_val=ind.get("inst",0)
    inst_txt=("法人買超 "+str(inst_val)+"億") if inst_val>0 else ("法人小幅參與 "+str(abs(inst_val))+"億")
    bearish=p.get("bearish",False); mkt_weak=p.get("mkt_weak",False)
    is_def=p.get("is_def",False); is_growth=p.get("is_growth",False)
    buy_sc=p.get("buy_score",sc)
    ep=p.get("ep",{})
    condition=ep.get("condition","wait")
    entry_low=ep.get("entry_low",round(price*0.99,1))
    entry_high=ep.get("entry_high",round(price*1.01,1))
    entry_msg=ep.get("entry_msg","觀察中")
    stop=ep.get("stop",round(price*0.95,1))
    risk_pct=ep.get("risk_pct",5.0)
    # Entry badge color & label
    if condition=="now":
        entry_color="#3fb950"; entry_label="✅ 今日可入手"
    elif condition=="pullback":
        entry_color="#79c0ff"; entry_label="🔵 等回測入場"
    elif condition=="limit":
        entry_color="#e3b341"; entry_label="🟡 限價掛單"
    else:
        entry_color="#8b949e"; entry_label="⏳ 尚未就緒"
    # Stock type label
    if is_def:
        type_label="🛡️ 防禦"; type_color="#6e7681"
    elif mkt_weak:
        type_label="⚠️ 盤弱"; type_color="#e3b341"
    elif bearish:
        type_label="🟠 今日轉弱"; type_color="#f0883e"
    else:
        type_label="✅ 技術偏多"; type_color="#3fb950"
    # Signals
    signals=[]
    if ind.get("above_ma20"): signals.append("MA20✅")
    if ind.get("macd_cross"): signals.append("MACD📈")
    if ind.get("k",50)<80 and ind.get("k",50)>ind.get("d",50): signals.append("KD🔁")
    if inst_val>0: signals.append("法人🏦")
    if bearish: signals.append("開高走低🔻")
    signals = p.get("signals", [])
    vol_r = p.get("vol_ratio", 1.0)
    today_g = p.get("today_gain", 0)
    close_l = p.get("close_loc", 0.5)
    sig_str = " | ".join(signals) if signals else "—"
    vol_str = str(round(vol_r,1))+"x量"
    gain_str = ("+" if today_g>=0 else "")+str(today_g)+"%"
    close_str = str(int(close_loc*100 if False else close_l*100))+"%位"
    # === RENDER ===
    # 1. Entry price box (most prominent)
    st.markdown(
        '<div style="background:#0d1f12;border:1px solid '+entry_color+';border-radius:8px;padding:8px 12px;margin:4px 0;">'
        +'<div style="display:flex;justify-content:space-between;align-items:center;">'
        +'<span style="color:'+entry_color+';font-weight:700;font-size:0.88rem;">'+entry_label+'</span>'
        +'<span style="color:#8b949e;font-size:0.72rem;">評分 '+str(buy_sc)+'/5 &nbsp;'+type_label+'</span>'
        +'</div>'
        +'<div style="margin-top:5px;display:flex;gap:8px;flex-wrap:wrap;">'
        +'<span style="background:#21262d;border-radius:5px;padding:3px 8px;font-size:0.78rem;color:#e6edf3;">📍 入場區間 <b style=\"color:'+entry_color+'\">'+str(entry_low)+'－'+str(entry_high)+'</b></span>'
        +'<span style="background:#21262d;border-radius:5px;padding:3px 8px;font-size:0.78rem;color:#f85149;">🛑 停損 <b>'+str(stop)+'</b> (-'+str(risk_pct)+'%)</span>'
        +'</div>'
        +'<div style="margin-top:4px;font-size:0.78rem;color:#c9d1d9;">'+entry_msg+'</div>'
        +'</div>',
        unsafe_allow_html=True)
    # 2. Query links
    _num = ticker.replace(".TW","").replace(".TWO","")
    _yf_url = "https://tw.stock.yahoo.com/quote/"+_num
    _gi_url = "https://goodinfo.tw/tw/StockInfo.asp?STOCK_ID="+_num
    _tv_url = "https://www.tradingview.com/symbols/TWSE-"+_num
    st.markdown('<div style="display:flex;gap:8px;margin:4px 0;flex-wrap:wrap;">'
        +'<a href="'+_yf_url+'" target="_blank" style="background:#21262d;color:#58a6ff;border-radius:5px;padding:3px 9px;font-size:0.72rem;text-decoration:none;">📊 Yahoo</a>'
        +'<a href="'+_gi_url+'" target="_blank" style="background:#21262d;color:#79c0ff;border-radius:5px;padding:3px 9px;font-size:0.72rem;text-decoration:none;">📈 Goodinfo</a>'
        +'<a href="'+_tv_url+'" target="_blank" style="background:#21262d;color:#e3b341;border-radius:5px;padding:3px 9px;font-size:0.72rem;text-decoration:none;">🕯 TradingView</a>'
        +'</div>',unsafe_allow_html=True)
    # 3. Price / MA20 row
    prow([("現價",str(price),"#e6edf3"),("20MA",str(round(ma20,1)),"#8b949e")])
    # 3. Signals
    st.markdown('<div style="font-size:0.7rem;color:#8b949e;padding:2px 0 3px 0;"><span style="color:#58a6ff;">'+(sig_str)+'</span> &nbsp;|&nbsp; 漲幅:'+gain_str+' &nbsp;量比:'+vol_str+' &nbsp;收盤位置:'+close_str+'&nbsp;&nbsp;'+inst_txt+'</div>',unsafe_allow_html=True)
    # 4. K-line / AI buttons
    ai_key="ai_pick_"+ticker
    c1,c2=st.columns(2)
    with c1:
        if st.button("📊 K線",key="kp_"+ticker):
            st.session_state["skp_"+ticker]=not st.session_state.get("skp_"+ticker,False)
    with c2:
        if st.button("🤖 AI分析",key="ap_"+ticker):
            with st.spinner("分析中..."):
                _num_str = ticker.replace(".TW","").replace(".TWO","")
                news_txt = get_stock_news(name, _num_str)
                news_section = ("\n近期新聞（請根據以下標題撰寫【新聞】段落）：\n" + news_txt) if news_txt else "\n（無法取得近期新聞，【新聞】段落請說明無法取得即時資訊）"
                prompt=("[推薦股] "+name+"("+ticker+") | 現價"+str(price)+" | RSI"+str(round(ind.get("rsi",0),0))+" MACD"+str(round(ind.get("macd",0),2))+" K"+str(round(ind.get("k",0),0))+" 20MA"+str(round(ma20,0))+" | "+inst_txt+" | 盤中:"+("開高走低" if bearish else "正常")+" 你是台股分析師，數據已給你，禁止重複報價，今天日期是 "+str(datetime.date.today())+"，繁體中文，每個段落獨立，請輸出：【結論】一句話操作建議 【走勢】技術面偏多或偏空關鍵支撐壓力 【理由】進場依據或等待條件 【新聞】根據下方提供的新聞標題做重點摘要，勿自行捏造" + news_section)
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
    badge_map={"stop":("bg-stop","🔴 技術破位/停損"),"reduce":("bg-reduce","🟠 技術轉弱/減碼"),"watch":("bg-watch","⚠️ 觀望等待"),"strong":("bg-strong","💎 技術強勢/續抱"),"add":("bg-add","➕ 條件加碼"),"etf":("bg-etf","💚 ETF長期持有"),"nodata":("bg-nodata","❌ 評估失敗"),"profit":("bg-profit","💰 獲利了結區間")}
    badge_cls,badge_txt=badge_map.get(cl,("bg-watch","⚠️ 觀望等待"))
    if cl=="nodata": badge_txt+=" — 無法取得報價，技術面無法評估"
    if r.get("pos_pct",0)>20 and cl not in ("stop","nodata","etf"): badge_txt+=" ⚠️單檔過重"
    if r.get("sector_heavy",False) and cl not in ("stop","nodata","etf"): badge_txt+=" ⚠️族群過重"
    # Profit action banner (always compute for any profitable stock)
    profit_info=None
    if price_ok and pnl_pct>8 and not is_etf:
        profit_info=get_profit_action(r)
    if not price_ok:
        col_r1,col_r2=st.columns([3,1])
        no_reason="無法識別股票代碼" if not ticker else ("代碼:"+str(ticker)+" 抓取失敗")
        with col_r1: prow([("現價", "❌ "+no_reason, "#8b949e")])
        with col_r2:
            if st.button("🔄",key="retry_"+name,help="重新抓取現價"):
                new_p=get_current_price(ticker) if ticker else None
                if new_p and new_p>0:
                    r["price"]=new_p; r["price_ok"]=True
                    r["pnl_pct"]=(new_p-cost)/cost*100 if cost>0 else 0
                    r["pnl_amt"]=(new_p-cost)*shares
                    st.rerun()
    else:
        prow([("現價", str(price), "#e6edf3")])
    prow([("股數", str(int(shares))+"股", "#8b949e")])
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
        if profit_info:
            p_color={"🔴":"#f85149","⚡️":"#f0883e","🛡":"#58a6ff","💰":"#d2a679"}.get(profit_info["emoji"],"#d2a679")
            st.markdown('<div style="background:#1a1500;border:1px solid #c9871f;border-left:4px solid '+p_color+';border-radius:6px;padding:7px 10px;margin:5px 0;"><div style="color:'+p_color+';font-weight:700;font-size:0.82rem;">'+profit_info["action"]+'</div><div style="color:#c9d1d9;font-size:0.78rem;margin-top:3px;">'+profit_info["msg"]+'</div><div style="color:#8b949e;font-size:0.72rem;margin-top:2px;">追蹤停利線：<b style=\"color:'+p_color+'\">'+str(profit_info["trail_stop"])+'</b></div></div>',unsafe_allow_html=True)
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
                _num_str2 = str(ticker).replace(".TW","").replace(".TWO","") if ticker else ""
                news_txt2 = get_stock_news(name, _num_str2) if _num_str2 and not is_etf else ""
                if is_etf:
                    news_section2 = "\n（ETF請分析近期配息與績效表現）"
                elif news_txt2:
                    news_section2 = "\n近期新聞（請根據以下標題撰寫【新聞】段落）：\n" + news_txt2
                else:
                    news_section2 = "\n（無法取得近期新聞，【新聞】段落請說明無法取得即時資訊）"
                prompt=("[持股] "+name+"("+str(ticker)+") | 現價"+str(price)+" 成本"+str(cost)+" 損益"+str(round(pnl_pct,1))+"% | RSI "+rsi_v+" K "+k_v+" | "+inst_disp+"\n你是台股分析師，數據已給你，禁止重複報價，今天日期是 "+str(datetime.date.today())+"，繁體中文，請完整輸出，每個段落獨立換行：\n【結論】一句話說明現在操作建議\n【走勢】技術面偏多或偏空，關鍵支撐壓力\n【理由】為何適合或不適合現在操作\n【新聞】根據下方提供的新聞標題做重點摘要，勿自行捏造" + news_section2)
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
    # Swipe gesture: left/right swipe to switch tabs
    st.components.v1.html("""<script>
(function(){
  var sx=0,sy=0,startEl=null;
  document.addEventListener('touchstart',function(e){
    var t=e.touches[0];sx=t.clientX;sy=t.clientY;startEl=document.elementFromPoint(sx,sy);
  },{passive:true});
  document.addEventListener('touchend',function(e){
    var t=e.changedTouches[0],dx=t.clientX-sx,dy=t.clientY-sy;
    if(Math.abs(dx)<50||Math.abs(dx)<Math.abs(dy)*1.5)return;
    // Find closest tab group to swipe start point
    var allGroups=Array.from(document.querySelectorAll('[data-testid="stTabs"]'));
    var best=null,bestDist=9999;
    allGroups.forEach(function(g){
      var r=g.getBoundingClientRect();
      if(sy>=r.top&&sy<=r.bottom){var d=Math.abs((r.left+r.right)/2-sx);if(d<bestDist){bestDist=d;best=g;}}
    });
    var container=best||allGroups[allGroups.length-1];
    if(!container)return;
    var tabs=Array.from(container.querySelectorAll('button[role="tab"]'));
    if(!tabs.length)return;
    var active=tabs.findIndex(function(b){return b.getAttribute('aria-selected')==='true';});
    if(active<0)active=0;
    var next=dx<0?Math.min(active+1,tabs.length-1):Math.max(active-1,0);
    if(next!==active)tabs[next].click();
  },{passive:true});
})();
</script>""",height=0)
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
    st.markdown('<div style="display:flex;gap:8px;padding:2px 0 4px 0;font-size:0.72rem;flex-wrap:wrap;">'
        +'<span style="color:#8b949e;">台指</span><span style="color:'+_mc(tw_c)+';">'+str(int(mkt.get("台指",{}).get("price",0)))+' '+_ms(tw_c)+'</span>'
        +'<span style="color:#8b949e;">｜納指</span><span style="color:'+_mc(nas_c)+';">'+str(int(mkt.get("納指",{}).get("price",0)))+' '+_ms(nas_c)+'</span>'
        +'<span style="color:#8b949e;">｜TSM ADR</span><span style="color:'+_mc(tsm_c)+';">'+str(round(mkt.get("TSM",{}).get("price",0),1))+' '+_ms(tsm_c)+'</span>'
        +'</div>',unsafe_allow_html=True)
    # All-in-one tab bar: 匯入 | 持有股 | 推薦 (同一行)
    n_port=len(st.session_state.get("portfolio",[]))
    tab0,tab1,tab2,tab3,tab4=st.tabs(["⬆️ 匯入("+str(n_port)+"筆)" if n_port>0 else "⬆️ 匯入","📁 持有股","⭐ 推薦","🔍 查股","⚙️ 設定"])
    with tab0:
        # --- Smart CSV Import UI ---
        if st.session_state.get('uploaded_csv_name'):
            st.caption('📎 目前持倉：'+st.session_state['uploaded_csv_name'])
        uploaded=st.file_uploader(
            "上傳對帳單 CSV（任何券商皆可）",
            type=["csv","txt"],label_visibility="visible",key="csv_upload",
            help="支援永豐、玉山、元大、富邦、國泰...等各家券商匯出格式，上傳後自動偵測欄位"
        )
        _csv_src=uploaded
        if not _csv_src and st.session_state.get('uploaded_csv') is not None:
            try:
                st.session_state['uploaded_csv'].seek(0)
                _csv_src=st.session_state['uploaded_csv']
            except: pass
        if _csv_src:
            # Detect columns
            _csv_src.seek(0)
            _header,_data_rows,_content=detect_csv_columns(_csv_src)
            _col_map=st.session_state.get('col_map')
            _auto=auto_guess_cols(_header) if _header else None
            _need_manual=not _col_map and (not _auto or any(v is None for v in _auto.values()))
            if _col_map:
                # Already have remembered mapping - use it
                stocks=parse_csv_with_map(_content,_col_map)
            elif _auto and all(v is not None for v in _auto.values()):
                # Auto-detected successfully
                stocks=parse_csv_with_map(_content,_auto)
                st.session_state['col_map']=_auto
            else:
                # Need manual mapping
                stocks=[]
                if _header:
                    st.info("📋 無法自動辨識欄位，請選擇一次，之後自動記憶")
                    _opts=["（請選擇）"]+[f"第{i+1}欄：{h}" for i,h in enumerate(_header)]
                    _cn=st.selectbox("📌 股票名稱 欄位",_opts,key="map_name")
                    _cs=st.selectbox("📌 持有股數 欄位",_opts,key="map_shares")
                    _cc=st.selectbox("📌 成本/均價 欄位",_opts,key="map_cost")
                    if st.button("✅ 確認欄位對應",use_container_width=True):
                        if "（請選擇）" in [_cn,_cs,_cc]:
                            st.warning("請選擇所有欄位")
                        else:
                            _mi=_opts.index(_cn)-1; _si=_opts.index(_cs)-1; _ci=_opts.index(_cc)-1
                            _new_map={"name_col":_mi,"shares_col":_si,"cost_col":_ci}
                            st.session_state['col_map']=_new_map
                            stocks=parse_csv_with_map(_content,_new_map)
                    else:
                        st.stop()
                else:
                    st.error("❌ 無法讀取 CSV，請確認檔案格式")
            if stocks:
                st.session_state["portfolio"]=stocks
                portfolio=stocks
                if uploaded:
                    st.session_state['uploaded_csv']=uploaded
                    st.session_state['uploaded_csv_name']=uploaded.name
                st.success("✅ 已載入 "+str(len(stocks))+" 筆持股："+", ".join([s["name"] for s in stocks]))
                if _col_map or (_auto and all(v is not None for v in _auto.values())):
                    if st.button("🗑 清除欄位記憶（換券商時用）",key="clr_colmap"):
                        st.session_state.pop('col_map',None)
                        st.rerun()
            elif not _need_manual:
                st.error("❌ 解析失敗，可能欄位設定不符，請清除欄位記憶後重試")
        cur_port=st.session_state.get("portfolio",[])
        if cur_port:
            res_t0=analyze_portfolio(cur_port)
            tpnl=sum(r["pnl_amt"] for r in res_t0 if r.get("price_ok"))
            tcost=sum(r["cost"]*r["shares"] for r in res_t0 if r.get("price_ok"))
            tpct=tpnl/tcost*100 if tcost>0 else 0
            pc="#3fb950" if tpnl>=0 else "#f85149"
            ps="+" if tpnl>=0 else ""; pp="+" if tpct>=0 else ""
            st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 14px;margin:6px 0;display:flex;justify-content:space-between;align-items:center;"><span style="color:#8b949e;font-size:0.8rem;">📊 持倉總損益（'+str(len(cur_port))+'筆）</span><span style="color:'+pc+';font-size:1.1rem;font-weight:800;">'+ps+str(int(tpnl))+'元 （'+pp+str(round(tpct,1))+'%）</span></div>',unsafe_allow_html=True)
            bk="daily_brief"; dk="brief_date"; td=datetime.date.today().isoformat()
            cb1,cb2=st.columns([3,1])
            with cb1: st.markdown('<span style="color:#58a6ff;font-weight:700;font-size:0.85rem;">🌐 今日盤前AI總結</span>',unsafe_allow_html=True)
            with cb2:
                if st.button("🔄",key="ref_brief",help="重新生成"):
                    for k in [bk,dk]: st.session_state.pop(k,None)
            if bk not in st.session_state or st.session_state.get(dk)!=td:
                with st.spinner("AI分析中..."):
                    us=get_us_overnight()
                    st.session_state[bk]=generate_daily_brief(mkt,us,cur_port)
                    st.session_state[dk]=td
            if st.session_state.get(bk):
                st.markdown('<div style="background:linear-gradient(135deg,#0d1f2e,#0a1628);border:1px solid #1f6feb;border-radius:8px;padding:10px 14px;margin:4px 0;font-size:0.83rem;color:#c9d1d9;line-height:1.6;">'+str(st.session_state[bk]).replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")+'</div>',unsafe_allow_html=True)
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
            profit_l=[r for r in results if classify(r)=="profit"]
            # Build tab list - only show tabs with items (hide (0) tabs), always show ETF and nodata if>0
            _all_groups=[
                ("💰 獲利出場",profit_l),
                ("🔴 停損",stop_l),
                ("🟠 減碼",reduce_l),
                ("⚠️ 觀望",watch_l),
                ("💎 續抱",strong_l),
                ("➕ 加碼",add_l),
                ("💚 ETF",etf_l),
                ("❌ 評估失敗",nodata_l),
            ]
            _visible=[(lbl+"("+str(len(grp))+")",grp) for lbl,grp in _all_groups if len(grp)>0]
            if not _visible: _visible=[("💰 獲利出場(0)",[]),("💎 續抱(0)",[])]
            _tab_labels=[v[0] for v in _visible]; _tab_groups=[v[1] for v in _visible]
            tabs=st.tabs(_tab_labels)
            for ti,(tab,group) in enumerate(zip(tabs,_tab_groups)):
                with tab:
                    is_profit_tab=profit_l and group is profit_l
                    if is_profit_tab:
                        st.markdown('<div style="background:#1a1500;border:1px solid #c9871f;border-radius:8px;padding:8px 12px;margin-bottom:6px;font-size:0.8rem;color:#d2a679;">📌 以下持股已達獲利了結條件：大幅獲利或技術轉弱，建議優先處理，設追蹤停利或分批出場。</div>',unsafe_allow_html=True)
                    if not group: st.caption("本區無持股")
                    for r in group:
                        pnl_s="+" if r["pnl_pct"]>=0 else ""
                        pnl_clr="#3fb950" if r["pnl_pct"]>=0 else "#f85149"
                        pnl_disp=(pnl_s+str(int(r["pnl_amt"]))+"("+pnl_s+str(round(r["pnl_pct"],1))+"%)") if r.get("price_ok") else "⚙️"
                        with st.expander(r["name"]+" | "+pnl_disp+" | "+str(r["price"]),expanded=False):
                            render_stock_card(r)
    with tab2:
        st.caption("依技術評分排序 | 盤勢轉弱時不顯示買進訊號")
        with st.spinner("掃描推薦中..."):
            buy_picks,watch_picks,def_picks=get_recommendations(mkt)
        if not buy_picks and not watch_picks and not def_picks:
            st.info("目前無符合條件推薦股（評分≥2）")
        else:
            if buy_picks:
                st.markdown('<div style="color:#3fb950;font-weight:700;font-size:0.85rem;margin:4px 0;">✅ 今日可入手／等回測</div>',unsafe_allow_html=True)
                for p in buy_picks:
                    with st.expander(p["name"]+"  "+p["ticker"]+"  +"+str(p["buy_score"])+"分",expanded=False):
                        render_pick_card(p)
            if watch_picks:
                st.markdown('<div style="color:#e3b341;font-weight:700;font-size:0.85rem;margin:4px 0;">⏳ 尚未就緒／技術待確認</div>',unsafe_allow_html=True)
                for p in watch_picks:
                    with st.expander(p["name"]+"  "+p["ticker"]+"  +"+str(p["score"])+"分",expanded=False):
                        render_pick_card(p)
            if def_picks:
                st.markdown('<div style="color:#6e7681;font-weight:700;font-size:0.85rem;margin:4px 0;">🛡️ 防禦/穩定型</div>',unsafe_allow_html=True)
                for p in def_picks:
                    with st.expander(p["name"]+"  "+p["ticker"]+"  +"+str(p["score"])+"分",expanded=False):
                        render_pick_card(p)
    with tab3:
        st.caption("輸入股票代碼（如 2330）或名稱（如 台積電）— 資料來源：Yahoo Finance")
        sq_col1, sq_col2 = st.columns([4,1])
        with sq_col1:
            sq_input = st.text_input("", placeholder="輸入代碼或名稱，例：2330 或 台積電", label_visibility="collapsed", key="sq_input")
        with sq_col2:
            sq_btn = st.button("🔍 查詢", key="sq_btn", use_container_width=True)
        if sq_btn and sq_input:
            st.session_state["sq_query"] = sq_input.strip()
        sq_query = st.session_state.get("sq_query","")
        if sq_query:
            # Resolve ticker: try NAME_TO_TICKER, then resolve_ticker on bare number
            sq_ticker = get_ticker(sq_query)
            if sq_ticker and not sq_ticker.endswith(".TW") and not sq_ticker.endswith(".TWO"):
                sq_ticker = resolve_ticker(sq_ticker) or sq_ticker
            if not sq_ticker:
                sq_ticker = resolve_ticker(sq_query)
            if not sq_ticker:
                st.error("找不到「"+sq_query+"」，請確認代碼或名稱")
            else:
                sq_df = fetch_stock(sq_ticker, "6mo")
                sq_ind = calc_indicators_ext(sq_df) if sq_df is not None and len(sq_df)>=21 else (calc_indicators(sq_df) if sq_df is not None and len(sq_df)>=20 else {})
                sq_price = sq_ind.get("price",0) if sq_ind else 0
                sq_name = sq_query if sq_query in NAME_TO_TICKER else sq_query
                _sq_num = sq_ticker.replace(".TW","").replace(".TWO","")
                # Data source note
                st.markdown('<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 12px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;">'
                    +'<span style="color:#e6edf3;font-weight:700;font-size:1rem;">'+sq_name+' <span style="color:#8b949e;font-size:0.75rem;">'+sq_ticker+'</span></span>'
                    +'<span style="color:#3fb950;font-size:1.1rem;font-weight:800;">'+str(sq_price)+'</span>'
                    +'</div>',unsafe_allow_html=True)
                # Query links
                st.markdown('<div style="display:flex;gap:8px;margin:4px 0;">'
                    +'<a href="https://tw.stock.yahoo.com/quote/'+_sq_num+'" target="_blank" style="background:#21262d;color:#58a6ff;border-radius:5px;padding:3px 9px;font-size:0.72rem;text-decoration:none;">📊 Yahoo</a>'
                    +'<a href="https://goodinfo.tw/tw/StockInfo.asp?STOCK_ID='+_sq_num+'" target="_blank" style="background:#21262d;color:#79c0ff;border-radius:5px;padding:3px 9px;font-size:0.72rem;text-decoration:none;">📈 Goodinfo</a>'
                    +'<a href="https://www.tradingview.com/symbols/TWSE-'+_sq_num+'" target="_blank" style="background:#21262d;color:#e3b341;border-radius:5px;padding:3px 9px;font-size:0.72rem;text-decoration:none;">🕯 TradingView</a>'
                    +'<span style="color:#8b949e;font-size:0.68rem;align-self:center;">資料來源：Yahoo Finance (yfinance)</span>'
                    +'</div>',unsafe_allow_html=True)
                if sq_ind:
                    # Indicators row
                    ma_icon="✅" if sq_ind.get("above_ma20") else "❌"
                    st.markdown('<div class="sbar">RSI:'+str(sq_ind.get("rsi","-"))+" MACD:"+str(round(sq_ind.get("macd",0),3))+" K:"+str(sq_ind.get("k","-"))+" D:"+str(sq_ind.get("d","-"))+" MA20:"+str(sq_ind.get("ma20","-"))+" "+ma_icon+' | 今漲:'+str(sq_ind.get("today_gain","—"))+'% 量比:'+str(sq_ind.get("vol_ratio","—"))+'x</div>',unsafe_allow_html=True)
                    # Signal grade
                    sq_grade, sq_sigs = get_signal_grade(sq_ind)
                    grade_map={"ready":("#3fb950","✅ 訊號明確，可留意入場"),"pullback":("#79c0ff","🔵 有訊號但漲太多，等回測"),"watch":("#e3b341","⏳ 技術待確認，觀望"),"none":("#8b949e","— 目前無明確進場訊號")}
                    gc,gt=grade_map.get(sq_grade,("#8b949e","—"))
                    sigs_str=" | ".join(sq_sigs) if sq_sigs else "無突破訊號"
                    st.markdown('<div style="background:#161b22;border-left:3px solid '+gc+';border-radius:6px;padding:6px 10px;margin:4px 0;"><span style="color:'+gc+';font-weight:700;font-size:0.82rem;">'+gt+'</span><br><span style="color:#8b949e;font-size:0.72rem;">訊號：'+sigs_str+'</span></div>',unsafe_allow_html=True)
                else:
                    st.warning("無法取得技術指標（資料不足）")
                # K-line
                sq_kline_key = "sq_kline_"+sq_ticker
                if st.button("📈 顯示K線圖", key="sq_kbtn_"+sq_ticker):
                    st.session_state[sq_kline_key] = not st.session_state.get(sq_kline_key, False)
                if st.session_state.get(sq_kline_key):
                    show_kline(sq_ticker, height=300)
                # AI analysis
                sq_ai_key = "sq_ai_"+sq_ticker
                if st.button("🤖 AI分析", key="sq_aibtn_"+sq_ticker):
                    with st.spinner("AI分析中..."):
                        rsi_v=str(sq_ind.get("rsi","-")) if sq_ind else "-"
                        macd_v=str(round(sq_ind.get("macd",0),3)) if sq_ind else "-"
                        k_v=str(sq_ind.get("k","-")) if sq_ind else "-"
                        ma_v=str(sq_ind.get("ma20","-")) if sq_ind else "-"
                        gain_v=str(sq_ind.get("today_gain","—")) if sq_ind else "-"
                        news_txt3 = get_stock_news(sq_name, _sq_num)
                        news_section3 = ("\n近期新聞（請根據以下標題撰寫【新聞】段落）：\n" + news_txt3) if news_txt3 else "\n（無法取得近期新聞，【新聞】段落請說明無法取得即時資訊）"
                        prompt=("[查股] "+sq_name+"("+sq_ticker+") 現價"+str(sq_price)+" RSI"+rsi_v+" MACD"+macd_v+" K"+k_v+" MA20"+ma_v+" 今漲"+gain_v+"% 你是台股分析師數據已給你禁止重複報價今天日期是 "+str(datetime.date.today())+" 繁體中文完整輸出每段獨立：【結論】一句話操作建議 【走勢】技術面偏多偏空關鍵支撐壓力 【理由】進場依據或等待條件 【新聞】根據下方提供的新聞標題做重點摘要勿自行捏造" + news_section3)
                        st.session_state[sq_ai_key] = call_ai(prompt)
                if st.session_state.get(sq_ai_key):
                    with st.expander("🤖 AI分析（"+sq_name+"）", expanded=True):
                        import re as _re2
                        _txt2 = str(st.session_state[sq_ai_key])
                        _parts2 = _re2.split(r'(【[^】]+】)', _txt2)
                        _colors2 = {"結論":"#f0883e","走勢":"#79c0ff","理由":"#e3b341","新聞":"#7ee787"}
                        _cur2 = "#c9d1d9"
                        for _p2 in _parts2:
                            if _p2.startswith("【") and _p2.endswith("】"):
                                _cur2 = _colors2.get(_p2[1:-1],"#c9d1d9")
                                st.markdown('<span style="color:'+_cur2+';font-weight:700;font-size:0.95rem;">'+_p2+'</span>',unsafe_allow_html=True)
                            elif _p2.strip():
                                st.markdown('<div style="color:#c9d1d9;font-size:0.88rem;line-height:1.6;margin:4px 0 12px 0;padding-left:8px;border-left:2px solid '+_cur2+';">'+_p2.strip()+'</div>',unsafe_allow_html=True)


    with tab4:
        st.markdown('### ⚙️ 設定')
        st.markdown('#### 🔑 API Key 設定')
        import streamlit.components.v1 as components
        _qp=st.query_params
        if _qp.get('_wk') and not st.session_state.get('user_api_key'):
            st.session_state['user_api_key']=_qp['_wk']
            st.session_state['user_api_provider']=_qp.get('_wp','gemini')
            st.query_params.clear()
            st.rerun()
        if not st.session_state.get('user_api_key'):
            _js='<script>(function(){var k=localStorage.getItem("wap_key");var p=localStorage.getItem("wap_provider");if(k&&k.length>0){var u=new URL(window.parent.location.href);u.searchParams.set("_wk",k);u.searchParams.set("_wp",p||"gemini");window.parent.history.replaceState({},"",u.toString());window.parent.location.reload();}})()</script>'
            components.html(_js,height=0)
        provider_choices = ['claude (Claude AI)', 'openai (ChatGPT)', 'gemini (Google 免費)']
        provider_map = {'claude (Claude AI)': 'claude', 'openai (ChatGPT)': 'openai', 'gemini (Google 免費)': 'gemini'}
        cur_provider = st.session_state.get('user_api_provider', 'gemini')
        display_choices = list(provider_map.keys())
        default_idx = 2
        for i, (kk, vv) in enumerate(provider_map.items()):
            if vv == cur_provider:
                default_idx = i
                break
        selected_display = st.selectbox('🤖 AI 提供商', display_choices, index=default_idx)
        selected_provider = provider_map[selected_display]
        _api_links = {
            'gemini': '🔗 [免費申請 Gemini Key](https://aistudio.google.com/app/apikey)',
            'openai': '🔗 [申請 OpenAI Key](https://platform.openai.com/api-keys)',
            'claude': '🔗 [申請 Claude Key](https://console.anthropic.com/settings/keys)'
        }
        if selected_provider in _api_links:
            st.caption(_api_links[selected_provider])
        api_key_val = st.session_state.get('user_api_key', '')
        provider_hints = {
            'claude': '格式: sk-ant-api03-...',
            'openai': '格式: sk-proj-...',
            'gemini': '格式: AIzaSy... (免費)'
        }
        api_key_input = st.text_input(
            'API Key', value=api_key_val, type='password',
            placeholder=provider_hints.get(selected_provider, '請輸入 API Key')
        )
        st.markdown('<div style="display:flex;gap:8px;margin-bottom:8px">',unsafe_allow_html=True)
        _col1,_col2=st.columns(2)
        with _col1:
            _do_save=st.button('💾 儲存',use_container_width=True,key='api_save_btn')
        with _col2:
            _do_clear=st.button('🗑️ 清除',use_container_width=True,key='api_clear_btn')
        st.markdown('</div>',unsafe_allow_html=True)
        if _do_save:
            if api_key_input.strip():
                st.session_state['user_api_provider'] = selected_provider
                st.session_state['user_api_key'] = api_key_input.strip()
                safe_k = api_key_input.strip().replace("'", "\'")
                safe_p = selected_provider
                    components.html(f"""<script>try{{localStorage.setItem('wap_provider','{safe_p}');localStorage.setItem('wap_key','{safe_k}');}}catch(e){{}}</script>""", height=0)
                st.success(f'✅ 已儲存！{selected_provider.upper()}')
            else:
                st.warning('請先輸入 API Key')
        if _do_clear:
            st.session_state.pop('user_api_provider', None)
            st.session_state.pop('user_api_key', None)
                components.html("""<script>try{localStorage.removeItem('wap_provider');localStorage.removeItem('wap_key');}catch(e){}</script>""", height=0)
            st.info('已清除。')
        if st.session_state.get('user_api_key'):
            k = st.session_state['user_api_key']
            masked = k[:6] + '•'*8 + k[-4:] if len(k) > 10 else '•'*len(k)
            st.info(f'🟢 目前：{st.session_state.get("user_api_provider","").upper()} | {masked}')
        else:
            st.warning('⚠️ 尚未設定 API Key')
        st.markdown('---')
        st.markdown('#### 📱 安裝到手機')
        st.info('在手機瀏覽器打開此 APP 後，點瀏覽器選單 → 新增到主螢幕 / 安裝應用程式，即可安裝到手機。')

if __name__ == "__main__":
    main()
