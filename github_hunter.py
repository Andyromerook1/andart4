# github_hunter.py
"""
Módulo de caza de spam/estafas en GitHub.
Usa exclusivamente la API pública oficial de GitHub (docs.github.com/rest/search).
No hace scraping del HTML de github.com ni evade ningún límite: cuando la API
devuelve 403/429 por rate limit, el módulo espera el tiempo indicado por GitHub
en el header X-RateLimit-Reset y continúa.
"""
import requests
import time
import re
from datetime import datetime, timedelta

# Palabras clave típicas de spam SEO de apuestas/lotería ilegal (observadas en
# repos como el de la Captura 479). Vas sumando acá lo que vayas encontrando.
KEYWORDS_SPAM = [
    "福彩快3",      # "lotería rápida 3" - apuestas
    "大发一分钟",    # "un minuto Dafa" - casino
    "PK10",         # juego de apuestas
    "彩神",         # "dios de la lotería" - branding típico de estas redes
    "官方专享",      # "exclusivo oficial" - lenguaje típico de spam de este tipo
]

GITHUB_API = "https://api.github.com"


class GitHubHunter:
    def __init__(self, token: str = None, requester=None):
        """
        token: Personal Access Token de GitHub (opcional pero recomendado).
               Sin token: 10 búsquedas/min. Con token: 30 búsquedas/min.
               Se usa solo para levantar el límite oficial, no para nada más.
        requester: instancia de SecureRequester, para reusar el mismo cliente
                   HTTP a la hora de bajar el contenido de archivos raw.
        """
        self.headers = {"Accept": "application/vnd.github+json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.requester = requester

    def _get(self, url, params=None):
        """GET a la API de GitHub respetando rate limits oficiales."""
        resp = requests.get(url, headers=self.headers, params=params, timeout=15)
        if resp.status_code == 403 and "X-RateLimit-Remaining" in resp.headers:
            if resp.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                espera = max(reset - int(time.time()), 1)
                print(f"⏳ Rate limit de GitHub alcanzado. Esperando {espera}s (límite oficial)...")
                time.sleep(espera + 1)
                return self._get(url, params)
        return resp

    def buscar_repos_recientes(self, dias=1, max_resultados=20):
        """
        Busca repos públicos creados/actualizados en los últimos `dias` que
        contengan alguno de los KEYWORDS_SPAM en el nombre de archivo o contenido.
        Devuelve lista de dicts: {repo, owner, url, archivo, score}
        """
        desde = (datetime.utcnow() - timedelta(days=dias)).strftime("%Y-%m-%d")
        hallazgos = []

        for kw in KEYWORDS_SPAM:
            print(f"🔎 Buscando keyword: {kw}")
            params = {
                "q": f'"{kw}" in:file,path created:>={desde}',
                "per_page": min(max_resultados, 30),
            }
            resp = self._get(f"{GITHUB_API}/search/code", params=params)
            if resp.status_code != 200:
                print(f"   ⚠️ Búsqueda falló ({resp.status_code}): {resp.text[:150]}")
                time.sleep(2)
                continue

            data = resp.json()
            for item in data.get("items", []):
                hallazgos.append({
                    "keyword": kw,
                    "repo": item["repository"]["full_name"],
                    "owner": item["repository"]["owner"]["login"],
                    "archivo": item["path"],
                    "repo_url": item["repository"]["html_url"],
                    "raw_url": self._to_raw_url(item),
                })
            # Respetar el límite oficial de búsqueda (10-30 req/min según haya token)
            time.sleep(2.5)

        print(f"✅ {len(hallazgos)} archivos sospechosos encontrados en GitHub")
        return hallazgos

    @staticmethod
    def _to_raw_url(item):
        """Convierte el resultado de la Search API en una URL raw descargable."""
        repo_full = item["repository"]["full_name"]
        branch = item["repository"].get("default_branch", "main")
        path = item["path"]
        return f"https://raw.githubusercontent.com/{repo_full}/{branch}/{path}"

    def evaluar_repo(self, repo_full_name):
        """
        Trae metadata del repo para ayudar a confirmar que es spam:
        cantidad de archivos, fecha de creación, estrellas, descripción.
        Un repo con 0 estrellas, miles de archivos .md creados en bloque
        y sin descripción es la huella típica de estas redes.
        """
        resp = self._get(f"{GITHUB_API}/repos/{repo_full_name}")
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "nombre": data.get("full_name"),
            "creado": data.get("created_at"),
            "actualizado": data.get("pushed_at"),
            "estrellas": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "descripcion": data.get("description"),
            "sospechoso": (
                data.get("stargazers_count", 0) == 0
                and not data.get("description")
            ),
        }

    def extraer_contenido_y_filtrar(self, hallazgos, motor_filtro, limite_archivos=15):
        """
        Descarga el contenido de una muestra de los archivos encontrados
        (no todos: con 15-20 alcanza para sacar los dominios/wallets que
        se repiten en toda la campaña de spam) y lo pasa por el MotorFiltro
        existente para extraer wallets, dominios clonados, etc.
        """
        resultados = []
        for h in hallazgos[:limite_archivos]:
            if self.requester:
                texto = self.requester.get_text(h["raw_url"])
            else:
                r = requests.get(h["raw_url"], timeout=15)
                texto = r.text if r.status_code == 200 else None

            if not texto:
                continue

            hallazgos_filtro = motor_filtro.escanear_texto(texto, origen=h["repo_url"])
            if hallazgos_filtro:
                resultados.append({"origen": h, "hallazgos": hallazgos_filtro})

            time.sleep(0.5)
        return resultados


def campaña_completa(token=None, requester=None, motor_filtro=None, dias=1):
    """
    Punto de entrada simple para correr todo el flujo desde app.py:
    busca repos spam recientes -> evalúa cuáles son sospechosos ->
    extrae contenido -> filtra wallets/dominios.
    """
    hunter = GitHubHunter(token=token, requester=requester)
    hallazgos = hunter.buscar_repos_recientes(dias=dias)

    repos_unicos = {h["repo"] for h in hallazgos}
    print(f"\n📦 Repos únicos detectados: {len(repos_unicos)}")
    for repo in repos_unicos:
        info = hunter.evaluar_repo(repo)
        if info:
            marca = "🚨 SOSPECHOSO" if info["sospechoso"] else "  "
            print(f"   {marca} {info['nombre']} — ⭐{info['estrellas']} — creado {info['creado']}")

    if motor_filtro and hallazgos:
        print("\n🧪 Extrayendo y filtrando contenido de archivos...")
        return hunter.extraer_contenido_y_filtrar(hallazgos, motor_filtro)
    return []
