# test_candidate_store.py
from candidate_store import CandidateStore

store = CandidateStore(ruta="candidatos_test.json")

dominio = "paypa1-login.xyz"

print("=== Día 1: CT lo encuentra ===")
store.add_signal(dominio, tipo="deteccion", valor="ct_monitor",
                  discovered_by="ct_monitor",
                  campos_score={"dias_desde_emision_certificado": 0, "tld": "xyz"})
c = store.recalculate(dominio)
print(f"discovered_by={c['discovered_by']}  score={c['score']:.1f}  nivel={c['level']}")

print("\n=== Día 2: GitHub lo encuentra también ===")
store.add_signal(dominio, tipo="deteccion", valor="github_hunter",
                  discovered_by="github_hunter", campos_score={})
c = store.recalculate(dominio)
print(f"discovered_by={c['discovered_by']}  score={c['score']:.1f}  nivel={c['level']}")

print("\n=== Día 3: OpenPhish lo confirma ===")
store.add_signal(dominio, tipo="deteccion", valor="openphish",
                  discovered_by="openphish", campos_score={})
c = store.recalculate(dominio)
print(f"discovered_by={c['discovered_by']}  score={c['score']:.1f}  nivel={c['level']}")
print("\nDetalle de señales del score:")
for s in c["score_signals"]:
    print(f"  {s['description']}: {s['score']}")

store.save()
