# candidate_store.py
"""
Persistencia de candidatos detectados por las distintas fuentes
(ct_monitor, github_hunter, feeds, fraud_detector, etc.). No hace HTTP,
no decide niveles — solo guarda observaciones y delega a risk_score.py /
content_risk_score.py / analysis_policy.py el cálculo de score y nivel.

Principio clave: candidate_store ACUMULA OBSERVACIONES.
Los motores de score DECIDEN cómo interpretarlas. candidate_store nunca
elige "la mejor fuente" ni ninguna otra lógica de scoring — eso sería
meter conocimiento de riesgo dentro del almacenamiento.

Dos dimensiones de riesgo, calculadas por separado (ver discusión de
diseño): DOMAIN_RISK (infraestructura: edad, TLD, typosquatting, CT,
fuente) y CONTENT_RISK (texto: reclutamiento, inversión fraudulenta,
etc.). No se mezclan en un solo score — analysis_policy.py decide el
nivel mirando ambos.

Un candidate se identifica por dominio normalizado, pero conserva
hostnames y URLs originales (importante para correlación de
infraestructura más adelante).

Persistencia: JSON simple en OUTPUT_BASE/candidatos.json.
"""

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from risk_score import calcular_score, RiskScoreResult
from content_risk_score import calcular_content_risk, ContentRiskResult
from analysis_policy import decidir

import config


RUTA_CANDIDATOS = os.path.join(
    config.OUTPUT_BASE,
    "candidatos.json",
)


