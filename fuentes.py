import requests
import random

class FuentesSemillas:
    def __init__(self):
        pass

    # =============================================================
    # 🌐 SEMILLAS GLOBALES — PUERTAS DE ENTRADA A TODO EL MUNDO
    # =============================================================
    def obtener_todas(self):
        print("\n" + "="*70)
        print("   🌍 CARGANDO SEMILLAS GLOBALES — TODOS LOS CONTINENTES")
        print("="*70)
        urls = []

        # =====================================================
        # 🏛️ BLOQUE 1: DIRECTORIOS Y CATÁLOGOS QUE ENLAZAN A TODO
        # =====================================================
        urls.extend([
            # Datos abiertos y portales internacionales
            "https://data.worldbank.org",
            "https://datacatalog.worldbank.org",
            "https://data.europa.eu",
            "https://ckan.org",
            "https://github.com/public-apis/public-apis",
            "https://www.un.org",
            "https://www.oas.org",
            "https://www.worldbank.org",
            "https://www.unesco.org",
            "https://www.who.int",
            "https://www.interpol.int",
            "https://www.imf.org",
            "https://www.oecd.org",
            "https://www.nato.int",
            "https://www.wto.org",
            "https://www.itu.int",
            "https://www.fao.org",
            "https://www.ohchr.org",
        ])

        # =====================================================
        # 🇪🇸 BLOQUE 2: IBEROAMÉRICA Y ESPAÑA
        # =====================================================
        urls.extend([
            # Argentina
            "https://www.argentina.gob.ar",
            "https://datos.gob.ar",
            "https://www.boletinoficial.gob.ar",
            # México
            "https://www.gob.mx",
            "https://www.datos.gob.mx",
            # Brasil
            "https://www.gov.br",
            "https://dados.gov.br",
            # España
            "https://www.mpr.gob.es",
            "https://www.boe.es",
            "https://administracion.gob.es",
            # Chile
            "https://www.gob.cl",
            "https://datos.gob.cl",
            # Colombia
            "https://www.gov.co",
            "https://www.datos.gov.co",
            # Perú
            "https://www.gob.pe",
            "https://www.datos.gob.pe",
            # Uruguay
            "https://www.gub.uy",
            "https://datos.gub.uy",
            # Ecuador
            "https://www.gob.ec",
            "https://www.datos.gob.ec",
            # Paraguay
            "https://www.gov.py",
            # Bolivia
            "https://www.gob.bo",
            # Venezuela
            "https://www.gob.ve",
            # Guatemala
            "https://www.gob.gt",
            # El Salvador
            "https://www.gob.sv",
            # Honduras
            "https://www.gob.hn",
            # Nicaragua
            "https://www.gob.ni",
            # Costa Rica
            "https://www.gob.cr",
            # Panamá
            "https://www.gob.pa",
            # República Dominicana
            "https://www.gob.do",
            # Cuba
            "https://www.gob.cu",
            # Puerto Rico
            "https://www.pr.gov",
        ])

        # =====================================================
        # 🇺🇸 BLOQUE 3: NORTEAMÉRICA Y ANGLÓFONOS
        # =====================================================
        urls.extend([
            # EE.UU.
            "https://www.usa.gov",
            "https://www.data.gov",
            "https://www.whitehouse.gov",
            "https://www.congress.gov",
            # Canadá
            "https://www.canada.ca",
            "https://open.canada.ca",
            # Reino Unido
            "https://www.gov.uk",
            "https://data.gov.uk",
            # Australia
            "https://www.gov.au",
            "https://data.gov.au",
            # Nueva Zelanda
            "https://www.govt.nz",
            "https://www.data.govt.nz",
        ])

        # =====================================================
        # 🇪🇺 BLOQUE 4: UNIÓN EUROPEA Y EUROPA
        # =====================================================
        urls.extend([
            "https://european-union.europa.eu",
            "https://ec.europa.eu",
            "https://www.europarl.europa.eu",
            # Francia
            "https://www.service-public.fr",
            "https://www.gouv.fr",
            # Alemania
            "https://www.bund.de",
            "https://www.deutschland.de",
            # Italia
            "https://www.governo.it",
            # Portugal
            "https://www.portugal.gov.pt",
            # Polonia
            "https://www.gov.pl",
            # Países Bajos
            "https://www.rijksoverheid.nl",
            # Bélgica
            "https://www.belgium.be",
            # Suiza
            "https://www.admin.ch",
            # Suecia
            "https://www.regeringen.se",
            # Noruega
            "https://www.regjeringen.no",
            # Dinamarca
            "https://www.regeringen.dk",
            # Finlandia
            "https://www.valtioneuvosto.fi",
            # Grecia
            "https://www.gov.gr",
            # Rusia
            "https://www.gov.ru",
            "https://www.kremlin.ru",
            # Ucrania
            "https://www.kmu.gov.ua",
        ])

        # =====================================================
        # 🇨🇳 BLOQUE 5: ASIA Y OCEANÍA
        # =====================================================
        urls.extend([
            # China
            "https://www.gov.cn",
            "https://www.www.gov.cn",
            # Japón
            "https://www.japan.go.jp",
            "https://www.kantei.go.jp",
            # India
            "https://www.india.gov.in",
            "https://data.gov.in",
            # Corea del Sur
            "https://www.korea.kr",
            "https://www.go.kr",
            # Singapur
            "https://www.gov.sg",
            # Filipinas
            "https://www.gov.ph",
            # Tailandia
            "https://www.thaigov.go.th",
            # Vietnam
            "https://www.gov.vn",
            # Malasia
            "https://www.gov.my",
            # Indonesia
            "https://www.kemendag.go.id",
            # Arabia Saudita
            "https://www.saudi.gov.sa",
            # Emiratos Árabes
            "https://u.ae",
            # Israel
            "https://www.gov.il",
            # Turquía
            "https://www.turkiye.gov.tr",
        ])

        # =====================================================
        # 🇿🇦 BLOQUE 6: ÁFRICA
        # =====================================================
        urls.extend([
            "https://www.gov.za",          # Sudáfrica
            "https://www.nigeria.gov.ng",  # Nigeria
            "https://www.egypt.gov.eg",    # Egipto
            "https://www.maroc.ma",        # Marruecos
            "https://www.gouv.sn",         # Senegal
            "https://www.gouv.ci",         # Costa de Marfil
            "https://www.mfa.gov.et",      # Etiopía
            "https://www.ug.go.ug",        # Uganda
            "https://www.tanzania.go.tz",  # Tanzania
            "https://www.gov.ke",          # Kenia
            "https://www.rwanda.gov.rw",   # Ruanda
            "https://www.gov.gh",          # Ghana
            "https://www.mozambique.gov.mz", # Mozambique
            "https://www.angola.gov.ao",   # Angola
            "https://www.algeria.gov.dz",  # Argelia
            "https://www.tunisie.tn",      # Túnez
        ])

        # =====================================================
        # 📖 BLOQUE 7: WIKIPEDIA — LA LLAVE MAESTRA
        # =====================================================
        urls.extend([
            # Español
            "https://es.wikipedia.org/wiki/Portada",
            "https://es.wikipedia.org/wiki/Anexo:Pa%C3%ADses_del_mundo",
            "https://es.wikipedia.org/wiki/Categor%C3%ADa:Gobiernos_nacionales",
            "https://es.wikipedia.org/wiki/Categor%C3%ADa:Municipios_por_pa%C3%ADs",
            "https://es.wikipedia.org/wiki/Anexo:Organizaciones_internacionales",
            # Inglés
            "https://en.wikipedia.org/wiki/List_of_sovereign_states",
            "https://en.wikipedia.org/wiki/List_of_governments",
            "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies",
            "https://en.wikipedia.org/wiki/Category:Governments_by_country",
            "https://en.wikipedia.org/wiki/Category:Municipalities_by_country",
            # Francés
            "https://fr.wikipedia.org/wiki/Liste_des_pays_du_monde",
            "https://fr.wikipedia.org/wiki/Gouvernement",
            # Alemán
            "https://de.wikipedia.org/wiki/Liste_der_Staaten_der_Erde",
            # Portugués
            "https://pt.wikipedia.org/wiki/Lista_de_pa%C3%ADses",
            # Italiano
            "https://it.wikipedia.org/wiki/Lista_di_stati_del_mondo",
            # Ruso
            "https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B3%D0%BE%D1%81%D1%83%D0%B4%D0%B0%D1%80%D1%81%D1%82%D0%B2",
            # Árabe
            "https://ar.wikipedia.org/wiki/قائمة_الدول",
            # Chino
            "https://zh.wikipedia.org/wiki/世界各国列表",
        ])

        # =====================================================
        # 🔍 BLOQUE 8: BUSCADORES Y AGREGADORES MASIVOS
        # =====================================================
        urls.extend([
            "https://www.google.com",
            "https://www.bing.com",
            "https://www.yahoo.com",
            "https://duckduckgo.com",
            "https://www.wikipedia.org",
            "https://news.google.com",
            "https://www.bbc.com",
            "https://www.reuters.com",
            "https://www.nytimes.com",
            "https://www.wikidata.org",
            "https://www.data.gov",
            "https://www.opendata.aws",
        ])

        # =====================================================
        # 🏙️ BLOQUE 9: MUNICIPALIDADES Y GOBIERNOS LOCALES 🌍
        # =====================================================
        # ⚡ ESTAS SON LAS PÁGINAS QUE LISTAN CIENTOS DE MUNICIPIOS → EL BOT LOS SIGUE
        urls.extend([
            # --- ARGENTINA ---
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_Argentina",
            "https://es.wikipedia.org/wiki/Anexo:Comunas_de_la_provincia_de_Buenos_Aires",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_C%C3%B3rdoba",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Santa_Fe",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Mendoza",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Entre_R%C3%ADos",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_San_Luis",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_San_Juan",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Catamarca",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_La_Rioja",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Santiago_del_Estero",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Tucum%C3%A1n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Salta",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Jujuy",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Chubut",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_R%C3%ADo_Negro",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Neuqu%C3%A9n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_La_Pampa",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Corrientes",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Misiones",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Formosa",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Chaco",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_La_Pampa",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Santa_Cruz",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Tierra_del_Fuego",

            # --- MÉXICO ---
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_M%C3%A9xico",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Jalisco",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Nuevo_Le%C3%B3n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_del_Estado_de_M%C3%A9xico",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Veracruz",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Puebla",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Guanajuato",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Chihuahua",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Oaxaca",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Quer%C3%A9taro",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Yucat%C3%A1n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Quintana_Roo",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Campeche",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Sonora",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Tamaulipas",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_San_Luis_Potos%C3%AD",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Hidalgo",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Michoac%C3%A1n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Colima",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Nayarit",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Sinaloa",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Durango",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Zacatecas",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Aguascalientes",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Baja_California",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Baja_California_Sur",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Coahuila",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Chiapas",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Guerrero",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Morelos",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Tlaxcala",

            # --- ESPAÑA ---
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Espa%C3%B1a",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_Comunidad_de_Madrid",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_la_provincia_de_Barcelona",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Andaluc%C3%ADa",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Catalu%C3%B1a",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Comunidad_Valenciana",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Galicia",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Castilla_y_Le%C3%B3n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Castilla-La_Mancha",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Pa%C3%ADs_Vasco",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Asturias",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Cantabria",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_La_Rioja",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Murcia",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Extremadura",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Arag%C3%B3n",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Canarias",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Baleares",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Navarra",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Ceuta",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Melilla",

            # --- BRASIL ---
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Brasil",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_estado_de_S%C3%A3o_Paulo",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Rio_de_Janeiro",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Minas_Gerais",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_da_Bahia",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Rio_Grande_do_Sul",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Paran%C3%A1",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Pernambuco",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Cear%C3%A1",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Par%C3%A1",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Santa_Catarina",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Goi%C3%A1s",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Maranh%C3%A3o",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Piau%C3%AD",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Rio_Grande_do_Norte",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_da_Para%C3%ADba",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Amazonas",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Esp%C3%ADrito_Santo",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Alagoas",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Sergipe",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Amap%C3%A1",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Roraima",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Tocantins",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_de_Rond%C3%B4nia",
            "https://pt.wikipedia.org/wiki/Lista_de_munic%C3%ADpios_do_Acre",

            # --- CHILE, COLOMBIA, PERÚ, URUGUAY, PARAGUAY, BOLIVIA, VENEZUELA ---
            "https://es.wikipedia.org/wiki/Anexo:Comunas_de_Chile",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Colombia",
            "https://es.wikipedia.org/wiki/Anexo:Distritos_del_Per%C3%BA",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Uruguay",
            "https://es.wikipedia.org/wiki/Anexo:Distritos_de_Paraguay",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Bolivia",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Venezuela",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Ecuador",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Panam%C3%A1",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Costa_Rica",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Honduras",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_El_Salvador",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Guatemala",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Nicaragua",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Rep%C3%BAblica_Dominicana",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Cuba",
            "https://es.wikipedia.org/wiki/Anexo:Municipios_de_Puerto_Rico",

            # --- ESTADOS UNIDOS Y CANADÁ ---
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_the_United_States",
            "https://en.wikipedia.org/wiki/List_of_cities_in_the_United_States",
            "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_California",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Texas",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Florida",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_New_York_(state)",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Pennsylvania",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Illinois",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Ohio",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Georgia_(U.S._state)",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_North_Carolina",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Michigan",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Virginia",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_New_Jersey",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Washington_(state)",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Arizona",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Massachusetts",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Colorado",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Maryland",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Minnesota",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Wisconsin",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Oregon",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Oklahoma",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Connecticut",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Iowa",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Missouri",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Nevada",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Canada",

            # --- EUROPA NO HISPANA ---
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_the_United_Kingdom",
            "https://en.wikipedia.org/wiki/List_of_cities_in_the_United_Kingdom",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_France",
            "https://en.wikipedia.org/wiki/List_of_communes_in_France",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Germany",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Germany",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Italy",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Portugal",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Poland",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_the_Netherlands",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Belgium",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Switzerland",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Sweden",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Norway",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Denmark",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Finland",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Greece",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Russia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Russia",
            "https://en.wikipedia.org/wiki/List_of_municipalities_in_Ukraine",
            "https://en.wikipedia.org/wiki/List_of_local_government_areas_in_Australia",
            "https://en.wikipedia.org/wiki/List_of_twinned_cities_and_towns_in_the_United_States",

            # --- ASIA Y OCEANÍA ---
            "https://en.wikipedia.org/wiki/List_of_cities_in_China",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Japan",
            "https://en.wikipedia.org/wiki/List_of_cities_in_India",
            "https://en.wikipedia.org/wiki/List_of_cities_in_South_Korea",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Southeast_Asia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_the_Philippines",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Indonesia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Malaysia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Vietnam",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Thailand",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Singapore",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Saudi_Arabia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_the_United_Arab_Emirates",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Israel",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Turkey",
            "https://en.wikipedia.org/wiki/List_of_cities_in_New_Zealand",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Australia",

            # --- ÁFRICA ---
            "https://en.wikipedia.org/wiki/List_of_cities_in_South_Africa",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Nigeria",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Egypt",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Morocco",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Kenya",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Ghana",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Ethiopia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Tanzania",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Uganda",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Algeria",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Tunisia",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Senegal",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Ivory_Coast",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Angola",
            "https://en.wikipedia.org/wiki/List_of_cities_in_Mozambique",
        ])

        # =====================================================
        # ✅ ELIMINAR DUPLICADOS Y DEVOLVER
        # =====================================================
        urls_unicas = list(dict.fromkeys(urls))
        print(f"✅ TOTAL SEMILLAS CARGADAS: {len(urls_unicas)}")
        print(f"🌍 Iberoamérica/ES: {sum(1 for u in urls_unicas if '.ar' in u or '.mx' in u or '.br' in u or '.gob' in u)}")
        print(f"🌎 Norteamérica/UK/AU: {sum(1 for u in urls_unicas if '.gov' in u or '.ca' in u or '.uk' in u or '.au' in u)}")
        print(f"🌏 Europa: {sum(1 for u in urls_unicas if '.eu' in u or '.de' in u or '.fr' in u or '.it' in u or '.ru' in u)}")
        print(f"🌏 Asia: {sum(1 for u in urls_unicas if '.cn' in u or '.jp' in u or '.in' in u or '.kr' in u or '.sg' in u)}")
        print(f"🌍 África: {sum(1 for u in urls_unicas if '.za' in u or '.ng' in u or '.eg' in u or '.gov.af' in u)}")
        print(f"📖 Wikipedia: {sum(1 for u in urls_unicas if 'wikipedia.org' in u)}")
        print("="*70)
        return urls_unicas

    # =====================================================
    # API Wikipedia: traer artículos al azar como semillas extra
    # =====================================================
    def desde_wikipedia(self, cantidad=15):
        urls = []
        idiomas = ["es", "en", "fr", "de", "pt", "it", "ru", "zh", "ar"]
        try:
            for lang in idiomas:
                resp = requests.get(
                    f"https://{lang}.wikipedia.org/w/api.php?action=query&list=random&rnnamespace=0&rnlimit={cantidad}&format=json",
                    timeout=10, headers={"User-Agent": "MiBot/1.0"}
                )
                if resp.status_code == 200:
                    datos = resp.json()
                    for item in datos.get("query", {}).get("random", []):
                        titulo = item["title"].replace(" ", "_")
                        urls.append(f"https://{lang}.wikipedia.org/wiki/{titulo}")
        except Exception:
            pass
        return urls

    # =====================================================
    # API GitHub: traer repositorios públicos al azar
    # =====================================================
    def desde_github_api(self, cantidad=15):
        urls = []
        try:
            resp = requests.get(
                "https://api.github.com/repositories?since=0",
                timeout=10, headers={"User-Agent": "MiBot/1.0"}
            )
            if resp.status_code == 200:
                datos = resp.json()
                for repo in datos[:cantidad]:
                    if "html_url" in repo:
                        urls.append(repo["html_url"])
        except Exception:
            pass
        return urls

    # =====================================================
    # Cargar semillas desde archivo local
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
