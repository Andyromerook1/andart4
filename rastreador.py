# rastreador.py
import requests  # ya no se usa directamente, pero lo dejamos por si acaso
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from filtro import MotorFiltro
from network_client import SecureRequester
import config  # Importamos la configuración central

class Rastreador:
    def __init__(self, semilla, limite=None, use_tor=None, max_retries=None):
        """
        Inicializa el rastreador.
        - semilla: lista de URLs iniciales.
        - limite: número máximo de páginas a visitar (por defecto config.DEFAULT_PAGE_LIMIT).
        - use_tor: si se usa Tor (si es None, toma config.USE_TOR).
        - max_retries: reintentos (si es None, toma config.MAX_RETRIES).
        """
        self.cola = list(set(semilla))
        self.visitados = set()
        self.limite = limite if limite is not None else config.DEFAULT_PAGE_LIMIT
        self.filtro = MotorFiltro()

        # Parámetros con fallback a config
        use_tor = use_tor if use_tor is not None else config.USE_TOR
        max_retries = max_retries if max_retries is not None else config.MAX_RETRIES

        # Cliente avanzado con evasión
        self.requester = SecureRequester(
            use_tor=use_tor,
            tor_proxy=config.TOR_PROXY,
            max_retries=max_retries,
            backoff_factor=config.BACKOFF_FACTOR,
            jitter=config.JITTER,
            timeout=config.TIMEOUT,
            verify_ssl=config.VERIFY_SSL
        )

        # Rutas sensibles (desde config)
        self.rutas_sensibles = config.SENSITIVE_PATHS

    def es_mismo_dominio(self, base, url):
        # Desactivado → acepta todos los dominios
        return True

    def extraer_enlaces(self, url, html_o_texto):
        enlaces = []
        try:
            soup = BeautifulSoup(html_o_texto, "html.parser")

            # 1. Enlaces estándar (<a href="...">)
            for a in soup.find_all("a", href=True):
                absoluto = urljoin(url, a["href"])
                if absoluto.startswith("http") and self.es_mismo_dominio(url, absoluto):
                    enlaces.append(absoluto.split("#")[0].rstrip("/"))

            # 2. Archivos JavaScript (<script src="...">)
            for script in soup.find_all("script", src=True):
                absoluto_js = urljoin(url, script["src"])
                if absoluto_js.startswith("http") and self.es_mismo_dominio(url, absoluto_js):
                    enlaces.append(absoluto_js)

            # 3. Recursos enlazados como CSS, manifiestos o JSON (<link href="...">)
            for link in soup.find_all("link", href=True):
                absoluto_link = urljoin(url, link["href"])
                if absoluto_link.startswith("http") and self.es_mismo_dominio(url, absoluto_link):
                    enlaces.append(absoluto_link)

        except Exception:
            # Si el contenido no es HTML (JS, JSON, etc.), continúa sin fallar
            pass

        return enlaces

    def agregar_rutas_sensibles(self, url_base):
        """Genera pruebas automáticas para archivos de configuración expuestos."""
        parsed = urlparse(url_base)
        dominio_base = f"{parsed.scheme}://{parsed.netloc}"
        
        for ruta in self.rutas_sensibles:
            url_sensible = dominio_base + ruta
            if url_sensible not in self.visitados and url_sensible not in self.cola:
                self.cola.append(url_sensible)

    def iniciar(self):
        print(f"🔄 INICIANDO RASTREO — {len(self.cola)} semillas cargadas")
        print(f"   🌐 Restricción de dominio: DESACTIVADO → cualquier sitio")
        print(f"   📄 Límite de páginas: {self.limite} (prácticamente ilimitado)")
        print(f"   🔒 Tor activado: {self.requester.use_tor}")
        print(f"   🔄 Reintentos máximos: {self.requester.max_retries}\n")

        # Agrega rutas sensibles automáticamente a cada semilla
        for semilla in list(self.cola):
            self.agregar_rutas_sensibles(semilla)

        while self.cola and len(self.visitados) < self.limite:
            url = self.cola.pop(0)
            if url in self.visitados:
                continue

            print(f"🔍 [{len(self.visitados)+1}/{self.limite}] Leyendo: {url[:80]}")
            try:
                # === USAMOS EL CLIENTE AVANZADO ===
                resp = self.requester.get(url)
                if resp is None or resp.status_code != 200:
                    continue

                self.visitados.add(url)

                # Escanea TODO el contenido: HTML, JS, JSON, CSS, lo que sea
                hallazgos = self.filtro.escanear_texto(resp.text, origen=url)
                for h in hallazgos:
                    self.filtro.guardar_hallazgo(h)

                # Descubre nuevos enlaces dentro de la página
                nuevos = self.extraer_enlaces(url, resp.text)
                for enlace in nuevos:
                    if enlace not in self.visitados and enlace not in self.cola:
                        self.cola.append(enlace)

            except Exception as e:
                print(f"    ⚠️ No se pudo leer: {type(e).__name__}")
                continue

        print(f"\n✅ RASTREO FINALIZADO")
        print(f"   Páginas y archivos visitados: {len(self.visitados)}")
        print(f"   Hallazgos guardados en: hallazgos.txt")
