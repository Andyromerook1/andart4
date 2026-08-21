# test_analysis_policy_v2.py
from risk_score import calcular_score
from content_risk_score import calcular_content_risk
from analysis_policy import decidir

# Casos originales — solo DOMAIN_RISK, sin contenido leído todavía
casos_dominio = [
    ("A. Dominio viejo, sin nada más", dict(edad_dominio_dias=200, tld="com"), 0),
    ("B. OpenPhish + dominio viejo", dict(fuente="openphish", edad_dominio_dias=800), 1),
    ("C. Dominio nuevo aislado", dict(edad_dominio_dias=3, tld="com"), 1),
    ("D. Nuevo + typosquatting + TLD (sin fuente)", dict(
        similitud_typosquatting=0.95, edad_dominio_dias=5, tld="xyz"), 2),
    ("E. Todo combinado + OpenPhish", dict(
        fuente="openphish", similitud_typosquatting=0.93,
        edad_dominio_dias=5, tld="top", tiene_contexto_pago=True), 2),
    ("F. Solo mención en blog", dict(fuente="referencia"), 0),
    ("G. CT + typosquatting + certificado nuevo", dict(
        fuente="ct_monitor", similitud_typosquatting=0.97,
        dias_desde_emision_certificado=0), 2),
    ("H. Nuevo + TLD, señales débiles acumuladas", dict(
        tld="xyz", edad_dominio_dias=10), 1),
]

print("=== CASOS DE DOMINIO (sin contenido) ===\n")
todos_ok = True
for nombre, kwargs, nivel_esperado in casos_dominio:
    domain_resultado = calcular_score(**kwargs)
    decision = decidir(domain_resultado, content_resultado=None)
    ok = "✅" if decision.nivel == nivel_esperado else "❌"
    if decision.nivel != nivel_esperado:
        todos_ok = False
    print(f"{ok} {nombre}")
    print(f"    domain_risk={decision.domain_risk:.1f} content_risk={decision.content_risk:.1f} → Nivel {decision.nivel} (esperado: {nivel_esperado})")
    print(f"    {decision.motivo}")

# Casos nuevos — combinando DOMAIN_RISK y CONTENT_RISK
print("\n=== CASOS COMBINADOS (dominio + contenido) ===\n")

content_signals_reclutamiento_fuerte = [
    {"type": "reclutamiento:pago_ingreso", "category": "reclutamiento", "weight": 25, "count": 1},
    {"type": "reclutamiento:comision_referidos", "category": "reclutamiento", "weight": 25, "count": 1},
]

content_signals_debiles = [
    {"type": "persuasion:urgencia", "category": "persuasion", "weight": 8, "count": 1},
]

casos_combinados = [
    (
        "I. Dominio viejo/tranquilo + contenido de fraude fuerte (tu ejemplo del análisis)",
        dict(edad_dominio_dias=1500, tld="com"),
        content_signals_reclutamiento_fuerte,
        2,
    ),
    (
        "J. Dominio muy sospechoso + SIN contenido leído todavía (recién descubierto)",
        dict(fuente="openphish", similitud_typosquatting=0.95, edad_dominio_dias=3, tld="xyz"),
        [],
        2,
    ),
    (
        "K. Dominio tranquilo + contenido con solo persuasión débil (no debería subir)",
        dict(edad_dominio_dias=1500, tld="com"),
        content_signals_debiles,
        0,
    ),
]

for nombre, kwargs_dominio, content_signals, nivel_esperado in casos_combinados:
    domain_resultado = calcular_score(**kwargs_dominio)
    content_resultado = calcular_content_risk(content_signals)
    decision = decidir(domain_resultado, content_resultado)
    ok = "✅" if decision.nivel == nivel_esperado else "❌"
    if decision.nivel != nivel_esperado:
        todos_ok = False
    print(f"{ok} {nombre}")
    print(f"    domain_risk={decision.domain_risk:.1f} content_risk={decision.content_risk:.1f} "
          f"(decisivo: {decision.dimension_decisiva}) → Nivel {decision.nivel} (esperado: {nivel_esperado})")
    print(f"    {decision.motivo}")

print("\n" + ("✅ TODOS los casos coinciden con lo acordado" if todos_ok else "❌ Hay discrepancias — revisar"))
