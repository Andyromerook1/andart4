# ct_monitor.py
"""
Monitorea Certificate Transparency logs (vía crt.sh, público y gratuito)
en busca de dominios de phishing recién creados — ANTES de que aparezcan
en cualquier feed de threat intel.

Dos estrategias, porque una lista de marcas nunca cubre todo:
1. Por marca conocida (marcas_vigiladas.json) — rápido, preciso, pero
   limitado a lo que ya está en la lista.
2. Por patrón sospechoso (palabras de estafa + TLD barato) — más lento
   y con más ruido, pero no depende de conocer la marca de antemano.

Cada resultado incluye ahora los datos crudos que candidate_store /
risk_score necesitan: tld, días desde la emisión del certificado, y la
similitud de typosquatting calculada por phishing_detector.py (reusado,
no reinventado).
"""
import requests
import time
import json
import os
from datetime import datetime, timezone

from phishing_detector import PhishingDetector

PALABRAS_SOSPECHOSAS = [
    "verificar", "verificacion", "seguro", "soporte", "recuperar",
    "recuperacion", "actualizar", "bloqueado", "confirmar",
    "verify", "secure", "login", "support", "recovery", "update",
    "confirm", "suspended", "unlock",
    "seguranca", "suporte",
]

TLDS_BARATOS = [
    "xyz", "top", "icu", "tk", "ml", "ga", "cf", "club",
    "online", "site", "store", "info", "biz", "live", "vip"
]


class MonitorCertificados:
    def __init__(self, archivo_marcas="marcas_vigiladas.json"):
        self.base_url = "https://crt.sh/"
        self.marcas = self._cargar_marcas(archivo_marcas)
        self.phishing_detector = PhishingDetector()

    def _cargar_marcas(self, archivo):
        if not os.path.exists(archivo):
            print(f"⚠️ No se encontró {archivo}, usando lista mínima por defecto.")
            return ["paypal", "mercadopago", "binance", "whatsapp"]
        with open(archivo, encoding="utf-8") as f:
            data = json.load(f)
        todas = []
        for categoria in data.values():
            todas.extend(categoria)
        return list(dict.fromkeys(todas))

    def _consultar_crtsh(self, query):
        try:
            resp = requests.get(
                self.base_url,
                params={"q": query, "output": "json"},
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Andart-OSINT)"}
            )
            if resp.status_code != 200:
                return []
            return resp.json()
        except Exception as e:
            print(f"⚠️ Error consultando crt.sh para '{query}': {e}")
            return []

    @staticmethod
    def _extraer_tld(dominio: str) -> str:
        partes = dominio.rstrip(".").split(".")
        return partes[-1] if len(partes) >= 2 else ""

    @staticmethod
    def _dias_desde_emision(entry_timestamp: str):
        if not entry_timestamp:
            return None
        try:
            # crt.sh devuelve algo como "2026-08-19T12:34:56"
            fecha = datetime.fromisoformat(entry_timestamp.replace("Z", "+00:00"))
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            return max((datetime.now(timezone.utc) - fecha).days, 0)
        except Exception:
            return None

    def _enriquecer(self, nombre: str, motivo: str, id_certificado, entry_timestamp: str) -> dict:
        _, dominio_legitimo, similitud = self.phishing_detector.es_clon(nombre)
        return {
            "dominio": nombre,
            "motivo": motivo,
            "id_certificado": id_certificado,
            "tld": self._extraer_tld(nombre),
            "dias_desde_emision_certificado": self._dias_desde_emision(entry_timestamp),
            "similitud_typosquatting": similitud if similitud else None,
            "marca_imitada": dominio_legitimo,
        }

    # =============================================================
    # ESTRATEGIA 1: por marca conocida
    # =============================================================
    def buscar_por_marca(self, marca):
        data = self._consultar_crtsh(f"%{marca}%")
        dominios_vistos = set()
        resultados = []
        for entrada in data:
            nombre = entrada.get("name_value", "").lower().strip()
            if not nombre or nombre in dominios_vistos:
                continue
            dominios_vistos.add(nombre)
            if nombre.endswith(f"{marca}.com") or nombre == marca:
                continue  # dominio oficial, no es el objetivo
            resultados.append(self._enriquecer(
                nombre, f"imita marca: {marca}",
                entrada.get("id"), entrada.get("entry_timestamp"),
            ))
        return resultados

    def escanear_marcas(self, pausa=2.0):
        todos = []
        for marca in self.marcas:
            print(f"🔎 [Marca] Buscando: {marca}")
            encontrados = self.buscar_por_marca(marca)
            for r in encontrados:
                print(f"   🚨 {r['dominio']} ({r['motivo']}, similitud={r['similitud_typosquatting']})")
            todos.extend(encontrados)
            time.sleep(pausa)
        return todos

    # =============================================================
    # ESTRATEGIA 2: por patrón sospechoso
    # =============================================================
    def buscar_por_patron(self, palabra, tld):
        query = f"%{palabra}%.{tld}"
        data = self._consultar_crtsh(query)
        dominios_vistos = set()
        resultados = []
        for entrada in data:
            nombre = entrada.get("name_value", "").lower().strip()
            if not nombre or nombre in dominios_vistos:
                continue
            dominios_vistos.add(nombre)
            resultados.append(self._enriquecer(
                nombre, f"patrón sospechoso: '{palabra}' + .{tld}",
                entrada.get("id"), entrada.get("entry_timestamp"),
            ))
        return resultados

    def escanear_patrones(self, pausa=2.5, limite_combinaciones=None):
        todos = []
        combinaciones = [(p, t) for p in PALABRAS_SOSPECHOSAS for t in TLDS_BARATOS]
        if limite_combinaciones:
            combinaciones = combinaciones[:limite_combinaciones]

        print(f"🔎 [Patrón] {len(combinaciones)} combinaciones palabra+TLD a revisar")
        for palabra, tld in combinaciones:
            encontrados = self.buscar_por_patron(palabra, tld)
            for r in encontrados:
                print(f"   🚨 {r['dominio']} ({r['motivo']})")
            todos.extend(encontrados)
            time.sleep(pausa)
        return todos

    def escanear_todo(self, incluir_patrones=False, limite_patrones=40):
        resultados = self.escanear_marcas()
        if incluir_patrones:
            resultados.extend(self.escanear_patrones(limite_combinaciones=limite_patrones))
        vistos = set()
        finales = []
        for r in resultados:
            if r["dominio"] not in vistos:
                vistos.add(r["dominio"])
                finales.append(r)
        return finales
