from fuentes import FuentesAutomaticas
from rastreador import Rastreador
from escaner_red import EscanerRed

def menu():
    print("="*60)
    print("   🤖 BOT RASTREADOR AUTÓNOMO")
    print("   Reconocimiento Automático — Fuentes Públicas")
    print("="*60)
    print(" 1. Rastreo Web → APIs automáticas + Busca claves")
    print(" 2. Escaneo Red → Genera rango IP automáticamente")
    print(" 3. AMBOS → Web + Red (todo automático)")
    print(" 0. Salir")
    print("="*60)
    return input("Seleccioná opción [1-3 / 0]: ").strip()

if __name__ == "__main__":
    fuentes = FuentesAutomaticas()

    while True:
        opcion = menu()

        if opcion == "1":
            semillas = fuentes.obtener_todas()
            if not semillas:
                print("⚠️ No se obtuvieron URLs.")
                continue
            limite = int(input("Cantidad máxima de páginas a visitar: "))
            bot = Rastreador(semilla=semillas, limite=limite)
            bot.iniciar()

        elif opcion == "2":
            print("\n🌐 Generando rango IP automáticamente...")
            base = fuentes.generar_rango_ip(cantidad=50)
            puertos = [22, 80, 443, 3306, 5432, 27017]
            print(f"   Puertos: {', '.join(map(str, puertos))}")
            confirmar = input("¿Iniciar escaneo? (s/n): ").strip().lower()
            if confirmar == "s":
                escaner = EscanerRed(rango_ip=(base, 1, 50), puertos=puertos)
                escaner.iniciar()

        elif opcion == "3":
            semillas = fuentes.obtener_todas()
            limite = int(input("Páginas a rastrear por sitio: "))

            print("\n--- INICIANDO RASTREO WEB ---")
            bot = Rastreador(semilla=semillas, limite=limite)
            bot.iniciar()

            print("\n--- INICIANDO ESCANEO DE RED ---")
            base = fuentes.generar_rango_ip(cantidad=50)
            puertos = [22, 80, 443, 3306, 5432, 27017]
            escaner = EscanerRed(rango_ip=(base, 1, 50), puertos=puertos)
            escaner.iniciar()

        elif opcion == "0":
            print("\n👋 ¡Finalizado!")
            break

        input("\nEnter para volver al menú...")