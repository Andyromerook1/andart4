# config.py
import os

# Red
MAX_RETRIES = 2
BACKOFF_FACTOR = 1.5
TIMEOUT = 15
VERIFY_SSL = True

# Límites
DEFAULT_PAGE_LIMIT = 1_000_000

# Rutas públicas (pensadas para ser leídas por crawlers)
SENSITIVE_PATHS = ["/robots.txt", "/sitemap.xml"]

# =====================================================
# CONFIGURACIÓN DE BLOCKCHAIN APIS
# =====================================================
TRONSCAN_API_KEY = ""   # ⚠️ VER NOTA ABAJO — rotar esta clave
ETHERSCAN_API_KEY = ""
BSCSCAN_API_KEY = ""

MAX_CALLS_PER_SECOND = 5
MAX_CALLS_PER_DAY = 100000

AUTO_BLOCKCHAIN_ANALYSIS = True

# =====================================================
# DETECCIÓN DE PHISHING Y ANÁLISIS JS
# =====================================================
ENABLE_PHISHING_DETECTION = True
ENABLE_JS_ANALYSIS = True

# =====================================================
# RUTAS DE SALIDA
# =====================================================
OUTPUT_BASE = os.path.expanduser("~/storage/downloads/andart_output")
HALLAZGOS_FILE = os.path.join(OUTPUT_BASE, "hallazgos.txt")
BLOCKCHAIN_INSIGHTS_FILE = os.path.join(OUTPUT_BASE, "blockchain_insights.txt")
CHECKPOINT_FILE = os.path.join(OUTPUT_BASE, "checkpoint.json")

os.makedirs(OUTPUT_BASE, exist_ok=True)
