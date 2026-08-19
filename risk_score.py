# risk_score.py
"""
Motor de scoring de riesgo — PURO, sin efectos secundarios.

No hace HTTP, no consulta DNS/RDAP, no toca archivos, no decide niveles de
crawling. Solo recibe señales ya calculadas por otros módulos
(phishing_detector, whois_lookup, ct_monitor, etc.) y devuelve un score
explicable: CUÁNTO aportó cada señal y POR QUÉ.

La decisión de "qué nivel de análisis merece esto" es de OTRO módulo,
que todavía no existe — este archivo no sabe qué es un "Nivel 1" o
"Nivel 2", solo calcula puntaje.

Todas las curvas son funciones independientes y configurables — cambiar
una no afecta a las demás. Los pesos son PROVISIONALES: existen para
poder probar el sistema con casos sintéticos, no son la versión final.
"""
from dataclasses import dataclass, field
from typing import Optional


# =====================================================
# PESOS — provisionales, ajustables sin tocar la lógica
# =====================================================
PESOS = {
    "typosquatting_max": 35,       # tope de puntos por similitud de marca
    "typosquatting_umbral": 0.85,  # por debajo de esto, no suma nada

    "edad_dominio_max": 30,        # tope de puntos por dominio recién creado
    "edad_dominio_dias_maximo": 30,   # a partir de acá, la señal ya no suma
    "edad_dominio_dias_neutro": 180,  # a partir de acá, empieza a restar
    "edad_dominio_min_negativo": -10, # tope de resta por dominio muy viejo
    "edad_dominio_dias_min_negativo": 730,  # 2 años: resta máxima

    "tld_sospechoso": 15,          # TLD barato (.xyz, .top, etc.)

    "fuentes": {
        # procedencia != veredicto — esto es confianza en la fuente,
        # no una afirmación de que el dominio sea malicioso
        "openphish": 25,
        "urlhaus": 25,
        "phishstats": 20,
        "ct_monitor": 15,
        "github_hunter": 15,
        "dork_manual": 10,
        "referencia": 5,       # mención en un artículo/blog de seguridad
        "desconocida": 0,
    },

    "señal_pago_o_wallet": 20,     # menciona wallet/CBU/login/pago en el contexto
    "certificado_recien_emitido_dias": 7,   # certificado emitido hace <7 días
    "certificado_recien_emitido_puntos": 15,
}

TLDS_SOSPECHOSOS = {
    "top", "xyz", "icu", "tk", "ml", "ga", "cf", "club",
    "online", "site", "tech", "store", "info", "biz", "live", "vip"
}


@dataclass
class Signal:
    """Una señal individual que contribuyó al score."""
    tipo: str
    valor_original: object   # el dato crudo, SIN redondear (ej: 0.9734, no 0.97)
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


# =====================================================
# CURVAS — cada señal es una función independiente
# =====================================================

def _curva_typosquatting(similitud: Optional[float]) -> Optional[Signal]:
    """
    similitud viene de phishing_detector.py, ya es 0.0–1.0.
    Por debajo del umbral no aporta nada (no es señal, es ruido).
    Escala linealmente desde el umbral hasta 1.0.
    """
    if similitud is None or similitud < PESOS["typosquatting_umbral"]:
        return None
    rango = 1.0 - PESOS["typosquatting_umbral"]
    proporcion = (similitud - PESOS["typosquatting_umbral"]) / rango if rango > 0 else 1.0
    puntos = proporcion * PESOS["typosquatting_max"]
    return Signal(
        tipo="typosquatting",
        valor_original=similitud,
        puntos=puntos,
        descripcion=f"typosquatting (similitud {similitud:.2%})",
    )


