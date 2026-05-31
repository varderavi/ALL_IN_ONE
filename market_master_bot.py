import requests
import pytz
import xml.etree.ElementTree as ET
import time
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = "8874026729:AAEgzZr0UslgaKGdPiUjZMONNuFCKL-pqsY"
CHAT_ID   = "1358803794"

IST = pytz.timezone("Asia/Kolkata")
ROUTINE_PRE_VOLUME = 5000  

user_status = {}

def now_ist():
    return datetime.now(IST)

def get_expiry_alert():
    n = now_ist()
    weekday = n.weekday() 
    if weekday == 0: return "📅 <b>EXPIRY ALERT:</b> આજે <b>MIDCAP SELECT</b> ની એક્સપાયરી છે! 🎯"
    elif weekday == 1: return "📅 <b>EXPIRY ALERT:</b> આજે <b>FINNIFTY</b> ની ધાંસુ એક્સપાયરી છે! 🎯"
    elif weekday == 2: return "📅 <b>EXPIRY ALERT:</b> આજે <b>BANKNIFTY</b> નો મોટો દિવસ (Expiry) છે! 🎯"
    elif weekday == 3: return "📅 <b>EXPIRY ALERT:</b> આજે <b>NIFTY 50</b> નો મેઈન એક્સપાયરી ધડાકો છે! 🎯"
    elif weekday == 4: return "📅 <b>EXPIRY ALERT:</b> આજે <b>SENSEX</b> ની ધમાકેદાર એક્સપાયરી છે! 🎯"
    return ""

def fetch_live_data(symbol, interval="5m", timeframe_range="2d", include_prepost=False):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={timeframe_range}&includePrePost={'true' if include_prepost else 'false'}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes = [x for x in res["indicators"]["quote"][0]["close"] if x is not None]
        highs  = [x for x in res["indicators"]["quote"][0]["high"] if x is not None]
        lows   = [x for x in res["indicators"]["quote"][0]["low"] if x is not None]
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price = res["meta"]["regularMarketPrice"]
        prev_close = res["meta"].get("previousClose", price)
        pre_price = res["meta"].get("preMarketPrice", price)
        
        name = symbol
        if symbol == "^NSEI": name = "NIFTY 50"
        elif symbol == "^NSEBANK": name = "BANK NIFTY"
        elif symbol == "^BSESN": name = "SENSEX"
        elif symbol == "^NSMIDCP": name = "NIFTY MIDCAP 100"
        elif symbol == "^NSE91": name = "NIFTY NEXT 50"
        elif symbol == "HBLENGINE.NS": name = "HBL POWER"
        
        day_high = round(highs[-1], 2) if highs else price
        day_low = round(lows[-1], 2) if lows else price
        
        return round(price, 2), closes, volumes, round(prev_close, 2), round(pre_price, 2), name, day_high, day_low
    except:
        return None, [], [], None, None, symbol, None, None

def calc_ema(data, p):
    if len(data) < p: return None
    k = 2/(p+1); e = sum(data[:p])/p
    for v in data[p:]: e = v*k + e*(1-k)
    return round(e, 2)

def calc_rsi(data, p=14):
    if len(data) < p+1: return "N/A"
    g = sum(max(data[i]-data[i-1],0) for i in range(len(data)-p,len(data)))
    l = sum(max(data[i-1]-data[i],0) for i in range(len(data)-p,len(data)))
    ag, al = g/p, l/p
    return round(100 - 100/(1+ag/al), 1) if al else 100.0

def fetch_google_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(r.text)
        for item in root.findall(".//item")[:1]:
            title = item.find("title").text.split(" - ")[0]
            link = item.find("link").text
            return f"\n\n📢 <b>LATEST NEWS:</b>\n• <b>{title}</b>\n  🔗 <a href='{link}'>વાંચવા માટે ક્લિક કરો</a>"
    except:
        pass
    return ""

