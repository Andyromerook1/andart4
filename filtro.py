import re
import json
import config
from blockchain_client import BlockchainClient
from phishing_detector import PhishingDetector
from js_analyzer import JSAnalyzer

class MotorFiltro:
    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)
        self.patrones = {
            nombre: re.compile(regex)
            for nombre, regex in datos.items()
            if regex  # ignora la clave separadora "===== CRIPTOMONEDAS ====="
        }

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

        self.direcciones_fallidas = set()

    @staticmethod
    def es_ruido_obvio(valor: str) -> bool:
        s = re.sub(r'[\s\-]+', '', valor)
        if len(set(s)) == 1:
            return True
        if s.count('0') > len(s) / 2:
            return True
        return False

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
        elif texto.startswith(('L', 'M', 'ltc1')):
            return 'litecoin'
        elif texto.startswith('D'):
            return 'dogecoin'
        elif 43 <= len(texto) <= 44 and re.match(r'^[A-Za-z0-9]{43,44}$', texto):
            return 'solana'
        return None

    @staticmethod
    def es_direccion_valida(direccion, blockchain):
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
        return len(direccion) > 25

    def _enriquecer_direccion(self, direccion, blockchain):
        if not self.blockchain_client or direccion in self.direcciones_fallidas:
            return None
        if not self.es_direccion_valida(direccion, blockchain):
            self.direcciones_fallidas.add(direccion)
            return None
        try:
            if blockchain in ['tron', 'ethereum', 'bsc']:
                return self.blockchain_client.analyze_address(direccion, blockchain)
        except Exception as e:
            self.direcciones_fallidas.add(direccion)
            print(f"⚠️ Error en análisis blockchain para {direccion}: {e}")
        return None

    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        ya_encontrado = set()

        # --- 1. Patrones: email + direcciones cripto ---
        for nombre, regex in self.patrones.items():
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if not valor or len(valor) <= 5 or self.es_ruido_obvio(valor):
                    continue
                clave_unica = f"{nombre}:{valor[:80]}"
                if clave_unica in ya_encontrado:
                    continue
                ya_encontrado.add(clave_unica)
                hallazgo = {"tipo": nombre, "valor": valor, "origen": origen, "peligro": "🔴 ALTO"}
                hallazgos.append(hallazgo)

                if nombre != "Correo Electrónico":
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

        # --- 2. Dominios clonados (phishing) ---
        if config.ENABLE_PHISHING_DETECTION and self.phishing_detector:
            for url in re.findall(r'https?://[^\s<>"\']+', texto):
                try:
                    dominio = url.split('/')[2]
                    es_clon, legitimo, similitud = self.phishing_detector.es_clon(dominio)
                    if es_clon:
                        h = {"tipo": "Dominio Clonado (Phishing)", "valor": dominio, "origen": origen,
                             "peligro": "🔴 ALTO", "detalles": f"Clon de {legitimo} (similitud: {similitud:.2%})"}
                        hallazgos.append(h)
                        self.guardar_hallazgo(h)
                        print(f"   🚨 DOMINIO CLONADO: {dominio} → imita a {legitimo}")
                except Exception:
                    pass

        # --- 3. Análisis JS: endpoints + direcciones cripto (SIN cosecha de claves) ---
        if config.ENABLE_JS_ANALYSIS and self.js_analyzer:
            if origen.endswith('.js') or ('function' in texto and 'var' in texto and '=' in texto):
                resultados_js = self.js_analyzer.analizar_js(texto, origen)
                for endpoint in resultados_js.get('endpoints', []):
                    if endpoint:
                        h = {"tipo": "Endpoint API (JS)", "valor": endpoint, "origen": origen, "peligro": "🟡 MEDIO"}
                        hallazgos.append(h)
                        self.guardar_hallazgo(h)
                for addr in resultados_js.get('crypto_addresses', []):
                    if addr:
                        h = {"tipo": "Dirección Cripto (JS)", "valor": addr, "origen": origen, "peligro": "🔴 ALTO"}
                        hallazgos.append(h)
                        self.guardar_hallazgo(h)
                        blockchain = self._detectar_blockchain(addr)
                        if blockchain:
                            enriquecido = self._enriquecer_direccion(addr, blockchain)
                            if enriquecido:
                                try:
                                    with open(config.BLOCKCHAIN_INSIGHTS_FILE, "a", encoding="utf-8") as f:
                                        f.write(json.dumps(enriquecido, indent=2) + "\n")
                                except Exception as e:
                                    print(f"   ⚠️ Error guardando insight blockchain: {e}")
                # NOTA: se quitó el bloque que reportaba resultados_js['keys_tokens']

        return hallazgos

    def guardar_hallazgo(self, hallazgo):
        detalles = hallazgo.get('detalles', '')
        linea = f"{hallazgo['peligro']} | [{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}"
        if detalles:
            linea += f" (Detalles: {detalles})"
        linea += "\n"
        with open(config.HALLAZGOS_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
        print(f"✅ {hallazgo['peligro']} HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
