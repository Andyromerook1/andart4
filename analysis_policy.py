# analysis_policy.py
"""
Traduce un RiskScoreResult (de risk_score.py) en una DECISIÓN de cuánto
analizar un candidato. No hace HTTP ni crawling — solo decide, con
explicación, qué nivel de profundidad amerita.

Separado de risk_score.py a propósito: los umbrales y reglas de acá van
a cambiar con la práctica mucho más seguido que las matemáticas del score.
"""
from dataclasses import dataclass
from risk_score import RiskScoreResult

# Umbrales PROVISIONALES — igual que en risk_score.py, existen para poder
# probar la política, no son la versión final.
UMBRAL_NIVEL_1 = None   # a definir con casos de prueba
UMBRAL_NIVEL_2 = None   # a definir con casos de prueba

FUENTES_CONFIRMADAS = {"openphish", "urlhaus", "phishstats"}


@dataclass
class Decision:
    nivel: int              # 0 = descartar, 1 = HTML liviano, 2 = análisis profundo
    motivo: str              # explicación legible
    forzado_por_evidencia: bool = False  # True si saltó el umbral normal


def decidir(resultado: RiskScoreResult) -> Decision:
    ...  # a implementar una vez acordados los umbrales
