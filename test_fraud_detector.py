# test_fraud_detector.py
from fraud_detector import FraudDetector

detector = FraudDetector()

casos = [
    ("A. Texto legítimo de trabajo", """
        Buscamos vendedor con experiencia en atención al cliente.
        Sueldo fijo más comisiones por venta. Horario full time.
    """),
    ("B. Programa de referidos normal (ej: apps legítimas)", """
        Invitá a tus amigos y ambos reciben $500 de crédito
        para usar en tu próxima compra. Sin límite de invitaciones.
    """),
    ("C. Reclutamiento piramidal claro", """
        Sumate a nuestro equipo. Ingreso inicial $100.000.
        Por cada persona que invites ganás $30.000.
        Generá ingresos pasivos desde tu casa.
    """),
    ("D. Curso caro SIN piramidal (no debería confundirse)", """
        Curso de programación intensivo. Costo $100.000.
        Clases en vivo, certificado al finalizar, cupos limitados.
    """),
    ("E. Inversión legítima, sin promesas exageradas", """
        Fondo común de inversión regulado por la CNV.
        Rentabilidad histórica variable según el mercado. Consultá con
        tu asesor financiero antes de invertir.
    """),
    ("F. Promesa de rentabilidad garantizada (señal fuerte)", """
        Invertí con nosotros y generá un 20% semanal garantizado.
        Últimos cupos disponibles, sumate antes que se acabe.
    """),
]

for nombre, texto in casos:
    resultado = detector.analizar(texto)
    print(f"\n{'='*70}\n{nombre}\n{'='*70}")
    print(resultado.explicacion_legible())
