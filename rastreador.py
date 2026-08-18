# rastreador.py
import signal
import sys
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from filtro import MotorFiltro
from network_client import SecureRequester
from wayback_client import WaybackClient
import config


class Rastreador:
    def __init__(self, semilla, limite=None, max_retries=None):
        self.cola = list(set(semilla))
        self.visitados = set()
        self.bloqueados = []
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
        self.wayback = WaybackClient()

        self.rutas_publicas = config.SENSITIVE_PATHS  # robots.txt, sitemap.xml, etc.

        signal.signal(signal.SIGINT, self._manejador_ctrl_c)

    def _manejador_ctrl_c(self, sig, frame):
        print("\n\n⚠️ Deteniendo rastreo (Ctrl+C)... Guardando progreso...")
        self.detener = True
        self._guardar_bloqueados()
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

    def _intentar_wayback(self, url):
        """
        Si el sitio bloquea el acceso directo, se intenta UNA vez recuperar
        la última copia archivada públicamente en Wayback Machine, en vez
        de reintentar disfrazando la petición. Si tampoco hay copia, se
        deja la URL para revisión manual.
        """
        snapshot = self.wayback.snapshot_mas_reciente(url)
        if not snapshot:
            return None
        print(f"    📦 Recuperando vía Wayback Machine: {snapshot[:70]}")
        return self.requester.get(snapshot)

    def _guardar_bloqueados(self):
        if not self.bloqueados:
            return
        try:
            with open(config.BLOQUEADOS_FILE, "a", encoding="utf-8") as f:
                for url in self.bloqueados:
                    f.write(url + "\n")
            print(f"   🔒 {len(self.bloqueados)} URLs sin acceso guardadas en: {config.BLOQUEADOS_FILE}")
            print(f"      → Revisalas manualmente en el navegador cuando quieras")
        except Exception as e:
            print(f"   ⚠️ Error guardando bloqueados: {e}")

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
                    # No se pudo acceder directo — se prueba una copia
                    # archivada pública antes de darlo por perdido.
                    resp = self._intentar_wayback(url)
                    if resp is None or resp.status_code != 200:
                        self.bloqueados.append(url)
                        print(f"    🔒 Sin acceso ni copia archivada — guardado para revisión manual")
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

        self._guardar_bloqueados()

        if self.detener:
            print("\n🛑 Rastreo detenido por el usuario.")
        else:
            print(f"\n✅ RASTREO FINALIZADO")
        print(f"   Páginas visitadas: {len(self.visitados)}")
        print(f"   Hallazgos guardados en: {config.HALLAZGOS_FILE}")
        print(f"   Insights blockchain en: {config.BLOCKCHAIN_INSIGHTS_FILE}")
