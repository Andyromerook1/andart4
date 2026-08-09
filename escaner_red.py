import socket
from concurrent.futures import ThreadPoolExecutor

class EscanerRed:
    def __init__(self, rango_ip, puertos, max_threads=20):
        self.base_ip, self.inicio, self.fin = rango_ip
        self.puertos = puertos
        self.activos = []
        self.max_threads = max_threads

    def probar_conexion(self, ip, puerto):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.8)
        try:
            if sock.connect_ex((ip, puerto)) == 0:
                return True
        except Exception:
            pass
        finally:
            sock.close()
        return False

    def _evaluar_objetivo(self, args):
        ip, puerto = args
        if self.probar_conexion(ip, puerto):
            registro = f"{ip}:{puerto} — ABIERTO"
            print(f"   ✅ {registro}")
            return registro
        return None

    def iniciar(self):
        print(f"🌐 ESCANEANDO: {self.base_ip}.{self.inicio} → {self.base_ip}.{self.fin}")
        print(f"   Puertos: {', '.join(map(str, self.puertos))}\n")

        # Generar la lista completa de combinaciones IP:Puerto
        tareas = [
            (f"{self.base_ip}.{i}", puerto)
            for i in range(self.inicio, self.fin + 1)
            for puerto in self.puertos
        ]

        # Ejecución concurrente mediante hilos
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            resultados = executor.map(self._evaluar_objetivo, tareas)
            for res in resultados:
                if res:
                    self.activos.append(res)

        print(f"\n✅ ESCANEADO COMPLETO — {len(self.activos)} puertos abiertos encontrados")
        if self.activos:
            with open("hallazgos.txt", "a", encoding="utf-8") as f:
                f.write("\n=== PUERTOS ABIERTOS ENCONTRADOS ===\n")
                f.write("\n".join(self.activos))
                f.write("\n")
        return self.activos
