# test_fraud_detector.py
from fraud_detector import FraudDetector

detector = FraudDetector()

casos = [
    ("A. Texto legítimo de trabajo", """
        Buscamos vendedor con experiencia en atención al cliente.
        Sueldo fijo más comisiones por venta. Horario full time.
    """),
    ("B. Programa de referidos normal", """
        Invitá a tus amigos y ambos reciben $500 de crédito
        para usar en tu próxima compra. Sin límite de invitaciones.
    """),
    ("C. Reclutamiento piramidal claro", """
        Sumate a nuestro equipo. Ingreso inicial $100.000.
        Por cada persona que invites ganás $30.000.
        Generá ingresos pasivos desde tu casa.
    """),
    ("D. Curso caro SIN piramidal", """
        Curso de programación intensivo. Costo $100.000.
        Clases en vivo, certificado al finalizar, cupos limitados.
    """),
    ("E. Inversión legítima, sin promesas exageradas", """
        Fondo común de inversión regulado por la CNV.
        Rentabilidad histórica variable según el mercado. Consultá con
        tu asesor financiero antes de invertir.
    """),
    ("F. Inversión fraudulenta clara (rentabilidad garantizada)", """
        Últimos cupos. Invertí hoy y obtené 20% semanal garantizado.
    """),
    ("G. Curso legítimo + urgencia comercial normal", """
        Últimos cupos para nuestro curso de Python. Inscribite ya.
    """),
    ("H. MLM legítimo con producto real (no debería marcar fraude)", """
        Sumate como distribuidor de nuestra línea de cosmética.
        Ganás comisión por cada venta que hagas del catálogo.
    """),
    ("I. Piramidal con pago de entrada + referidos (caso fuerte)", """
        Pagá $50.000 para ingresar al sistema. Por cada persona que
        invites al equipo ganás $15.000. Últimos cupos disponibles.
    """),
    ("J. Ecommerce con 'últimas unidades' (no es fraude)", """
        Últimas unidades disponibles de nuestra colección de invierno.
        Envío gratis en compras superiores a $30.000.
    """),
    ("K. Crypto con 'duplicá tus fondos' (señal fuerte)", """
        Duplicá tu inversión en 7 días con nuestro sistema automatizado
        de trading. Sin riesgo, resultados garantizados.
    """),
]

for nombre, texto in casos:
    resultado = detector.analizar(texto)
    print(f"\n{'='*70}\n{nombre}\n{'='*70}")
    print(resultado.explicacion_legible())
