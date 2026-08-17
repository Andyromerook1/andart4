# rastreador.py
import signal
import sys
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from filtro import MotorFiltro
from network_client import SecureRequester
import config

class Rastreador:
    def __init__(self, semilla, limite=None, max_retries=None):
        self.cola = list(set(semilla))
        self.visitados = set()
        self.limite = limite if limite is not None else config.DEFAULT_PAGE_LIMIT
        self.filtro = MotorFiltro()
        self.detener = False

        max_retries = max_retries if max_retries is not None else config.MAX_RETRIES

        self.requester = SecureRequester(
            max_retries=max_retries,
            backoff_factor=config.BACKOFF_FACTOR,
            timeout=config.TIMEOUT,
            verify_ssl=config.VERIFY_SSL
        )

        self.rutas_publicas = config.SENSITIVE_PATHS  # robots.txt, sitemap.xml, etc.

        signal.signal(signal.SIGINT, self._manejador_ctrl_c)

    def _manejador_ctrl_c(self, sig, frame):
        print("\n\n⚠️ Deteniendo rastreo (Ctrl+C)... Guardando progreso...")
        self.detener = True
        sys.exit(0)

    def es_mismo_dominio(self, base, url):
        return True

    def extraer_enlaces(self, url, html_o_texto):
        enlaces = []
        try:
            soup = BeautifulSoup(html_o_texto, "html.parser")
            for a in soup.find_all("a", href=True):
                absoluto = urljoin(url, a["href"])
                if absoluto.startswith("http"):
                    enlaces.append(absoluto.split("#")[0].rstrip("/"))
            for script in soup.find_all("script", src=True):
                absoluto_js = urljoin(url, script["src"])
                if absoluto_js.startswith("http"):
                    enlaces.append(absoluto_js)
        except Exception:
            pass
        return enlaces

    def agregar_rutas_publicas(self, url_base):
        parsed = urlparse(url_base)
        dominio_base = f"{parsed.scheme}://{parsed.netloc}"
        for ruta in self.rutas_publicas:
            url_publica = dominio_base + ruta
            if url_publica not in self.visitados and url_publica not in self.cola:
                self.cola.append(url_publica)

    def iniciar(self):
        print(f"🔄 INICIANDO RASTREO — {len(self.cola)} semillas cargadas")
        print(f"   📄 Límite de páginas: {self.limite}")
        print(f"   🔄 Reintentos máximos: {self.requester.max_retries}")
        print(f"   📁 Archivos guardados en: {config.OUTPUT_BASE}")
        print("   💡 Presiona Ctrl+C para detener en cualquier momento\n")

        for semilla in list(self.cola):
            self.agregar_rutas_publicas(semilla)

        while self.cola and len(self.visitados) < self.limite and not self.detener:
            url = self.cola.pop(0)
            if url in self.visitados:
                continue

            print(f"🔍 [{len(self.visitados)+1}/{self.limite}] Leyendo: {url[:80]}")
            try:
                resp = self.requester.get(url)
                if resp is None or resp.status_code != 200:
                    continue

                self.visitados.add(url)

                hallazgos = self.filtro.escanear_texto(resp.text, origen=url)
                for h in hallazgos:
                    self.filtro.guardar_hallazgo(h)

                nuevos = self.extraer_enlaces(url, resp.text)
                for enlace in nuevos:
                    if enlace not in self.visitados and enlace not in self.cola:
                        self.cola.append(enlace)

                time.sleep(0.1)

            except Exception as e:
                print(f"    ⚠️ No se pudo leer: {type(e).__name__}")
                continue

        if self.detener:
            print("\n🛑 Rastreo detenido por el usuario.")
        else:
            print(f"\n✅ RASTREO FINALIZADO")
        print(f"   Páginas visitadas: {len(self.visitados)}")
        print(f"   Hallazgos guardados en: {config.HALLAZGOS_FILE}")
        print(f"   Insights blockchain en: {config.BLOCKCHAIN_INSIGHTS_FILE}")
