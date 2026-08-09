import re
import json

class MotorFiltro:
    # Patrones que NO distinguen mayúsculas/minúsculas
    IGNORE_CASE = [
        "Contraseña",
        "Clave API",
        "Cadena",
        "Número Tarjeta",
        "Clave Secreta",
        "Cadena tipo"
    ]

    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)

        self.patrones = {}
        for nombre, regex in datos.items():
            # Aplicar re.IGNORECASE solo a los patrones que corresponda
            banderas = re.IGNORECASE if any(ignorado in nombre for ignorado in self.IGNORE_CASE) else 0
            self.patrones[nombre] = re.compile(regex, banderas)

    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        for nombre, regex in self.patrones.items():
            # Encontrar todas las coincidencias
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if valor:
                    hallazgos.append({
                        "tipo": nombre,
                        "valor": valor,
                        "origen": origen
                    })
        return hallazgos

    def guardar_hallazgo(self, hallazgo):
        linea = f"[{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}\n"
        with open("hallazgos.txt", "a", encoding="utf-8") as f:
            f.write(linea)
        # Mostrar en consola (truncado si es muy largo)
        print(f"⚠️  HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
