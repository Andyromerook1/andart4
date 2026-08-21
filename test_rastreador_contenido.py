# test_rastreador_contenido.py
"""
Prueba controlada: simula que el rastreador ya descargó 3 páginas
(HTML sintético, sin ir a internet) y verifica que fraud_detector +
candidate_store + analysis_policy reaccionen como esperamos.

No usa Rastreador completo (eso requeriría red real) — llama
directamente a las piezas internas que agregamos, con HTML de prueba.
"""
from bs4 import BeautifulSoup
from fraud_detector import FraudDetector
from candidate_store import CandidateStore

fraud_detector = FraudDetector()
store = CandidateStore(ruta="candidatos_test_rastreador.json")


def extraer_texto_visible(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


paginas = [
    ("1. Página normal (blog de cocina)", "https://recetas-caseras-ejemplo.com/torta", """
        <html><body>
            <h1>Receta de torta de chocolate</h1>
            <p>Mezclá la harina con el cacao. Horneá 40 minutos a 180 grados.
            Dejá enfriar antes de desmoldar.</p>
        </body></html>
    """),
    ("2. Reclutamiento piramidal fuerte", "https://oportunidad-unica-ejemplo.xyz/equipo", """
        <html><body>
            <h1>Sumate a nuestro equipo</h1>
            <p>Ingreso inicial $100.000. Por cada persona que invites
            ganás $30.000. Generá ingresos pasivos desde tu casa.</p>
        </body></html>
    """),
    ("3. Inversión fraudulenta", "https://trading-facil-ejemplo.top/invertir", """
        <html><body>
            <h1>Invertí con nosotros</h1>
            <p>Últimos cupos. Obtené 20% semanal garantizado.
            Duplicá tu inversión en 30 días.</p>
        </body></html>
    """),
]

for nombre, url, html in paginas:
    print(f"\n{'='*70}\n{nombre}\n{'='*70}")
    texto = extraer_texto_visible(html)
    print(f"Texto extraído: \"{texto[:80]}...\"")

    resultado = fraud_detector.analizar(texto)
    if not resultado.senales:
        print("Sin señales de fraude detectadas.")
        continue

    store.get_or_create(url, discovered_by="rastreador_web")
    store.add_content_signals(url, resultado, origen_url=url)
    candidate = store.recalculate(url)

    print(f"content_type_posible: {candidate['content_type_posible']}")
    print(f"content_risk: {candidate['content_risk']:.1f}")
    print(f"domain_risk: {candidate['domain_risk']:.1f}")
    print(f"level: {candidate['level']}  ({candidate['level_reason']})")

store.save()
print(f"\n✅ Test finalizado. Candidatos guardados en candidatos_test_rastreador.json")
