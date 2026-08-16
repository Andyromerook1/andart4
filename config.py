# config.py
# Configuración centralizada para el rastreador Andart

# Red y evasión
USE_TOR = False                 # Activar/desactivar Tor globalmente
TOR_PROXY = "socks5://127.0.0.1:9050"
MAX_RETRIES = 3                 # Reintentos ante errores (429, 403, timeouts)
BACKOFF_FACTOR = 1.5            # Factor de espera exponencial
JITTER = 0.3                    # Variación aleatoria en la espera (segundos)
TIMEOUT = 30                    # Timeout de petición en segundos
VERIFY_SSL = True               # Verificar certificados SSL

# Límites
DEFAULT_PAGE_LIMIT = 1_000_000  # Límite de páginas (prácticamente ilimitado)
DEFAULT_IP_LIMIT = 1000         # IPs a escanear por defecto

# Puertos a escanear (usado por escaner_red.py)
COMMON_PORTS = [
    21, 22, 23, 25, 53, 67, 68, 69, 80, 81, 110, 111, 135, 139,
    143, 161, 162, 179, 389, 443, 445, 465, 514, 515, 587, 636,
    993, 995, 1080, 1433, 1434, 1521, 1723, 2049, 2121, 3306,
    3389, 5060, 5432, 5900, 5901, 6379, 8000, 8080, 8443,
    8888, 9000, 9200, 9300, 11211, 27017
]

# Rutas sensibles a probar (se mantiene igual)
SENSITIVE_PATHS = ["/.env", "/config.json", "/robots.txt", "/sitemap.xml", "/manifest.json"]
