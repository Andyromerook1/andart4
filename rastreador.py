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
    def __init__(self, semilla, limite=None, use_tor=None, max_retries=None):
        self.cola = list(set(semilla))
        self.visitados = set()
        self.limite = limite if limite is not None else config.DEFAULT_PAGE_LIMIT
        self.filtro = MotorFiltro()
        self.detener = False  # Bandera para detener el bucle con Ctrl+C

        use_tor = use_tor if use_tor is not None else config.USE_TOR
        max_retries = max_retries if max_retries is not None else config.MAX_RETRIES

        self.requester = SecureRequester(
            use_tor=use_tor,
            tor_proxy=config.TOR_PROXY,
            max_retries=max_retries,
            backoff_factor=config.BACKOFF_FACTOR,
            jitter=config.JITTER,
            timeout=config.TIMEOUT,
            verify_ssl=config.VERIFY_SSL
        )

        self.rutas_sensibles = config.SENSITIVE_PATHS

        # Capturar Ctrl+C para detener el bucle de forma limpia
        signal.signal(signal.SIGINT, self._manejador_ctrl_c)

    def _manejador_ctrl_c(self, sig, frame):
        print("\n\n⚠️ Deteniendo rastreo (Ctrl+C)... Guardando progreso...")
        self.detener = True
        # Guardar checkpoint si existe la función (opcional)
        if hasattr(self, 'guardar_checkpoint'):
            self.guardar_checkpoint()

    def es_mismo_dominio(self, base, url):
        return True

    def extraer_enlaces(self, url, html_o_texto):
        enlaces = []
        try:
            soup = BeautifulSoup(html_o_texto, "html.parser")
            for a in soup.find_all("a", href=True):
                absoluto = urljoin(url, a["href"])
                if absoluto.startswith("http") and self.es_mismo_dominio(url, absoluto):
                    enlaces.append(absoluto.split("#")[0].rstrip("/"))
            for script in soup.find_all("script", src=True):
                absoluto_js = urljoin(url, script["src"])
                if absoluto_js.startswith("http") and self.es_mismo_dominio(url, absoluto_js):
                    enlaces.append(absoluto_js)
            for link in soup.find_all("link", href=True):
                absoluto_link = urljoin(url, link["href"])
                if absoluto_link.startswith("http") and self.es_mismo_dominio(url, absoluto_link):
                    enlaces.append(absoluto_link)
        except Exception:
            pass
        return enlaces

    def agregar_rutas_sensibles(self, url_base):
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
        print(f"   🔄 Reintentos máximos: {self.requester.max_retries}")
        print("   💡 Presiona Ctrl+C para detener en cualquier momento\n")

        for semilla in list(self.cola):
            self.agregar_rutas_sensibles(semilla)

        while self.cola and len(self.visitados) < self.limite and not self.detener:
            url = self.cola.pop(0)
            if url in self.visitados:
                continue

            print(f"🔍 [{len(self.visitados)+1}/{self.limite}] Leyendo: {url[:80]}")
            try:
                resp = self.requester.get(url)
                if resp is None or resp.status_code != 200:
                    # Si la URL falló, no la añadimos a visitados para reintentar después
                    if resp is None:
                        print(f"    ⚠️ Sin respuesta para {url[:60]}")
                    continue

                self.visitados.add(url)

                hallazgos = self.filtro.escanear_texto(resp.text, origen=url)
                for h in hallazgos:
                    self.filtro.guardar_hallazgo(h)

                nuevos = self.extraer_enlaces(url, resp.text)
                for enlace in nuevos:
                    if enlace not in self.visitados and enlace not in self.cola:
                        self.cola.append(enlace)

                # Pequeña pausa para no saturar (0.1-0.3 segundos)
                time.sleep(0.1)

            except Exception as e:
                print(f"    ⚠️ No se pudo leer: {type(e).__name__}")
                # Si es un error de conexión, esperar un poco antes de continuar
                if "Connection" in str(e) or "timeout" in str(e).lower():
                    time.sleep(1)
                continue

        if self.detener:
            print("\n🛑 Rastreo detenido por el usuario.")
        else:
            print(f"\n✅ RASTREO FINALIZADO")
        print(f"   Páginas y archivos visitados: {len(self.visitados)}")
        print(f"   URLs pendientes en cola: {len(self.cola)}")
        print(f"   Hallazgos guardados en: hallazgos.txt")