def _curva_edad_dominio(edad_dias: Optional[int]) -> Optional[Signal]:
    """
    Dominios muy nuevos suman fuerte. A partir de cierta edad, la señal
    se vuelve neutra, y dominios muy viejos restan un poco (nunca mucho:
    la antigüedad es una señal débil de "esto lleva tiempo existiendo",
    no una prueba de inocencia).
    """
    if edad_dias is None:
        return None

    if edad_dias <= PESOS["edad_dominio_dias_maximo"]:
        puntos = PESOS["edad_dominio_max"]
    elif edad_dias >= PESOS["edad_dominio_dias_min_negativo"]:
        puntos = PESOS["edad_dominio_min_negativo"]
    elif edad_dias <= PESOS["edad_dominio_dias_neutro"]:
        # entre "nuevo" y "neutro": decae de max a 0
        rango = PESOS["edad_dominio_dias_neutro"] - PESOS["edad_dominio_dias_maximo"]
        proporcion = (edad_dias - PESOS["edad_dominio_dias_maximo"]) / rango
        puntos = PESOS["edad_dominio_max"] * (1 - proporcion)
    else:
        # entre "neutro" y "muy viejo": decae de 0 a negativo
        rango = PESOS["edad_dominio_dias_min_negativo"] - PESOS["edad_dominio_dias_neutro"]
        proporcion = (edad_dias - PESOS["edad_dominio_dias_neutro"]) / rango
        puntos = PESOS["edad_dominio_min_negativo"] * proporcion

    return Signal(
        tipo="domain_age",
        valor_original=edad_dias,
        puntos=puntos,
        descripcion=f"dominio de {edad_dias} días",
    )


def _curva_tld(tld: Optional[str]) -> Optional[Signal]:
    if not tld:
        return None
    tld = tld.lower().lstrip(".")
    if tld not in TLDS_SOSPECHOSOS:
        return None
    return Signal(
        tipo="tld_sospechoso",
        valor_original=tld,
        puntos=PESOS["tld_sospechoso"],
        descripcion=f"TLD de bajo costo (.{tld})",
    )


def _curva_fuente(fuente: Optional[str]) -> Optional[Signal]:
    if not fuente:
        return None
    puntos = PESOS["fuentes"].get(fuente, PESOS["fuentes"]["desconocida"])
    if puntos == 0:
        return None
    return Signal(
        tipo="source",
        valor_original=fuente,
        puntos=puntos,
        descripcion=f"descubierto vía {fuente}",
    )


def _curva_certificado_reciente(dias_desde_emision: Optional[int]) -> Optional[Signal]:
    if dias_desde_emision is None:
        return None
    if dias_desde_emision > PESOS["certificado_recien_emitido_dias"]:
        return None
    return Signal(
        tipo="certificate_age",
        valor_original=dias_desde_emision,
        puntos=PESOS["certificado_recien_emitido_puntos"],
        descripcion=f"certificado SSL emitido hace {dias_desde_emision} días",
    )


def _curva_contexto_pago(tiene_contexto_pago: Optional[bool]) -> Optional[Signal]:
    if not tiene_contexto_pago:
        return None
    return Signal(
        tipo="payment_context",
        valor_original=True,
        puntos=PESOS["señal_pago_o_wallet"],
        descripcion="menciona wallet/CBU/login/pago en el contenido",
    )


# =====================================================
# FUNCIÓN PRINCIPAL — pura, sin efectos secundarios
# =====================================================

def calcular_score(
    similitud_typosquatting: Optional[float] = None,
    edad_dominio_dias: Optional[int] = None,
    tld: Optional[str] = None,
    fuente: Optional[str] = None,
    dias_desde_emision_certificado: Optional[int] = None,
    tiene_contexto_pago: Optional[bool] = None,
) -> RiskScoreResult:
    """
    Todas las entradas son opcionales — un candidate puede tener solo
    algunas señales disponibles (ej: recién descubierto por CT, todavía
    sin visitar, así que no hay contexto_pago todavía).

    Ninguna entrada faltante penaliza: simplemente esa señal no aporta
    puntos porque no hay dato, no porque se asuma "inocente".
    """
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
