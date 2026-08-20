# analysis_policy.py
"""
Traduce un RiskScoreResult (de risk_score.py) en una DECISIÓN de nivel
de análisis. No hace HTTP, no crawlea, no toca risk_score.py.

Nivel 0: no analizar ahora. NO significa "descartado para siempre" — el
         candidate se conserva y puede subir de nivel si aparecen nuevas
         señales más adelante (vía candidate_store).
Nivel 1: HTML liviano de la página en sí. Sin seguir recursos externos,
         sin análisis profundo de JS.
Nivel 2: análisis profundo completo (filtro.py tal como existe hoy).
"""
from dataclasses import dataclass
from risk_score import RiskScoreResult

UMBRAL_NIVEL_1 = 15
UMBRAL_NIVEL_2 = 50


@dataclass
class Decision:
    nivel: int
    score_efectivo: float
    score_original: float
    motivo: str


def decidir(resultado: RiskScoreResult) -> Decision:
    score_efectivo = max(resultado.score, 0)

    if score_efectivo >= UMBRAL_NIVEL_2:
        nivel = 2
        motivo = f"score {score_efectivo:.1f} ≥ {UMBRAL_NIVEL_2} → análisis profundo"
    elif score_efectivo >= UMBRAL_NIVEL_1:
        nivel = 1
        motivo = f"score {score_efectivo:.1f} ≥ {UMBRAL_NIVEL_1} → HTML liviano"
    else:
        nivel = 0
        motivo = f"score {score_efectivo:.1f} < {UMBRAL_NIVEL_1} → no analizar ahora (se conserva el candidate)"

    return Decision(
        nivel=nivel,
        score_efectivo=score_efectivo,
        score_original=resultado.score,
        motivo=motivo,
    )
