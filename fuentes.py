# fuentes.py

# Roles de procedencia — deben coincidir con los que usan
# candidate_store.py / rastreador.py para decidir cómo tratar cada
# hallazgo. Una semilla nunca es "sospechosa" solo por estar en la
# lista; el role determina si lo que se encuentra ahí se acusa contra
# ESE dominio o se trata como mención/referencia hacia otros.
ROL_REFERENCIA = "reference"        # habla DE estafas, no ES una estafa
ROL_FEED_AMENAZAS = "threat_feed"   # ya reportado como malicioso por terceros
ROL_CANDIDATO = "candidate"         # default: se trata como sospechoso a evaluar


class FuentesSemillas:
    def __init__(self):
        pass

    def obtener_todas(self):
        """
        Devuelve una lista de tuplas (url, role) — no solo URLs. El role
        viaja con cada semilla desde el origen, así rastreador.py sabe
        desde el primer momento si lo que encuentre ahí es una
        OBSERVACIÓN DIRECTA (candidate/threat_feed) o una MENCIÓN
        (reference) antes de escanear una sola línea de HTML.
        """
        print("\n" + "="*70)
        print("   🕵️‍♂️ CARGANDO SEMILLAS DE CACERÍA — SPAM, PHISHING Y ESTAFAS")
        print("="*70)

        semillas = []

        # NOTA: los dorks de Google (site:github.com, inurl:login, etc.) se
        # sacaron de acá. Google bloquea pedidos automatizados a /search
        # (devuelve CAPTCHA), así que no aportaban resultados reales — solo
        # generaban ruido. La caza de spam en GitHub se hace con la API
        # oficial en github_hunter.py (opción 2 del menú).
        dorks_phishing_sugeridos = [
            # Para revisar VOS A MANO en el navegador, no se rastrean automático:
            'inurl:login intext:"sign in to your account" intext:"verification"',
            '"connect wallet" intext:"verify" intext:"security"',
            'site:*.top intext:"login" intext:"microsoft" intext:"office365"',
            'intitle:"index of" intext:"phishing" OR "login"',
        ]

        # --- FEEDS DE AMENAZAS: ya reportados por terceros ---
        # Un dominio que sale de acá NO es "mencionado por un blog" — es
        # una lista curada de sitios activamente maliciosos. Lo que Andart
        # encuentre AHÍ (en el propio dominio listado) sí es observación
        # directa contra ese dominio, no una referencia.
        feeds = [
            "https://urlhaus.abuse.ch/feeds/rss/",
            "https://phishstats.info/phish_score.csv",
            "https://openphish.com/feed.txt",
            "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links.txt",
            "https://cybercrime-tracker.net/rss.xml",
            "https://cert.europa.eu/static/SecurityAdvisories/",
        ]
        semillas.extend((url, ROL_FEED_AMENAZAS) for url in feeds)

        # --- SITIOS DE REFERENCIA/INVESTIGACIÓN ---
        # Publican artículos SOBRE estafas — no son ellos mismos el
        # objetivo. Lo que Andart encuentre en sus páginas (wallets,
        # Telegram, CBU mencionados en un artículo) es una MENCIÓN, y se
        # trata como candidato-mencionado, nunca como hallazgo contra el
        # propio sitio de referencia.
        sitios_investigacion = [
            "https://www.ripoffreport.com",
            "https://www.scamwarners.com",
            "https://www.antifraud.org",
            "https://www.scamadviser.com",
            "https://www.bleepingcomputer.com/news/security/",
            "https://www.malwarebytes.com/blog/news",
            "https://www.hackread.com/feed/",
            "https://www.krebsonsecurity.com",
            "https://www.cybernews.com",
            "https://www.threatpost.com",
            "https://www.zerodayinitiative.com",
        ]
        semillas.extend((url, ROL_REFERENCIA) for url in sitios_investigacion)

        # Deduplicar por URL, conservando el role de la primera aparición
        vistas = set()
        semillas_unicas = []
        for url, role in semillas:
            if url not in vistas:
                vistas.add(url)
                semillas_unicas.append((url, role))

        print(f"✅ TOTAL SEMILLAS CARGADAS: {len(semillas_unicas)}")
        print(f"📡 Feeds de amenazas (role={ROL_FEED_AMENAZAS}): {len(feeds)}")
        print(f"🕵️ Sitios de referencia (role={ROL_REFERENCIA}): {len(sitios_investigacion)}")
        print(f"💡 Dorks sugeridos (revisión manual): {len(dorks_phishing_sugeridos)}")
        print("="*70)
        return semillas_unicas

    def desde_archivo(self):
        """
        Semillas cargadas manualmente por el usuario en semillas.txt.
        Se tratan como ROL_CANDIDATO (default): el usuario las agregó
        porque las considera sospechosas, no como referencia de lectura.
        """
        semillas = []
        try:
            with open("semillas.txt", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea and not linea.startswith("#"):
                        semillas.append((linea, ROL_CANDIDATO))
        except FileNotFoundError:
            pass
        return semillas
