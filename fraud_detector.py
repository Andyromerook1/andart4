# fraud_detector.py
"""
Detector de señales de fraude en TEXTO — no en dominios, no en HTML
estructurado. No sabe de dónde vino el texto ni decide nada por sí
solo: identifica qué señales aparecen y con qué fuerza.

Dos tipos de categoría, con roles distintos:
- Familias de fraude (reclutamiento, inversion, ...): señales propias
  de cada tipo de estafa. Pueden decidir el 'tipo_posible'.
- 'persuasion': señales transversales (urgencia, presión social, etc.)
  que aparecen en marketing legítimo TANTO como en fraude. NUNCA deciden
  el tipo por sí solas — solo refuerzan una familia que ya tiene señales
  propias. Urgencia sola no es fraude.
"""
import re
from dataclasses import dataclass, field

FAMILIAS_DE_FRAUDE = {"reclutamiento", "inversion"}  # se amplía más adelante
CATEGORIA_TRANSVERSAL = "persuasion"


@dataclass
class SenalFraude:
    categoria: str
    tipo: str
    fragmento: str
    peso: float


@dataclass
class ResultadoFraude:
    tipo_posible: str
    senales: list = field(default_factory=list)

    def explicacion_legible(self) -> str:
        if not self.senales:
            return f"tipo posible: {self.tipo_posible} (sin señales)"
        lineas = [f"tipo posible: {self.tipo_posible}"]
        por_categoria = {}
        for s in self.senales:
            por_categoria.setdefault(s.categoria, []).append(s)
        for categoria, senales in por_categoria.items():
            lineas.append(f"  [{categoria}]")
            for s in senales:
                lineas.append(f"    {s.tipo}: \"{s.fragmento[:60]}\"")
        return "\n".join(lineas)

    def as_dict(self) -> dict:
        return {
            "tipo_posible": self.tipo_posible,
            "signals": [
                {"category": s.categoria, "type": s.tipo, "fragment": s.fragmento, "weight": s.peso}
                for s in self.senales
            ],
        }


# =====================================================
# FAMILIA: RECLUTAMIENTO / PIRAMIDAL
# =====================================================
SENALES_RECLUTAMIENTO = [
    ("pago_ingreso", 25, [
        r'\b(pag[aá]|deposit[aá]|invert[íi])\w*\s+(\$?\s*[\d.,]+|dinero|plata)\s+(para|y)\s+(ingres|entr|un[íi]rte|form)',
        r'\binversi[oó]n\s+inicial\b',
        r'\bcuota\s+de\s+ingreso\b',
        r'\bingreso\s+inicial\s+(de\s+)?\$?\s*[\d.,]+',
        r'\b(costo|precio|valor)\s+de\s+(ingreso|entrada|inscripci[oó]n)\b',
    ]),
    ("comision_referidos", 25, [
        r'\bpor\s+cada\s+persona\s+que\s+(invit|traig|refier)',
        r'\bcomisi[oó]n\s+por\s+(referido|invitad|afiliad)',
        r'\bgan[aá]s?\s+\$?\s*[\d.,]+\s+por\s+cada\b',
    ]),
    ("reclutamiento_equipo", 15, [
        r'\bsum[aá]te\s+a\s+(nuestro|mi|el)\s+equipo\b',
        r'\bform[aá]\s+tu\s+(propio\s+)?equipo\b',
        r'\bbusc[oa]mos\s+(gente|personas)\s+(emprendedor|con\s+ganas)',
        r'\bs[eé]\s+tu\s+propio\s+jefe\b',
    ]),
    ("promesa_ingresos_pasivos", 20, [
        r'\bingresos?\s+(pasivo|extra|desde\s+(tu\s+)?(casa|celular))\b',
        r'\bganan?\s+dinero\s+sin\s+(hacer\s+nada|esfuerzo|salir)',
        r'\blibertad\s+financiera\b',
    ]),
]

