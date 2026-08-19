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

RUTA_CANDIDATOS = os.path.join(config.OUTPUT_BASE, "candidatos.json")


def normalizar_dominio(url_o_dominio: str) -> str:
    """
    Devuelve el dominio raíz normalizado (sin protocolo, sin www, sin
    ruta) para usar como candidate_id.
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
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self):
        try:
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando candidatos.json: {e}")

    # =========================================================
    # OPERACIONES BÁSICAS
    # =========================================================
    def get(self, domain: str):
        return self._data.get(normalizar_dominio(domain))

    def create(self, url_o_dominio: str, discovered_by: str = None) -> dict:
        domain = normalizar_dominio(url_o_dominio)
        ahora = _ahora_iso()
        candidate = {
            "domain": domain,
            "first_seen": ahora,
            "last_seen": ahora,
            "discovered_by": [discovered_by] if discovered_by else [],
            "hostnames": [],
            "urls": [],
            "signals": [],
            "_score_inputs": {},
            "score": 0.0,
            "score_signals": [],
            "level": 0,
            "level_reason": "",
            "analysis_status": "pending",
        }
        self._registrar_url_y_host(candidate, url_o_dominio)
        self._data[domain] = candidate
        return candidate

    def get_or_create(self, url_o_dominio: str, discovered_by: str = None) -> dict:
        domain = normalizar_dominio(url_o_dominio)
        existente = self._data.get(domain)
        if existente:
            existente["last_seen"] = _ahora_iso()
            self._registrar_url_y_host(existente, url_o_dominio)
            if discovered_by and discovered_by not in existente["discovered_by"]:
                existente["discovered_by"].append(discovered_by)
            return existente
        return self.create(url_o_dominio, discovered_by)

    @staticmethod
    def _registrar_url_y_host(candidate: dict, url_o_dominio: str):
        if "://" in url_o_dominio:
            hostname = urlparse(url_o_dominio).netloc
            if hostname and hostname not in candidate["hostnames"]:
                candidate["hostnames"].append(hostname)
            if url_o_dominio not in candidate["urls"]:
                candidate["urls"].append(url_o_dominio)
        else:
            if url_o_dominio not in candidate["hostnames"]:
                candidate["hostnames"].append(url_o_dominio)

    # =========================================================
    # SEÑALES
    # =========================================================
    def add_signal(self, domain: str, tipo: str, valor, discovered_by: str = None,
                    campos_score: dict = None):
        candidate = self._data.get(normalizar_dominio(domain))
        if not candidate:
            candidate = self.create(domain)

        ahora = _ahora_iso()
        existente = next((s for s in candidate["signals"] if s["type"] == tipo), None)
        if existente:
            existente["last_seen"] = ahora
            existente["count"] += 1
            existente["value"] = valor
        else:
            candidate["signals"].append({
                "type": tipo, "value": valor,
                "first_seen": ahora, "last_seen": ahora, "count": 1,
            })

        if discovered_by and discovered_by not in candidate["discovered_by"]:
            candidate["discovered_by"].append(discovered_by)

        if campos_score:
            candidate["_score_inputs"].update(campos_score)

        candidate["last_seen"] = ahora
        return candidate

    # =========================================================
    # SCORE / NIVEL
    # =========================================================
    def recalculate(self, domain: str):
        candidate = self._data.get(normalizar_dominio(domain))
        if not candidate:
            return None

        inputs = dict(candidate.get("_score_inputs", {}))
        inputs["fuente"] = candidate["discovered_by"]

        resultado: RiskScoreResult = calcular_score(**inputs)
        decision = decidir(resultado)

        candidate["score"] = resultado.score
        candidate["score_signals"] = resultado.as_dict()["signals"]
        candidate["level"] = decision.nivel
        candidate["level_reason"] = decision.motivo
        return candidate

    def save_all_recalculated(self):
        for domain in list(self._data.keys()):
            self.recalculate(domain)
        self.save()
