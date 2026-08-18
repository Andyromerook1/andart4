# app.py
import os
import threading
from fuentes import FuentesSemillas
from rastreador import Rastreador
from filtro import MotorFiltro
from github_hunter import campaña_completa
from ct_monitor import MonitorCertificados
import config


def menu():
    print("="*60)
    print("   🤖 BOT RASTREADOR AUTÓNOMO - ANDART")
    print("   Reconocimiento Automático — Fuentes Públicas")
    print("="*60)
    print(" 1. Rastreo Web → dorks, feeds y sitios de investigación")
    print(" 2. Caza en GitHub → repos de spam/estafa (API oficial)")
    print(" 3. AMBOS a la vez → Rastreo Web + GitHub en paralelo")
    print(" 4. Certificate Transparency → dominios recién creados (crt.sh)")
    print(" 0. Salir")
    print("="*60)
    return input("Seleccioná opción [1-4 / 0]: ").strip()


def tarea_rastreo_web(limite):
    fuentes = FuentesSemillas()
    semillas = fuentes.obtener_todas()
    if not semillas:
        print("⚠️ [Rastreo Web] No se obtuvieron URLs desde las fuentes.")
        return
    bot = Rastreador(semilla=semillas, limite=limite)
    bot.iniciar()


def tarea_github(token, dias):
    motor = MotorFiltro()
    resultados = campaña_completa(token=token, motor_filtro=motor, dias=dias)
    print(f"\n✅ [GitHub] {len(resultados)} archivos con hallazgos relevantes")


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
            token = os.environ.get("GITHUB_TOKEN")
            dias_input = input("Buscar repos de los últimos N días [Enter = 1]: ").strip()
            dias = int(dias_input) if dias_input else 1
            tarea_github(token, dias)

        elif opcion == "3":
            entrada = input("Páginas web a rastrear [Enter = ilimitado]: ").strip()
            limite_web = int(entrada) if entrada else config.DEFAULT_PAGE_LIMIT
            dias_input = input("GitHub: buscar repos de los últimos N días [Enter = 1]: ").strip()
            dias_gh = int(dias_input) if dias_input else 1
            token = os.environ.get("GITHUB_TOKEN")

            print("\n🚀 Iniciando Rastreo Web y Caza en GitHub EN PARALELO...\n")

            hilo_web = threading.Thread(target=tarea_rastreo_web, args=(limite_web,), daemon=True)
            hilo_github = threading.Thread(target=tarea_github, args=(token, dias_gh), daemon=True)

            hilo_web.start()
            hilo_github.start()

            hilo_web.join()
            hilo_github.join()

            print("\n✅ Ambas tareas finalizaron.")

        elif opcion == "4":
            monitor = MonitorCertificados()
            dominios = monitor.escanear_todas_las_marcas()
            print(f"\n✅ {len(dominios)} dominios sospechosos encontrados vía Certificate Transparency")
            if dominios:
                confirmar = input("¿Rastrear estos dominios ahora para buscar wallets/CBU/phishing? (s/n): ").strip().lower()
                if confirmar == "s":
                    semillas_nuevas = [f"https://{d['dominio']}" for d in dominios]
                    bot = Rastreador(semilla=semillas_nuevas, limite=len(semillas_nuevas) * 5)
                    bot.iniciar()

        elif opcion == "0":
            print("\n👋 ¡Finalizado!")
            break

        else:
            print("❌ Opción no válida.")

        input("\nPresioná Enter para volver al menú...")
