# config.py
import os

MAX_RETRIES = 2
BACKOFF_FACTOR = 1.5
TIMEOUT = 15
VERIFY_SSL = True

DEFAULT_PAGE_LIMIT = 1_000_000

SENSITIVE_PATHS = ["/robots.txt", "/sitemap.xml"]

TRONSCAN_API_KEY = os.environ.get("TRONSCAN_API_KEY", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
BSCSCAN_API_KEY = os.environ.get("BSCSCAN_API_KEY", "")

MAX_CALLS_PER_SECOND = 5
MAX_CALLS_PER_DAY = 100000

AUTO_BLOCKCHAIN_ANALYSIS = False

ENABLE_PHISHING_DETECTION = True
ENABLE_JS_ANALYSIS = True

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

OUTPUT_BASE = os.path.expanduser("~/storage/downloads/andart_output")
HALLAZGOS_FILE = os.path.join(OUTPUT_BASE, "hallazgos.txt")
BLOCKCHAIN_INSIGHTS_FILE = os.path.join(OUTPUT_BASE, "blockchain_insights.txt")
CASOS_PUENTE_FILE = os.path.join(OUTPUT_BASE, "casos_puente.jsonl")
CORRELACION_FILE = os.path.join(OUTPUT_BASE, "correlaciones.jsonl")
CORRELACION_INDEX_FILE = os.path.join(OUTPUT_BASE, "indice_correlacion.json")
BLOQUEADOS_FILE = os.path.join(OUTPUT_BASE, "revision_manual.txt")
CHECKPOINT_FILE = os.path.join(OUTPUT_BASE, "checkpoint.json")

os.makedirs(OUTPUT_BASE, exist_ok=True)
