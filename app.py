import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

PAGE = r"""
<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MarkeTGyan AI Stock Analyst</title>
<style>
:root{--bg:#0b1220;--panel:#121d31;--line:#263650;--text:#eef4ff;--muted:#a8b7ce;--gold:#ffc857;--green:#4ade80;--red:#fb7185}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#07101e,#101d32);font-family:Arial,"Noto Sans Devanagari",sans-serif;color:var(--text)}
main{max-width:1050px;margin:0 auto;padding:22px}header{padding:24px 0 12px}h1{font-size:clamp(26px,4vw,42px);margin:0 0 8px} .sub{color:var(--muted);line-height:1.6}
.panel{background:rgba(18,29,49,.96);border:1px solid var(--line);border-radius:18px;padding:20px;margin:16px 0;box-shadow:0 12px 30px #0002}
form{display:flex;gap:10px;flex-wrap:wrap}input{flex:1;min-width:210px;background:#07101e;color:white;border:1px solid #3b4d68;border-radius:10px;padding:15px;font-size:17px}
button{border:0;border-radius:10px;padding:14px 20px;background:var(--gold);color:#1c2433;font-weight:800;font-size:16px;cursor:pointer}button:disabled{opacity:.6;cursor:wait}
.hint{font-size:13px;color:var(--muted);margin-top:10px;line-height:1.5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.metric{background:#0a1425;border:1px solid var(--line);border-radius:12px;padding:15px}.metric small{display:block;color:var(--muted);margin-bottom:8px}.metric strong{font-size:24px;overflow-wrap:anywhere}
.green{color:var(--green)}.red{color:var(--red)}.gold{color:var(--gold)}h2{font-size:22px;margin:0 0 14px}h3{margin:0 0 8px}.section{margin-top:22px}.copy{line-height:1.75;color:#e4ecf8}.tag{display:inline-block;padding:6px 10px;border-radius:20px;background:#24344c;color:var(--gold);font-size:13px;font-weight:bold}
table{width:100%;border-collapse:collapse}td,th{text-align:left;border-bottom:1px solid var(--line);padding:11px 8px;vertical-align:top}th{color:var(--muted)}.notice{font-size:13px;color:var(--muted);line-height:1.65}.error{color:var(--red);white-space:pre-wrap}.hidden{display:none}
footer{color:var(--muted);font-size:12px;line-height:1.6;padding:18px 0 30px}
</style>
</head>
<body><main>
<header><div class="tag">MarkeTGyan • EDUCATIONAL PURPOSE ONLY</div>
<h1>AI Stock Analyst</h1><div class="sub">स्टॉक का नाम या NSE symbol लिखिए। यह एजेंट trend, momentum, moving averages, support/resistance, valuation उपलब्धता और risk को सरल हिंदी में समझाएगा।</div></header>
<div class="panel">
<form id="stockForm"><input id="symbol" placeholder="उदाहरण: ZEEL, RELIANCE, TCS, INFY" required autocomplete="off"><button id="go" type="submit">विश्लेषण करें ↗</button></form>
<div class="hint">भारतीय शेयर के लिए NSE symbol लिखें (जैसे ZEEL)। कंपनी का नाम भी आज़मा सकते हैं। डेटा Yahoo Finance से आता है; कभी-कभी देरी या डेटा की कमी हो सकती है।</div>
</div>
<div id="status" class="panel hidden"></div>
<div id="results" class="hidden">
<div class="panel"><div id="company"></div><div id="metrics" class="grid"></div></div>
<div class="panel"><h2>🧭 Trend और Momentum</h2><div id="trend" class="copy"></div></div>
<div class="panel"><h2>📍 Support और Resistance</h2><div id="levels"></div><p class="notice">ये हाल के दैनिक डेटा से निकले अनुमानित स्तर हैं, गारंटीशुदा स्तर नहीं।</p></div>
<div class="panel"><h2>🏢 Fundamental Snapshot</h2><div id="fundamentals"></div></div>
<div class="panel"><h2>🧠 AI-जैसा नियम-आधारित निष्कर्ष</h2><div id="verdict" class="copy"></div></div>
<div class="panel"><h2>⚠️ Risk Checklist</h2><div id="risks" class="copy"></div></div>
</div>
<footer>शैक्षिक उद्देश्य मात्र; यह SEBI-registered investment advice नहीं है। खरीद/बिक्री का निर्देश नहीं। शेयर बाजार में पूँजी का नुकसान संभव है। निर्णय से पहले अपने स्रोतों से डेटा जाँचें। यह ऐप किसी ब्रोकर में order place नहीं करता।</footer>
</main>
<script>
const $=id=>document.getElementById(id);
function fmt(v, suffix=''){if(v===null||v===undefined||!Number.isFinite(Number(v)))return 'उपलब्ध नहीं';return Number(v).toLocaleString('en-IN',{maximumFractionDigits:2})+suffix}
function metric(label,value,cls=''){return `<div class="metric"><small>${label}</small><strong class="${cls}">${value}</strong></div>`}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function table(rows){return '<table><tbody>'+rows.map(r=>'<tr><th>'+esc(r[0])+'</th><td>'+esc(r[1])+'</td></tr>').join('')+'</tbody></table>'}
$('stockForm').addEventListener('submit',async e=>{
 e.preventDefault(); const sym=$('symbol').value.trim(); if(!sym)return;
 $('go').disabled=true;$('go').textContent='डेटा जाँच रहा है…';$('results').classList.add('hidden');$('status').classList.remove('hidden');$('status').innerHTML='दैनिक भाव और उपलब्ध fundamentals प्राप्त किए जा रहे हैं…';
 try{
  const r=await fetch('/api/analyze?symbol='+encodeURIComponent(sym));const d=await r.json();
  if(!r.ok)throw new Error(d.error||'डेटा प्राप्त नहीं हुआ');
  $('status').classList.add('hidden');$('results').classList.remove('hidden');
  $('company').innerHTML=`<h2>${esc(d.company)} <span class="tag">${esc(d.symbol)}</span></h2><div class="sub">डेटा समय: ${esc(d.as_of)} · स्रोत: Yahoo Finance</div>`;
  $('metrics').innerHTML=[
   metric('अंतिम बंद भाव',fmt(d.price,d.currency==='INR'?' ₹':' '+(d.currency||''))),
   metric('आज का बदलाव',fmt(d.change_pct,'%'),d.change_pct>=0?'green':'red'),
   metric('RSI (14)',fmt(d.rsi),d.rsi<30?'gold':d.rsi>70?'red':''),
   metric('ट्रेंड स्कोर',esc(d.score_label),d.score>=2?'green':d.score<=-2?'red':'gold'),
   metric('52-सप्ताह उच्च',fmt(d.high52,' '+(d.currency||''))),
   metric('52-सप्ताह निम्न',fmt(d.low52,' '+(d.currency||'')))
  ].join('');
  $('trend').innerHTML=`<p><b>तकनीकी स्थिति:</b> ${esc(d.trend)}</p><p><b>मूविंग एवरेज:</b> ${esc(d.ma_comment)}</p><p><b>RSI संकेत:</b> ${esc(d.rsi_comment)}</p><p><b>MACD:</b> ${esc(d.macd_comment)}</p>`;
  $('levels').innerHTML=table([['निकटतम अनुमानित सपोर्ट',fmt(d.support,' '+(d.currency||''))],['निकटतम अनुमानित रेजिस्टेंस',fmt(d.resistance,' '+(d.currency||''))],['20-दिन EMA',fmt(d.ema20,' '+(d.currency||''))],['50-दिन SMA',fmt(d.sma50,' '+(d.currency||''))],['200-दिन SMA',fmt(d.sma200,' '+(d.currency||''))]]);
  $('fundamentals').innerHTML=table([['Market Cap',d.market_cap||'उपलब्ध नहीं'],['P/E',fmt(d.pe)],['Forward P/E',fmt(d.forward_pe)],['Price/Book',fmt(d.pb)],['ROE',fmt(d.roe,'%')],['Debt/Equity',fmt(d.debt_equity)],['Profit Margin',fmt(d.profit_margin,'%')],['Dividend Yield',fmt(d.dividend_yield,'%')],['Business summary',d.summary||'सारांश उपलब्ध नहीं']]);
  $('verdict').innerHTML=`<p><b>संकेत:</b> <span class="${d.score>=2?'green':d.score<=-2?'red':'gold'}">${esc(d.score_label)}</span></p><p>${esc(d.verdict)}</p><p><b>संभावित bullish confirmation:</b> ${esc(d.bullish_confirmation)}</p><p><b>कमजोरी का संकेत:</b> ${esc(d.bearish_confirmation)}</p><p><b>व्यावहारिक कदम:</b> ${esc(d.action)}</p>`;
  $('risks').innerHTML='<ul>'+d.risks.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>';
 }catch(err){$('status').innerHTML='<div class="error">विश्लेषण नहीं हो पाया: '+esc(err.message)+'</div><p class="notice">NSE symbol दोबारा जाँचें, जैसे ZEEL। कुछ शेयरों का डेटा उपलब्ध न भी हो सकता है।</p>'}
 finally{$('go').disabled=false;$('go').textContent='विश्लेषण करें ↗'}
});
</script></body></html>
"""

