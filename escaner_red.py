import socket

class EscanerRed:
    def __init__(self, rango_ip, puertos):
        self.base_ip, self.inicio, self.fin = rango_ip
        self.puertos = puertos
        self.activos = []

    def probar_conexion(self, ip, puerto):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.8)
            if sock.connect_ex((ip, puerto)) == 0:
                sock.close()
                return True
        except:
            pass
        return False

    def iniciar(self):
        total = (self.fin - self.inicio + 1) * len(self.puertos)
        contador = 0
        print(f"🌐 ESCANEANDO: {self.base_ip}.{self.inicio} → {self.base_ip}.{self.fin}")
        print(f"   Puertos: {', '.join(map(str, self.puertos))}\n")

        for i in range(self.inicio, self.fin + 1):
            ip = f"{self.base_ip}.{i}"
            for puerto in self.puertos:
                contador += 1
                print(f"   [{contador}/{total}] {ip}:{puerto}...", end="\r")
                if self.probar_conexion(ip, puerto):
                    registro = f"{ip}:{puerto} — ABIERTO"
                    self.activos.append(registro)
                    print(f"\n   ✅ {registro}")

        print(f"\n✅ ESCANEADO COMPLETO — {len(self.activos)} puertos abiertos encontrados")
        if self.activos:
            with open("hallazgos.txt", "a", encoding="utf-8") as f:
                f.write("\n=== PUERTOS ABIERTOS ENCONTRADOS ===\n")
                f.write("\n".join(self.activos))
                f.write("\n")
        return self.activos