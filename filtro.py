import re
import json

class MotorFiltro:
    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)
        self.patrones = {nombre: re.compile(regex) for nombre, regex in datos.items()}

    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        for nombre, regex in self.patrones.items():
            coincidencias = regex.findall(texto)
            for c in coincidencias:
                valor = c if isinstance(c, str) else c[0]
                hallazgos.append({
                    "tipo": nombre,
                    "valor": valor.strip(),
                    "origen": origen
                })
        return hallazgos

    def guardar_hallazgo(self, hallazgo):
        linea = f"[{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}\n"
        with open("hallazgos.txt", "a", encoding="utf-8") as f:
            f.write(linea)
        print(f"⚠️  HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")