def normalizar_dominio(url_o_dominio: str) -> str:
    """
    Devuelve el dominio normalizado (sin protocolo, sin www, sin ruta)
    para usar como candidate_id.
    """
    valor = url_o_dominio.strip().lower()

    if "://" in valor:
        valor = urlparse(valor).netloc or valor
    else:
        valor = valor.split("/")[0]

    if valor.startswith("www."):
        valor = valor[4:]

    return valor


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CandidateStore:
    def __init__(self, ruta=None):
        self.ruta = ruta or RUTA_CANDIDATOS
        self._data = self._cargar()

    def _cargar(self) -> dict:
        try:
            with open(self.ruta, encoding="utf-8") as f:
                data = json.load(f)

                if isinstance(data, dict):
                    return data

                print(
                    "⚠️ candidatos.json no contiene un objeto JSON válido. "
                    "Se iniciará un store vacío."
                )
                return {}

        except (FileNotFoundError, json.JSONDecodeError):
            return {}

        except Exception as e:
            print(f"⚠️ Error cargando candidatos.json: {e}")
            return {}

    def save(self):
        try:
            directorio = os.path.dirname(self.ruta)

            if directorio:
                os.makedirs(directorio, exist_ok=True)

            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(
                    self._data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

        except Exception as e:
            print(f"⚠️ Error guardando candidatos.json: {e}")

    # =========================================================
    # OPERACIONES BÁSICAS
    # =========================================================

    def get(self, domain: str):
        return self._data.get(normalizar_dominio(domain))

    def create(
        self,
        url_o_dominio: str,
        discovered_by: str = None,
    ) -> dict:
        domain = normalizar_dominio(url_o_dominio)
        ahora = _ahora_iso()

        candidate = {
            "domain": domain,

            "first_seen": ahora,
            "last_seen": ahora,

            "discovered_by": (
                [discovered_by]
                if discovered_by
                else []
            ),

            "hostnames": [],
            "urls": [],

            # Señales generales / infraestructura (DOMAIN_RISK)
            "signals": [],

            # Señales obtenidas analizando contenido con fraud_detector.py
            # (CONTENT_RISK)
            "content_signals": [],
            "content_type_posible": None,

            # Entradas que consume risk_score.py
            "_score_inputs": {},

            # DOMAIN_RISK
            "score": 0.0,             # se mantiene por compatibilidad hacia atrás
            "domain_risk": 0.0,
            "score_signals": [],

            # CONTENT_RISK
            "content_risk": 0.0,
            "content_risk_detail": {},

            "level": 0,
            "level_reason": "",

            "analysis_status": "pending",
        }

        self._registrar_url_y_host(
            candidate,
            url_o_dominio,
        )

        self._data[domain] = candidate

        return candidate

    def get_or_create(
        self,
        url_o_dominio: str,
        discovered_by: str = None,
    ) -> dict:
        domain = normalizar_dominio(url_o_dominio)

        existente = self._data.get(domain)

        if existente:
            existente["last_seen"] = _ahora_iso()

            self._registrar_url_y_host(
                existente,
                url_o_dominio,
            )

            existente.setdefault("discovered_by", [])

            if (
                discovered_by
                and discovered_by not in existente["discovered_by"]
            ):
                existente["discovered_by"].append(
                    discovered_by
                )

            # Compatibilidad con candidatos guardados por versiones
            # anteriores del store.
            existente.setdefault("hostnames", [])
            existente.setdefault("urls", [])
            existente.setdefault("signals", [])
            existente.setdefault("content_signals", [])
            existente.setdefault("content_type_posible", None)
            existente.setdefault("_score_inputs", {})
            existente.setdefault("score_signals", [])
            existente.setdefault("domain_risk", existente.get("score", 0.0))
            existente.setdefault("content_risk", 0.0)
            existente.setdefault("content_risk_detail", {})

            return existente

        return self.create(
            url_o_dominio,
            discovered_by,
        )

    @staticmethod
    def _registrar_url_y_host(
        candidate: dict,
        url_o_dominio: str,
    ):
        candidate.setdefault("hostnames", [])
        candidate.setdefault("urls", [])

        valor = url_o_dominio.strip()

        if "://" in valor:
            parsed = urlparse(valor)

            hostname = parsed.netloc.lower()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            if (
                hostname
                and hostname not in candidate["hostnames"]
            ):
                candidate["hostnames"].append(hostname)

            if valor not in candidate["urls"]:
                candidate["urls"].append(valor)

        else:
            hostname = valor.lower().split("/")[0]

            if hostname.startswith("www."):
                hostname = hostname[4:]

            if (
                hostname
                and hostname not in candidate["hostnames"]
            ):
                candidate["hostnames"].append(hostname)

    # =========================================================
    # SEÑALES GENERALES (DOMAIN_RISK)
    # =========================================================

    def add_signal(
        self,
        domain: str,
        tipo: str,
        valor,
        discovered_by: str = None,
        campos_score: dict = None,
    ):
        candidate = self._data.get(
            normalizar_dominio(domain)
        )

        if not candidate:
            candidate = self.create(domain)

        candidate.setdefault("signals", [])
        candidate.setdefault("discovered_by", [])
        candidate.setdefault("_score_inputs", {})

        ahora = _ahora_iso()

        existente = next(
            (
                signal
                for signal in candidate["signals"]
                if signal.get("type") == tipo
            ),
            None,
        )

        if existente:
            existente["last_seen"] = ahora
            existente["count"] = (
                existente.get("count", 0) + 1
            )
            existente["value"] = valor

        else:
            candidate["signals"].append(
                {
                    "type": tipo,
                    "value": valor,
                    "first_seen": ahora,
                    "last_seen": ahora,
                    "count": 1,
                }
            )

        if (
            discovered_by
            and discovered_by not in candidate["discovered_by"]
        ):
            candidate["discovered_by"].append(
                discovered_by
            )

        if campos_score:
            candidate["_score_inputs"].update(
                campos_score
            )

        candidate["last_seen"] = ahora

        return candidate

    # =========================================================
    # SEÑALES DE CONTENIDO / FRAUD DETECTOR (CONTENT_RISK)
    # =========================================================

    def add_content_signals(
        self,
        domain: str,
        resultado_fraude,
        origen_url: str = None,
    ):
        """
        Recibe un ResultadoFraude de fraud_detector.py y registra cada
        señal de contenido en el candidate. Reutiliza la misma lógica
        de deduplicación por tipo que add_signal() (first_seen,
        last_seen, count). No calcula CONTENT_RISK acá — eso lo hace
        recalculate() llamando a content_risk_score.py.
        """

        candidate = self._data.get(
            normalizar_dominio(domain)
        )

        if not candidate:
            candidate = self.create(domain)

        candidate.setdefault(
            "content_signals",
            [],
        )

        candidate["content_type_posible"] = getattr(
            resultado_fraude,
            "tipo_posible",
            None,
        )

        señales = getattr(
            resultado_fraude,
            "senales",
            [],
        )

        for senal in señales:
            categoria = getattr(senal, "categoria", "desconocida")
            tipo = getattr(senal, "tipo", "desconocido")
            fragmento = getattr(senal, "fragmento", None)
            peso = getattr(senal, "peso", 0)

            tipo_completo = f"{categoria}:{tipo}"
            ahora = _ahora_iso()

            existente = next(
                (
                    signal
                    for signal in candidate["content_signals"]
                    if signal.get("type") == tipo_completo
                ),
                None,
            )

            if existente:
                existente["last_seen"] = ahora
                existente["count"] = existente.get("count", 0) + 1
                existente["fragment"] = fragmento
                existente["weight"] = peso
                if origen_url:
                    existente["source_url"] = origen_url

            else:
                candidate["content_signals"].append(
                    {
                        "type": tipo_completo,
                        "category": categoria,
                        "fragment": fragmento,
                        "weight": peso,
                        "source_url": origen_url,
                        "first_seen": ahora,
                        "last_seen": ahora,
                        "count": 1,
                    }
                )

        if origen_url:
            self._registrar_url_y_host(
                candidate,
                origen_url,
            )

        candidate["last_seen"] = _ahora_iso()

        return candidate

    # =========================================================
    # SCORE / NIVEL — DOMAIN_RISK + CONTENT_RISK, sin sumarse
    # =========================================================

    def recalculate(
        self,
        domain: str,
    ):
        candidate = self._data.get(
            normalizar_dominio(domain)
        )

        if not candidate:
            return None

        # --- DOMAIN_RISK ---
        inputs = dict(
            candidate.get(
                "_score_inputs",
                {},
            )
        )
        inputs["fuente"] = candidate.get(
            "discovered_by",
            [],
        )
        domain_resultado: RiskScoreResult = calcular_score(**inputs)

        # --- CONTENT_RISK ---
        content_resultado: ContentRiskResult = calcular_content_risk(
            candidate.get("content_signals", [])
        )

        # --- Decisión combinada, sin sumar los dos scores ---
        decision = decidir(domain_resultado, content_resultado)

        candidate["domain_risk"] = domain_resultado.score
        candidate["score"] = domain_resultado.score  # compatibilidad hacia atrás
        candidate["score_signals"] = domain_resultado.as_dict().get("signals", [])

        candidate["content_risk"] = content_resultado.score
        candidate["content_risk_detail"] = content_resultado.as_dict()

        candidate["level"] = decision.nivel
        candidate["level_reason"] = decision.motivo

        return candidate

    def save_all_recalculated(self):
        for domain in list(
            self._data.keys()
        ):
            self.recalculate(domain)

        self.save()
