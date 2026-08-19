# test_analysis_policy.py
"""
Casos de prueba para analysis_policy.py — corridos ANTES de fijar
ningún umbral, para poder discutir qué decisión esperaríamos en cada
uno antes de que el código decida por nosotros.

Reutiliza risk_score.py tal cual (ya aprobado, sin tocar).
"""
from risk_score import calcular_score

casos = [
    # (nombre, kwargs para calcular_score, decisión esperada según NOSOTROS,
    #  no según código — esto es la referencia para calibrar la política)
    ("A. Score bajo, sin evidencia externa (candidato normal)", dict(
        edad_dominio_dias=200, tld="com",
    ), "Nivel 0 — descartar"),

    ("B. Score bajo, PERO con feed confirmado", dict(
        fuente="openphish", edad_dominio_dias=800,
    ), "¿Nivel 1 igual, por la fuente? — A DISCUTIR"),

    ("C. Score medio, típico dominio nuevo aislado", dict(
        edad_dominio_dias=3, tld="com",
    ), "Nivel 1 — vale la pena mirar el HTML"),

    ("D. Score alto, solo heurística (sin fuente externa)", dict(
        similitud_typosquatting=0.95, edad_dominio_dias=5, tld="xyz",
    ), "Nivel 1 o 2 — A DISCUTIR cuánto pesa 'sin confirmación externa'"),

    ("E. Score alto Y con feed confirmado (el caso ideal)", dict(
        fuente="openphish", similitud_typosquatting=0.93,
        edad_dominio_dias=5, tld="top", tiene_contexto_pago=True,
    ), "Nivel 2 directo — evidencia + heurística coinciden"),

    ("F. Solo mención en blog de referencia, nada más", dict(
        fuente="referencia",
    ), "Nivel 0 — no amerita ni mirar"),

    ("G. Certificate Transparency + typosquatting fuerte, recién nacido", dict(
        fuente="ct_monitor", similitud_typosquatting=0.97,
        dias_desde_emision_certificado=0,
    ), "Nivel 1 prioritario — A DISCUTIR si merece Nivel 2 directo"),

    ("H. Score técnicamente alto por acumulación de señales débiles", dict(
        tld="xyz", edad_dominio_dias=10,
    ), "Nivel 1 — ninguna señal individual es fuerte, hay que mirar"),
]

for nombre, kwargs, esperado in casos:
    resultado = calcular_score(**kwargs)
    print(f"\n{'='*70}\n{nombre}\n{'='*70}")
    print(resultado.explicacion_legible())
    print(f"\n  → Decisión esperada (nuestra referencia): {esperado}")
