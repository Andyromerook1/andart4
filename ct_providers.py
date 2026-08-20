# ct_providers.py
"""
Proveedores de Certificate Transparency, con fallback automático — pero
el fallback respeta qué tipo de búsqueda soporta cada proveedor.

BRAND_SEARCH: buscar cualquier certificado que contenga un término en
              cualquier posición (ej: "%paypal%" encuentra
              "paypa1-login.xyz"). Necesario para descubrir dominios que
              NO conocemos de antemano — el caso de uso central de Andart.
DOMAIN_SEARCH: buscar certificados de un dominio conocido y sus
               subdominios (ej: "bybit.com" -> "login.bybit.com").
               Útil para otra cosa, pero no reemplaza a BRAND_SEARCH.

Un proveedor que no soporta el tipo de consulta pedido se SALTA sin
contarlo como caído — no es una falla, es una incompatibilidad de diseño.
"""
import requests
import subprocess
import json

HEADERS = {"User-Agent": "curl/8.0"}

BRAND_SEARCH = "brand_search"
DOMAIN_SEARCH = "domain_search"


class CTProviderError(Exception):
    pass


class CTProviderNoSoportado(Exception):
    """El proveedor no soporta este TIPO de consulta — no es una falla."""
    pass


class CrtShProvider:
    nombre = "crt.sh"
    soporta = {BRAND_SEARCH, DOMAIN_SEARCH}

    def query(self, termino: str, tipo: str = BRAND_SEARCH) -> list:
        if tipo not in self.soporta:
            raise CTProviderNoSoportado(f"{self.nombre} no soporta {tipo}")

        query_str = f"%{termino}%" if tipo == BRAND_SEARCH else termino
        try:
            resp = requests.get(
                "https://crt.sh/",
                params={"q": query_str, "output": "json"},
                timeout=20,
                headers=HEADERS,
            )
        except Exception as e:
            raise CTProviderError(f"crt.sh: {type(e).__name__} {e}")

        if resp.status_code != 200:
            raise CTProviderError(f"crt.sh: status {resp.status_code}")

        try:
            data = resp.json()
        except Exception as e:
            raise CTProviderError(f"crt.sh: respuesta no-JSON ({e})")

        return [
            {
                "name_value": entrada.get("name_value", ""),
                "id_certificado": entrada.get("id"),
                "entry_timestamp": entrada.get("entry_timestamp"),
                "provider": self.nombre,
            }
            for entrada in data
        ]


class CertSpotterProvider:
    """
    Solo soporta DOMAIN_SEARCH (dominios conocidos + subdominios) — así
    lo diseñó SSLMate. No sirve como fallback de BRAND_SEARCH.
    Usa curl real vía subprocess porque su WAF bloquea el fingerprint
    TLS de la librería requests (no es tema de headers).
    """
    nombre = "certspotter"
    soporta = {DOMAIN_SEARCH}

    def query(self, termino: str, tipo: str = BRAND_SEARCH) -> list:
        if tipo not in self.soporta:
            raise CTProviderNoSoportado(f"{self.nombre} no soporta {tipo}")

        url = (
            f"https://api.certspotter.com/v1/issuances"
            f"?domain={termino}&include_subdomains=true&match_wildcards=true&expand=dns_names"
        )
        try:
            resultado = subprocess.run(
                ["curl", "-s", "--max-time", "20", url],
                capture_output=True, text=True, timeout=25,
            )
        except Exception as e:
            raise CTProviderError(f"certspotter (curl): {type(e).__name__} {e}")

        if resultado.returncode != 0:
            raise CTProviderError(f"certspotter (curl): exit code {resultado.returncode}")

        try:
            data = json.loads(resultado.stdout)
        except Exception as e:
            raise CTProviderError(f"certspotter (curl): respuesta no-JSON ({e})")

        if isinstance(data, dict):
            error_msg = data.get("message") or data.get("error")
            if error_msg:
                raise CTProviderError(f"certspotter: {error_msg}")

        return [
            {
                "name_value": "\n".join(entrada.get("dns_names", [])),
                "id_certificado": entrada.get("id"),
                "entry_timestamp": entrada.get("not_before"),
                "provider": self.nombre,
            }
            for entrada in data
        ]


class CTProvider:
    def __init__(self, proveedores=None):
        self.proveedores = proveedores or [CrtShProvider(), CertSpotterProvider()]
        self.ultimo_estado = {}

    def query(self, termino: str, tipo: str = BRAND_SEARCH) -> list:
        for provider in self.proveedores:
            try:
                resultados = provider.query(termino, tipo=tipo)
                self.ultimo_estado[provider.nombre] = "OK"
                return resultados
            except CTProviderNoSoportado:
                # No es una falla — este proveedor simplemente no
                # atiende este tipo de consulta. No se loguea como error.
                continue
            except CTProviderError as e:
                self.ultimo_estado[provider.nombre] = str(e)
                print(f"   ⚠️ {provider.nombre} no disponible, probando siguiente proveedor... ({e})")
                continue

        print(f"   🔴 CT_STATUS = DEGRADED para {tipo} — ningún proveedor compatible respondió para '{termino}'")
        return []

    def estado_actual(self) -> dict:
        return dict(self.ultimo_estado)