# =========================================================
# 🪙 BITCOIN પાવરફુલ સેન્ટિમેન્ટ એન્જિન (Risk-Reward 1:2)
# =========================================================
def get_btc_advanced_report():
    price, closes, _, prev_close, _, name, d_high, d_low = fetch_live_data("BTC-USD")
    if not price: return "❌ Bitcoin નો લાઈવ ડેટા મળી શક્યો નહિ."
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    rsi = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    
    sentiment = "⚖️ SIDEWAYS / NEUTRAL"
    action = "👀 કરંટ પ્રાઇઝ ન્યુટ્રલ રેન્જમાં છે, વેટ કરો."
    
    if ema9 and ema21 and rsi != "N/A":
        if price > ema9 and price > ema21 and rsi >= 58:
            sentiment = "🚀 STRONG BULLISH"
            action = "🟢 <b>BUY / LONG:</b> ક્રિપ્ટો ભારે તેજીમાં છે, પોઝિશન હોલ્ડ રખાય અથવા બાય કરાય."
        elif price > ema9 and 50 <= rsi < 58:
            sentiment = "🟢 MILD BULLISH"
            action = "📉 <b>BUY ON DIPS:</b> મોમેન્ટમ સારો છે, લોઅર લેવલ પર એન્ટ્રી લઈ શકાય."
        elif price < ema9 and price < ema21 and rsi <= 42:
            sentiment = "⚠️ BEARISH PRESSURE"
            action = "🔴 <b>AVOID / SHORT:</b> સેલિંગ પ્રેશર ચાલુ છે, નવી ખરીદી ટાળવી."
            
    # 🔥 Risk-Reward 1:2 Logic (SL = -$50 | Target = +$100)
    t_btc = round(price + 100, 2)
    sl_btc = round(price - 50, 2)
    news = fetch_google_news("Bitcoin Crypto")
    
    return f"""🪙 <b>{name} LIVE REPORT & SENTIMENT</b>

💰 <b>Live Price:</b> ${price:,} ({change:+} | {p_change:+}-%)
🔼 <b>Day High:</b> ${d_high:,} | 🔽 <b>Day Low:</b> ${d_low:,}
📉 <b>RSI (14):</b> {rsi} | 📈 <b>EMA9:</b> {ema9 or 'N/A'}
------------------------------------------
🔥 <b>Intraday Sentiment:</b> {sentiment}
👉 <b>કરંટ પ્રાઈઝથી શું કરવું?:</b> {action}
------------------------------------------
🎯 <b>Logic Target (+$100):</b> ${t_btc:,} [R:R 1:2]
🛑 <b>Logic Stop Loss (-$50):</b> ${sl_btc:,}
{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

# =========================================================
# ⚡ HBL પાવરફુલ સેન્ટિમેન્ટ એન્જિન (Risk-Reward 1:2)
# =========================================================
def get_hbl_advanced_report():
    price, closes, _, prev_close, _, name, d_high, d_low = fetch_live_data("HBLENGINE.NS")
    if not price: return "❌ HBL નો લાઈવ ડેટા મળી શક્યો નહિ."
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    rsi = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    
    sentiment = "⚖️ SIDEWAYS / NEUTRAL"
    action = "👀 અત્યારે શાંતિ રાખો, કન્ફર્મ બ્રેકઆઉટની વેટ કરો."
    
    if ema9 and ema21 and rsi != "N/A":
        if price > ema9 and price > ema21 and rsi >= 55:
            sentiment = "🚀 STRONG BULLISH"
            action = "🟢 <b>BUY / HOLD:</b> કરંટ પ્રાઈઝથી ઇન્ટ્રાડે બાય કરી શકાય અથવા પોઝિશન હોલ્ડ રખાય."
        elif price > ema9 and 50 <= rsi < 55:
            sentiment = "🟢 MILD BULLISH"
            action = "📉 <b>BUY ON DIPS:</b> નાની અન્ડરલાઈંગ મોમેન્ટમ છે, ડીપમાં એડ કરી શકાય."
        elif price < ema9 and price < ema21 and rsi <= 40:
            sentiment = "⚠️ BEARISH PRESSURE"
            action = "🔴 <b>AVOID / SHORT:</b> નવો ટ્રેડ લેવો નહિ, સેલિંગ પ્રેશર વધારે છે."
            
    # 🔥 Risk-Reward 1:2 Logic (SL = -₹5 | Target = +₹10)
    t_intra = round(price + 10, 2)
    sl_intra = round(price - 5, 2)
    news = fetch_google_news("HBL Power")
    
    return f"""⚡ <b>{name} LIVE REPORT & SENTIMENT</b>

