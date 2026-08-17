# fuentes.py
import requests
import random

class FuentesSemillas:
    def __init__(self):
        pass

    def obtener_todas(self):
        print("\n" + "="*70)
        print("   🕵️‍♂️ CARGANDO SEMILLAS DE CACERÍA — SPAM, PHISHING Y ESTAFAS")
        print("="*70)
        urls = []

        dorks_github = [
            "https://www.google.com/search?q=site:github.com+%222026%22+%22%E8%AE%A1%E5%88%92%22+%22%E7%BE%A4%22&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+%22%E7%A6%8F%E5%BD%A9%22+%22%E9%A2%84%E6%B5%8B%22&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+inurl:blob+intext:%22%E5%A4%A7%E5%8F%91%22+intext:%E8%B4%A2%E7%BB%8F&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+%22%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF%22+intext:%E8%B5%9A%E9%92%B1&tbs=qdr:d",
            "https://www.google.com/search?q=site:github.com+intext:t.me+intext:lotto+intext:bet+intext:%E4%B8%AD%E5%9B%BD&tbs=qdr:d"
        ]
        urls.extend(dorks_github)

        dorks_phishing = [
            "https://www.google.com/search?q=inurl:login+intext:%22sign+in+to+your+account%22+intext:%22verification%22&tbs=qdr:d",
            "https://www.google.com/search?q=%22connect+wallet%22+intext:%22verify%22+intext:%22security%22&tbs=qdr:d",
            "https://www.google.com/search?q=site:*.top+intext:%22login%22+intext:%22microsoft%22+intext:%22office365%22&tbs=qdr:d",
            "https://www.google.com/search?q=intitle:%22index+of%22+intext:%22phishing%22+OR+%22login%22&tbs=qdr:d"
        ]
        urls.extend(dorks_phishing)

        feeds = [
            "https://urlhaus.abuse.ch/feeds/rss/",
            "https://phishstats.info/phish_score.csv",
            "https://openphish.com/feed.txt",
            "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-links.txt",
            "https://cybercrime-tracker.net/rss.xml",
            "https://cert.europa.eu/static/SecurityAdvisories/",
        ]
        urls.extend(feeds)

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
            "https://www.bitcointalk.org",
            "https://www.cryptocompare.com",
        ]
        urls.extend(sitios_investigacion)

        urls_unicas = list(dict.fromkeys(urls))
        print(f"✅ TOTAL SEMILLAS CARGADAS: {len(urls_unicas)}")
        print(f"🎯 Dorks GitHub: {len(dorks_github)}")
        print(f"🎣 Dorks Phishing: {len(dorks_phishing)}")
        print(f"📡 Feeds de amenazas: {len(feeds)}")
        print(f"🕵️ Sitios de investigación: {len(sitios_investigacion)}")
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
