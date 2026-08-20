# ct_monitor.py
"""
Monitorea Certificate Transparency logs en busca de dominios de phishing
recién creados. No depende de un solo índice — usa CTProvider, que
intenta crt.sh y, si falla, CertSpotter como respaldo automático.
"""
import time
import json
import os
import re
from datetime import datetime, timezone

from phishing_detector import PhishingDetector
from ct_providers import CTProvider

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

SUFIJOS_HOSTING_COMPARTIDO = {
    "pages.dev", "github.io", "vercel.app", "netlify.app",
    "herokuapp.com", "repl.co", "glitch.me", "workers.dev",
    "web.app", "firebaseapp.com", "surge.sh", "ondigitalocean.app",
}

PATRON_HOSTNAME_VALIDO = re.compile(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)+$')


class MonitorCertificados:
    def __init__(self, archivo_marcas="marcas_vigiladas.json"):
        self.provider = CTProvider()
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

    @staticmethod
    def _separar_hostnames(name_value: str) -> list:
        candidatos = []
        for linea in name_value.split("\n"):
            h = linea.strip().lower().lstrip("*.")
            if h and PATRON_HOSTNAME_VALIDO.match(h):
                candidatos.append(h)
        return list(dict.fromkeys(candidatos))

    @staticmethod
    def _extraer_tld(dominio: str) -> str:
        partes = dominio.rstrip(".").split(".")
        return partes[-1] if len(partes) >= 2 else ""

    @staticmethod
    def _dias_desde_emision(entry_timestamp):
        if not entry_timestamp:
            return None
        try:
            fecha = datetime.fromisoformat(str(entry_timestamp).replace("Z", "+00:00"))
            if fecha.tzinfo is None:
                fecha = fecha.replace(tzinfo=timezone.utc)
            return max((datetime.now(timezone.utc) - fecha).days, 0)
        except Exception:
            return None

    def _dominio_relevante_para_similitud(self, hostname: str) -> str:
        for sufijo in SUFIJOS_HOSTING_COMPARTIDO:
            if hostname.endswith("." + sufijo):
                return hostname[: -(len(sufijo) + 1)]
        return hostname

    def _enriquecer(self, hostname: str, motivo: str, id_certificado, entry_timestamp) -> dict:
        dominio_para_similitud = self._dominio_relevante_para_similitud(hostname)
        _, dominio_legitimo, similitud = self.phishing_detector.es_clon(dominio_para_similitud)
        return {
            "dominio": hostname,
            "motivo": motivo,
            "id_certificado": id_certificado,
            "tld": self._extraer_tld(hostname),
            "dias_desde_emision_certificado": self._dias_desde_emision(entry_timestamp),
            "similitud_typosquatting": similitud if similitud else None,
            "marca_imitada": dominio_legitimo,
        }

    # =============================================================
    # ESTRATEGIA 1: por marca conocida
    # =============================================================
    def buscar_por_marca(self, marca):
        data = self.provider.query(marca)
        dominios_vistos = set()
        resultados = []
        for entrada in data:
            name_value = entrada.get("name_value", "")
            for hostname in self._separar_hostnames(name_value):
                if hostname in dominios_vistos:
                    continue
                dominios_vistos.add(hostname)
                if hostname.endswith(f"{marca}.com") or hostname == f"{marca}.com":
                    continue
                resultados.append(self._enriquecer(
                    hostname, f"imita marca: {marca}",
                    entrada.get("id_certificado"), entrada.get("entry_timestamp"),
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
        print(f"   ℹ️ Estado de proveedores CT: {self.provider.estado_actual()}")
        return todos

    # =============================================================
    # ESTRATEGIA 2: por patrón sospechoso
    # =============================================================
    def buscar_por_patron(self, palabra, tld):
        data = self.provider.query(f"{palabra}.{tld}")
        dominios_vistos = set()
        resultados = []
        for entrada in data:
            name_value = entrada.get("name_value", "")
            for hostname in self._separar_hostnames(name_value):
                if hostname in dominios_vistos:
                    continue
                dominios_vistos.add(hostname)
                resultados.append(self._enriquecer(
                    hostname, f"patrón sospechoso: '{palabra}' + .{tld}",
                    entrada.get("id_certificado"), entrada.get("entry_timestamp"),
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
