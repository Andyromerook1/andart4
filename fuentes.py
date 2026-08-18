# fuentes.py
class FuentesSemillas:
    def __init__(self):
        pass

    def obtener_todas(self):
        print("\n" + "="*70)
        print("   🕵️‍♂️ CARGANDO SEMILLAS DE CACERÍA — SPAM, PHISHING Y ESTAFAS")
        print("="*70)
        urls = []

        # NOTA: los dorks de Google (site:github.com, inurl:login, etc.) se
        # sacaron de acá. Google bloquea pedidos automatizados a /search
        # (devuelve CAPTCHA), así que no aportaban resultados reales — solo
        # generaban ruido (ej: terminaba rastreando robots.txt de google.com
        # porque ESA era la URL semilla). La caza de spam en GitHub ya se
        # hace mejor con la API oficial en github_hunter.py (opción 2 del menú).

        dorks_phishing_sugeridos = [
            # Para revisar VOS A MANO en el navegador, no se rastrean automático:
            'inurl:login intext:"sign in to your account" intext:"verification"',
            '"connect wallet" intext:"verify" intext:"security"',
            'site:*.top intext:"login" intext:"microsoft" intext:"office365"',
            'intitle:"index of" intext:"phishing" OR "login"',
        ]
        # (no se agregan a `urls` — son solo referencia, ver README)

        feeds = [
            "https://urlhaus.abuse.ch/feeds/rss/",
            "https://phishstats.info/phish_score.csv",
            "https://openphish.com/feed.txt",
            "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links.txt",
            "https://cybercrime-tracker.net/rss.xml",
            "https://cert.europa.eu/static/SecurityAdvisories/",
        ]
        urls.extend(feeds)

        # Sitios de investigación/noticias de seguridad — SÍ se rastrean,
        # porque publican artículos puntuales sobre estafas reales (no son
        # sitios "grandes" con miles de páginas internas no relacionadas).
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
        # Se sacaron de esta lista: cryptocompare.com, bitcointalk.org,
        # haveibeenpwned.com — son sitios de referencia con miles de páginas
        # internas legítimas (foros, sitemaps). El bot terminaba rastreando
        # SUS páginas internas y marcándolas como sospechosas por error.
        # Si querés usarlos como referencia de lectura, visitalos a mano.
        urls.extend(sitios_investigacion)

        urls_unicas = list(dict.fromkeys(urls))
        print(f"✅ TOTAL SEMILLAS CARGADAS: {len(urls_unicas)}")
        print(f"📡 Feeds de amenazas: {len(feeds)}")
        print(f"🕵️ Sitios de investigación: {len(sitios_investigacion)}")
        print(f"💡 Dorks sugeridos (revisión manual): {len(dorks_phishing_sugeridos)}")
        print("="*70)
        return urls_unicas

    def desde_archivo(self):
        urls = []
        try:
            with open("semillas.txt", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea and not linea.startswith("#"):
                        urls.append(linea)
        except FileNotFoundError:
            pass
        return urls
