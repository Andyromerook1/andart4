# test_enlaces_dependencias.py
"""
Prueba controlada de la clasificación interno vs. dependencia,
replicando el árbol de ejemplo que definimos:

pagina ejemplo.com
├── /login                 → SEGUIR
├── /contacto              → SEGUIR
├── cdn.jsdelivr.net       → NO SEGUIR (dependencia: script)
├── googletagmanager.com   → NO SEGUIR (dependencia: script)
├── facebook.net           → NO SEGUIR (dependencia: script)
└── otro-sitio.xyz         → registrar, NO seguir (dependencia: link_externo)
"""
from rastreador import Rastreador
from candidate_store import CandidateStore

html_prueba = """
<html><body>
    <a href="/login">Iniciar sesión</a>
    <a href="/contacto">Contacto</a>
    <a href="https://otro-sitio.xyz/pagina">Visitar otro sitio</a>
    <script src="https://cdn.jsdelivr.net/algo.js"></script>
    <script src="https://www.googletagmanager.com/gtag.js"></script>
    <script src="https://connect.facebook.net/sdk.js"></script>
    <img src="https://cdn.jsdelivr.net/logo.png">
</body></html>
"""

url_base = "https://ejemplo.com/inicio"

r = Rastreador(semilla=[url_base], limite=1)
r.candidate_store = CandidateStore(ruta="candidatos_test_enlaces.json")  # archivo aparte

enlaces_internos = r.extraer_enlaces(url_base, html_prueba)

print("Enlaces INTERNOS extraídos (deberían entrar a la cola):")
for e in enlaces_internos:
    print(f"  ✅ {e}")

candidate = r.candidate_store.get(url_base)
print("\nDependencias registradas (NO deberían entrar a la cola):")
if candidate and candidate.get("dependencies"):
    for d in candidate["dependencies"]:
        print(f"  🔗 {d['domain']} ({d['type']}, count={d['count']})")
else:
    print("  (ninguna)")

r.candidate_store.save()

# Verificación automática
esperados_internos = {"https://ejemplo.com/login", "https://ejemplo.com/contacto"}
obtenidos = set(enlaces_internos)
if obtenidos == esperados_internos:
    print("\n✅ Enlaces internos correctos")
else:
    print(f"\n❌ Esperado: {esperados_internos}")
    print(f"   Obtenido: {obtenidos}")
