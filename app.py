from fuentes import FuentesAutomaticas
from rastreador import Rastreador
from escaner_red import EscanerRed

def menu():
    print("="*60)
    print("   🤖 BOT RASTREADOR AUTÓNOMO")
    print("   Reconocimiento Automático — Fuentes Públicas")
    print("="*60)
    print(" 1. Rastreo Web → APIs automáticas + Busca claves")
    print(" 2. Escaneo Red → Genera rangos de IP masivos")
    print(" 3. AMBOS → Web + Red (todo automático)")
    print(" 0. Salir")
    print("="*60)
    return input("Seleccioná opción [1-3 / 0]: ").strip()


def ejecutar_escaneo_masivo(fuentes, total_objetivos=1000, puertos=None):
    """Genera subredes completas y escanea hasta cubrir la cantidad solicitada."""
    if puertos is None:
        # Lista completa de puertos más usados (agregados todos los comunes)
        puertos = [
            21, 22, 23, 25, 53, 67, 68, 69, 80, 81, 110, 111, 135, 139,
            143, 161, 162, 179, 389, 443, 445, 465, 514, 515, 587, 636,
            993, 995, 1080, 1433, 1434, 1521, 1723, 2049, 2121, 3306,
            3389, 5060, 5432, 5900, 5901, 6379, 8000, 8080, 8443,
            8888, 9000, 9200, 9300, 11211, 27017
        ]

    ips_procesadas = 0
    print(f"\n🌐 INICIANDO ESCANEO MASIVO DE RED — Objetivo: ~{total_objetivos} IPs")
    print(f"   {len(puertos)} Puertos por IP\n")

    while ips_procesadas < total_objetivos:
        # Genera una subred nueva completa (ej: "185.220.101")
        base = fuentes.generar_rango_ip()

        # Cuántas IPs faltan para llegar al objetivo (máx 254 por subred)
        restantes = total_objetivos - ips_procesadas
        bloque = min(254, restantes)

        # Escanea .1 hasta .bloque de esa subred
        escaner = EscanerRed(rango_ip=(base, 1, bloque), puertos=puertos)
        escaner.iniciar()

        ips_procesadas += bloque
        print(f"\n📊 Progreso acumulado: {ips_procesadas}/{total_objetivos} IPs escaneadas\n")


if __name__ == "__main__":
    fuentes = FuentesAutomaticas()

    while True:
        opcion = menu()

        # === OPCIÓN 1: RASTREO WEB ===
        if opcion == "1":
            semillas = fuentes.obtener_todas()
            if not semillas:
                print("⚠️ No se obtuvieron URLs.")
                continue
            limite = int(input("Cantidad máxima de páginas a visitar [ej: 9999]: "))
            bot = Rastreador(semilla=semillas, limite=limite)
            bot.iniciar()

        # === OPCIÓN 2: ESCANEO MASIVO DE RED ===
        elif opcion == "2":
            limite_ips = int(input("Cantidad total de IPs a escanear [ej: 1000 o 9999]: "))
            confirmar = input(f"¿Iniciar escaneo de {limite_ips} IPs? (s/n): ").strip().lower()
            if confirmar == "s":
                ejecutar_escaneo_masivo(fuentes, total_objetivos=limite_ips)

        # === OPCIÓN 3: TODO JUNTO ===
        elif opcion == "3":
            semillas = fuentes.obtener_todas()
            limite_web = int(input("Páginas web a rastrear [ej: 9999]: "))
            limite_ips = int(input("Cantidad de IPs a escanear [ej: 1000]: "))

            print("\n--- INICIANDO RASTREO WEB ---")
            bot = Rastreador(semilla=semillas, limite=limite_web)
            bot.iniciar()

            print("\n--- INICIANDO ESCANEO DE RED ---")
            ejecutar_escaneo_masivo(fuentes, total_objetivos=limite_ips)

        elif opcion == "0":
            print("\n👋 ¡Finalizado!")
            break

        input("\nEnter para volver al menú...")