def clean_num(value):
    try:
        if value is None or pd.isna(value):
            return None
        value = float(value)
        return round(value, 2) if np.isfinite(value) else None
    except Exception:
        return None

def human_large(value, currency=""):
    try:
        if value is None or pd.isna(value): return "उपलब्ध नहीं"
        value=float(value)
        for unit, div in [("T",1e12),("B",1e9),("Cr",1e7),("M",1e6),("L",1e5)]:
            if abs(value)>=div: return f"{currency}{value/div:,.2f} {unit}"
        return f"{currency}{value:,.2f}"
    except Exception:
        return "उपलब्ध नहीं"

def analyze_symbol(raw):
    symbol = raw.strip().upper().replace(" ", "")
    if not symbol:
        raise ValueError("कृपया स्टॉक का नाम या symbol लिखें।")
    # Indian NSE is the default. Explicit suffixes are respected.
    if "." not in symbol and not symbol.startswith("^"):
        ticker_symbol = symbol + ".NS"
    else:
        ticker_symbol = symbol
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty or len(hist) < 30:
        # Try BSE when NSE symbol is unavailable and user supplied an unsuffixed Indian symbol.
        if "." not in symbol and not symbol.startswith("^"):
            ticker_symbol = symbol + ".BO"
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty or len(hist) < 30:
        raise ValueError(f"{symbol} का पर्याप्त दैनिक डेटा नहीं मिला। NSE symbol जाँचें या .NS / .BO suffix के साथ कोशिश करें।")
    hist = hist.dropna(subset=["Close"])
    close = hist["Close"].astype(float)
    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close)>1 else price
    change_pct = ((price/prev)-1)*100 if prev else 0
    ema20 = close.ewm(span=20, adjust=False).mean()
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100/(1+rs))
    rsi = float(rsi_series.iloc[-1]) if pd.notna(rsi_series.iloc[-1]) else (100.0 if loss.iloc[-1] == 0 else 50.0)
    exp12=close.ewm(span=12,adjust=False).mean()
    exp26=close.ewm(span=26,adjust=False).mean()
    macd=exp12-exp26
    signal=macd.ewm(span=9,adjust=False).mean()
    macd_bull=bool(macd.iloc[-1] > signal.iloc[-1])
    ema20v=float(ema20.iloc[-1])
    sma50v=clean_num(sma50.iloc[-1])
    sma200v=clean_num(sma200.iloc[-1])
    # Support/resistance are recent 20-session swing zones, not guaranteed levels.
    recent=hist.tail(20)
    support=float(recent["Low"].min()) if "Low" in recent else float(close.tail(20).min())
    resistance=float(recent["High"].max()) if "High" in recent else float(close.tail(20).max())
    info={}
    try: info=ticker.get_info() or {}
    except Exception: info={}
    score=0
    if price>ema20v: score+=1
    if sma50v is not None and price>sma50v: score+=1
    if sma200v is not None and price>sma200v: score+=1
    if macd_bull: score+=1
    if 50<=rsi<=70: score+=1
    if rsi<40: score-=1
    if sma50v is not None and price<sma50v: score-=1
    if sma200v is not None and price<sma200v: score-=1
    if not macd_bull: score-=1
    score=max(-5,min(5,score))
    score_label="मजबूत सकारात्मक" if score>=3 else "सकारात्मक" if score>=1 else "नकारात्मक" if score<=-2 else "मिश्रित / पुष्टि बाकी"
    if price>ema20v and (sma50v is None or price>sma50v):
        trend="निकट अवधि में सुधार/तेजी के संकेत हैं, लेकिन व्यापक ट्रेंड के लिए 200-दिन SMA और swing structure भी देखें।"
    elif sma200v is not None and price<sma200v:
        trend="भाव 200-दिन SMA के नीचे है; व्यापक ट्रेंड कमजोर है। उछाल को पुष्टि के बिना reversal न मानें।"
    else:
        trend="ट्रेंड मिश्रित है। साफ दिशा के लिए moving averages, higher high/higher low और volume की पुष्टि जरूरी है।"
    ma_comment=f"भाव 20-दिन EMA के {'ऊपर' if price>ema20v else 'नीचे'}; 50-दिन SMA के "+("ऊपर" if sma50v is not None and price>sma50v else "नीचे" if sma50v is not None else "का डेटा उपलब्ध नहीं")+"; 200-दिन SMA के "+("ऊपर" if sma200v is not None and price>sma200v else "नीचे" if sma200v is not None else "का डेटा उपलब्ध नहीं")+"."
    rsi_comment="ओवरसोल्ड क्षेत्र (<30); गिरावट के बाद bounce संभव है, लेकिन यह अकेले BUY संकेत नहीं है।" if rsi<30 else "ओवरबॉट क्षेत्र (>70); momentum मजबूत हो सकता है, पर pullback का जोखिम भी है।" if rsi>70 else "RSI 30–70 के बीच है; इसे trend और price action के साथ पढ़ें।"
    macd_comment="MACD line signal line के ऊपर है (सकारात्मक momentum संकेत)।" if macd_bull else "MACD line signal line के नीचे है (कमजोर momentum संकेत)।"
    if score>=3:
        verdict="कई तकनीकी संकेत सकारात्मक हैं। फिर भी प्रवेश से पहले breakout/retetst, volume, liquidity और stop-loss की पुष्टि करें।"
        action="तुरंत market order देने के बजाय entry trigger और invalidation level तय करें; gap-up के पीछे न भागें।"
    elif score<=-2:
        verdict="तकनीकी संकेतों में कमजोरी अधिक है। केवल कम कीमत या oversold RSI देखकर खरीदना जोखिमपूर्ण हो सकता है।"
        action="नया long लेने से पहले trend reversal की पुष्टि का इंतजार करना अधिक अनुशासित तरीका है।"
    else:
        verdict="संकेत मिश्रित हैं; अभी स्पष्ट edge नहीं दिखता। अपनी strategy के confirmation rules पूरे होने तक प्रतीक्षा करें।"
        action="support/resistance breakout या breakdown के बाद retest और volume की पुष्टि देखें।"
    try: currency=info.get("currency") or ("INR" if ticker_symbol.endswith((".NS",".BO")) else "")
    except Exception: currency="INR" if ticker_symbol.endswith((".NS",".BO")) else ""
    risks=[
        "यह नियम-आधारित विश्लेषण है, AI भविष्यवाणी या गारंटीकृत target नहीं।",
        "कंपनी के परिणाम, समाचार, corporate actions और बाजार की खबरें कीमत बदल सकती हैं।",
        "Fundamental fields Yahoo Finance में खाली, पुराने या अलग परिभाषा वाले हो सकते हैं।",
        "Support/resistance पिछले 20 कारोबारी सत्रों के high/low से निकाले गए अनुमान हैं।",
        "इंट्राडे उपयोग के लिए डेटा real-time मानकर न चलें; broker terminal पर live price सत्यापित करें।"
    ]
    name=info.get("longName") or info.get("shortName") or symbol
    summary=info.get("longBusinessSummary") or ""
    if len(summary)>420: summary=summary[:417]+"..."
    def pct_info(k):
        v=info.get(k)
        return clean_num(v*100) if v is not None else None
    return {
        "symbol":ticker_symbol,"company":name,"as_of":str(hist.index[-1].date()),
        "price":clean_num(price),"change_pct":clean_num(change_pct),"currency":currency,
        "rsi":clean_num(rsi),"score":score,"score_label":score_label,"trend":trend,
        "ema20":clean_num(ema20v),"sma50":sma50v,"sma200":sma200v,
        "support":clean_num(support),"resistance":clean_num(resistance),
        "high52":clean_num(info.get("fiftyTwoWeekHigh") or close.tail(252).max()),
        "low52":clean_num(info.get("fiftyTwoWeekLow") or close.tail(252).min()),
        "ma_comment":ma_comment,"rsi_comment":rsi_comment,"macd_comment":macd_comment,
        "market_cap":human_large(info.get("marketCap"),currency+" "),
        "pe":clean_num(info.get("trailingPE")),"forward_pe":clean_num(info.get("forwardPE")),
        "pb":clean_num(info.get("priceToBook")),"roe":pct_info("returnOnEquity"),
        "debt_equity":clean_num(info.get("debtToEquity")),"profit_margin":pct_info("profitMargins"),
        "dividend_yield":pct_info("dividendYield"),"summary":summary,
        "verdict":verdict,
        "bullish_confirmation":"रेजिस्टेंस के ऊपर दैनिक close, बेहतर volume और higher low / higher high structure।",
        "bearish_confirmation":"सपोर्ट के नीचे close, lower high और कमजोर volume/negative momentum।",
        "action":action,"risks":risks
    }

@app.get("/")
def home():
    return render_template_string(PAGE)

@app.get("/health")
def health():
    return jsonify({"status":"ok","service":"MarkeTGyan Stock Analysis Agent"})

@app.get("/api/analyze")
def api_analyze():
    symbol=request.args.get("symbol","")
    try:
        return jsonify(analyze_symbol(symbol))
    except ValueError as e:
        return jsonify({"error":str(e)}),400
    except Exception as e:
        app.logger.exception("Analysis failed")
        return jsonify({"error":"डेटा स्रोत से जानकारी नहीं मिल सकी। कुछ देर बाद कोशिश करें या symbol जाँचें।"}),502

if __name__ == "__main__":
    port=int(os.environ.get("PORT","5000"))
    app.run(host="0.0.0.0",port=port,debug=False)
