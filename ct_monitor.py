# ct_monitor.py
"""
Monitorea Certificate Transparency logs (vía crt.sh, público y gratuito)
en busca de certificados SSL recién emitidos para dominios que imitan
marcas conocidas. Esto detecta sitios de phishing ANTES de que aparezcan
en cualquier feed de threat intel — apenas el estafador activa HTTPS.
"""
import requests
import time
from difflib import SequenceMatcher

# Marcas frecuentemente imitadas — la misma lista base que ya usa
# phishing_detector.py, pensada para lo que un estafador clonaría.
MARCAS_A_VIGILAR = [
    "paypal", "mercadopago", "mercadolibre", "bbva", "santander",
    "galicia", "bancoprovincia", "bancociudad", "afip", "anses",
    "binance", "coinbase", "tronscan", "metamask",
]


class MonitorCertificados:
    def __init__(self):
        self.base_url = "https://crt.sh/"

    def buscar_dominios_recientes(self, marca, dias=1):
        """
        Busca certificados emitidos recientemente para dominios que
        contienen la marca. crt.sh permite buscar con % como wildcard.
        """
        try:
            resp = requests.get(
                self.base_url,
                params={"q": f"%{marca}%", "output": "json"},
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Andart-OSINT)"}
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
        except Exception as e:
            print(f"⚠️ Error consultando crt.sh para '{marca}': {e}")
            return []

        dominios_vistos = set()
        resultados = []
        for entrada in data:
            nombre = entrada.get("name_value", "").lower().strip()
            if not nombre or nombre in dominios_vistos:
                continue
            dominios_vistos.add(nombre)
            # Filtra el dominio oficial de la marca (ej: paypal.com legítimo)
            if nombre.endswith(f"{marca}.com") or nombre == marca:
                continue
            resultados.append({
                "dominio": nombre,
                "marca_imitada": marca,
                "id_certificado": entrada.get("id"),
                "emitido": entrada.get("entry_timestamp"),
            })
        return resultados

    def escanear_todas_las_marcas(self, pausa=2.0):
        """Recorre todas las marcas vigiladas, respetando un ritmo razonable con crt.sh."""
        todos = []
        for marca in MARCAS_A_VIGILAR:
            print(f"🔎 Buscando certificados recientes para: {marca}")
            encontrados = self.buscar_dominios_recientes(marca)
            for r in encontrados:
                print(f"   🚨 {r['dominio']} (imita: {marca})")
            todos.extend(encontrados)
            time.sleep(pausa)
        return todos
