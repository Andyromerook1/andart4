# network_client.py
import random
import time
from typing import Optional, Dict, Any
import requests

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
]

class SecureRequester:
    """
    Cliente HTTP simple para rastreo de fuentes públicas:
    - Rotación de User-Agent (etiqueta habitual de crawler, no evasión).
    - Reintentos con backoff SOLO ante errores transitorios de red (timeouts, 5xx).
    - Si el sitio responde 403/429, se respeta y se descarta la URL (no se reintenta disfrazado).
    """
    def __init__(self, max_retries: int = 2, backoff_factor: float = 1.5,
                 timeout: int = 15, verify_ssl: bool = True):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        }

    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Optional[Any]:
        attempt = 0
        while attempt < self.max_retries:
            try:
                headers = self._get_headers()
                if "headers" in kwargs:
                    headers.update(kwargs.pop("headers"))
                response = requests.get(
                    url, params=params, headers=headers,
                    timeout=self.timeout, verify=self.verify_ssl, **kwargs
                )
                if response.status_code in (403, 429):
                    print(f"🚫 {url} bloqueó el acceso ({response.status_code}) — se respeta y se omite.")
                    return None
                return response
            except requests.RequestException as e:
                attempt += 1
                if attempt >= self.max_retries:
                    print(f"❌ Falló la petición a {url}: {e}")
                    return None
                time.sleep(self.backoff_factor ** attempt)
        return None

    def get_text(self, url: str, params: Optional[Dict] = None, **kwargs) -> Optional[str]:
        resp = self.get(url, params=params, **kwargs)
        if resp and resp.status_code == 200:
            return resp.text
        return None
