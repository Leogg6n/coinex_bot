import time
import json
import os
from config import *
from coin_ex_api import get_kline, get_ticker, place_order, get_position, cancel_order
from strategy import get_signal

STATE_FILE = "state.json"

balance_usdt = CAPITAL
current_position = None
trailing_stop_price = None

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_state():
    global balance_usdt, current_position, trailing_stop_price
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                balance_usdt = data.get('balance_usdt', CAPITAL)
                current_position = data.get('current_position')
                trailing_stop_price = data.get('trailing_stop_price')
                log(f"📂 Estado cargado. Balance real: {balance_usdt:.2f} USDT")
        except Exception as e:
            log(f"⚠️ Error al cargar estado. Usando por defecto. Error: {e}")

def save_state():
    data = {
        'balance_usdt': balance_usdt,
        'current_position': current_position,
        'trailing_stop_price': trailing_stop_price
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f)

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
    
    # --- Lógica de cierre de posición ---
    if current_position:
        entry = current_position['entry_price']
        side = current_position['side']
        is_long = (side == 'buy')
        position_qty = current_position['position_qty']
        margin_used = current_position['margin_used']
        
        # Calculamos el precio de cierre (SL/TP o Trailing)
        close_price = None
        sl_triggered = False
        tp_triggered = False
        
        # Trailing Stop Logic
        if trailing_stop_price is None:
            if is_long and price >= entry * 1.02:
                trailing_stop_price = entry * 1.01
                log(f"🛡️ Trailing Stop ACTIVADO (Long). Stop en {trailing_stop_price:.2f}")
            elif not is_long and price <= entry * 0.98:
                trailing_stop_price = entry * 0.99
                log(f"🛡️ Trailing Stop ACTIVADO (Short). Stop en {trailing_stop_price:.2f}")
        
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
        
        # Chequeo de Stop Loss y Take Profit
        if is_long:
            if price <= (trailing_stop_price if trailing_stop_price else entry * (1 - SL_PERCENT)):
                close_price = price
                sl_triggered = True
                log(f"🔴 STOP LOSS (Long) ejecutado a {price}")
            elif price >= entry * (1 + TP_PERCENT):
                close_price = price
                tp_triggered = True
                log(f"🟢 TAKE PROFIT (Long) ejecutado a {price}")
        else:  # Short
            if price >= (trailing_stop_price if trailing_stop_price else entry * (1 + SL_PERCENT)):
                close_price = price
                sl_triggered = True
                log(f"🔴 STOP LOSS (Short) ejecutado a {price}")
            elif price <= entry * (1 - TP_PERCENT):
                close_price = price
                tp_triggered = True
                log(f"🟢 TAKE PROFIT (Short) ejecutado a {price}")
        
        # Si se activó cierre, calculamos ganancias/pérdidas REALES con comisiones
        if sl_triggered or tp_triggered:
            # Cálculo del P&L y comisiones
            position_value_close = position_qty * close_price
            
            if is_long:
                pnl = (close_price - entry) * position_qty
            else:
                pnl = (entry - close_price) * position_qty
            
            fee_open = (position_qty * entry) * FEE_PERCENT
            fee_close = position_value_close * FEE_PERCENT
            total_fees = fee_open + fee_close
            
            net_balance_change = pnl - total_fees
            
            balance_usdt += margin_used + net_balance_change
            log(f"💰 Ganancia bruta: {pnl:.2f} | Comisiones totales: -{total_fees:.2f} | Beneficio NETO: {net_balance_change:.2f} USDT")
            log(f"💰 Nuevo balance real: {balance_usdt:.2f} USDT")
            
            current_position = None
            trailing_stop_price = None
            save_state()
            return
    
    # --- Lógica de apertura de posición ---
    if not current_position and signal != 'none':
        # Calculamos el margen a invertir
        margin_to_invest = balance_usdt * POSITION_SIZE_PERCENT
        
        # VALIDACIÓN DE MONTO MÍNIMO DE COINEX
        position_value = margin_to_invest * LEVERAGE
        if position_value < MIN_POSITION_VALUE_USDT:
            margin_to_invest = MIN_POSITION_VALUE_USDT / LEVERAGE
            log(f"⚠️ Ajustando margen para cumplir el mínimo de CoinEx ({MIN_POSITION_VALUE_USDT} USDT en valor de posición)")
        
        # Si no tenemos suficiente balance, no abrimos
        if margin_to_invest > balance_usdt:
            log("❌ Balance insuficiente para abrir posición.")
            return
        
        # Calcular cantidad de contrato (por ejemplo, BTC)
        position_qty = (margin_to_invest * LEVERAGE) / price
        fee_open = (position_qty * price) * FEE_PERCENT
        
        log(f"📈 Señal {signal.upper()} confirmada. Abriendo posición a {price}")
        log(f"📊 Margen usado: {margin_to_invest:.2f} USDT | Valor posición: {position_qty * price:.2f} USDT | Comisión apertura: -{fee_open:.2f} USDT")
        
        current_position = {
            'side': 'buy' if signal == 'buy' else 'sell',
            'entry_price': price,
            'position_qty': position_qty,
            'margin_used': margin_to_invest,
            'order_id': 'paper_' + str(int(time.time()))
        }
        
        # Descontamos el margen y la comisión de apertura del balance
        balance_usdt -= (margin_to_invest + fee_open)
        log(f"✅ Posición abierta. Balance restante tras comisión: {balance_usdt:.2f} USDT")
        save_state()

def main_loop():
    load_state()
    log("🚀 Bot ULTRA REALISTA: Comisiones 0.05% + Mínimo CoinEx (5 USDT)")
    log(f"Capital inicial: {CAPITAL} USDT | Balance actual: {balance_usdt:.2f} USDT")
    
    while True:
        try:
            kline = get_kline(SYMBOL, TIMEFRAME, limit=250)
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
            
            save_state()
            time.sleep(300)
            
        except KeyboardInterrupt:
            log("🛑 Bot detenido.")
            save_state()
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
