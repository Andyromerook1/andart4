# test_risk_score.py — casos extremos, correr suelto: python test_risk_score.py
from risk_score import calcular_score

casos = [
    ("Dominio legítimo enorme (google.com)", dict(
        similitud_typosquatting=0.0, edad_dominio_dias=9000,
        tld="com", fuente="referencia",
    )),
    ("Phishing nuevo, nadie lo reportó todavía", dict(
        similitud_typosquatting=0.97, edad_dominio_dias=3,
        tld="xyz", fuente="ct_monitor",
        dias_desde_emision_certificado=1, tiene_contexto_pago=True,
    )),
    ("Typosquatting pero dominio viejo (tu ejemplo)", dict(
        similitud_typosquatting=0.92, edad_dominio_dias=240,
        tld="com", fuente="desconocida",
    )),
    ("Candidato de feed de threat intel confirmado", dict(
        similitud_typosquatting=0.60, edad_dominio_dias=15,
        tld="top", fuente="openphish", tiene_contexto_pago=True,
    )),
    ("Mención en artículo de seguridad (Krebs, etc.)", dict(
        similitud_typosquatting=None, edad_dominio_dias=None,
        tld=None, fuente="referencia",
    )),
    ("Dominio nuevo pero sin ninguna otra señal", dict(
        similitud_typosquatting=None, edad_dominio_dias=2,
        tld="com", fuente="desconocida",
    )),
]

for nombre, kwargs in casos:
    resultado = calcular_score(**kwargs)
    print(f"\n{'='*60}\n{nombre}\n{'='*60}")
    print(resultado.explicacion_legible())
