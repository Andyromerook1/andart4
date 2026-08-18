# config.py
import os

# =====================================================
# RED
# =====================================================
MAX_RETRIES = 2
BACKOFF_FACTOR = 1.5
TIMEOUT = 15
VERIFY_SSL = True

# =====================================================
# LÍMITES
# =====================================================
DEFAULT_PAGE_LIMIT = 1_000_000

# Rutas públicas (pensadas para ser leídas por crawlers)
SENSITIVE_PATHS = ["/robots.txt", "/sitemap.xml"]

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

# =====================================================
# DETECCIÓN DE PHISHING Y ANÁLISIS JS
# =====================================================
ENABLE_PHISHING_DETECTION = True
ENABLE_JS_ANALYSIS = True

# =====================================================
# CAZA EN GITHUB
# =====================================================
# Opcional. Sin token: 10 búsquedas/min contra la Search API.
# Con un Personal Access Token (solo lectura pública): 30/min.
#   export GITHUB_TOKEN="tu_token"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# =====================================================
# RUTAS DE SALIDA (accesibles desde el explorador de archivos)
# =====================================================
OUTPUT_BASE = os.path.expanduser("~/storage/downloads/andart_output")
HALLAZGOS_FILE = os.path.join(OUTPUT_BASE, "hallazgos.txt")
BLOCKCHAIN_INSIGHTS_FILE = os.path.join(OUTPUT_BASE, "blockchain_insights.txt")
CASOS_PUENTE_FILE = os.path.join(OUTPUT_BASE, "casos_puente.jsonl")
CORRELACION_FILE = os.path.join(OUTPUT_BASE, "correlaciones.jsonl")
CORRELACION_INDEX_FILE = os.path.join(OUTPUT_BASE, "indice_correlacion.json")
CHECKPOINT_FILE = os.path.join(OUTPUT_BASE, "checkpoint.json")

os.makedirs(OUTPUT_BASE, exist_ok=True)
