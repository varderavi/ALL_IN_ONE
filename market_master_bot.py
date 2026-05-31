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

def get_range_for_interval(interval):
    if interval in ["5m", "15m", "30m"]: return "5d"
    elif interval == "1h": return "1mo"
    elif interval == "1d": return "3mo"
    return "5d"

def fetch_live_data(symbol, interval="5m"):
    timeframe_range = get_range_for_interval(interval)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={timeframe_range}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        res = r.json()["chart"]["result"][0]
        closes = [x for x in res["indicators"]["quote"][0]["close"] if x is not None]
        highs  = [x for x in res["indicators"]["quote"][0]["high"] if x is not None]
        lows   = [x for x in res["indicators"]["quote"][0]["low"] if x is not None]
        price = res["meta"]["regularMarketPrice"]
        prev_close = res["meta"].get("previousClose", price)
        
        name = symbol
        if symbol == "^NSEI": name = "NIFTY 50"
        elif symbol == "^NSEBANK": name = "BANK NIFTY"
        elif symbol == "^BSESN": name = "SENSEX"
        elif symbol == "^NSMIDCP": name = "NIFTY MIDCAP 100"
        elif symbol == "^NSE91": name = "NIFTY NEXT 50"
        elif symbol == "HBLENGINE.NS": name = "HBL POWER"
        
        day_high = round(highs[-1], 2) if highs else price
        day_low = round(lows[-1], 2) if lows else price
        
        return round(price, 2), closes, round(prev_close, 2), name, day_high, day_low
    except:
        return None, [], None, symbol, None, None

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
# 🔄 ટકાવારી (%-Based) સેન્ટિમેન્ટ અને રિસ્ક-રિવોર્ડ એન્જિન
# =========================================================
def generate_advanced_report(symbol, interval="5m", is_crypto=False):
    price, closes, prev_close, name, d_high, d_low = fetch_live_data(symbol, interval)
    if not price: return f"❌ '{symbol}' નો લાઈવ ડેટા મળી શક્યો નહિ.", None
    
    rsi = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    sign = "$" if is_crypto else "₹"
    
    # 🎯 🔥 ટકાવારી સેટ કરવાનું લોજિક (ઇન્ટ્રાડે વિ. સ્વિંગ)
    if interval in ["5m", "15m", "30m"]:
        trade_type = "INTRADAY"
        risk_pct = 0.01 if is_crypto else 0.005   # ક્રિપ્ટો 1%, સ્ટોક્સ 0.5%
        reward_pct = 0.02 if is_crypto else 0.01 # ક્રિપ્ટો 2%, સ્ટોક્સ 1.0%
    else:
        trade_type = "SWING TRADING"
        risk_pct = 0.04 if is_crypto else 0.02   # ક્રિપ્ટો 4%, સ્ટોક્સ 2.0%
        reward_pct = 0.08 if is_crypto else 0.04 # ક્રિપ્ટો 8%, સ્ટોક્સ 4.0%
        
    # ટકાવારી પ્રમાણે અસલી રૂપિયાની ગણતરી
    risk_amount = round(price * risk_pct, 2)
    reward_amount = round(price * reward_pct, 2)
    
    sentiment = "⚖️ SIDEWAYS / NEUTRAL"
    action = f"👀 {trade_type} માટે માર્કેટ ન્યુટ્રલ ઝોનમાં છે, ઉતાવળ કર્યા વગર વેટ કરો."
    
    buffer = 20 if "NIFTY" in name or "SENSEX" in name else (30 if is_crypto else 1.5)
    buy_above = round(max(ema9 or price, d_high) + buffer, 2)
    entry_logic_text = f"💡 <b>SUGGESTED ENTRY POINT:</b>\n🚀 <b>Buy Breakout:</b> {sign}{buy_above:,} ની ઉપર કેન્ડલ ક્લોઝ થાય તો જ નવો ટ્રેડ લેવો."
    
    if ema9 and ema21 and rsi != "N/A":
        # ૧. તેજી (Bullish)
        if price > ema9 and price > ema21 and rsi >= 55:
            sentiment = "🚀 STRONG BULLISH"
            action = f"🟢 <b>BUY / HOLD:</b> ચાર્ટ પર મજબૂત અપ-ટ્રેન્ડ છે. {trade_type} માટે પોઝિશન હોલ્ડ રખાય અથવા બાય કરાય."
            entry_logic_text = f"🎯 <b>TGT (+{risk_pct*200}%):</b> {sign}{round(price + reward_amount, 2):,} [R:R 1:2]\n🛑 <b>SL (-{risk_pct*100}%):</b> {sign}{round(price - risk_amount, 2):,}"
            
        elif price > ema9 and 50 <= rsi < 55:
            sentiment = "🟢 MILD BULLISH"
            action = f" odds <b>BUY ON DIPS:</b> ટ્રેન્ડ પોઝિટિવ બની રહ્યો છે, નાના ડીપ પર એન્ટ્રી લઈ શકાય."
            entry_logic_text = f"🎯 <b>TGT (+{risk_pct*200}%):</b> {sign}{round(price + reward_amount, 2):,} [R:R 1:2]\n🛑 <b>SL (-{risk_pct*100}%):</b> {sign}{round(price - risk_amount, 2):,}"
            
        # ૨. મંદી (Bearish)
        elif price < ema9 and price < ema21 and rsi <= 42:
            sentiment = "⚠️ BEARISH PRESSURE"
            if "NIFTY" in name or "SENSEX" in name:
                action = f"🔴 <b>AVOID NEW BUY:</b> આખો ઇન્ડેક્સ મંદીમાં છે. નવી કોઈ બાયિંગ એન્ટ્રી અત્યારે ભૂલથી પણ ન કરવી.\n\n🛑 <b>HOLDING EXIT ALERT:</b> આખા માર્કેટનો ટ્રેન્ડ ડાઉન હોવાથી, જો તમારા પર્સનલ સ્ટોક્સ તૂટતા હોય તો મોટું નુકસાન રોકવા <b>SELL (Exit)</b> કરવાનું સજેશન છે!"
            else:
                action = f"🔴 <b>AVOID NEW BUY:</b> શેરમાં ભારે કડાકો છે, નવી ખરીદી ટાળવી.\n\n🛑 <b>HOLDING EXIT ALERT:</b> નુકસાન વધે એ પહેલાં સેફ્ટી માટે કરંટ ભાવથી હોલ્ડિંગ <b>SELL (Exit)</b> કરવાનું ખાસ સજેશન છે!"
            entry_logic_text = f"🎯 <b>Short TGT (-{risk_pct*200}%):</b> {sign}{round(price - reward_amount, 2):,} [R:R 1:2]\n🛑 <b>Short SL (+{risk_pct*100}%):</b> {sign}{round(price + risk_amount, 2):,}"

    news = fetch_google_news("Bitcoin Crypto" if is_crypto else name) if interval == "5m" else ""
    expiry_text = get_expiry_alert() if (not is_crypto and interval == "5m") else ""
    if expiry_text: expiry_text = f"\n\n{expiry_text}"
    
    emoji = "🟢📈" if change >= 0 else "🔴📉"
    
    text = f"""{emoji} <b>{name} LIVE REPORT ({interval} | {trade_type})</b>

💰 <b>Live Price:</b> {sign}{price:,} ({change:+} | {p_change:+}-%)
🔼 <b>Day High:</b> {sign}{d_high:,} | 🔽 <b>Day Low:</b> {sign}{d_low:,}
📉 <b>RSI (14):</b> {rsi} | 📈 <b>EMA9:</b> {ema9 or 'N/A'}
------------------------------------------
🔥 <b>Intraday Sentiment:</b> {sentiment}
👉 <b>કરંટ પ્રાઈઝથી શું કરવું?:</b> {action}
------------------------------------------
{entry_logic_text}{expiry_text}{news}
⏰ {now_ist().strftime('%H:%M:%S IST')}"""

    c_type = "1" if is_crypto else "0"
    markup = {
        "inline_keyboard": [
            [
                {"text": "⏱️ 5 Min", "callback_data": f"tf_{symbol}_{interval}_{c_type}_5m"},
                {"text": "⏱️ 15 Min", "callback_data": f"tf_{symbol}_{interval}_{c_type}_15m"},
                {"text": "⏱️ 30 Min", "callback_data": f"tf_{symbol}_{interval}_{c_type}_30m"}
            ],
            [
                {"text": "⏳ 1 Hour", "callback_data": f"tf_{symbol}_{interval}_{c_type}_1h"},
                {"text": "📅 1 Day", "callback_data": f"tf_{symbol}_{interval}_{c_type}_1d"}
            ],
            [{"text": "🔙 Back to Main Menu", "callback_data": "go_main"}]
        ]
    }
    return text, markup

