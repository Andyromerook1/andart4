# content_risk_score.py
"""
Motor de scoring de riesgo de CONTENIDO — PURO, sin efectos secundarios.
Hermano de risk_score.py, pero mide una dimensión distinta: qué tan
fuerte es la evidencia de fraude en el TEXTO de una página, no en su
dominio/infraestructura.

No se combinan en el mismo número a propósito — DOMAIN_RISK y
CONTENT_RISK miden cosas de naturaleza distinta (ver discusión de
diseño). La combinación en un CASE_RISK único ocurre en
analysis_policy.py, no acá.

Entrada: una lista de content_signals tal como las guarda
candidate_store.py (con category, type, weight, count).
"""
from dataclasses import dataclass, field
from typing import Optional

# Tope de puntos que UNA familia puede aportar, sin importar cuántas
# señales distintas tenga dentro. Evita que una página con muchas
# señales débiles de la misma familia infle el score más que una con
# pocas señales pero contundentes.
TOPE_POR_FAMILIA = 60  # antes era 45

# El 'count' (cuántas veces se vio la misma señal en visitas repetidas)
# NO multiplica el peso — solo se usa como señal de persistencia con un
# bonus chico y con techo, nunca proporcional al conteo bruto.
BONUS_MAX_POR_PERSISTENCIA = 5
COUNT_PARA_BONUS_MAXIMO = 5  # a partir de esta cantidad de visitas, el bonus ya no crece


@dataclass
class ContentSignalAgregada:
    familia: str
    puntos: float
    tipos_incluidos: list


@dataclass
class ContentRiskResult:
    score: float
    tipo_dominante: Optional[str]
    detalle_por_familia: list = field(default_factory=list)

    def explicacion_legible(self) -> str:
        if not self.detalle_por_familia:
            return f"content_risk = {self.score:.1f} (sin señales de contenido)"
        lineas = [f"content_risk = {self.score:.1f}  (tipo dominante: {self.tipo_dominante})"]
        for f in self.detalle_por_familia:
            lineas.append(f"  +{f.puntos:.1f}  [{f.familia}] {', '.join(f.tipos_incluidos)}")
        return "\n".join(lineas)

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 2),
            "dominant_type": self.tipo_dominante,
            "families": [
                {"family": f.familia, "score": round(f.puntos, 2), "types": f.tipos_incluidos}
                for f in self.detalle_por_familia
            ],
        }


def _bonus_persistencia(count: int) -> float:
    """Sube un poco si la misma señal se vio en varias visitas, con techo."""
    if count <= 1:
        return 0.0
    proporcion = min(count, COUNT_PARA_BONUS_MAXIMO) / COUNT_PARA_BONUS_MAXIMO
    return proporcion * BONUS_MAX_POR_PERSISTENCIA


def calcular_content_risk(content_signals: list) -> ContentRiskResult:
    """
    content_signals: lista de dicts como los que guarda
    candidate_store.add_content_signals(), cada uno con
    {type, category, weight, count, ...}.

    'persuasion' nunca aporta si es la única familia presente — mismo
    principio que fraud_detector.py: la urgencia sola no es evidencia.
    """
    if not content_signals:
        return ContentRiskResult(score=0.0, tipo_dominante=None, detalle_por_familia=[])

    por_familia = {}
    for senal in content_signals:
        familia = senal.get("category", "desconocida")
        peso_base = senal.get("weight", 0)
        bonus = _bonus_persistencia(senal.get("count", 1))
        puntos = peso_base + bonus

        por_familia.setdefault(familia, {"puntos": 0.0, "tipos": []})
        por_familia[familia]["puntos"] += puntos
        tipo_corto = senal.get("type", "").split(":")[-1]
        if tipo_corto not in por_familia[familia]["tipos"]:
            por_familia[familia]["tipos"].append(tipo_corto)

    # Tope por familia — evita que muchas señales débiles de la misma
    # familia inflen más que pocas señales contundentes de otra.
    for familia in por_familia:
        por_familia[familia]["puntos"] = min(por_familia[familia]["puntos"], TOPE_POR_FAMILIA)

    familias_fraude = {f: d for f, d in por_familia.items() if f != "persuasion"}

    if not familias_fraude:
        # Solo hubo persuasión, sin ninguna familia de fraude real.
        return ContentRiskResult(score=0.0, tipo_dominante=None, detalle_por_familia=[])

    detalle = [
        ContentSignalAgregada(familia=f, puntos=d["puntos"], tipos_incluidos=d["tipos"])
        for f, d in familias_fraude.items()
    ]
    detalle.sort(key=lambda x: -x.puntos)

    score_total = sum(d.puntos for d in detalle)
    # Tope global también, por las dudas de que sumen varias familias a la vez
    score_total = min(score_total, 100.0)

    tipo_dominante = detalle[0].familia

    return ContentRiskResult(score=score_total, tipo_dominante=tipo_dominante, detalle_por_familia=detalle)
