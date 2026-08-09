import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from filtro import MotorFiltro

class Rastreador:
    def __init__(self, semilla, limite=1000000):
        # ⚠️ limite=1000000 → prácticamente SIN LÍMITE de páginas
        self.cola = list(set(semilla))
        self.visitados = set()
        self.limite = limite
        self.filtro = MotorFiltro()
        self.headers = {"User-Agent": "MiBot/1.0"}
        # Archivos típicos donde se suelen filtrar claves por mala configuración
        self.rutas_sensibles = ["/.env", "/config.json", "/robots.txt", "/sitemap.xml", "/manifest.json"]

    # ✅ LÍMITE DE DOMINIO DESACTIVADO → acepta TODOS los enlaces, cualquier sitio
    def es_mismo_dominio(self, base, url):
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
        print(f"   📄 Límite de páginas: {self.limite} (prácticamente ilimitado)\n")
        
        # Agrega rutas sensibles automáticamente a cada semilla
        for semilla in list(self.cola):
            self.agregar_rutas_sensibles(semilla)

        while self.cola and len(self.visitados) < self.limite:
            url = self.cola.pop(0)
            if url in self.visitados:
                continue
                
            print(f"🔍 [{len(self.visitados)+1}/{self.limite}] Leyendo: {url[:80]}")
            try:
                resp = requests.get(url, timeout=10, headers=self.headers)
                if resp.status_code != 200:
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
