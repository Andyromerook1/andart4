# fuentes.py - Versión definitiva: Semillas de cacería + inteligencia de amenazas
import requests
import random

class FuentesSemillas:
    def __init__(self):
        pass

    # =============================================================
    # 🌐 SEMILLAS DE CACERÍA E INTELIGENCIA DE AMENAZAS
    # =============================================================
    def obtener_todas(self):
        print("\n" + "="*70)
        print("   🕵️‍♂️ CARGANDO SEMILLAS DE CACERÍA — SPAM, PHISHING Y ESTAFAS")
        print("="*70)
        urls = []

        # =====================================================
        # 🎯 BLOQUE 0: DORKS DE GOOGLE (Cacería de repositorios de spam)
        #    Buscan repositorios de spam recién creados (últimas 24h)
        # =====================================================
        # Estos dorks usan operadores de búsqueda avanzada de Google
        # para localizar repositorios de GitHub con contenido de apuestas/finanzas en chino.
        # El parámetro &tbs=qdr:d limita los resultados a las últimas 24 horas.
        dorks_github = [
            "https://www.google.com/search?q=site:github.com+%222026%22+%22%E8%AE%A1%E5%88%92%22+%22%E7%BE%A4%22&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+%22%E7%A6%8F%E5%BD%A9%22+%22%E9%A2%84%E6%B5%8B%22&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+inurl:blob+intext:%22%E5%A4%A7%E5%8F%91%22+intext:%E8%B4%A2%E7%BB%8F&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+%22%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF%22+intext:%E8%B5%9A%E9%92%B1&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+intext:t.me+intext:lotto+intext:bet+intext:%E4%B8%AD%E5%9B%BD&tbs=qdr:d"
        ]
        urls.extend(dorks_github)

        # =====================================================
        # 🎣 BLOQUE 1: DORKS DE PHISHING GENERAL
        #    Buscan páginas de phishing nuevas (bancos, redes sociales, cripto)
        # =====================================================
        dorks_phishing = [
            # Phishing de inicio de sesión genérico
            "https://www.google.com/search?q=inurl:login+intext:%22sign+in+to+your+account%22+intext:%22verification%22&tbs=qdr:d",
            # Phishing de cripto (wallets)
            "https://www.google.com/search?q=%22connect+wallet%22+intext:%22verify%22+intext:%22security%22&tbs=qdr:d",
            # Páginas de error falsas o "documentos compartidos"
            "https://www.google.com/search?q=site:*.top+intext:%22login%22+intext:%22microsoft%22+intext:%22office365%22&tbs=qdr:d",
            # Directorios con archivos de phishing
            "https://www.google.com/search?q=intitle:%22index+of%22+intext:%22phishing%22+OR+%22login%22&tbs=qdr:d"
        ]
        urls.extend(dorks_phishing)

        # =====================================================
        # 📡 BLOQUE 2: FEEDS DE INTELIGENCIA DE AMENAZAS (Listas negras en tiempo real)
        #    Estas fuentes ya tienen el trabajo de identificar sitios maliciosos
        # =====================================================
        feeds = [
            "https://urlhaus.abuse.ch/feeds/rss/",                       # Malware y sitios de descarga
            "https://phishstats.info/phish_score.csv",                   # Lista CSV de phishings activos
            "https://openphish.com/feed.txt",                           # Feed directo de URLs de phishing
            "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links.txt", # Base de datos comunitaria
            "https://cybercrime-tracker.net/rss.xml",                   # Rastreador de sitios maliciosos
            "https://cert.europa.eu/static/SecurityAdvisories/",        # Avisos de seguridad (puede tener enlaces)
        ]
        urls.extend(feeds)

        # =====================================================
        # 🕵️ BLOQUE 3: FOROS Y SITIOS DE REPORTE DE ESTAFAS
        #    Donde los investigadores publican hallazgos
        # =====================================================
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
            "https://www.haveibeenpwned.com",
            "https://www.bitcointalk.org",                       # Foro de cripto, a veces se filtran estafas
            "https://www.cryptocompare.com",                    # Noticias de cripto
        ]
        urls.extend(sitios_investigacion)

        # =====================================================
        # 🧅 BLOQUE 4: DEEP WEB / TOR (Onion links)
        #    Algunas estafas operan en la red Tor, aunque no todas son accesibles
        # =====================================================
        onion = [
            "http://duskgytldkxiuqc6.onion",
            "http://zqktlwiuavvvqqt4.onion",
            "http://torlinksd6pdnihy.onion",
            "http://onionlinksjr4d2i7.onion",
            "http://xmh57jrzrnw6insl.onion",
            "http://hss3uro2hsxfogfq.onion",
            "http://msydqstlz2kzerdg.onion",
            "http://ahmiadnbyx5m7qwx.onion",
            "http://wikidplw7h6b3fvg.onion",
            "http://check.torproject.org",
            "http://facebookcorewwwi.onion",                    # Facebook Tor (puede tener información)
            "http://twitter3e4tixl4xy.onion",
            "http://protonmailrmez3lotccipshtkleegetolb73fuirgj7r4o4vfu7ozyd.onion",
            "http://secmailw453j7piv.onion",
            "http://mailtorxbyap6t7o.onion",
            "http://bitcoinheist.com",
            "http://blockchainbdgpzk.onion",
            "http://dnmooooddf3d3ffq.onion",
            "http://silkroad6ownowfk.onion",
            "http://alphabaym2fgs3ew.onion",
            "http://hydraclubbioknikokex7njhwuahc2l67lfiz7z36md2jvopda7nchid.onion",
            "http://asap2u4pvln7f3lo.onion",
            "http://whitehouse2i6z2s7.onion",
            "http://darknetlive.com",
            "http://www.gwern.net",
            "http://www.globaleaks.org",
            "http://www.riseup.net",
        ]
        urls.extend(onion)

        # =====================================================
        # ✅ ELIMINAR DUPLICADOS Y DEVOLVER
        # =====================================================
        urls_unicas = list(dict.fromkeys(urls))
        print(f"✅ TOTAL SEMILLAS CARGADAS: {len(urls_unicas)}")
        print(f"🎯 Dorks GitHub: {len(dorks_github)}")
        print(f"🎣 Dorks Phishing: {len(dorks_phishing)}")
        print(f"📡 Feeds de amenazas: {len(feeds)}")
        print(f"🕵️ Sitios de investigación: {len(sitios_investigacion)}")
        print(f"🧅 Onion: {len(onion)}")
        print("="*70)
        return urls_unicas

    # =====================================================
    # (Opcional) Cargar semillas desde archivo local
    # =====================================================
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
