# risk_score.py
"""
Motor de scoring de riesgo — PURO, sin efectos secundarios.
"""
from dataclasses import dataclass, field
from typing import Optional, Union, List


PESOS = {
    "typosquatting_max": 35,
    "typosquatting_umbral": 0.85,
    "typosquatting_curva_exponente": 0.5,

    "edad_dominio_max": 30,
    "edad_dominio_dias_maximo": 30,
    "edad_dominio_dias_neutro": 180,
    "edad_dominio_min_negativo": -3,
    "edad_dominio_dias_min_negativo": 730,

    "tld_sospechoso": 15,

    "fuentes": {
        "openphish": 25,
        "urlhaus": 25,
        "phishstats": 20,
        "ct_monitor": 15,
        "github_hunter": 15,
        "dork_manual": 10,
        "referencia": 5,
        "desconocida": 0,
    },

    "señal_pago_o_wallet": 20,
    "certificado_recien_emitido_dias": 7,
    "certificado_recien_emitido_puntos": 15,
}

TLDS_SOSPECHOSOS = {
    "top", "xyz", "icu", "tk", "ml", "ga", "cf", "club",
    "online", "site", "tech", "store", "info", "biz", "live", "vip"
}


@dataclass
class Signal:
    tipo: str
    valor_original: object
    puntos: float
    descripcion: str


@dataclass
class RiskScoreResult:
    score: float
    signals: list = field(default_factory=list)

    def explicacion_legible(self) -> str:
        if not self.signals:
            return f"score = {self.score:.1f} (sin señales)"
        lineas = [f"score = {self.score:.1f}"]
        for s in sorted(self.signals, key=lambda x: -abs(x.puntos)):
            signo = "+" if s.puntos >= 0 else ""
            lineas.append(f"  {signo}{s.puntos:.1f}  {s.descripcion}")
        return "\n".join(lineas)

    def as_dict(self) -> dict:
        return {
            "score": round(self.score, 2),
            "signals": [
                {
                    "type": s.tipo,
                    "value": s.valor_original,
                    "score": round(s.puntos, 2),
                    "description": s.descripcion,
                }
                for s in self.signals
            ],
        }


def _curva_typosquatting(similitud: Optional[float]) -> Optional[Signal]:
    if similitud is None or similitud < PESOS["typosquatting_umbral"]:
        return None
    rango = 1.0 - PESOS["typosquatting_umbral"]
    proporcion_lineal = (similitud - PESOS["typosquatting_umbral"]) / rango if rango > 0 else 1.0
    proporcion_ajustada = proporcion_lineal ** PESOS["typosquatting_curva_exponente"]
    puntos = proporcion_ajustada * PESOS["typosquatting_max"]
    return Signal(
        tipo="typosquatting", valor_original=similitud, puntos=puntos,
        descripcion=f"typosquatting (similitud {similitud:.2%})",
    )


def _curva_edad_dominio(edad_dias: Optional[int]) -> Optional[Signal]:
    if edad_dias is None:
        return None

    if edad_dias <= PESOS["edad_dominio_dias_maximo"]:
        puntos = PESOS["edad_dominio_max"]
    elif edad_dias >= PESOS["edad_dominio_dias_min_negativo"]:
        puntos = PESOS["edad_dominio_min_negativo"]
    elif edad_dias <= PESOS["edad_dominio_dias_neutro"]:
        rango = PESOS["edad_dominio_dias_neutro"] - PESOS["edad_dominio_dias_maximo"]
        proporcion = (edad_dias - PESOS["edad_dominio_dias_maximo"]) / rango
        puntos = PESOS["edad_dominio_max"] * (1 - proporcion)
    else:
        rango = PESOS["edad_dominio_dias_min_negativo"] - PESOS["edad_dominio_dias_neutro"]
        proporcion = (edad_dias - PESOS["edad_dominio_dias_neutro"]) / rango
        puntos = PESOS["edad_dominio_min_negativo"] * proporcion

    return Signal(
        tipo="domain_age", valor_original=edad_dias, puntos=puntos,
        descripcion=f"dominio de {edad_dias} días",
    )


def _curva_tld(tld: Optional[str]) -> Optional[Signal]:
    if not tld:
        return None
    tld = tld.lower().lstrip(".")
    if tld not in TLDS_SOSPECHOSOS:
        return None
    return Signal(
        tipo="tld_sospechoso", valor_original=tld, puntos=PESOS["tld_sospechoso"],
        descripcion=f"TLD de bajo costo (.{tld})",
    )


def _curva_fuente(fuente: Optional[Union[str, List[str]]]) -> Optional[Signal]:
    if not fuente:
        return None

    lista_fuentes = [fuente] if isinstance(fuente, str) else list(fuente)
    lista_fuentes = [f for f in lista_fuentes if f]
    if not lista_fuentes:
        return None

    pesos_por_fuente = {
        f: PESOS["fuentes"].get(f, PESOS["fuentes"]["desconocida"])
        for f in lista_fuentes
    }
    mejor_fuente = max(pesos_por_fuente, key=pesos_por_fuente.get)
    puntos = pesos_por_fuente[mejor_fuente]
    if puntos == 0:
        return None

    otras = [f for f in lista_fuentes if f != mejor_fuente]
    descripcion = f"descubierto vía {mejor_fuente}"
    if otras:
        descripcion += f" (también: {', '.join(otras)})"

    return Signal(
        tipo="source", valor_original=lista_fuentes, puntos=puntos,
        descripcion=descripcion,
    )


def _curva_certificado_reciente(dias_desde_emision: Optional[int]) -> Optional[Signal]:
    if dias_desde_emision is None:
        return None
    if dias_desde_emision > PESOS["certificado_recien_emitido_dias"]:
        return None
    return Signal(
        tipo="certificate_age", valor_original=dias_desde_emision,
        puntos=PESOS["certificado_recien_emitido_puntos"],
        descripcion=f"certificado SSL emitido hace {dias_desde_emision} días",
    )


def _curva_contexto_pago(tiene_contexto_pago: Optional[bool]) -> Optional[Signal]:
    if not tiene_contexto_pago:
        return None
    return Signal(
        tipo="payment_context", valor_original=True, puntos=PESOS["señal_pago_o_wallet"],
        descripcion="menciona wallet/CBU/login/pago en el contenido",
    )


def calcular_score(
    similitud_typosquatting: Optional[float] = None,
    edad_dominio_dias: Optional[int] = None,
    tld: Optional[str] = None,
    fuente: Optional[Union[str, List[str]]] = None,
    dias_desde_emision_certificado: Optional[int] = None,
    tiene_contexto_pago: Optional[bool] = None,
) -> RiskScoreResult:
    signals = []
    for resultado in (
        _curva_typosquatting(similitud_typosquatting),
        _curva_edad_dominio(edad_dominio_dias),
        _curva_tld(tld),
        _curva_fuente(fuente),
        _curva_certificado_reciente(dias_desde_emision_certificado),
        _curva_contexto_pago(tiene_contexto_pago),
    ):
        if resultado is not None:
            signals.append(resultado)

    score_total = sum(s.puntos for s in signals)
    return RiskScoreResult(score=score_total, signals=signals)
