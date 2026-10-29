# MarkeTGyan AI Stock Analyst (MVP)

## क्या करता है
- NSE symbol (उदा. ZEEL, RELIANCE, TCS) डालकर हिंदी में stock snapshot
- अंतिम उपलब्ध daily close, RSI(14), EMA20, SMA50/SMA200, MACD दिशा
- पिछले 20 कारोबारी सत्रों से अनुमानित support/resistance
- उपलब्ध valuation/fundamental fields: market cap, P/E, P/B, ROE, debt/equity, profit margin, dividend yield
- सरल rule-based verdict और risk checklist
- `/health` endpoint

## महत्वपूर्ण सीमाएँ
- यह वास्तविक generative AI model नहीं है; indicators + नियम-आधारित हिंदी व्याख्या है।
- Yahoo Finance/yfinance अनौपचारिक data source है। डेटा delayed, अनुपलब्ध, rate-limited या गलत हो सकता है।
- NSE के लिए daily data प्रायः पिछली close तक होता है; इसे live intraday price न मानें।
- Fundamentals खाली हो सकते हैं। कोई buy/sell recommendation या guaranteed target नहीं।
- सार्वजनिक इंटरनेट पर deploy करने से पहले usage limits, monitoring, caching और trusted market-data provider जोड़ें।

## Render पर deploy
1. इस ZIP को extract करें।
2. `app.py`, `requirements.txt`, `render.yaml` को GitHub repository में upload करें।
3. Render पर New + > Blueprint चुनें और repository connect करें, या Web Service बनाएँ।
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app --workers 1 --threads 4 --timeout 120`
6. Deploy होने पर Render URL खोलें; `/health` पर `{"status":"ok",...}` दिखना चाहिए।

## Google Sites में जोड़ना
Google Sites Python/Flask backend को सीधे host नहीं करता। पहले Render (या किसी दूसरे Python hosting service) पर backend deploy करें।
फिर Google Sites > Insert > Embed > By URL में Render की HTTPS URL डालें। यदि embed policy के कारण न खुले, Google Sites में Button/link लगाकर app को नए tab में खोलें।
आपके पास public HTTPS URL होने के बाद ही embed संभव है।

## Local Windows test
```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
फिर browser में http://127.0.0.1:5000 खोलें।

## Files
- app.py: Flask website + analysis API
- requirements.txt: dependencies
- render.yaml: Render Blueprint configuration
