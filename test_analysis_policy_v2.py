# test_analysis_policy_v2.py
from risk_score import calcular_score
from analysis_policy import decidir

casos = [
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

todos_ok = True
for nombre, kwargs, nivel_esperado in casos:
    resultado = calcular_score(**kwargs)
    decision = decidir(resultado)
    ok = "✅" if decision.nivel == nivel_esperado else "❌"
    if decision.nivel != nivel_esperado:
        todos_ok = False
    print(f"{ok} {nombre}")
    print(f"    score={decision.score_efectivo:.1f} → Nivel {decision.nivel} (esperado: {nivel_esperado})")
    print(f"    {decision.motivo}")

print("\n" + ("✅ TODOS los casos coinciden con lo acordado" if todos_ok else "❌ Hay discrepancias — revisar"))
