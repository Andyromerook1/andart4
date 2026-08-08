import requests
import random

class FuentesAutomaticas:

    def desde_github_api(self, cantidad=15):
        urls = []
        try:
            print("🔗 Consultando API de GitHub...")
            resp = requests.get("https://api.github.com/events", timeout=15, headers={
                "User-Agent": "MiBot/1.0"
            })
            if resp.status_code == 200:
                eventos = resp.json()
                for ev in eventos:
                    if "repo" in ev and ev["repo"]:
                        url = f"https://github.com/{ev['repo']['name']}"
                        if url not in urls:
                            urls.append(url)
                            if len(urls) >= cantidad:
                                break
            print(f"   ✅ Obtenidas {len(urls)} URLs desde GitHub")
        except Exception as e:
            print(f"   ⚠️ Error GitHub: {type(e).__name__}")
        return urls

    def desde_wikipedia(self, cantidad=10):
        urls = []
        try:
            print("🔗 Consultando semillas automáticas de Wikipedia...")
            url_api = "https://es.wikipedia.org/w/api.php?action=query&list=random&rnnamespace=0&rnlimit=10&format=json"
            resp = requests.get(url_api, timeout=10, headers={"User-Agent": "MiBot/1.0"})
            if resp.status_code == 200:
                datos = resp.json()
                for item in datos.get("query", {}).get("random", []):
                    titulo = item["title"].replace(" ", "_")
                    urls.append(f"https://es.wikipedia.org/wiki/{titulo}")
            print(f"   ✅ Obtenidas {len(urls)} URLs desde Wikipedia")
        except Exception as e:
            print(f"   ⚠️ Error Wikipedia: {type(e).__name__}")
        return urls

    def desde_archivo(self, nombre="semillas.txt"):
        try:
            with open(nombre, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f if l.strip().startswith("http")]
                print(f"   ✅ Cargadas {len(lineas)} URLs desde {nombre}")
                return lineas
        except FileNotFoundError:
            print(f"   ℹ️ {nombre} no existe, se omite")
            return []

    def generar_rango_ip(self, cantidad=50):
        a = random.randint(1, 223)
        b = random.randint(0, 255)
        c = random.randint(0, 255)
        base = f"{a}.{b}.{c}"
        print(f"   ✅ Generado rango: {base}.1 → {base}.{cantidad}")
        return base

    def obtener_todas(self):
        print("\n" + "="*60)
        print("   🔄 CARGANDO FUENTES AUTOMÁTICAS...")
        print("="*60)
        urls = []
        urls.extend(self.desde_github_api())
        urls.extend(self.desde_wikipedia())
        urls.extend(self.desde_archivo())
        urls_unicas = list(dict.fromkeys(urls))
        print(f"\n✅ TOTAL SEMILLAS CARGADAS: {len(urls_unicas)}\n")
        return urls_unicas