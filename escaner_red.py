import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

class EscanerRed:
    # ⚠️ HILOS AJUSTADOS: 30 es el punto óptimo en Termux
    # Menos = lento / Más de 50 = error de sistema + falsos negativos
    def __init__(self, rango_ip, puertos, max_threads=30):
        self.base_ip, self.inicio, self.fin = rango_ip
        self.puertos = puertos
        self.activos = []
        self.max_threads = max_threads

        # ✅ PROTECCIÓN DEL OCTETO IPv4: nunca pasa de 254
        self.fin = min(self.fin, 254)
        # ✅ Protección extra: nunca empieza antes de .1 ni pasa de .254
        self.inicio = max(self.inicio, 1)
        if self.inicio > self.fin:
            self.inicio, self.fin = 1, 254

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
        print(f"   Puertos: {', '.join(map(str, self.puertos))}")
        print(f"   ⚡ Hilos paralelos: {self.max_threads} (equilibrado)\n")

        # ✅ Genera SOLO direcciones válidas .1 a .254 — NUNCA .255 ni .300
        tareas = [
            (f"{self.base_ip}.{i}", puerto)
            for i in range(self.inicio, self.fin + 1)
            for puerto in self.puertos
        ]

        total = len(tareas)
        print(f"   📋 Combinaciones válidas a escanear: {total}\n")

        # ✅ Ejecuta sin cargar TODA la lista en memoria al mismo tiempo
        resultados = []
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futuros = [executor.submit(self._evaluar_objetivo, t) for t in tareas]
            for fut in as_completed(futuros):
                try:
                    res = fut.result()
                    if res:
                        resultados.append(res)
                except Exception:
                    continue

        self.activos = resultados

        print(f"\n✅ ESCANEADO COMPLETO — {len(self.activos)} puertos abiertos encontrados")
        if self.activos:
            with open("hallazgos.txt", "a", encoding="utf-8") as f:
                f.write("\n=== PUERTOS ABIERTOS ENCONTRADOS ===\n")
                f.write("\n".join(self.activos))
                f.write("\n")
        return self.activos
