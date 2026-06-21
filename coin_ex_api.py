import requests
from config import BASE_URL

# Esta función obtiene datos públicos SIN NECESITAR API KEY
def public_request(endpoint, params=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error en API pública: {e}")
        return None

def get_ticker(symbol):
    return public_request("/v1/market/ticker", {"market": symbol})

def get_kline(symbol, timeframe, limit=100):
    return public_request("/v1/market/kline", {"market": symbol, "type": timeframe, "limit": limit})

# Mantenemos estas funciones para que no dé error, pero en paper trading no se usan
def place_order(symbol, side, order_type, price=None, amount=None):
    print("⚠️ Modo Paper Trading: no se envía orden real a la API.")
    return {"status": "simulated"}

def get_position(symbol):
    return {"status": "simulated"}

def cancel_order(symbol, order_id):
    return {"status": "simulated"}
