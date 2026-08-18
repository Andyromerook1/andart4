# phishing_detector.py
import re
from difflib import SequenceMatcher

DOMINIOS_LEGITIMOS = [
    "paypal.com", "google.com", "amazon.com", "apple.com", "microsoft.com",
    "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
    "dropbox.com", "onedrive.com", "gofundme.com", "kickstarter.com",
    "indiegogo.com", "alibaba.com", "aliexpress.com", "mercadolibre.com",
    "ebay.com", "etsy.com", "shopify.com", "wix.com", "weebly.com",
    "squarespace.com", "wordpress.com", "blogger.com", "tumblr.com",
    "medium.com", "reddit.com", "quora.com", "stackoverflow.com",
    "github.com", "gitlab.com", "bitbucket.org", "wikipedia.org",
    "wikidata.org", "bbc.com", "reuters.com", "nytimes.com", "wsj.com",
    "ft.com", "economist.com", "bloomberg.com", "cnbc.com",
    "marketwatch.com", "investing.com", "forexfactory.com",
    "coingecko.com", "coinmarketcap.com", "cryptocompare.com",
    "tradingview.com", "bitcointalk.org", "virustotal.com",
    "haveibeenpwned.com"
]


class PhishingDetector:
    def __init__(self, dominios_legitimos=None):
        self.dominios_legitimos = dominios_legitimos or DOMINIOS_LEGITIMOS
        self.patrones = self._compilar_patrones()

    def _compilar_patrones(self):
        patrones = []
        for dominio in self.dominios_legitimos:
            base = dominio.split('.')[0]
            variaciones = [base]
            for letra in 'aeiou':
                if letra in base:
                    variaciones.append(base.replace(letra, letra * 2))
            if 'o' in base:
                variaciones.append(base.replace('o', '0'))
            if 'e' in base:
                variaciones.append(base.replace('e', '3'))
            if 'a' in base:
                variaciones.append(base.replace('a', '4'))
            if 'i' in base:
                variaciones.append(base.replace('i', '1'))
            if 's' in base:
                variaciones.append(base.replace('s', '5'))
            # Ancla al INICIO del dominio (^) para no matchear subdominios legítimos
            patron = r'^(' + '|'.join(re.escape(v) for v in variaciones) + \
                     r')[a-zA-Z0-9-]*\.(com|net|org|xyz|top|icu|tk|ml|ga|cf|club|online|site|tech|store|info|biz)$'
            patrones.append((patron and re.compile(patron, re.IGNORECASE), dominio))
        return patrones

    def _es_dominio_o_subdominio_legitimo(self, dominio_limpio):
        """
        True si dominio_limpio ES uno de los legítimos, o es un subdominio
        REAL de uno de ellos (ej: plus.google.com termina en .google.com).
        Esto es lo que faltaba: sin este chequeo, cualquier subdominio
        auténtico se compara como si fuera un dominio nuevo sospechoso.
        """
        for legitimo in self.dominios_legitimos:
            if dominio_limpio == legitimo or dominio_limpio.endswith("." + legitimo):
                return True
        return False

    def es_clon(self, dominio):
        dominio_limpio = dominio.lower().strip()
        if dominio_limpio.startswith('http://') or dominio_limpio.startswith('https://'):
            dominio_limpio = dominio_limpio.split('/')[2] if '/' in dominio_limpio else dominio_limpio.split('/')[0]
        if dominio_limpio.startswith('www.'):
            dominio_limpio = dominio_limpio[4:]

        # 0. Si es el dominio legítimo o un subdominio REAL de uno legítimo,
        #    nunca es un clon — corta acá antes de cualquier heurística.
        if self._es_dominio_o_subdominio_legitimo(dominio_limpio):
            return False, None, 1.0

        # 1. TLD sospechoso + similitud alta con un dominio legítimo
        partes = dominio_limpio.split('.')
        if len(partes) >= 2:
            tld = partes[-1]
            tlds_sospechosos = ['top', 'xyz', 'icu', 'tk', 'ml', 'ga', 'cf',
                                 'club', 'online', 'site', 'tech', 'store', 'info', 'biz']
            if tld in tlds_sospechosos:
                base = partes[-2]
                mejor_match = None
                mejor_similitud = 0
                for legitimo in self.dominios_legitimos:
                    legit_base = legitimo.split('.')[0]
                    similitud = SequenceMatcher(None, base, legit_base).ratio()
                    if similitud > mejor_similitud:
                        mejor_similitud = similitud
                        mejor_match = legitimo
                if mejor_similitud > 0.85:
                    return True, mejor_match, mejor_similitud

        # 2. Variantes engañosas (rn→m, 0 en vez de o, etc.) SOLO en el
        #    dominio raíz completo, anclado — no como substring de cualquier lado.
        for patron, dominio_origen in self.patrones:
            if patron and patron.match(dominio_limpio):
                return True, dominio_origen, 0.9

        return False, None, 0.0
