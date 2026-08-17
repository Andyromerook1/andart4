import re
import json
import os
import config
from blockchain_client import BlockchainClient
from phishing_detector import PhishingDetector
from js_analyzer import JSAnalyzer

class MotorFiltro:
    # Patrones que NO distinguen mayúsculas/minúsculas
    IGNORE_CASE = [
        "Contraseña",
        "Clave API",
        "Cadena",
        "Número Tarjeta",
        "Clave Secreta",
        "Cadena tipo"
    ]

    # 🔴 Nivel ALTO → Claves reales que permiten acceso
    ALTO_RIESGO = [
        "Clave AWS", "Token Telegram", "Token GitHub", "Clave API Google",
        "Clave OpenAI", "Clave Stripe", "Clave Discord", "Clave SSH privada",
        "Clave SendGrid", "Token Google Cloud", "Clave Groq", "Clave OpenRouter",
        "Clave MercadoPago", "Clave Twilio", "Clave Resend Email",
        "Conexión MongoDB", "Conexión Postgres/MySQL"
    ]
    
    # 🟡 Nivel MEDIO → Posibles secretos
    MEDIO_RIESGO = [
        "Clave Firebase", "Clave Slack", "Token Discord Bot",
        "Clave Anthropic", "Clave DeepSeek", "Clave Gemini",
        "Clave Mistral AI", "Clave Together AI", "Clave Replicate",
        "Clave Cohere", "Clave ElevenLabs", "Clave Hugging Face",
        "Clave Perplexity AI", "Token DigitalOcean", "Clave OpenAI Project"
    ]

    # =============================================================
    # 🧠 FILTROS INTELIGENTES — SIN ROMPER TU LÓGICA
    # =============================================================
    @staticmethod
    def validar_luhn(numero: str) -> bool:
        digitos = [int(d) for d in numero if d.isdigit()]
        if len(digitos) < 13 or len(digitos) > 19:
            return False
        suma = 0
        alternar = False
        for d in reversed(digitos):
            if alternar:
                d *= 2
                if d > 9:
                    d -= 9
            suma += d
            alternar = not alternar
        return suma % 10 == 0

    @staticmethod
    def es_ruido_obvio(valor: str) -> bool:
        s = re.sub(r'[\s\-]+', '', valor)
        if len(set(s)) == 1:
            return True
        if "00000" in s or s.endswith("000000"):
            return True
        if s in "0123456789" or s in "9876543210":
            return True
        if s.count('0') > len(s) / 2:
            return True
        return False

    # =============================================================
    # 🚀 TU LÓGICA ORIGINAL — INTACTA
    # =============================================================
    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)
        self.patrones = {}
        for nombre, regex in datos.items():
            banderas = re.IGNORECASE if any(ignorado in nombre for ignorado in self.IGNORE_CASE) else 0
            self.patrones[nombre] = re.compile(regex, banderas)

        # Inicializamos el cliente blockchain solo si está activado
        self.blockchain_client = None
        if config.AUTO_BLOCKCHAIN_ANALYSIS:
            try:
                self.blockchain_client = BlockchainClient()
            except Exception as e:
                print(f"⚠️ Error inicializando BlockchainClient: {e}")

        self.phishing_detector = None
        self.js_analyzer = None
        if config.ENABLE_PHISHING_DETECTION:
            try:
                self.phishing_detector = PhishingDetector()
            except Exception as e:
                print(f"⚠️ Error inicializando PhishingDetector: {e}")
        if config.ENABLE_JS_ANALYSIS:
            try:
                self.js_analyzer = JSAnalyzer()
            except Exception as e:
                print(f"⚠️ Error inicializando JSAnalyzer: {e}")

        # 🔥 NUEVO: caché de direcciones fallidas para no repetir consultas
        self.direcciones_fallidas = set()

    def _nivel_peligro(self, nombre):
        if any(peligro in nombre for peligro in self.ALTO_RIESGO):
            return "🔴 ALTO"
        if any(peligro in nombre for peligro in self.MEDIO_RIESGO):
            return "🟡 MEDIO"
        return "🟢 BAJO"

    def _detectar_blockchain(self, texto):
        texto = texto.strip()
        if texto.startswith('0x'):
            return 'ethereum'
        elif texto.startswith('T'):
            return 'tron'
        elif texto.startswith('bc1') or texto.startswith('1') or texto.startswith('3'):
            return 'bitcoin'
        elif texto.startswith('addr1'):
            return 'cardano'
        elif texto.startswith('r'):
            return 'ripple'
        elif texto.startswith('L') or texto.startswith('M') or texto.startswith('ltc1'):
            return 'litecoin'
        elif texto.startswith('D'):
            return 'dogecoin'
        else:
            if 43 <= len(texto) <= 44 and re.match(r'^[A-Za-z0-9]{43,44}$', texto):
                return 'solana'
        return None

    @staticmethod
    def es_direccion_valida(direccion, blockchain):
        """Valida el formato de una dirección de criptomoneda antes de consultar la API."""
        if not direccion or len(direccion) < 20:
            return False
        if blockchain == 'tron':
            return bool(re.match(r'^T[a-zA-Z0-9]{33}$', direccion))
        elif blockchain == 'ethereum':
            return bool(re.match(r'^0x[a-fA-F0-9]{40}$', direccion))
        elif blockchain == 'bitcoin':
            return bool(re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', direccion) or
                        re.match(r'^bc1[a-z0-9]{39,59}$', direccion))
        elif blockchain == 'solana':
            return bool(re.match(r'^[A-Za-z0-9]{43,44}$', direccion))
        else:
            # Para otras cadenas (ADA, XRP, etc.) solo verificamos longitud
            return len(direccion) > 25

    def _enriquecer_direccion(self, direccion, blockchain):
        """Consulta blockchain solo si la dirección es válida y no ha fallado antes."""
        if not self.blockchain_client:
            return None
        if direccion in self.direcciones_fallidas:
            return None
        if not self.es_direccion_valida(direccion, blockchain):
            self.direcciones_fallidas.add(direccion)
            return None
        try:
            if blockchain in ['tron', 'ethereum', 'bsc']:
                return self.blockchain_client.analyze_address(direccion, blockchain)
            else:
                return None
        except Exception as e:
            self.direcciones_fallidas.add(direccion)
            print(f"⚠️ Error en análisis blockchain para {direccion}: {e}")
            return None

    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        ya_encontrado = set()
        ruido_descartado = 0

        # --- 1. Escaneo de patrones generales (tu lógica original) ---
        for nombre, regex in self.patrones.items():
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if not valor or len(valor) <= 5:
                    continue

                es_valido = True
                if "Tarjeta" in nombre:
                    if self.es_ruido_obvio(valor) or not self.validar_luhn(valor):
                        es_valido = False
                else:
                    if self.es_ruido_obvio(valor):
                        es_valido = False

                if not es_valido:
                    ruido_descartado += 1
                    continue

                clave_unica = f"{nombre}:{valor[:80]}"
                if clave_unica not in ya_encontrado:
                    ya_encontrado.add(clave_unica)
                    hallazgo = {
                        "tipo": nombre,
                        "valor": valor,
                        "origen": origen,
                        "peligro": self._nivel_peligro(nombre)
                    }
                    hallazgos.append(hallazgo)

                    # Enriquecimiento blockchain con validación
                    if "Billetera" in nombre or any(c in nombre for c in ["BTC", "ETH", "TRX", "SOL", "ADA", "XRP"]):
                        blockchain = self._detectar_blockchain(valor)
                        if blockchain:
                            enriquecido = self._enriquecer_direccion(valor, blockchain)
                            if enriquecido:
                                try:
                                    with open(config.BLOCKCHAIN_INSIGHTS_FILE, "a", encoding="utf-8") as f:
                                        f.write(json.dumps(enriquecido, indent=2) + "\n")
                                    print(f"   🔗 Blockchain enriquecida: {valor} - Balance: {enriquecido.get('balance', 'N/A')}")
                                except Exception as e:
                                    print(f"   ⚠️ Error guardando insight blockchain: {e}")

        # --- 2. Detección de dominios clonados (phishing) ---
        if config.ENABLE_PHISHING_DETECTION and self.phishing_detector:
            urls_encontradas = re.findall(r'https?://[^\s<>"\']+', texto)
            for url in urls_encontradas:
                try:
                    dominio = url.split('/')[2]
                    es_clon, legitimo, similitud = self.phishing_detector.es_clon(dominio)
                    if es_clon:
                        hallazgo_clon = {
                            "tipo": "Dominio Clonado (Phishing)",
                            "valor": dominio,
                            "origen": origen,
                            "peligro": "🔴 ALTO",
                            "detalles": f"Clon de {legitimo} (similitud: {similitud:.2%})"
                        }
                        hallazgos.append(hallazgo_clon)
                        self.guardar_hallazgo(hallazgo_clon)
                        print(f"   🚨 DOMINIO CLONADO: {dominio} → imita a {legitimo} (similitud: {similitud:.2%})")
                except Exception:
                    pass

        # --- 3. Análisis de archivos JavaScript ---
        if config.ENABLE_JS_ANALYSIS and self.js_analyzer:
            if origen.endswith('.js') or ('function' in texto and 'var' in texto and '=' in texto):
                resultados_js = self.js_analyzer.analizar_js(texto, origen)
                for endpoint in resultados_js['endpoints']:
                    if endpoint:
                        hallazgo_js = {
                            "tipo": "Endpoint API (JS)",
                            "valor": endpoint,
                            "origen": origen,
                            "peligro": "🟡 MEDIO"
                        }
                        hallazgos.append(hallazgo_js)
                        self.guardar_hallazgo(hallazgo_js)
                        print(f"   📡 Endpoint encontrado: {endpoint}")
                for addr in resultados_js['crypto_addresses']:
                    if addr:
                        hallazgo_js = {
                            "tipo": "Dirección Cripto (JS)",
                            "valor": addr,
                            "origen": origen,
                            "peligro": "🔴 ALTO"
                        }
                        hallazgos.append(hallazgo_js)
                        self.guardar_hallazgo(hallazgo_js)
                        print(f"   💰 Dirección cripto en JS: {addr}")
                        blockchain = self._detectar_blockchain(addr)
                        if blockchain:
                            enriquecido = self._enriquecer_direccion(addr, blockchain)
                            if enriquecido:
                                try:
                                    with open(config.BLOCKCHAIN_INSIGHTS_FILE, "a", encoding="utf-8") as f:
                                        f.write(json.dumps(enriquecido, indent=2) + "\n")
                                    print(f"   🔗 Blockchain enriquecida: {addr} - Balance: {enriquecido.get('balance', 'N/A')}")
                                except Exception as e:
                                    print(f"   ⚠️ Error guardando insight blockchain: {e}")
                for token in resultados_js['keys_tokens']:
                    if token:
                        hallazgo_js = {
                            "tipo": "Clave/Token (JS)",
                            "valor": token,
                            "origen": origen,
                            "peligro": "🔴 ALTO"
                        }
                        hallazgos.append(hallazgo_js)
                        self.guardar_hallazgo(hallazgo_js)
                        print(f"   🔑 Clave/Token en JS: {token}")

        if ruido_descartado > 0:
            print(f"   🧹 {ruido_descartado} coincidencias descartadas en: {origen[:50]}")
        return hallazgos

    def guardar_hallazgo(self, hallazgo):
        detalles = hallazgo.get('detalles', '')
        linea = f"{hallazgo['peligro']} | [{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}"
        if detalles:
            linea += f" (Detalles: {detalles})"
        linea += "\n"
        # Usamos la ruta definida en config
        with open(config.HALLAZGOS_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
        print(f"✅ {hallazgo['peligro']} HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
