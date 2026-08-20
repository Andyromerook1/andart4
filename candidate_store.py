# candidate_store.py
"""
Persistencia de candidatos detectados por las distintas fuentes
(ct_monitor, github_hunter, feeds, etc.). No hace HTTP, no decide
niveles — solo guarda observaciones y delega a risk_score.py /
analysis_policy.py el cálculo de score y nivel.

Principio clave: candidate_store ACUMULA OBSERVACIONES.
risk_score DECIDE cómo interpretarlas. candidate_store nunca elige
"la mejor fuente" ni ninguna otra lógica de scoring — eso sería meter
conocimiento de riesgo dentro del almacenamiento.

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

            # Señales generales / infraestructura
            "signals": [],

            # Señales obtenidas analizando contenido
            # con fraud_detector.py
            "content_signals": [],
            "content_type_posible": None,

            # Entradas que luego consume risk_score.py
            "_score_inputs": {},

            "score": 0.0,
            "score_signals": [],

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
    # SEÑALES GENERALES
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
    # SEÑALES DE CONTENIDO / FRAUD DETECTOR
    # =========================================================

    def add_content_signals(
        self,
        domain: str,
        resultado_fraude,
        origen_url: str = None,
    ):
        """
        Recibe un ResultadoFraude de fraud_detector.py y registra
        cada señal de contenido en el candidate.

        Reutiliza una lógica de deduplicación por tipo similar a
        add_signal():

        - first_seen
        - last_seen
        - count

        No modifica el score directamente.

        La interpretación de estas señales deberá hacerse después
        desde risk_score.py mediante recalculate().
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

        # Tipo general que fraud_detector considera más probable.
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
            categoria = getattr(
                senal,
                "categoria",
                "desconocida",
            )

            tipo = getattr(
                senal,
                "tipo",
                "desconocido",
            )

            fragmento = getattr(
                senal,
                "fragmento",
                None,
            )

            peso = getattr(
                senal,
                "peso",
                None,
            )

            tipo_completo = (
                f"{categoria}:{tipo}"
            )

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

                existente["count"] = (
                    existente.get("count", 0) + 1
                )

                # Conservamos el fragmento detectado más reciente.
                existente["fragment"] = fragmento

                # También actualizamos el peso por si en el futuro
                # fraud_detector cambia la ponderación.
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

        # Si conocemos la URL concreta donde se encontró el contenido,
        # también la conservamos dentro del candidate.
        if origen_url:
            self._registrar_url_y_host(
                candidate,
                origen_url,
            )

        candidate["last_seen"] = _ahora_iso()

        return candidate

    # =========================================================
    # SCORE / NIVEL
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

        inputs = dict(
            candidate.get(
                "_score_inputs",
                {},
            )
        )

        # candidate_store entrega todas las fuentes observadas.
        # La interpretación corresponde exclusivamente a risk_score.py.
        inputs["fuente"] = candidate.get(
            "discovered_by",
            [],
        )

        resultado: RiskScoreResult = calcular_score(
            **inputs
        )

        decision = decidir(resultado)

        candidate["score"] = resultado.score

        candidate["score_signals"] = (
            resultado.as_dict().get(
                "signals",
                [],
            )
        )

        candidate["level"] = decision.nivel
        candidate["level_reason"] = decision.motivo

        return candidate

    def save_all_recalculated(self):
        for domain in list(
            self._data.keys()
        ):
            self.recalculate(domain)

        self.save()
