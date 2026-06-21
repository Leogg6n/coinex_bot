import numpy as np

def calculate_ema(prices, period):
    if len(prices) < period:
        return None
    alpha = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price * alpha) + (ema * (1 - alpha))
    return ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains = []
    losses = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i-1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def get_signal(kline_data):
    if not kline_data or 'data' not in kline_data:
        return 'none'
    
    closes = [float(candle[2]) for candle in kline_data['data']]
    volumes = [float(candle[5]) for candle in kline_data['data']]  # Índice 5 es volumen
    
    if len(closes) < 200:  # Necesitamos al menos 200 velas para la EMA 200
        return 'none'
    
    # Cálculo de EMAs
    ema_20 = calculate_ema(closes[-20:], 20)
    ema_50 = calculate_ema(closes[-50:], 50)
    ema_200 = calculate_ema(closes[-200:], 200)  # Nueva EMA macro
    prev_ema_20 = calculate_ema(closes[-21:-1], 20)
    prev_ema_50 = calculate_ema(closes[-51:-1], 50)
    
    # RSI
    rsi = calculate_rsi(closes[-20:], 14)
    
    # Volumen promedio (últimas 20 velas)
    avg_volume = np.mean(volumes[-20:])
    current_volume = volumes[-1]
    
    if None in (ema_20, ema_50, ema_200, prev_ema_20, prev_ema_50):
        return 'none'
    
    # --- Lógica combinada ---
    # Condición 1: Volumen > 1.2x el promedio (para filtrar ruido)
    volume_ok = current_volume > (avg_volume * 1.2)
    
    # Condición 2: EMA 200 (Tendencia macro)
    current_price = closes[-1]
    
    # SEÑAL DE COMPRA:
    # Cruce dorado + RSI < 70 + Volumen OK + Precio por encima de EMA 200
    if (prev_ema_20 <= prev_ema_50 and ema_20 > ema_50 and 
        rsi < 70 and volume_ok and current_price > ema_200):
        return 'buy'
    
    # SEÑAL DE VENTA (Corto):
    # Cruce de muerte + RSI > 30 + Volumen OK + Precio por debajo de EMA 200
    elif (prev_ema_20 >= prev_ema_50 and ema_20 < ema_50 and 
          rsi > 30 and volume_ok and current_price < ema_200):
        return 'sell'
    
    else:
        return 'none'