# ============================================
# TELEGRAM UI & MAIN MENUS
# ============================================
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
    send_telegram_msg("👋 <b>નમસ્તે રવિ! (Market Master Panel)</b>\n\nતમારો નવો **% બેઝ્ડ સ્માર્ટ રિસ્ક-રિવોર્ડ** કોડ લાઈવ થઈ ગયો છે. નીચે ક્લિક કરો:", reply_markup=markup)

def handle_callback(callback_id, data):
    global user_status
    text, markup = "", None
    
    if data == "m_hbl": text, markup = generate_advanced_report("HBLENGINE.NS", "5m")
    elif data == "m_btc": text, markup = generate_advanced_report("BTC-USD", "5m", is_crypto=True)
    elif data == "m_nifty": text, markup = generate_advanced_report("^NSEI", "5m")
    elif data == "m_bnifty": text, markup = generate_advanced_report("^NSEBANK", "5m")
    elif data == "m_sensex": text, markup = generate_advanced_report("^BSESN", "5m")
    elif data == "m_next50": text, markup = generate_advanced_report("^NSE91", "5m")
    elif data == "m_midcap": text, markup = generate_advanced_report("^NSMIDCP", "5m")
    elif data == "go_main": 
        send_main_menu()
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})
        return
    elif data == "m_search":
        user_status[CHAT_ID] = "WAITING_FOR_SEARCH"
        send_telegram_msg("🔍 <b>Script Search Activated:</b>\n\nકૃપા કરીને નામ મોકલો:")
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})
        return
    elif data.startswith("tf_"):
        parts = data.split("_")
        sym = parts[1]
        is_cry = True if parts[3] == "1" else False
        new_tf = parts[4]
        text, markup = generate_advanced_report(sym, new_tf, is_crypto=is_cry)

    if text: send_telegram_msg(text, reply_markup=markup)
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})

def handle_search_text(user_text):
    global user_status
    query = user_text.upper().strip()
    mapping = {
        "RELIANCE": "RELIANCE.NS", "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS",
        "TCS": "TCS.NS", "SBI": "SBIN.NS", "HDFC": "HDFCBANK.NS"
    }
    symbol = mapping.get(query, f"{query}.NS")
    text, markup = generate_advanced_report(symbol, "5m")
    send_telegram_msg(text, reply_markup=markup)
    user_status[CHAT_ID] = None 

# ============================================
# MAIN LOOP
# ============================================
print("Percentage-Based Multi-Timeframe Engine Active...")
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
