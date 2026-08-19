# ct_to_candidates.py
"""
Conecta ct_monitor.py con candidate_store.py: toma los dominios que
Certificate Transparency encontró y los registra/actualiza como
candidatos, con sus señales reales (tld, edad de certificado,
similitud de typosquatting) — sin decidir nada de riesgo acá, eso lo
hace candidate_store delegando a risk_score.py.
"""
from ct_monitor import MonitorCertificados
from candidate_store import CandidateStore


def procesar_hallazgos_ct(incluir_patrones=False, limite_patrones=40, store: CandidateStore = None):
    """
    Corre ct_monitor y carga cada dominio encontrado en candidate_store.
    Devuelve el store (nuevo o el que se pasó) ya actualizado y guardado.
    """
    monitor = MonitorCertificados()
    hallazgos = monitor.escanear_todo(
        incluir_patrones=incluir_patrones, limite_patrones=limite_patrones
    )

    store = store or CandidateStore()

    for h in hallazgos:
        campos_score = {}
        if h.get("tld"):
            campos_score["tld"] = h["tld"]
        if h.get("dias_desde_emision_certificado") is not None:
            campos_score["dias_desde_emision_certificado"] = h["dias_desde_emision_certificado"]
        if h.get("similitud_typosquatting") is not None:
            campos_score["similitud_typosquatting"] = h["similitud_typosquatting"]

        store.add_signal(
            h["dominio"],
            tipo="ct_hallazgo",
            valor=h["motivo"],
            discovered_by="ct_monitor",
            campos_score=campos_score,
        )
        candidate = store.recalculate(h["dominio"])
        print(f"   📋 {h['dominio']} → score={candidate['score']:.1f} nivel={candidate['level']}")

    store.save()
    print(f"\n✅ {len(hallazgos)} candidatos procesados desde Certificate Transparency")
    return store


if __name__ == "__main__":
    procesar_hallazgos_ct(incluir_patrones=False)
