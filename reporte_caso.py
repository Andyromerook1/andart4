# reporte_caso.py
"""
Cruza hallazgos.txt, correlaciones.jsonl, casos_puente.jsonl y
blockchain_insights.txt para armar UN informe legible por cada red/actor
detectado — en vez de que tengas que cruzar 4 archivos a mano.

Agrupa por "clusters": orígenes que comparten al menos un identificador
(email, wallet, CBU, dominio clonado, metadata de PDF) según lo que ya
detectó el módulo de correlación durante el rastreo.
"""
import json
import os
from datetime import datetime
from collections import defaultdict
import config


class GeneradorInforme:
    def __init__(self):
        self.uf_padre = {}  # union-find: origen -> padre

    # --- Union-Find simple para agrupar orígenes conectados ---
    def _find(self, x):
        self.uf_padre.setdefault(x, x)
        while self.uf_padre[x] != x:
            self.uf_padre[x] = self.uf_padre[self.uf_padre[x]]
            x = self.uf_padre[x]
        return x

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self.uf_padre[ra] = rb

    def _cargar_jsonl(self, path):
        items = []
        if not os.path.exists(path):
            return items
        with open(path, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    try:
                        items.append(json.loads(linea))
                    except json.JSONDecodeError:
                        continue
        return items

    def generar(self):
        correlaciones = self._cargar_jsonl(config.CORRELACION_FILE)
        puentes = self._cargar_jsonl(config.CASOS_PUENTE_FILE)

        # Conectar orígenes que comparten un identificador (correlación)
        for c in correlaciones:
            origenes = c.get("origenes", [])
            for i in range(1, len(origenes)):
                self._union(origenes[0], origenes[i])

        # Conectar cuenta financiera y wallet dentro del mismo origen (puente)
        # ya están en el mismo origen, no hace falta unir nada extra acá,
        # pero se guardan aparte para el detalle del informe.

        # Armar clusters de orígenes
        clusters = defaultdict(set)
        for origen in list(self.uf_padre.keys()):
            raiz = self._find(origen)
            clusters[raiz].add(origen)

        if not clusters:
            print("ℹ️  No hay correlaciones registradas todavía — nada que agrupar en informes.")
            print("    (Esto es normal si es la primera corrida o si ningún identificador se repitió)")
            return []

        rutas_generadas = []
        for idx, (raiz, origenes) in enumerate(clusters.items(), start=1):
            ruta = self._generar_informe_cluster(idx, origenes, correlaciones, puentes)
            rutas_generadas.append(ruta)

        print(f"\n✅ {len(rutas_generadas)} informe(s) de caso generado(s) en: {config.REPORTES_DIR}")
        return rutas_generadas

    def _generar_informe_cluster(self, idx, origenes, correlaciones, puentes):
        nombre_archivo = f"caso_{idx:03d}_{datetime.now().strftime('%Y%m%d')}.md"
        ruta = os.path.join(config.REPORTES_DIR, nombre_archivo)

        identificadores = [c for c in correlaciones if any(o in origenes for o in c.get("origenes", []))]
        puentes_cluster = [p for p in puentes if p.get("origen") in origenes]

        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"# Caso {idx:03d} — Red de {len(origenes)} orígenes vinculados\n\n")
            f.write(f"Generado: {datetime.now().isoformat()}\n\n")

            f.write("## Orígenes involucrados\n\n")
            for o in sorted(origenes):
                f.write(f"- {o}\n")

            f.write("\n## Identificadores que conectan estos orígenes\n\n")
            for c in identificadores:
                f.write(f"- **{c['tipo']}**: `{c['valor']}` — aparece en {c['cantidad_apariciones']} orígenes\n")

            if puentes_cluster:
                f.write("\n## ⚠️ Casos puente (cuenta financiera ↔ wallet cripto)\n\n")
                f.write("Estos son los más accionables: conectan una identidad real con el destino de los fondos.\n\n")
                for p in puentes_cluster:
                    cf = p["cuenta_financiera"]
                    w = p["wallet_cripto"]
                    f.write(f"- **{cf['tipo']}** `{cf['valor']}` ←→ **{w['tipo']}** `{w['valor']}`\n")
                    f.write(f"  - Origen: {p['origen']}\n")

            f.write("\n---\n")
            f.write("*Informe generado automáticamente por Andart a partir de fuentes públicas. ")
            f.write("Requiere revisión manual antes de cualquier presentación formal.*\n")

        print(f"   📄 Informe generado: {ruta}")
        return ruta


if __name__ == "__main__":
    gen = GeneradorInforme()
    gen.generar()
