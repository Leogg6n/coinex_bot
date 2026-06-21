import time
import json
from config import *
from coin_ex_api import get_kline, get_ticker, place_order, get_position, cancel_order
from strategy import get_signal

balance_usdt = CAPITAL
current_position = None
trailing_stop_price = None

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_current_price(symbol):
    ticker = get_ticker(symbol)
    if ticker and 'data' in ticker:
        if 'ticker' in ticker['data'] and 'last' in ticker['data']['ticker']:
            return float(ticker['data']['ticker']['last'])
        elif 'last' in ticker['data']:
            return float(ticker['data']['last'])
    return None

def paper_trade(signal, price):
    global balance_usdt, current_position, trailing_stop_price
    
    # --- Lógica de Trailing Stop ---
    if current_position:
        entry = current_position['entry_price']
        side = current_position['side']
        is_long = (side == 'buy')
        
        if trailing_stop_price is None:
            if is_long and price >= entry * 1.02:
                trailing_stop_price = entry * 1.01
                log(f"🛡️ Trailing Stop ACTIVADO (Long). Stop inicial en {trailing_stop_price:.2f}")
            elif not is_long and price <= entry * 0.98:
                trailing_stop_price = entry * 0.99
                log(f"🛡️ Trailing Stop ACTIVADO (Short). Stop inicial en {trailing_stop_price:.2f}")
        
        if trailing_stop_price is not None:
            if is_long and price > current_position.get('highest_price', entry):
                current_position['highest_price'] = price
                new_trail = price * 0.99
                if new_trail > trailing_stop_price:
                    trailing_stop_price = new_trail
                    log(f"🔄 Trailing Stop movido a {trailing_stop_price:.2f}")
            elif not is_long and price < current_position.get('lowest_price', entry):
                current_position['lowest_price'] = price
                new_trail = price * 1.01
                if new_trail < trailing_stop_price:
                    trailing_stop_price = new_trail
                    log(f"🔄 Trailing Stop movido a {trailing_stop_price:.2f}")
        
        sl_triggered = False
        if is_long:
            if price <= trailing_stop_price if trailing_stop_price else entry * (1 - SL_PERCENT):
                sl_triggered = True
                log(f"🔴 STOP LOSS / TRAILING (Long). Precio: {price}")
        else:
            if price >= trailing_stop_price if trailing_stop_price else entry * (1 + SL_PERCENT):
                sl_triggered = True
                log(f"🔴 STOP LOSS / TRAILING (Short). Precio: {price}")
        
        if sl_triggered:
            if is_long:
                balance_usdt += current_position['amount'] * price * LEVERAGE
            else:
                balance_usdt += current_position['amount'] * (2*entry - price) * LEVERAGE
            current_position = None
            trailing_stop_price = None
            log(f"💰 Balance actual: {balance_usdt:.2f} USDT")
            return
        
        if is_long and price >= entry * (1 + TP_PERCENT):
            log(f"🟢 TAKE PROFIT (Long). Precio: {price}")
            balance_usdt += current_position['amount'] * price * LEVERAGE
            current_position = None
            trailing_stop_price = None
            log(f"💰 Balance actual: {balance_usdt:.2f} USDT")
            return
        elif not is_long and price <= entry * (1 - TP_PERCENT):
            log(f"🟢 TAKE PROFIT (Short). Precio: {price}")
            balance_usdt += current_position['amount'] * (2*entry - price) * LEVERAGE
            current_position = None
            trailing_stop_price = None
            log(f"💰 Balance actual: {balance_usdt:.2f} USDT")
            return
    
    # --- Nueva posición ---
    if not current_position and signal != 'none':
        amount_to_invest = balance_usdt * POSITION_SIZE_PERCENT
        position_amount = amount_to_invest / price
        log(f"📈 Señal {signal.upper()} confirmada por Volumen y EMA200. Abriendo a {price}")
        current_position = {
            'side': 'buy' if signal == 'buy' else 'sell',
            'entry_price': price,
            'amount': position_amount,
            'order_id': 'paper_' + str(int(time.time()))
        }
        if signal == 'buy':
            balance_usdt -= amount_to_invest
        else:
            balance_usdt -= amount_to_invest
        log(f"✅ Posición abierta: {signal.upper()} a {price}. Balance restante: {balance_usdt:.2f} USDT")

def main_loop():
    log("🚀 Bot ULTRA MEJORADO: EMA 20/50 + EMA200 Macro + Volumen + RSI + Trailing")
    log(f"Capital inicial: {CAPITAL} USDT | Apalancamiento: {LEVERAGE}x")
    while True:
        try:
            kline = get_kline(SYMBOL, TIMEFRAME, limit=250)  # Pedimos más velas para la EMA 200
            price = get_current_price(SYMBOL)
            if not kline or not price:
                log("⚠️ No datos. Esperando 60s...")
                time.sleep(60)
                continue
            signal = get_signal(kline)
            log(f"Precio: {price} | Señal: {signal.upper() if signal != 'none' else 'Ninguna'}")
            paper_trade(signal, price)
            if current_position:
                log(f"📊 Posición: {current_position['side']} @ {current_position['entry_price']} | Balance: {balance_usdt:.2f} USDT")
            else:
                log(f"💰 Balance: {balance_usdt:.2f} USDT")
            time.sleep(300)
        except KeyboardInterrupt:
            log("🛑 Bot detenido.")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
