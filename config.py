import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COINEX_API_KEY", "dummy")
SECRET_KEY = os.getenv("COINEX_SECRET_KEY", "dummy")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1hour")
LEVERAGE = int(os.getenv("LEVERAGE", 3))
CAPITAL = float(os.getenv("CAPITAL_USDT", 100))
POSITION_SIZE_PERCENT = float(os.getenv("POSITION_SIZE_PERCENT", 0.1))
SL_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 0.02))
TP_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 0.04))

# NUEVAS VARIABLES PARA REALISMO
FEE_PERCENT = float(os.getenv("FEE_PERCENT", 0.0005))  # 0.05% de comisión por operación
MIN_POSITION_VALUE_USDT = float(os.getenv("MIN_POSITION_VALUE_USDT", 5))  # Mínimo para abrir posición en CoinEx (Futuros)

BASE_URL = "https://api.coinex.com"
