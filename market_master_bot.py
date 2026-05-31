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
        volumes = [x for x in res["indicators"]["quote"][0]["volume"] if x is not None]
        price = res["meta"]["regularMarketPrice"]
        prev_close = res["meta"].get("previousClose", price)
        
        name = symbol
        if symbol == "^NSEI": name = "NIFTY 50"
        elif symbol == "^NSEBANK": name = "BANK NIFTY"
        elif symbol == "^BSESN": name = "SENSEX"
        elif symbol == "^NSMIDCP": name = "NIFTY MIDCAP 100"
        elif symbol == "^NSE91": name = "NIFTY NEXT 50"
        elif symbol == "HBLENGINE.NS": name = "HBL POWER"
        
        recent_highs = highs[-20:] if len(highs) >= 20 else highs
        recent_lows = lows[-20:] if len(lows) >= 20 else lows
        recent_vols = volumes[-20:] if len(volumes) >= 20 else volumes
        
        tf_resistance = round(max(recent_highs), 2) if recent_highs else price
        tf_support = round(min(recent_lows), 2) if recent_lows else price
        
        current_vol = volumes[-1] if volumes else 0
        avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 1
        vol_ratio = round(current_vol / avg_vol, 1) if current_vol else 0
        
        return round(price, 2), closes, round(prev_close, 2), name, tf_resistance, tf_support, vol_ratio
    except:
        return None, [], None, symbol, None, None, 0

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

