# wayback_client.py
"""
Consulta y guarda versiones archivadas de páginas vía Wayback Machine
(archive.org). API pública oficial, sin autenticación ni API key.
Se usa como respaldo cuando un sitio bloquea el acceso directo del
rastreador, en vez de reintentar la petición disfrazada.
"""
import requests


class WaybackClient:
    def __init__(self, timeout=15):
        self.timeout = timeout

    def snapshot_mas_reciente(self, url):
        """
        Trae la URL de la copia archivada más reciente de `url`, si existe.
        Devuelve None si Wayback nunca archivó esa página.
        """
        try:
            resp = requests.get(
                "https://archive.org/wayback/available",
                params={"url": url},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                snap = data.get("archived_snapshots", {}).get("closest")
                if snap and snap.get("available"):
                    return snap.get("url")
        except Exception as e:
            print(f"⚠️ Error consultando Wayback para {url[:60]}: {e}")
        return None

    def archivar_ahora(self, url):
        """
        Pide a Wayback que archive la URL ahora mismo (servicio público
        'Save Page Now'). Útil para páginas de estafa/phishing recién
        encontradas que probablemente bajen pronto — así queda una copia
        pública como evidencia, con timestamp de terceros.
        """
        try:
            resp = requests.get(f"https://web.archive.org/save/{url}", timeout=30)
            if resp.status_code in (200, 302):
                return f"https://web.archive.org/web/2/{url}"
        except Exception as e:
            print(f"⚠️ Error archivando en Wayback: {e}")
        return None