💰 <b>Live Price:</b> ₹{price} ({change:+} | {p_change:+}-%)
🔼 <b>Day High:</b> ₹{d_high} | 🔽 <b>Day Low:</b> ₹{d_low}
📉 <b>RSI (14):</b> {rsi} | 📈 <b>EMA9:</b> {ema9 or 'N/A'}
------------------------------------------
🔥 <b>Intraday Sentiment:</b> {sentiment}
👉 <b>કરંટ પ્રાઈઝથી શું કરવું?:</b> {action}
------------------------------------------
🎯 <b>Logic Target (+₹10):</b> ₹{t_intra} [R:R 1:2]
🛑 <b>Logic Stop Loss (-₹5):</b> ₹{sl_intra}
{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

def get_report(symbol, is_crypto=False):
    if symbol == "HBLENGINE.NS": return get_hbl_advanced_report()
    if symbol == "BTC-USD": return get_btc_advanced_report()
        
    price, closes, _, prev_close, _, name, d_high, d_low = fetch_live_data(symbol)
    if not price: return f"❌ '{symbol}' નો લાઈવ ડેટા મળી શક્યો નહિ."
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    sign = "$" if is_crypto else "₹"
    emoji = "🟢📈" if change >= 0 else "🔴📉"
    
    news = fetch_google_news(name)
    expiry_text = get_expiry_alert() if not is_crypto else ""
    if expiry_text: expiry_text = f"\n\n{expiry_text}"
    
    return f"""{emoji} <b>{name} LIVE REPORT</b>

💰 <b>Live Price:</b> {sign}{price:,}
🔼 <b>Day High:</b> {sign}{d_high:,} | 🔽 <b>Day Low:</b> {sign}{d_low:,}
🔄 <b>Today's Change:</b> {change:+} ({p_change:+}%){expiry_text}{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

def send_telegram_msg(text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def send_main_menu():
    markup = {
        "inline_keyboard": [
            [{"text": "⚡ HBL Power", "callback_data": "m_hbl"}, {"text": "🪙 Bitcoin (24/7)", "callback_data": "m_btc"}],
            [{"text": "📊 NIFTY 50", "callback_data": "m_nifty"}, {"text": "📈 BANK NIFTY", "callback_data": "m_bnifty"}],
            [{"text": "💎 SENSEX", "callback_data": "m_sensex"}, {"text": "🚀 NIFTY NEXT 50", "callback_data": "m_next50"}],
            [{"text": "🔥 MIDCAP 100", "callback_data": "m_midcap"}, {"text": "🔍 Search Stock", "callback_data": "m_search"}]
        ]
    }
    send_telegram_msg("👋 <b>નમસ્તે રવિ! (Market Master Panel)</b>\n\nનવો Risk-Reward 1:2 રેશિયો સેટ થઈ ગયો છે! ડેટા જોવા માટે નીચે ટેબ પર ક્લિક કરો:", reply_markup=markup)

def handle_callback(callback_id, data):
    global user_status
    text = ""
    if data == "m_hbl": text = get_report("HBLENGINE.NS")
    elif data == "m_btc": text = get_report("BTC-USD", is_crypto=True)
    elif data == "m_nifty": text = get_report("^NSEI")
    elif data == "m_bnifty": text = get_report("^NSEBANK")
    elif data == "m_sensex": text = get_report("^BSESN")
    elif data == "m_next50": text = get_report("^NSE91")
    elif data == "m_midcap": text = get_report("^NSMIDCP")
    elif data == "m_search":
        user_status[CHAT_ID] = "WAITING_FOR_SEARCH"
        text = "🔍 <b>Script Search Activated:</b>\n\nકૃપા કરીને નામ મોકલો:"
    
    if text: send_telegram_msg(text)
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})

def handle_search_text(user_text):
    global user_status
    query = user_text.upper().strip()
    mapping = {
        "RELIANCE": "RELIANCE.NS", "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS",
        "TCS": "TCS.NS", "SBI": "SBIN.NS", "HDFC": "HDFCBANK.NS"
    }
    symbol = mapping.get(query, f"{query}.NS")
    text = get_report(symbol)
    send_telegram_msg(text)
    user_status[CHAT_ID] = None 

# ============================================
# MAIN LOOP
# ============================================
print("Master engine with 1:2 Risk-Reward Active...")
offset = 0
start_time = time.time()

while time.time() - start_time < 110:
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=5"
        r = requests.get(url, timeout=10).json()
        if "result" in r:
            for update in r["result"]:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    user_msg = update["message"]["text"]
                    if user_msg.lower() in ["hi", "hello", "menu"]:
                        send_main_menu()
                    else:
                        handle_search_text(user_msg)
                elif "callback_query" in update:
                    handle_callback(update["callback_query"]["id"], update["callback_query"]["data"])
    except:
        pass
    time.sleep(1)
