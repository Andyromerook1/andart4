# fraud_detector.py
"""
Detector de señales de fraude en TEXTO — no en dominios, no en HTML
estructurado. No sabe de dónde vino el texto (web, TikTok, Telegram,
WhatsApp) ni decide nada por sí solo: solo identifica qué señales de
fraude aparecen y con qué fuerza, igual que risk_score.py hace con
dominios.

Empieza con UNA familia (reclutamiento/piramidal) para poder calibrar
bien antes de sumar las demás (inversión, crypto, ecommerce, extorsión).
La estructura ya prevé esas familias, pero no se implementan todavía.
"""
import re
from dataclasses import dataclass, field


@dataclass
class SenalFraude:
    categoria: str       # familia (ej: "reclutamiento")
    tipo: str             # señal puntual (ej: "pago_ingreso")
    fragmento: str        # el texto que disparó la señal (recortado)
    peso: float


@dataclass
class ResultadoFraude:
    tipo_posible: str
    senales: list = field(default_factory=list)

    def explicacion_legible(self) -> str:
        if not self.senales:
            return f"tipo posible: {self.tipo_posible} (sin señales)"
        lineas = [f"tipo posible: {self.tipo_posible}"]
        for s in self.senales:
            lineas.append(f"  [{s.categoria}] {s.tipo}: \"{s.fragmento[:60]}\"")
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
# Cada señal es un patrón de regex + un peso. El peso no decide nada acá
# (eso es trabajo de un futuro content_risk_score.py) — solo indica
# cuánta fuerza tiene ESTA señal puntual dentro de su categoría.
SENALES_RECLUTAMIENTO = [
    ("pago_ingreso", 25, [
        r'\b(pag[aá]|deposit[aá]|invert[íi])\w*\s+(\$?\s*[\d.,]+|dinero|plata)\s+(para|y)\s+(ingres|entr|un[íi]rte|form)',
        r'\binversi[oó]n\s+inicial\b',
        r'\bcuota\s+de\s+ingreso\b',
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
    ("urgencia_reclutamiento", 10, [
        r'\b[uú]ltimos?\s+cupos?\b',
        r'\bantes\s+que\s+se\s+acabe\b',
        r'\bsolo\s+por\s+hoy\b.*\b(equipo|red|negocio)\b',
    ]),
]


class FraudDetector:
    def __init__(self):
        self._compilado = {
            "reclutamiento": [
                (tipo, peso, [re.compile(p, re.IGNORECASE) for p in patrones])
                for tipo, peso, patrones in SENALES_RECLUTAMIENTO
            ]
        }

    def _buscar_familia(self, texto: str, categoria: str) -> list:
        senales = []
        for tipo, peso, regexes in self._compilado.get(categoria, []):
            for regex in regexes:
                match = regex.search(texto)
                if match:
                    senales.append(SenalFraude(
                        categoria=categoria, tipo=tipo,
                        fragmento=match.group(0), peso=peso,
                    ))
                    break  # una vez que un patrón de este tipo matcheó, no hace falta repetir
        return senales

    def analizar(self, texto: str) -> ResultadoFraude:
        """
        Analiza un texto y devuelve las señales de fraude detectadas,
        sin veredicto. La categoría con más señales/peso se sugiere como
        'tipo_posible', pero es solo orientativo.
        """
        if not texto or not texto.strip():
            return ResultadoFraude(tipo_posible="ninguno", senales=[])

        todas = []
        todas.extend(self._buscar_familia(texto, "reclutamiento"))

        if not todas:
            return ResultadoFraude(tipo_posible="ninguno", senales=[])

        # Categoría dominante = la que acumula más peso total
        pesos_por_categoria = {}
        for s in todas:
            pesos_por_categoria[s.categoria] = pesos_por_categoria.get(s.categoria, 0) + s.peso
        categoria_dominante = max(pesos_por_categoria, key=pesos_por_categoria.get)

        return ResultadoFraude(tipo_posible=categoria_dominante, senales=todas)
