# network_client.py
import random
import time
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

# Intentamos importar curl_cffi (mejor evasión TLS)
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import requests  # fallback

# Lista extensa de User-Agents reales (móviles + escritorio)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# Perfiles de impersonación para curl_cffi (navegadores)
IMPERSONATE_PROFILES = ["chrome110", "chrome116", "chrome120", "safari15_5", "edge99", "firefox102"]

class SecureRequester:
    """
    Cliente HTTP con evasión de WAF/Anti-bot:
    - Rotación de User-Agent y headers realistas.
    - Spoofing de TLS fingerprint (si curl_cffi está instalado).
    - Backoff exponencial con jitter en errores (429, 403, timeouts).
    - Soporte para proxy SOCKS5 (ej. Tor).
    - Timeouts configurables.
    """
    def __init__(self,
                 use_tor: bool = False,
                 tor_proxy: str = "socks5://127.0.0.1:9050",
                 max_retries: int = 3,
                 backoff_factor: float = 1.5,
                 jitter: float = 0.3,
                 timeout: int = 30,
                 verify_ssl: bool = True):
        self.use_tor = use_tor
        self.proxy = tor_proxy if use_tor else None
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Si usamos curl_cffi, podemos mantener una sesión persistente (opcional)
        self.session = None
        if HAS_CURL_CFFI:
            # No creamos sesión aún, la crearemos por petición para evitar problemas
            pass

    def _get_headers(self) -> Dict[str, str]:
        """Genera headers realistas con User-Agent aleatorio."""
        ua = random.choice(USER_AGENTS)
        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

    def _get_impersonate(self) -> str:
        """Elige un perfil de navegador para curl_cffi."""
        return random.choice(IMPERSONATE_PROFILES)

    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Optional[Any]:
        """
        Realiza una petición GET con reintentos, backoff y evasión.
        Retorna el objeto Response (de requests o curl_cffi) o None si falla definitivamente.
        """
        attempt = 0
        last_exception = None

        while attempt < self.max_retries:
            try:
                headers = self._get_headers()
                # Combinar headers por si el usuario pasa algunos extra
                if "headers" in kwargs:
                    headers.update(kwargs.pop("headers"))

                # Elegir método de petición
                if HAS_CURL_CFFI:
                    # Usamos curl_cffi con impersonate
                    response = curl_requests.get(
                        url,
                        params=params,
                        headers=headers,
                        impersonate=self._get_impersonate(),
                        proxy=self.proxy,
                        timeout=self.timeout,
                        verify=self.verify_ssl,
                        **kwargs
                    )
                else:
                    # Fallback con requests estándar (sin spoofing TLS, pero con proxies)
                    proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                    response = requests.get(
                        url,
                        params=params,
                        headers=headers,
                        proxies=proxies,
                        timeout=self.timeout,
                        verify=self.verify_ssl,
                        **kwargs
                    )

                # Si el código es 429 o 403, lanzamos excepción para reintentar
                if response.status_code in (429, 403):
                    raise Exception(f"Rate limit or forbidden: {response.status_code}")

                # Si todo bien, retornamos la respuesta
                return response

            except Exception as e:
                last_exception = e
                attempt += 1
                if attempt >= self.max_retries:
                    # Si ya no hay reintentos, salimos del bucle
                    break

                # Backoff exponencial con jitter
                sleep_time = (self.backoff_factor ** attempt) + random.uniform(0, self.jitter)
                # Si la excepción es de timeout, podemos esperar un poco más
                if "timeout" in str(e).lower():
                    sleep_time *= 1.5
                time.sleep(sleep_time)

        # Si llegamos aquí, todos los reintentos fallaron
        # Podemos registrar el error o simplemente retornar None
        print(f"❌ Falló la petición a {url} después de {self.max_retries} intentos: {last_exception}")
        return None

    def get_text(self, url: str, params: Optional[Dict] = None, **kwargs) -> Optional[str]:
        """
        Helper que retorna el texto de la respuesta si la petición fue exitosa.
        """
        resp = self.get(url, params=params, **kwargs)
        if resp and resp.status_code == 200:
            return resp.text
        return None
