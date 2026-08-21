# rastreador.py
import signal
import sys
import time
import json
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from filtro import MotorFiltro
from network_client import SecureRequester
from wayback_client import WaybackClient
from pdf_metadata import PDFMetadataExtractor
from fraud_detector import FraudDetector
from candidate_store import CandidateStore
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
        self.pdf_extractor = PDFMetadataExtractor()

        # --- señales de contenido (fraud_detector) hacia candidate_store ---
        self.fraud_detector = FraudDetector()
        self.candidate_store = CandidateStore()

        self.rutas_publicas = config.SENSITIVE_PATHS

        # --- robots.txt: un parser cacheado por dominio ---
        self._robots_cache = {}

        # --- rate limit por dominio: último acceso por dominio ---
        self._ultimo_acceso_dominio = {}

        signal.signal(signal.SIGINT, self._manejador_ctrl_c)

    def _manejador_ctrl_c(self, sig, frame):
        print("\n\n⚠️ Deteniendo rastreo (Ctrl+C)... Guardando progreso...")
        self.detener = True
        self._guardar_checkpoint()
        self._guardar_bloqueados()
        self.candidate_store.save()
        sys.exit(0)

    def es_mismo_dominio(self, base, url):
        try:
            dominio_base = urlparse(base).netloc.lower()
            if dominio_base.startswith("www."):
                dominio_base = dominio_base[4:]
            dominio_url = urlparse(url).netloc.lower()
            if dominio_url.startswith("www."):
                dominio_url = dominio_url[4:]
            return dominio_base == dominio_url
        except Exception:
            return False

    # =============================================================
    # 🤖 ROBOTS.TXT
    # =============================================================
    def _permitido_por_robots(self, url):
        if not config.RESPETAR_ROBOTS_TXT:
            return True
        try:
            parsed = urlparse(url)
            dominio = f"{parsed.scheme}://{parsed.netloc}"
            if dominio not in self._robots_cache:
                rp = RobotFileParser()
                rp.set_url(f"{dominio}/robots.txt")
                try:
                    texto = self.requester.get_text(f"{dominio}/robots.txt")
                    if texto:
                        rp.parse(texto.splitlines())
                    else:
                        rp = None
                except Exception:
                    rp = None
                self._robots_cache[dominio] = rp

            rp = self._robots_cache[dominio]
            if rp is None:
                return True
            return rp.can_fetch("*", url)
        except Exception:
            return True

    # =============================================================
    # ⏱️ RATE LIMIT POR DOMINIO
    # =============================================================
    def _esperar_turno(self, url):
        dominio = urlparse(url).netloc
        ahora = time.time()
        ultimo = self._ultimo_acceso_dominio.get(dominio)

        if ultimo is not None:
            transcurrido = ahora - ultimo
            espera_necesaria = config.DELAY_MISMO_DOMINIO - transcurrido
            if espera_necesaria > 0:
                time.sleep(espera_necesaria)
        else:
            time.sleep(config.DELAY_DOMINIO_DISTINTO)

        self._ultimo_acceso_dominio[dominio] = time.time()

    # =============================================================
    # 💾 CHECKPOINT / RESUME
    # =============================================================
    def _guardar_checkpoint(self):
        try:
            data = {
                "cola": self.cola,
                "visitados": list(self.visitados),
                "bloqueados": self.bloqueados,
                "limite": self.limite,
            }
            with open(config.CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"   ⚠️ Error guardando checkpoint: {e}")

    @staticmethod
    def _hay_checkpoint():
        import os
        return os.path.exists(config.CHECKPOINT_FILE) and os.path.getsize(config.CHECKPOINT_FILE) > 0

    def _cargar_checkpoint(self):
        try:
            with open(config.CHECKPOINT_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.cola = data.get("cola", self.cola)
            self.visitados = set(data.get("visitados", []))
            self.bloqueados = data.get("bloqueados", [])
            print(f"   ♻️  Checkpoint cargado: {len(self.visitados)} páginas ya visitadas, "
                  f"{len(self.cola)} en cola")
            return True
        except Exception as e:
            print(f"   ⚠️ No se pudo cargar el checkpoint: {e}")
            return False

    def _borrar_checkpoint(self):
        import os
        try:
            if os.path.exists(config.CHECKPOINT_FILE):
                os.remove(config.CHECKPOINT_FILE)
        except Exception:
            pass

    def _registrar_dependencia(self, url_origen, url_dependencia, tipo):
        """
        Un recurso cross-domain (script, iframe, imagen, o link a otro
        sitio) NUNCA entra a la cola de rastreo — se registra como
        dependencia del candidate. Ver la infraestructura que comparten
        varios sitios de phishing (mismo CDN, mismo panel) es valioso,
        pero seguir rastreándola como si fuera un nuevo objetivo es lo
        que generaba la explosión de ruido original.
        """
        try:
            candidate = self.candidate_store.get_or_create(url_origen, discovered_by="rastreador_web")
            candidate.setdefault("dependencies", [])
            dominio_dep = urlparse(url_dependencia).netloc.lower()
            if dominio_dep.startswith("www."):
                dominio_dep = dominio_dep[4:]
            existente = next(
                (d for d in candidate["dependencies"] if d["domain"] == dominio_dep and d["type"] == tipo),
                None
            )
            if existente:
                existente["count"] += 1
            else:
                candidate["dependencies"].append({
                    "domain": dominio_dep, "type": tipo, "count": 1,
                })
        except Exception:
            pass

    def extraer_enlaces(self, url, html_o_texto):
        """
        Devuelve SOLO enlaces internos (mismo dominio) para seguir
        rastreando. Todo lo cross-domain (scripts, iframes, imágenes,
        links externos) se registra como dependencia del candidate,
        pero NUNCA se agrega a la cola de rastreo.
        """
        enlaces_internos = []
        try:
            soup = BeautifulSoup(html_o_texto, "html.parser")

            for a in soup.find_all("a", href=True):
                absoluto = urljoin(url, a["href"])
                if not absoluto.startswith("http"):
                    continue
                absoluto = absoluto.split("#")[0].rstrip("/")
                if self.es_mismo_dominio(url, absoluto):
                    enlaces_internos.append(absoluto)
                else:
                    self._registrar_dependencia(url, absoluto, "link_externo")

            for script in soup.find_all("script", src=True):
                absoluto_js = urljoin(url, script["src"])
                if absoluto_js.startswith("http") and not self.es_mismo_dominio(url, absoluto_js):
                    self._registrar_dependencia(url, absoluto_js, "script")

            for iframe in soup.find_all("iframe", src=True):
                absoluto_iframe = urljoin(url, iframe["src"])
                if absoluto_iframe.startswith("http") and not self.es_mismo_dominio(url, absoluto_iframe):
                    self._registrar_dependencia(url, absoluto_iframe, "iframe")

            for img in soup.find_all("img", src=True):
                absoluto_img = urljoin(url, img["src"])
                if absoluto_img.startswith("http") and not self.es_mismo_dominio(url, absoluto_img):
                    self._registrar_dependencia(url, absoluto_img, "imagen")

        except Exception:
            pass
        return enlaces_internos

    def _extraer_texto_visible(self, html):
        """
        Extrae solo el texto legible de la página (sin tags, sin JS,
        sin CSS) para pasarlo a fraud_detector.py — que espera lenguaje
        natural, no marcado HTML.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return ""

    def _procesar_contenido_fraude(self, url, texto_visible):
        """
        Analiza el texto visible con fraud_detector y, si encuentra
        señales, las registra en candidate_store — sin frenar el
        rastreo si algo falla acá, mismo criterio defensivo que el
        resto del archivo.
        """
        if not texto_visible or len(texto_visible) < 30:
            return
        try:
            resultado = self.fraud_detector.analizar(texto_visible)
            if not resultado.senales:
                return
            self.candidate_store.get_or_create(url, discovered_by="rastreador_web")
            self.candidate_store.add_content_signals(url, resultado, origen_url=url)
            candidate = self.candidate_store.recalculate(url)
            if candidate:
                print(f"   🕵️ Señal de fraude ({candidate['content_type_posible']}) "
                      f"content_risk={candidate['content_risk']:.1f} nivel={candidate['level']} → {url[:70]}")
        except Exception as e:
            print(f"   ⚠️ Error analizando contenido de fraude: {e}")

    def agregar_rutas_publicas(self, url_base):
        parsed = urlparse(url_base)
        dominio_base = f"{parsed.scheme}://{parsed.netloc}"
        for ruta in self.rutas_publicas:
            url_publica = dominio_base + ruta
            if url_publica not in self.visitados and url_publica not in self.cola:
                self.cola.append(url_publica)

    def _intentar_wayback(self, url):
        snapshot = self.wayback.snapshot_mas_reciente(url)
        if not snapshot:
            return None
        print(f"    📦 Recuperando vía Wayback Machine: {snapshot[:70]}")
        return self.requester.get(snapshot)

    def _procesar_pdf(self, url, resp):
        meta = self.pdf_extractor.extraer(resp.content, origen=url)
        if not meta:
            return
        for campo in ("autor", "creador", "productor"):
            valor = meta.get(campo)
            if valor:
                self.filtro._registrar_correlacion(f"PDF {campo}", valor, url)
        try:
            with open(config.HALLAZGOS_FILE, "a", encoding="utf-8") as f:
                f.write(f"📄 PDF METADATA | {meta} → {url}\n")
            print(f"   📄 Metadata de PDF extraída: {meta}")
        except Exception as e:
            print(f"   ⚠️ Error guardando metadata de PDF: {e}")

    def _guardar_bloqueados(self):
        if not self.bloqueados:
            return
        try:
            with open(config.BLOQUEADOS_FILE, "a", encoding="utf-8") as f:
                for url in self.bloqueados:
                    f.write(url + "\n")
            print(f"   🔒 {len(self.bloqueados)} URLs sin acceso guardadas en: {config.BLOQUEADOS_FILE}")
        except Exception as e:
            print(f"   ⚠️ Error guardando bloqueados: {e}")

    def iniciar(self):
        if self._hay_checkpoint():
            resp = input("♻️  Hay un rastreo anterior sin terminar. ¿Retomarlo? (s/n): ").strip().lower()
            if resp == "s":
                self._cargar_checkpoint()
            else:
                self._borrar_checkpoint()

        print(f"🔄 INICIANDO RASTREO — {len(self.cola)} semillas en cola")
        print(f"   📄 Límite de páginas: {self.limite}")
        print(f"   🤖 Respeta robots.txt: {config.RESPETAR_ROBOTS_TXT}")
        print(f"   📁 Archivos guardados en: {config.OUTPUT_BASE}")
        print("   💡 Presiona Ctrl+C para detener en cualquier momento\n")

        for semilla in list(self.cola):
            self.agregar_rutas_publicas(semilla)

        paginas_desde_checkpoint = 0

        while self.cola and len(self.visitados) < self.limite and not self.detener:
            url = self.cola.pop(0)
            if url in self.visitados:
                continue

            if not self._permitido_por_robots(url):
                print(f"    🤖 robots.txt prohíbe esta ruta, se omite: {url[:70]}")
                continue

            print(f"🔍 [{len(self.visitados)+1}/{self.limite}] Leyendo: {url[:80]}")
            try:
                self._esperar_turno(url)
                resp = self.requester.get(url)

                if resp is None or resp.status_code != 200:
                    resp = self._intentar_wayback(url)
                    if resp is None or resp.status_code != 200:
                        self.bloqueados.append(url)
                        print(f"    🔒 Sin acceso ni copia archivada — guardado para revisión manual")
                        continue

                self.visitados.add(url)

                content_type = resp.headers.get("Content-Type", "")
                if url.lower().endswith(".pdf") or "application/pdf" in content_type:
                    self._procesar_pdf(url, resp)
                else:
                    hallazgos = self.filtro.escanear_texto(resp.text, origen=url)
                    for h in hallazgos:
                        self.filtro.guardar_hallazgo(h)

                    texto_visible = self._extraer_texto_visible(resp.text)
                    self._procesar_contenido_fraude(url, texto_visible)

                    nuevos = self.extraer_enlaces(url, resp.text)
                    for enlace in nuevos:
                        if enlace not in self.visitados and enlace not in self.cola:
                            self.cola.append(enlace)

                paginas_desde_checkpoint += 1
                if paginas_desde_checkpoint >= config.CHECKPOINT_CADA_N_PAGINAS:
                    self._guardar_checkpoint()
                    self.candidate_store.save()
                    paginas_desde_checkpoint = 0

            except Exception as e:
                print(f"    ⚠️ No se pudo leer: {type(e).__name__}")
                continue

        self._guardar_bloqueados()
        self.candidate_store.save()

        if self.detener:
            print("\n🛑 Rastreo detenido por el usuario.")
        elif len(self.visitados) >= self.limite:
            self._guardar_checkpoint()
            print(f"\n✅ LÍMITE ALCANZADO — hay más URLs en cola, checkpoint guardado")
        else:
            self._borrar_checkpoint()
            print(f"\n✅ RASTREO FINALIZADO — sin más URLs por visitar")

        print(f"   Páginas visitadas: {len(self.visitados)}")
        print(f"   Hallazgos guardados en: {config.HALLAZGOS_FILE}")
        print(f"   Insights blockchain en: {config.BLOCKCHAIN_INSIGHTS_FILE}")
