# =====================================================
# CONFIGURACIÓN DE BLOCKCHAIN APIS (opcional)
# =====================================================
TRONSCAN_API_KEY = os.environ.get("TRONSCAN_API_KEY", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
BSCSCAN_API_KEY = os.environ.get("BSCSCAN_API_KEY", "")

MAX_CALLS_PER_SECOND = 5
MAX_CALLS_PER_DAY = 100000

# Por defecto apagado: el bot detecta y guarda la dirección igual,
# pero no la consulta automáticamente contra Tronscan/Etherscan.
# La revisás vos a mano cuando el hallazgo te interese.
AUTO_BLOCKCHAIN_ANALYSIS = False
