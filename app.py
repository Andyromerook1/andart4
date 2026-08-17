from fuentes import FuentesSemillas
from rastreador import Rastreador
from escaner_red import EscanerRed
import config

def menu():
    print("="*60)
    print("   🤖 BOT RASTREADOR AUTÓNOMO - ANDART")
    print("   Reconocimiento Automático — Fuentes Públicas")
    print("="*60)
    print(" 1. Rastreo Web → APIs automáticas + Busca claves")
    print(" 2. Escaneo Red → Genera rangos de IP masivos")
    print(" 3. AMBOS → Web + Red (todo automático)")
    print(" 0. Salir")
    print("="*60)
    return input("Seleccioná opción [1-3 / 0]: ").strip()

def ejecutar_escaneo_masivo(fuentes, total_objetivos=1000, puertos=None):
    if puertos is None:
        puertos = config.COMMON_PORTS
    ips_procesadas = 0
    print(f"\n🌐 INICIANDO ESCANEO MASIVO DE RED — Objetivo: ~{total_objetivos} IPs")
    print(f"   {len(puertos)} Puertos por IP\n")
    while ips_procesadas < total_objetivos:
        base = fuentes.generar_rango_ip()
        if not base:
            print("⚠️ No se pudo generar rango de IPs.")
            break
        restantes = total_objetivos - ips_procesadas
        bloque = min(254, restantes)
        escaner = EscanerRed(rango_ip=(base, 1, bloque), puertos=puertos)
        escaner.iniciar()
        ips_procesadas += bloque
        print(f"\n📊 Progreso acumulado: {ips_procesadas}/{total_objetivos} IPs escaneadas\n")

if __name__ == "__main__":
    fuentes = FuentesSemillas()
    while True:
        opcion = menu()
        if opcion == "1":
            semillas = fuentes.obtener_todas()
            if not semillas:
                print("⚠️ No se obtuvieron URLs desde las fuentes.")
                continue
            # ✅ Primero preguntamos el límite
            entrada = input("Cantidad máxima de páginas a visitar [Enter = ilimitado]: ").strip()
            limite = int(entrada) if entrada else config.DEFAULT_PAGE_LIMIT
            # ✅ Luego preguntamos Tor (sin solapamiento)
            tor_input = input("¿Usar Tor para ocultar IP? (s/n) [Enter = no]: ").strip().lower()
            use_tor = True if tor_input == "s" else False
            bot = Rastreador(semilla=semillas, limite=limite, use_tor=use_tor)
            bot.iniciar()
        elif opcion == "2":
            entrada = input(f"Cantidad total de IPs a escanear [Enter = {config.DEFAULT_IP_LIMIT}]: ").strip()
            limite_ips = int(entrada) if entrada else config.DEFAULT_IP_LIMIT
            confirmar = input(f"¿Iniciar escaneo de ~{limite_ips} IPs? (s/n): ").strip().lower()
            if confirmar == "s":
                ejecutar_escaneo_masivo(fuentes, total_objetivos=limite_ips)
        elif opcion == "3":
            semillas = fuentes.obtener_todas()
            if not semillas:
                print("⚠️ No se obtuvieron URLs desde las fuentes.")
                continue
            entrada_web = input("Páginas web a rastrear [Enter = ilimitado]: ").strip()
            limite_web = int(entrada_web) if entrada_web else config.DEFAULT_PAGE_LIMIT
            entrada_ips = input(f"Cantidad de IPs a escanear [Enter = {config.DEFAULT_IP_LIMIT}]: ").strip()
            limite_ips = int(entrada_ips) if entrada_ips else config.DEFAULT_IP_LIMIT
            # ✅ Preguntamos Tor después del límite web
            tor_input = input("¿Usar Tor para el rastreo web? (s/n) [Enter = no]: ").strip().lower()
            use_tor = True if tor_input == "s" else False
            print("\n--- INICIANDO RASTREO WEB ---")
            bot = Rastreador(semilla=semillas, limite=limite_web, use_tor=use_tor)
            bot.iniciar()
            print("\n--- INICIANDO ESCANEO DE RED ---")
            ejecutar_escaneo_masivo(fuentes, total_objetivos=limite_ips)
        elif opcion == "0":
            print("\n👋 ¡Finalizado!")
            break
        else:
            print("❌ Opción no válida.")
        input("\nPresioná Enter para volver al menú...")
