# analysis_policy.py
"""
Traduce DOMAIN_RISK (risk_score.py) y CONTENT_RISK (content_risk_score.py)
en una DECISIÓN de nivel de análisis. No hace HTTP, no crawlea, no toca
la lógica interna de ninguno de los dos motores de score.

No se suman: cada dimensión puede empujar el nivel por su cuenta. Un
dominio muy sospechoso sin contenido leído todavía, y una página con
contenido de fraude clarísimo en un dominio viejo, deben poder llegar a
Nivel 2 por caminos distintos — sumarlos diluiría cualquiera de los dos
casos extremos.

Nivel 0: no analizar ahora. NO significa "descartado para siempre" — el
         candidate se conserva y puede subir de nivel si aparecen nuevas
         señales más adelante (vía candidate_store).
Nivel 1: HTML liviano de la página en sí. Sin seguir recursos externos,
         sin análisis profundo de JS.
Nivel 2: análisis profundo completo (filtro.py tal como existe hoy).
"""
from dataclasses import dataclass
from typing import Optional
from risk_score import RiskScoreResult
from content_risk_score import ContentRiskResult

UMBRAL_NIVEL_1 = 15
UMBRAL_NIVEL_2 = 50


@dataclass
class Decision:
    nivel: int
    domain_risk: float
    content_risk: float
    dimension_decisiva: str   # "dominio" o "contenido" — cuál empujó el nivel
    motivo: str


def decidir(
    domain_resultado: RiskScoreResult,
    content_resultado: Optional[ContentRiskResult] = None,
) -> Decision:
    """
    content_resultado es opcional: un candidate recién descubierto por
    CT/GitHub/feeds todavía no tiene contenido leído, así que
    CONTENT_RISK arranca en 0 hasta que el rastreador visite la página.
    """
    domain_score = max(domain_resultado.score, 0)
    content_score = max(content_resultado.score, 0) if content_resultado else 0.0

    score_decisivo = max(domain_score, content_score)
    dimension = "dominio" if domain_score >= content_score else "contenido"

    if score_decisivo >= UMBRAL_NIVEL_2:
        nivel = 2
        motivo = f"{dimension}: {score_decisivo:.1f} ≥ {UMBRAL_NIVEL_2} → análisis profundo"
    elif score_decisivo >= UMBRAL_NIVEL_1:
        nivel = 1
        motivo = f"{dimension}: {score_decisivo:.1f} ≥ {UMBRAL_NIVEL_1} → HTML liviano"
    else:
        nivel = 0
        motivo = (
            f"máximo entre dominio ({domain_score:.1f}) y contenido "
            f"({content_score:.1f}) < {UMBRAL_NIVEL_1} → no analizar ahora"
        )

    return Decision(
        nivel=nivel,
        domain_risk=domain_score,
        content_risk=content_score,
        dimension_decisiva=dimension,
        motivo=motivo,
    )
