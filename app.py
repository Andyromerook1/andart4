# app.py
import os
from fuentes import FuentesSemillas
from rastreador import Rastreador
from filtro import MotorFiltro
from github_hunter import campaña_completa
import config


def menu():
    print("="*60)
    print("   🤖 BOT RASTREADOR AUTÓNOMO - ANDART")
    print("   Reconocimiento Automático — Fuentes Públicas")
    print("="*60)
    print(" 1. Rastreo Web → dorks, feeds y sitios de investigación")
    print(" 2. Caza en GitHub → repos de spam/estafa (API oficial)")
    print(" 0. Salir")
    print("="*60)
    return input("Seleccioná opción [1 / 2 / 0]: ").strip()


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

        elif opcion == "2":
            token = os.environ.get("GITHUB_TOKEN")  # opcional, sube el rate limit
            dias_input = input("Buscar repos de los últimos N días [Enter = 1]: ").strip()
            dias = int(dias_input) if dias_input else 1
            motor = MotorFiltro()
            resultados = campaña_completa(token=token, motor_filtro=motor, dias=dias)
            print(f"\n✅ {len(resultados)} archivos con hallazgos relevantes")

        elif opcion == "0":
            print("\n👋 ¡Finalizado!")
            break

        else:
            print("❌ Opción no válida.")

        input("\nPresioná Enter para volver al menú...")
