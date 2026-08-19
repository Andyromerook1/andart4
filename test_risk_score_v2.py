# test_risk_score_v2.py
from risk_score import calcular_score

casos = [
    ("1. Dominio viejo + typosquatting fuerte", dict(
        similitud_typosquatting=0.97, edad_dominio_dias=800,
    )),
    ("2. Dominio nuevo + nombre normal (sin typosquatting)", dict(
        edad_dominio_dias=3, tld="com",
    )),
    ("3. Dominio nuevo + TLD barato, sin marca imitada", dict(
        edad_dominio_dias=5, tld="top",
    )),
    ("4. Typosquatting + TLD sospechoso", dict(
        similitud_typosquatting=0.93, tld="xyz",
    )),
    ("5. Typosquatting + contexto de pago/login", dict(
        similitud_typosquatting=0.90, tiene_contexto_pago=True,
    )),
    ("6. Dominio viejo + login/wallet (posible cuenta comprometida)", dict(
        edad_dominio_dias=900, tiene_contexto_pago=True,
    )),
    ("7. Confirmado por feed + dominio viejo", dict(
        fuente="openphish", edad_dominio_dias=800,
    )),
    ("8. CT monitor + typosquatting", dict(
        fuente="ct_monitor", similitud_typosquatting=0.95,
    )),
    ("9. CT monitor + TLD sospechoso, sin marca clara", dict(
        fuente="ct_monitor", tld="top",
    )),
    ("10. Referencia (blog) + dominio con TLD sospechoso", dict(
        fuente="referencia", tld="xyz", edad_dominio_dias=10,
    )),
    ("11. CONTRADICTORIO: dominio muy viejo + similitud extrema", dict(
        edad_dominio_dias=2000, similitud_typosquatting=0.99,
    )),
    ("12. Solo TLD sospechoso, nada más", dict(
        tld="xyz",
    )),
    ("13. Solo fuente=openphish, nada más", dict(
        fuente="openphish",
    )),
    ("14. Typosquatting justo en el umbral (0.85)", dict(
        similitud_typosquatting=0.85,
    )),
    ("15. TECHO: todas las señales al máximo a la vez", dict(
        similitud_typosquatting=1.0, edad_dominio_dias=0, tld="xyz",
        fuente="openphish", dias_desde_emision_certificado=0,
        tiene_contexto_pago=True,
    )),
]

for nombre, kwargs in casos:
    resultado = calcular_score(**kwargs)
    print(f"\n{'='*60}\n{nombre}\n{'='*60}")
    print(resultado.explicacion_legible())
