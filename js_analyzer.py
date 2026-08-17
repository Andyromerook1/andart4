# js_analyzer.py
import re
from urllib.parse import urljoin, urlparse

class JSAnalyzer:
    def __init__(self):
        # Patrones para extraer endpoints y URLs
        self.patrones = {
            'endpoints': [
                re.compile(r'["\'](/api/[^"\']+)["\']', re.IGNORECASE),  # /api/...
                re.compile(r'["\'](/v[0-9]+/[^"\']+)["\']', re.IGNORECASE),  # /v1/...
                re.compile(r'["\'](/(?:auth|login|signin|register|verify|wallet|transaction|withdraw|deposit|payment|confirm|kyc|support)/[^"\']*)["\']', re.IGNORECASE),
                re.compile(r'(?:url|endpoint|api|baseUrl|base_url|host)[\s]*:[\s]*["\']([^"\']+)["\']', re.IGNORECASE),
                re.compile(r'(?:fetch|axios|request|get|post|put|delete)[\s]*\([\s]*["\']([^"\']+)["\']', re.IGNORECASE),
                re.compile(r'["\'](https?://[^"\']+\.(?:php|asp|aspx|jsp|do|action|api)[^"\']*)["\']', re.IGNORECASE),
            ],
            'crypto_addresses': [
                re.compile(r'["\'](T[a-zA-Z0-9]{33})["\']'),  # TRX
                re.compile(r'["\'](0x[a-fA-F0-9]{40})["\']'), # ETH
                re.compile(r'["\'](bc1[a-z0-9]{39,59})["\']'), # BTC SegWit
                re.compile(r'["\']([13][a-km-zA-HJ-NP-Z1-9]{25,34})["\']'), # BTC legacy
            ],
            'keys_tokens': [
                re.compile(r'["\'](sk-(?:[a-zA-Z0-9]{48}|proj-[a-zA-Z0-9_-]{48,100}))["\']'),  # OpenAI
                re.compile(r'["\'](ghp_[a-zA-Z0-9]{36})["\']'),  # GitHub
                re.compile(r'["\'](AIza[A-Za-z0-9_-]{35})["\']'), # Google
                re.compile(r'["\'](ya29\\.[A-Za-z0-9_-]{40,100})["\']'), # Google Cloud
                re.compile(r'["\'](SG\\.[A-Za-z0-9_-]{22}\\.[A-Za-z0-9_-]{43})["\']'), # SendGrid
                re.compile(r'["\'](xox[baprs]-[A-Za-z0-9-]{10,48})["\']'), # Slack
            ]
        }

    def analizar_js(self, contenido, url_base):
        """Analiza contenido JavaScript y extrae endpoints, URLs, direcciones y tokens."""
        resultados = {
            'endpoints': [],
            'urls_absolutas': [],
            'crypto_addresses': [],
            'keys_tokens': [],
            'dominios': []
        }

        # Extraer endpoints y URLs relativas
        for patron in self.patrones['endpoints']:
            for match in patron.finditer(contenido):
                valor = match.group(1)
                if valor:
                    # Convertir a URL absoluta si es necesario
                    if valor.startswith('/'):
                        url_absoluta = urljoin(url_base, valor)
                        resultados['endpoints'].append(url_absoluta)
                    elif valor.startswith('http'):
                        resultados['endpoints'].append(valor)
                    else:
                        # Podría ser una ruta relativa, pero la guardamos tal cual
                        resultados['endpoints'].append(valor)

        # Extraer direcciones de criptomonedas
        for patron in self.patrones['crypto_addresses']:
            for match in patron.finditer(contenido):
                valor = match.group(1)
                if valor and len(valor) > 10:
                    resultados['crypto_addresses'].append(valor)

        # Extraer claves y tokens
        for patron in self.patrones['keys_tokens']:
            for match in patron.finditer(contenido):
                valor = match.group(1)
                if valor and len(valor) > 10:
                    resultados['keys_tokens'].append(valor)

        # Extraer dominios de URLs absolutas
        if resultados['endpoints']:
            for endpoint in resultados['endpoints']:
                if endpoint.startswith('http'):
                    parsed = urlparse(endpoint)
                    if parsed.netloc and parsed.netloc not in resultados['dominios']:
                        resultados['dominios'].append(parsed.netloc)

        return resultados