# =====================================================
# FAMILIA: INVERSIÓN FRAUDULENTA
# =====================================================
SENALES_INVERSION = [
    ("rentabilidad_garantizada", 30, [
        r'\b(rentabilidad|ganancia|retorno)\s+(garantizad|asegurad)',
        r'\b\d{1,3}\s*%\s+(semanal|diari|mensual)\s+(garantizad)?',
        r'\bsin\s+riesgo\b.*\b(invert|ganancia)',
    ]),
    ("retorno_extraordinario", 25, [
        r'\bduplic[aá]\s+tu\s+(inversi[oó]n|dinero|capital)',
        r'\btriplic[aá]\s+tu\s+(inversi[oó]n|dinero|capital)',
        r'\bganancias?\s+extraordinari',
    ]),
    ("urgencia_deposito", 15, [
        r'\b(deposit[aá]|invert[íi])\w*\s+(hoy|ahora|ya)\b',
    ]),
]

# =====================================================
# TRANSVERSAL: PERSUASIÓN (nunca decide el tipo por sí sola)
# =====================================================
SENALES_PERSUASION = [
    ("urgencia", 8, [
        r'\b[uú]ltimos?\s+cupos?\b',
        r'\bantes\s+que\s+se\s+acabe\b',
        r'\bsolo\s+por\s+hoy\b',
        r'\b[uú]ltimas?\s+unidades\b',
        r'\boferta\s+por\s+tiempo\s+limitado\b',
    ]),
]

# Peso mínimo que debe acumular una FAMILIA DE FRAUDE (sin contar
# persuasión) para que el resultado se declare con esa categoría.
UMBRAL_MINIMO_FAMILIA = 15


class FraudDetector:
    def __init__(self):
        self._compilado = {}
        for nombre, definicion in (
            ("reclutamiento", SENALES_RECLUTAMIENTO),
            ("inversion", SENALES_INVERSION),
            (CATEGORIA_TRANSVERSAL, SENALES_PERSUASION),
        ):
            self._compilado[nombre] = [
                (tipo, peso, [re.compile(p, re.IGNORECASE) for p in patrones])
                for tipo, peso, patrones in definicion
            ]

    def _buscar_categoria(self, texto: str, categoria: str) -> list:
        senales = []
        for tipo, peso, regexes in self._compilado.get(categoria, []):
            for regex in regexes:
                match = regex.search(texto)
                if match:
                    senales.append(SenalFraude(
                        categoria=categoria, tipo=tipo,
                        fragmento=match.group(0), peso=peso,
                    ))
                    break
        return senales

    def analizar(self, texto: str) -> ResultadoFraude:
        if not texto or not texto.strip():
            return ResultadoFraude(tipo_posible="ninguno", senales=[])

        todas = []
        for familia in FAMILIAS_DE_FRAUDE:
            todas.extend(self._buscar_categoria(texto, familia))
        senales_persuasion = self._buscar_categoria(texto, CATEGORIA_TRANSVERSAL)

        # Persuasión SOLA (sin ninguna señal de una familia de fraude
        # real) nunca produce un tipo_posible — es ruido de marketing.
        if not todas:
            if senales_persuasion:
                return ResultadoFraude(tipo_posible="ninguno", senales=senales_persuasion)
            return ResultadoFraude(tipo_posible="ninguno", senales=[])

        pesos_por_familia = {}
        for s in todas:
            pesos_por_familia[s.categoria] = pesos_por_familia.get(s.categoria, 0) + s.peso
        familia_dominante = max(pesos_por_familia, key=pesos_por_familia.get)
        peso_dominante = pesos_por_familia[familia_dominante]

        # Solo entonces persuasión se agrega como refuerzo del resultado.
        todas_con_persuasion = todas + senales_persuasion

        if peso_dominante < UMBRAL_MINIMO_FAMILIA:
            familia_dominante = f"{familia_dominante} (baja confianza)"

        return ResultadoFraude(tipo_posible=familia_dominante, senales=todas_con_persuasion)
