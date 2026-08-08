import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from filtro import MotorFiltro

class Rastreador:
    def __init__(self, semilla, limite=20):
        self.cola = list(set(semilla))
        self.visitados = set()
        self.limite = limite
        self.filtro = MotorFiltro()
        self.headers = {"User-Agent": "MiBot/1.0"}

    def es_mismo_dominio(self, base, url):
        return urlparse(base).netloc in urlparse(urljoin(base, url)).netloc

    def extraer_enlaces(self, url, html):
        enlaces = []
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            absoluto = urljoin(url, a["href"])
            if absoluto.startswith("http") and self.es_mismo_dominio(url, absoluto):
                enlaces.append(absoluto.split("#")[0].rstrip("/"))
        return enlaces

    def iniciar(self):
        print(f"🔄 INICIANDO RASTREO — {len(self.cola)} semillas cargadas\n")
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

                hallazgos = self.filtro.escanear_texto(resp.text, origen=url)
                for h in hallazgos:
                    self.filtro.guardar_hallazgo(h)

                nuevos = self.extraer_enlaces(url, resp.text)
                for enlace in nuevos:
                    if enlace not in self.visitados and enlace not in self.cola:
                        self.cola.append(enlace)

            except Exception as e:
                print(f"    ⚠️ No se pudo leer: {type(e).__name__}")
                continue

        print(f"\n✅ RASTREO FINALIZADO")
        print(f"   Páginas visitadas: {len(self.visitados)}")
        print(f"   Hallazgos guardados en: hallazgos.txt")