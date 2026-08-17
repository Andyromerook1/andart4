from fuentes import FuentesSemillas
from rastreador import Rastreador
import config

def menu():
    print("="*60)
    print("   🤖 BOT RASTREADOR AUTÓNOMO - ANDART")
    print("   Reconocimiento Automático — Fuentes Públicas")
    print("="*60)
    print(" 1. Rastreo Web → APIs automáticas + Detección de phishing/estafas")
    print(" 0. Salir")
    print("="*60)
    return input("Seleccioná opción [1 / 0]: ").strip()

if __name__ == "__main__":
    fuentes = FuentesSemillas()
    while True:
        opcion = menu()
        if opcion == "1":
            semillas = fuentes.obtener_todas()
            if not semillas:
                print("⚠️ No se obtuvieron URLs desde las fuentes.")
                continue
            entrada = input("Cantidad máxima de páginas a visitar [Enter = ilimitado]: ").strip()
            limite = int(entrada) if entrada else config.DEFAULT_PAGE_LIMIT
            bot = Rastreador(semilla=semillas, limite=limite)
            bot.iniciar()
        elif opcion == "0":
            print("\n👋 ¡Finalizado!")
            break
        else:
            print("❌ Opción no válida.")
        input("\nPresioná Enter para volver al menú...")
