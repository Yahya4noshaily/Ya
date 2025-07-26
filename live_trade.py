from pocketoptionapi.stable_api import PocketOption
import time

# ---- إعداد الاتصال ----
ssid = '7e8151e1f1d55d7b14388b328d14f5c9'  # استبدل بالقيم اللي بعثتها
account = PocketOption(ssid)
connected, msg = account.connect()
if not connected:
    print("❌ فشل الاتصال:", msg)
    exit(1)
balance = account.get_balance()
print(f"✅ تم الاتصال! رصيدك التجريبي: {balance:.2f} USD")

# ---- دوال المؤشرات ----
def simple_moving_average(data, period):
    return sum(data[-period:]) / period

def rsi(data, period=14):
    gains, losses = [], []
    for i in range(1, len(data)):
        diff = data[i] - data[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bollinger_bands(data, period=20, num_std_dev=2):
    window = data[-period:]
    sma = sum(window) / period
    variance = sum((x - sma)**2 for x in window) / period
    std = variance**0.5
    return sma, sma + num_std_dev*std, sma - num_std_dev*std

# ---- جلب الشموع ----
def fetch_candles(pair="EURUSD", timeframe=60, count=50):
    """
    يرجع قائمة dict لكل شمعة: {'open', 'high', 'low', 'close'}
    """
    return account.get_candles(pair, timeframe, count)

# ---- تحديد الإشارة ----
def get_signal(pair="EURUSD", timeframe=60):
    candles = fetch_candles(pair, timeframe)
    closes = [c['close'] for c in candles]
    if len(closes) < 20:
        print("⚠️ بيانات غير كافية للإشارة.")
        return None

    # حساب المؤشرات
    sma_short = simple_moving_average(closes, 5)
    sma_long  = simple_moving_average(closes, 15)
    current_rsi = rsi(closes, 14)
    bb_mid, bb_upper, bb_lower = bollinger_bands(closes, 20, 2)
    last_price = closes[-1]

    print(f"SMA5={sma_short:.5f}, SMA15={sma_long:.5f}, RSI={current_rsi:.2f}, "
          f"BB_mid={bb_mid:.5f}")

    # شروط الشراء
    buy_cond  = sma_short > sma_long and (current_rsi < 70) and (last_price > bb_mid)
    # شروط البيع
    sell_cond = sma_short < sma_long and (current_rsi > 30) and (last_price < bb_mid)

    if buy_cond and current_rsi > 50:
        return "call"
    if sell_cond and current_rsi < 50:
        return "put"
    return None

# ---- فتح الصفقة ----
def open_trade(pair="EURUSD", amount=1.0, duration=60):
    direction = get_signal(pair, duration)
    if not direction:
        print("⚠️ لا إشارة واضحة الآن، تأجل التداول.")
        return

    action = "شراء" if direction == "call" else "بيع"
    print(f"🔔 توصية قوية: {action} لمدة {duration} ثانية، مبلغ {amount} USD")

    trade_id = account.buy(pair, amount, direction, duration)
    time.sleep(duration + 1)
    result = account.check_win(trade_id)
    print("📊 نتيجة الصفقة:", "📈 ربح" if result > 0 else "📉 خسارة")
    return result

# ---- التنفيذ الرئيسي ----
if __name__ == "__main__":
    pair     = "EURUSD"  # EUR/USD OTC
    amount   = 1.0       # المبلغ بالدولار
    duration = 60        # ثواني

    open_trade(pair, amount, duration)
