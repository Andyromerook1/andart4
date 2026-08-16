# rastreador.py (versión mejorada)
import requests  # ya no se usa directamente, pero lo dejamos por si acaso
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from filtro import MotorFiltro
from network_client import SecureRequester  # <-- NUEVO

class Rastreador:
    def __init__(self, semilla, limite=1000000, use_tor=False, max_retries=3):
        self.cola = list(set(semilla))
        self.visitados = set()
        self.limite = limite
        self.filtro = MotorFiltro()
        # En lugar de headers fijos, usamos el cliente avanzado
        self.requester = SecureRequester(
            use_tor=use_tor,
            max_retries=max_retries,
            timeout=15  # puedes ajustar
        )
        # Rutas sensibles (igual que antes)
        self.rutas_sensibles = ["/.env", "/config.json", "/robots.txt", "/sitemap.xml", "/manifest.json"]

    # ... (los métodos es_mismo_dominio, extraer_enlaces, agregar_rutas_sensibles se mantienen IDÉNTICOS) ...

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
                # === CAMBIO AQUÍ: usamos el requester en lugar de requests.get ===
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
