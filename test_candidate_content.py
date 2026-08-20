# test_candidate_content.py
from candidate_store import CandidateStore
from fraud_detector import FraudDetector

store = CandidateStore(ruta="candidatos_test_content.json")
detector = FraudDetector()

dominio = "supuesto-trabajo-desde-casa.xyz"
texto_pagina = """
    Sumate a nuestro equipo. Ingreso inicial $100.000.
    Por cada persona que invites ganás $30.000.
"""

print("=== Primera visita a la página ===")
resultado = detector.analizar(texto_pagina)
c = store.add_content_signals(dominio, resultado, origen_url=f"https://{dominio}/oportunidad")
print(f"content_type_posible: {c['content_type_posible']}")
for s in c["content_signals"]:
    print(f"  {s['type']} (count={s['count']}) → \"{s['fragment'][:50]}\"")

print("\n=== Segunda visita, MISMO texto (no debería duplicar) ===")
resultado2 = detector.analizar(texto_pagina)
c = store.add_content_signals(dominio, resultado2, origen_url=f"https://{dominio}/oportunidad")
for s in c["content_signals"]:
    print(f"  {s['type']} (count={s['count']}) → \"{s['fragment'][:50]}\"")

store.save()
