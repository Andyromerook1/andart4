# phishing_detector.py
import re
from difflib import SequenceMatcher

# Lista de dominios legítimos (puedes ampliarla)
DOMINIOS_LEGITIMOS = [
    "paypal.com",
    "google.com",
    "amazon.com",
    "apple.com",
    "microsoft.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "linkedin.com",
    "dropbox.com",
    "onedrive.com",
    "gofundme.com",
    "kickstarter.com",
    "indiegogo.com",
    "alibaba.com",
    "aliexpress.com",
    "mercadolibre.com",
    "ebay.com",
    "etsy.com",
    "shopify.com",
    "wix.com",
    "weebly.com",
    "squarespace.com",
    "wordpress.com",
    "blogger.com",
    "tumblr.com",
    "medium.com",
    "reddit.com",
    "quora.com",
    "stackoverflow.com",
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "wikipedia.org",
    "wikidata.org",
    "bbc.com",
    "reuters.com",
    "nytimes.com",
    "wsj.com",
    "ft.com",
    "economist.com",
    "bloomberg.com",
    "cnbc.com",
    "marketwatch.com",
    "investing.com",
    "forexfactory.com",
    "coingecko.com",
    "coinmarketcap.com",
    "cryptocompare.com",
    "tradingview.com",
    "bitcointalk.org",
    "virustotal.com",
    "haveibeenpwned.com"
]

class PhishingDetector:
    def __init__(self, dominios_legitimos=None):
        self.dominios_legitimos = dominios_legitimos or DOMINIOS_LEGITIMOS
        # Precompilar patrones de dominios con variaciones
        self.patrones = self._compilar_patrones()

    def _compilar_patrones(self):
        """Compila patrones regex para detectar dominios con caracteres engañosos."""
        patrones = []
        # Caracteres que se usan para suplantar (ej: rn → m, cl → d, etc.)
        sustituciones = {
            'rn': 'm',
            'cl': 'd',
            'vv': 'w',
            'rl': 'rl',  # etc.
        }
        for dominio in self.dominios_legitimos:
            # Dominio sin TLD (ej: paypal)
            base = dominio.split('.')[0]
            # Crear variaciones con caracteres similares
            variaciones = [base]
            # Añadir versiones con caracteres duplicados o cambiados
            for letra in 'aeiou':
                if letra in base:
                    variaciones.append(base.replace(letra, letra*2))
            # Añadir versiones con números
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
            # Añadir patrones de typos comunes (ej: paypa, payapl, etc.)
            # Usar expresiones para capturar dominios similares
            patron = r'(?<![a-zA-Z0-9-])(' + '|'.join(variaciones) + r')[a-zA-Z0-9-]*\.(com|net|org|xyz|top|icu|tk|ml|ga|cf|club|online|site|tech|store|info|biz)'
            patrones.append(re.compile(patron, re.IGNORECASE))
        return patrones

    def es_clon(self, dominio):
        """
        Determina si un dominio es probablemente un clon de phishing.
        Retorna: (es_clon, dominio_legitimo_sospechoso, similitud)
        """
        dominio_limpio = dominio.lower().strip()
        # Quitar protocolo y www
        if dominio_limpio.startswith('http://') or dominio_limpio.startswith('https://'):
            dominio_limpio = dominio_limpio.split('/')[2] if '/' in dominio_limpio else dominio_limpio.split('/')[0]
        if dominio_limpio.startswith('www.'):
            dominio_limpio = dominio_limpio[4:]
        
        # 1. Verificar si el dominio coincide exactamente con uno legítimo
        if dominio_limpio in self.dominios_legitimos:
            return False, None, 1.0

        # 2. Detectar si el dominio usa un TLD sospechoso (ej: .top, .xyz) y se parece a uno legítimo
        partes = dominio_limpio.split('.')
        if len(partes) >= 2:
            tld = partes[-1]
            # TLDs sospechosos (baratos y usados en phishing)
            tlds_sospechosos = ['top', 'xyz', 'icu', 'tk', 'ml', 'ga', 'cf', 'club', 'online', 'site', 'tech', 'store', 'info', 'biz']
            if tld in tlds_sospechosos:
                # Intentar encontrar el dominio base sin TLD
                base = partes[-2]
                # Buscar el mejor match con dominios legítimos
                mejor_match = None
                mejor_similitud = 0
                for legitimo in self.dominios_legitimos:
                    legit_base = legitimo.split('.')[0]
                    # Usar SequenceMatcher para similitud de cadenas
                    similitud = SequenceMatcher(None, base, legit_base).ratio()
                    if similitud > mejor_similitud:
                        mejor_similitud = similitud
                        mejor_match = legitimo
                if mejor_similitud > 0.85:
                    return True, mejor_match, mejor_similitud

        # 3. Usar patrones regex para detectar variantes obvias
        for patron in self.patrones:
            if patron.search(dominio_limpio):
                # Encontrar qué dominio legítimo se está imitando
                for legitimo in self.dominios_legitimos:
                    legit_base = legitimo.split('.')[0]
                    if legit_base in dominio_limpio:
                        return True, legitimo, 0.9
        return False, None, 0.0
