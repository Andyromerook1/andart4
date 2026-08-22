# rastreador.py
import signal
import sys
import time
import json
import os
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from filtro import MotorFiltro
from network_client import SecureRequester
from wayback_client import WaybackClient
from pdf_metadata import PDFMetadataExtractor
from fraud_detector import FraudDetector
from candidate_store import CandidateStore
from fuentes import ROL_REFERENCIA, ROL_CANDIDATO, ROL_FEED_AMENAZAS
import config


class Rastreador:
    def __init__(self, semilla, limite=None, max_retries=None):
        # semilla ahora es una lista de (url, role) — pero se acepta
        # también una lista de strings sueltos (compatibilidad hacia
        # atrás), tratados como ROL_CANDIDATO por default.
        self.roles_por_dominio = {}
        self.cola = self._cargar_semillas(semilla)

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

        self.fraud_detector = FraudDetector()
        self.candidate_store = CandidateStore()

        self.rutas_publicas = config.SENSITIVE_PATHS

        self._robots_cache = {}
        self._ultimo_acceso_dominio = {}

        # Menciones dentro de fuentes de referencia: no acusan al dominio
        # de referencia, pero tampoco se descartan — quedan preservadas
        # acá para correlación futura (evidence_store, próxima ronda).
        self.menciones_file = os.path.join(
            os.path.dirname(config.HALLAZGOS_FILE), "menciones_en_referencias.jsonl"
        )

        signal.signal(signal.SIGINT, self._manejador_ctrl_c)

    # =============================================================
    # 🏷️ ROLES DE PROCEDENCIA
    # =============================================================
    @staticmethod
    def _dominio_de(url):
        try:
            dominio = urlparse(url).netloc.lower()
            if dominio.startswith("www."):
                dominio = dominio[4:]
            return dominio
        except Exception:
            return ""

    def _cargar_semillas(self, semilla):
        cola = []
        vistas = set()
        for item in semilla:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                url, role = item[0], item[1]
            else:
                url, role = item, ROL_CANDIDATO

            if url in vistas:
                continue
            vistas.add(url)
            cola.append(url)

            dominio = self._dominio_de(url)
            if dominio and dominio not in self.roles_por_dominio:
                self.roles_por_dominio[dominio] = role
        return cola

    def _rol_de(self, url):
        """
        Devuelve el role del DOMINIO de esta URL. Un enlace interno
        descubierto durante el rastreo (mismo dominio que una semilla)
        hereda automáticamente el role de esa semilla, sin que haga
        falta registrarlo aparte.
        """
        return self.roles_por_dominio.get(self._dominio_de(url), ROL_CANDIDATO)

    def _registrar_mencion(self, hallazgo_o_resumen, origen_referencia, tipo_registro="hallazgo"):
        """
        Preserva lo que una fuente de referencia MENCIONA, sin que eso
        se convierta en una acusación contra la propia fuente. No se
        pierde el dato (como pedías) ni se lo trata como si la
        referencia fuera sospechosa.
        """
        try:
            registro = {
                "tipo_registro": tipo_registro,   # "hallazgo" o "contenido_fraude"
                "mencionado_en": origen_referencia,
                "role_origen": ROL_REFERENCIA,
                **hallazgo_o_resumen,
            }
            with open(self.menciones_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"   ⚠️ Error registrando mención: {e}")

    def _manejador_ctrl_c(self, sig, frame):
        print("\n\n⚠️ Deteniendo rastreo (Ctrl+C)... Guardando progreso...")
        self.detener = True
        self._guardar_checkpoint()
        self._guardar_bloqueados()
        self.candidate_store.save()
        sys.exit(0)

    def es_mismo_dominio(self, base, url):
        return self._dominio_de(base) == self._dominio_de(url)

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
                "roles_por_dominio": self.roles_por_dominio,
            }
            with open(config.CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"   ⚠️ Error guardando checkpoint: {e}")

    @staticmethod
    def _hay_checkpoint():
        return os.path.exists(config.CHECKPOINT_FILE) and os.path.getsize(config.CHECKPOINT_FILE) > 0

    def _cargar_checkpoint(self):
        try:
            with open(config.CHECKPOINT_FILE, encoding="utf-8") as f:
                data = json.load(f)
            self.cola = data.get("cola", self.cola)
            self.visitados = set(data.get("visitados", []))
            self.bloqueados = data.get("bloqueados", [])
            # Los roles se restauran también — si no, un rastreo retomado
            # trataría todo como ROL_CANDIDATO por default y volvería a
            # acusar a las fuentes de referencia.
            self.roles_por_dominio.update(data.get("roles_por_dominio", {}))
            print(f"   ♻️  Checkpoint cargado: {len(self.visitados)} páginas ya visitadas, "
                  f"{len(self.cola)} en cola")
            return True
        except Exception as e:
            print(f"   ⚠️ No se pudo cargar el checkpoint: {e}")
            return False

    def _borrar_checkpoint(self):
        try:
            if os.path.exists(config.CHECKPOINT_FILE):
                os.remove(config.CHECKPOINT_FILE)
        except Exception:
            pass

    def _registrar_dependencia(self, url_origen, url_dependencia, tipo):
        """
        Un recurso cross-domain NUNCA entra a la cola de rastreo — se
        registra como dependencia. Si el origen es una fuente de
        REFERENCIA y el recurso es un link externo, además se crea un
        candidate propio para ese dominio externo (discovered_by
        "mencion_en_referencia") — es justo lo que un artículo de Krebs
        aporta: un dominio candidato a investigar, mencionado por un
        tercero confiable.
        """
        try:
            candidate = self.candidate_store.get_or_create(url_origen, discovered_by="rastreador_web")
            candidate.setdefault("dependencies", [])
            dominio_dep = self._dominio_de(url_dependencia)
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

            if tipo == "link_externo" and self._rol_de(url_origen) == ROL_REFERENCIA:
                self.candidate_store.get_or_create(url_dependencia, discovered_by="mencion_en_referencia")
        except Exception:
            pass

    def extraer_enlaces(self, url, html_o_texto):
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
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return ""

    # =============================================================
    # 🔍 PROCESAMIENTO SEGÚN ROLE
    # =============================================================
    def _procesar_hallazgos_filtro(self, url, hallazgos, rol):
        """
        candidate/threat_feed: se acusa al propio dominio (comportamiento
        de siempre). reference: los hallazgos son MENCIONES — se
        preservan para correlación, pero nunca se acusa al dominio de
        referencia por lo que su propio artículo describe.
        """
        if rol == ROL_REFERENCIA:
            for h in hallazgos:
                print(f"   ℹ️ (mención en fuente de referencia) {h['tipo']}: {h['valor'][:50]}")
                self._registrar_mencion(h, url)
        else:
            for h in hallazgos:
                self.filtro.guardar_hallazgo(h)

    def _procesar_contenido_fraude(self, url, texto_visible, rol):
        """
        fraud_detector SIEMPRE corre, sin importar el role — describir
        una estafa con detalle es información valiosa igual. La
        diferencia está en qué se hace con el resultado: contra un
        candidate se suma al content_risk (afecta su nivel); contra una
        referencia se preserva como contexto, sin tocar ningún score.
        """
        if not texto_visible or len(texto_visible) < 30:
            return
        try:
            resultado = self.fraud_detector.analizar(texto_visible)
            if not resultado.senales:
                return

            if rol == ROL_REFERENCIA:
                resumen = {
                    "content_type_posible": resultado.tipo_posible,
                    "cantidad_senales": len(resultado.senales),
                }
                self._registrar_mencion(resumen, url, tipo_registro="contenido_fraude")
                print(f"   ℹ️ (artículo describe: {resultado.tipo_posible}) → {url[:70]} "
                      f"— NO se suma a content_risk (fuente de referencia)")
            else:
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
        rol = self._rol_de(url)
        if rol == ROL_REFERENCIA:
            self._registrar_mencion({"tipo": "PDF metadata", "valor": meta}, url)
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
        print(f"   🏷️  Dominios con role registrado: {len(self.roles_por_dominio)}")
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

            rol = self._rol_de(url)
            etiqueta_rol = " [reference]" if rol == ROL_REFERENCIA else (
                " [threat_feed]" if rol == ROL_FEED_AMENAZAS else ""
            )
            print(f"🔍 [{len(self.visitados)+1}/{self.limite}]{etiqueta_rol} Leyendo: {url[:70]}")
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
                    self._procesar_hallazgos_filtro(url, hallazgos, rol)

                    texto_visible = self._extraer_texto_visible(resp.text)
                    self._procesar_contenido_fraude(url, texto_visible, rol)

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
        print(f"   Menciones en referencias: {self.menciones_file}")
        print(f"   Insights blockchain en: {config.BLOCKCHAIN_INSIGHTS_FILE}")
