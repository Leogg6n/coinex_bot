import os
from dotenv import load_dotenv

load_dotenv()

# Ya no necesitamos claves para la simulación, pero dejamos las variables
API_KEY = os.getenv("COINEX_API_KEY", "dummy")
SECRET_KEY = os.getenv("COINEX_SECRET_KEY", "dummy")

SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
LEVERAGE = int(os.getenv("LEVERAGE", 3))
CAPITAL = float(os.getenv("CAPITAL_USDT", 100))
POSITION_SIZE_PERCENT = float(os.getenv("POSITION_SIZE_PERCENT", 0.1))
SL_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 0.02))
TP_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 0.04))

# CAMBIO CRUCIAL: Usamos la API REAL para obtener datos públicos (sin llaves)
BASE_URL = "https://api.coinex.com"
