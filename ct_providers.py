# ct_providers.py
"""
Proveedores de Certificate Transparency, con fallback automático.

ct_monitor.py no debe saber CÓMO se consiguió un certificado (crt.sh,
CertSpotter, etc.) — solo que "CT" lo encontró. Por eso cada provider
normaliza su salida al mismo formato: una lista de dicts con
{hostname, id_certificado, entry_timestamp, provider}.

El campo `provider` queda registrado solo para diagnóstico/logs — NUNCA
llega a risk_score.py como una fuente distinta. Dos proveedores viendo
el mismo certificado siguen siendo UNA sola señal de tipo "ct_monitor".
"""
import requests
from datetime import datetime, timezone


class CTProviderError(Exception):
    """Un proveedor falló (timeout, error HTTP, respuesta inválida)."""
    pass


class CrtShProvider:
    nombre = "crt.sh"

    def query(self, termino: str) -> list:
        try:
            resp = requests.get(
                "https://crt.sh/",
                params={"q": f"%{termino}%", "output": "json"},
                timeout=20,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Andart-OSINT)"},
            )
        except Exception as e:
            raise CTProviderError(f"crt.sh: {type(e).__name__} {e}")

        if resp.status_code != 200:
            raise CTProviderError(f"crt.sh: status {resp.status_code}")

        try:
            data = resp.json()
        except Exception as e:
            raise CTProviderError(f"crt.sh: respuesta no-JSON ({e})")

        resultados = []
        for entrada in data:
            resultados.append({
                "name_value": entrada.get("name_value", ""),  # puede traer varios hosts separados por \n
                "id_certificado": entrada.get("id"),
                "entry_timestamp": entrada.get("entry_timestamp"),
                "provider": self.nombre,
            })
        return resultados


class CertSpotterProvider:
    """
    api.certspotter.com — SSLMate. El endpoint /v1/issuances funciona sin
    API key para uso liviano (rate limit más bajo que autenticado, pero
    suficiente como proveedor de respaldo, no como principal).
    """
    nombre = "certspotter"

    def query(self, termino: str) -> list:
        try:
            resp = requests.get(
                "https://api.certspotter.com/v1/issuances",
                params={
                    "domain": termino,
                    "include_subdomains": "true",
                    "match_wildcards": "true",
                    "expand": "dns_names",
                },
                timeout=20,
                headers={"User-Agent": "curl/8.0"},
            )
        except Exception as e:
            raise CTProviderError(f"certspotter: {type(e).__name__} {e}")

        if resp.status_code == 429:
            raise CTProviderError("certspotter: rate limit (429)")
        if resp.status_code != 200:
            raise CTProviderError(f"certspotter: status {resp.status_code}")

        try:
            data = resp.json()
        except Exception as e:
            raise CTProviderError(f"certspotter: respuesta no-JSON ({e})")

        resultados = []
        for entrada in data:
            dns_names = entrada.get("dns_names", [])
            # certspotter separa los hostnames en una lista propia, no en
            # un string con \n como crt.sh — se unen con \n para que
            # ct_monitor._separar_hostnames() los procese igual sea cual
            # sea el proveedor que respondió.
            resultados.append({
                "name_value": "\n".join(dns_names),
                "id_certificado": entrada.get("id"),
                "entry_timestamp": entrada.get("not_before"),  # certspotter no da timestamp de log, usamos not_before
                "provider": self.nombre,
            })
        return resultados


class CTProvider:
    """
    Intenta cada proveedor en orden hasta que uno responda. Si todos
    fallan, devuelve [] y deja constancia del estado — NUNCA levanta
    una excepción hacia arriba, así el resto de Andart sigue funcionando
    aunque CT esté completamente caído.
    """
    def __init__(self, proveedores=None):
        self.proveedores = proveedores or [CrtShProvider(), CertSpotterProvider()]
        self.ultimo_estado = {}  # nombre_proveedor -> "OK" | "TIMEOUT" | mensaje de error

    def query(self, termino: str) -> list:
        for provider in self.proveedores:
            try:
                resultados = provider.query(termino)
                self.ultimo_estado[provider.nombre] = "OK"
                return resultados
            except CTProviderError as e:
                self.ultimo_estado[provider.nombre] = str(e)
                print(f"   ⚠️ {provider.nombre} no disponible, probando siguiente proveedor... ({e})")
                continue

        # Todos fallaron
        print(f"   🔴 CT_STATUS = DEGRADED — ningún proveedor de Certificate Transparency respondió para '{termino}'")
        return []

    def estado_actual(self) -> dict:
        return dict(self.ultimo_estado)