def check_higher_tf_trend(symbol):
    # બેકગ્રાઉન્ડમાં મોટા ટાઇમફ્રેમ (1 Hour) નો ટ્રેન્ડ ચેક કરવા માટેનું હેલ્પર
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1h&range=1mo"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).json()
        res = r["chart"]["result"][0]
        closes = [x for x in res["indicators"]["quote"][0]["close"] if x is not None]
        price = res["meta"]["regularMarketPrice"]
        ema9 = calc_ema(closes, 9)
        if ema9 and price > ema9: return True
    except:
        pass
    return False

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
# 🔄 મલ્ટિ-ટાઇમફ્રેમ સપોર્ટ/રેઝિસ્ટન્સ અને જેકપોટ એન્જિન
# =========================================================
def generate_advanced_report(symbol, interval="5m", is_crypto=False):
    price, closes, prev_close, name, tf_res, tf_sup, vol_ratio = fetch_live_data(symbol, interval)
    if not price: return f"❌ '{symbol}' નો લાઈવ ડેટા મળી શક્યો નહિ.", None
    
    rsi = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    
    change = round(price - prev_close, 2)
    p_change = round((change / prev_close) * 100, 2)
    sign = "$" if is_crypto else "₹"
    
    if interval in ["5m", "15m", "30m"]:
        trade_type = "INTRADAY"
        is_intraday = True
    else:
        trade_type = "SWING TRADING"
        is_intraday = False
        
    sentiment = "⚖️ SIDEWAYS / NEUTRAL"
    action = f"👀 {trade_type}: પ્રાઇઝ અત્યારે સપોર્ટ અને રેઝિસ્ટન્સની વચ્ચે ફસાયેલી છે. બ્રેકઆઉટની વેટ કરો."
    
    vol_emoji = "📊"
    if vol_ratio >= 2.0: vol_emoji = "🔥 HIGH VOLUME BOOST"
    elif vol_ratio <= 0.5: vol_emoji = "💤 LOW VOLUME DRY"
    vol_text = f"{vol_emoji} ({vol_ratio}x of Avg)"
    
    entry_logic_text = f"📍 <b>CHART LEVELS ({interval}):</b>\n🚧 <b>TF Resistance:</b> {sign}{tf_res:,}\n🛡️ <b>TF Support:</b> {sign}{tf_sup:,}\n📈 <b>Volume Mood:</b> {vol_text}\n\n👉 <i>આ ટાઇમફ્રેમ પર કન્ફર્મ બ્રેકઆઉટ વગર નવી એન્ટ્રી હિતાવહ નથી.</i>"
    
    if len(closes) > 21 and ema9 and ema21 and rsi != "N/A":
        # ૧. તેજીનો ટ્રેન્ડ (Bullish Breakout Entry)
        if price > ema9 and price > ema21 and rsi >= 55:
            sentiment = "🚀 STRONG BULLISH"
            action = f"🟢 <b>TREND:</b> {interval} ચાર્ટ પર ટ્રેન્ડ જોરદાર અપ છે. રેઝિસ્ટન્સ ક્રોસ થતાં જ સ્માર્ટ એન્ટ્રી લઈ શકાય."
            
            suggested_entry = round(tf_res * 1.001, 2)
            suggested_sl = tf_sup
            risk_points = round(suggested_entry - suggested_sl, 2)
            suggested_tgt = round(suggested_entry + (risk_points * 2), 2)
            
            # 🔥 જેકપોટ મોમેન્ટમ ડિટેક્ટર લોજિક
            jackpot_text = ""
            if is_intraday and vol_ratio >= 2.0:
                # બેકગ્રાઉન્ડમાં હાયર ટાઇમફ્રેમ કન્ફર્મેશન લેવું
                if check_higher_tf_trend(symbol):
                    jackpot_text = "\n\n🚀 <b>🔥 JACKPOT RALLY ALERT:</b>\nઆ ઇન્ટ્રાડે સેટઅપમાં બહુ મોટું પોટેન્શિયલ છે! ભારે વોલ્યુમ અને મોટા ટાઇમફ્રેમનો પણ સપોર્ટ હોવાથી, એન્ટ્રી મળ્યા પછી નાનો પ્રોફિટ લઈને નીકળવાને બદલે <b>Trailing SL</b> સાથે મોટી રેલી માટે હોલ્ડ કરો!"
            
            entry_logic_text = f"📍 <b>CHART LEVELS ({interval}):</b>\n🚧 <b>TF Resistance:</b> {sign}{tf_res:,}\n🛡️ <b>TF Support:</b> {sign}{tf_sup:,}\n📈 <b>Volume Mood:</b> {vol_text}\n\n💡 <b>SMART TRADING SETUP (R:R 1:2):</b>\n🚀 <b>Suggested Entry (Above TF High):</b> {sign}{suggested_entry:,}\n🎯 <b>Target (TGT):</b> {sign}{suggested_tgt:,}\n🛑 <b>Stop Loss (SL):</b> {sign}{suggested_sl:,}{jackpot_text}"
            
        # ૨. મંદીનો ટ્રેન્ડ (Bearish Breakdown Entry)
        elif price < ema9 and price < ema21 and rsi <= 42:
            sentiment = "⚠️ BEARISH PRESSURE"
            if "NIFTY" in name or "SENSEX" in name:
                action = f"🔴 <b>TREND:</b> {interval} પર આખું માર્કેટ મંદીના સકંજામાં છે. નવી બાયિંગ એન્ટ્રી અત્યારે ભૂલથી પણ ન કરવી.\n\n🛑 <b>HOLDING EXIT ALERT:</b> આખા માર્કેટનો ટ્રેન્ડ નેગેટિવ હોવાથી, જો તમારા પર્સનલ સ્ટોક્સ સપોર્ટ તોડતા હોય તો મોટું નુકસાન રોકવા તાત્કાલિક <b>SELL (Exit)</b> કરવાનું સજેશન છે!"
            else:
                action = f"🔴 <b>TREND:</b> {interval} ચાર્ટ પર ભારે સેલિંગ પ્રેશર ચાલુ છે. નવી ખરીદી ટાળવી.\n\n🛑 <b>HOLDING EXIT ALERT:</b> નુકસાન વધુ મોટું થાય એ પહેલાં કેપિટલ બચાવવા કરંટ ભાવથી હોલ્ડિંગ <b>SELL (Exit)</b> કરવાનું ખાસ સજેશન છે!"
            
            suggested_entry = round(tf_sup * 0.999, 2)
            suggested_sl = tf_res
            risk_points = round(suggested_sl - suggested_entry, 2)
            suggested_tgt = round(suggested_entry - (risk_points * 2), 2)
            
            entry_logic_text = f"📍 <b>CHART LEVELS ({interval}):</b>\n🚧 <b>TF Resistance:</b> {sign}{tf_res:,}\n🛡️ <b>TF Support:</b> {sign}{tf_sup:,}\n📈 <b>Volume Mood:</b> {vol_text}\n\n💡 <b>SMART TRADING SETUP (R:R 1:2):</b>\n📉 <b>Suggested Short Entry (Below TF Low):</b> {sign}{suggested_entry:,}\n🎯 <b>Short Target:</b> {sign}{suggested_tgt:,}\n🛑 <b>Short Stop Loss:</b> {sign}{suggested_sl:,}"

    news = fetch_google_news("Bitcoin Crypto" if is_crypto else name) if interval == "5m" else ""
    expiry_text = get_expiry_alert() if (not is_crypto and interval == "5m") else ""
    if expiry_text: expiry_text = f"\n\n{expiry_text}"
    
    emoji = "🟢📈" if change >= 0 else "🔴📉"
    
    text = f"""{emoji} <b>{name} LIVE REPORT ({interval} | {trade_type})</b>

💰 <b>Live Price:</b> {sign}{price:,} ({change:+} | {p_change:+}-%)
📉 <b>RSI (14):</b> {rsi} | 📈 <b>EMA9:</b> {ema9 or 'N/A'}
------------------------------------------
🔥 <b>Intraday Sentiment:</b> {sentiment}
👉 <b>કરંટ માર્કેટ મૂડ:</b> {action}
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
# TELEGRAM UI & INTERACTIONS
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
    send_telegram_msg("👋 <b>નમસ્તે રવિ! (Market Master Panel)</b>\n\nજેકપોટ રેલી ડિટેક્ટર સાથેનું ફૂલ ફાઇનલ એન્જિન તૈયાર છે. ટેસ્ટ કરવા નીચે ક્લિક કરો:", reply_markup=markup)

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
print("Ultimate Jackpot & Multi-Timeframe Analysis Engine Active...")
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
