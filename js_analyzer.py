# js_analyzer.py
import re
from urllib.parse import urljoin, urlparse

class JSAnalyzer:
    def __init__(self):
        self.patrones = {
            'endpoints': [
                re.compile(r'["\'](/api/[^"\']+)["\']', re.IGNORECASE),
                re.compile(r'["\'](/v[0-9]+/[^"\']+)["\']', re.IGNORECASE),
                re.compile(r'["\'](/(?:auth|login|signin|register|verify|wallet|transaction|withdraw|deposit|payment|confirm|kyc|support)/[^"\']*)["\']', re.IGNORECASE),
                re.compile(r'(?:url|endpoint|api|baseUrl|base_url|host)[\s]*:[\s]*["\']([^"\']+)["\']', re.IGNORECASE),
                re.compile(r'(?:fetch|axios|request|get|post|put|delete)[\s]*\([\s]*["\']([^"\']+)["\']', re.IGNORECASE),
                re.compile(r'["\'](https?://[^"\']+\.(?:php|asp|aspx|jsp|do|action|api)[^"\']*)["\']', re.IGNORECASE),
            ],
            'crypto_addresses': [
                re.compile(r'["\'](T[a-zA-Z0-9]{33})["\']'),
                re.compile(r'["\'](0x[a-fA-F0-9]{40})["\']'),
                re.compile(r'["\'](bc1[a-z0-9]{39,59})["\']'),
                re.compile(r'["\']([13][a-km-zA-HJ-NP-Z1-9]{25,34})["\']'),
            ]
        }

    def analizar_js(self, contenido, url_base):
        resultados = {
            'endpoints': [],
            'urls_absolutas': [],
            'crypto_addresses': [],
            'dominios': []
        }
        for patron in self.patrones['endpoints']:
            for match in patron.finditer(contenido):
                valor = match.group(1)
                if valor:
                    if valor.startswith('/'):
                        resultados['endpoints'].append(urljoin(url_base, valor))
                    else:
                        resultados['endpoints'].append(valor)
        for patron in self.patrones['crypto_addresses']:
            for match in patron.finditer(contenido):
                valor = match.group(1)
                if valor and len(valor) > 10:
                    resultados['crypto_addresses'].append(valor)
        for endpoint in resultados['endpoints']:
            if endpoint.startswith('http'):
                parsed = urlparse(endpoint)
                if parsed.netloc and parsed.netloc not in resultados['dominios']:
                    resultados['dominios'].append(parsed.netloc)
        return resultados
