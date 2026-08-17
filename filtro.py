# filtro.py
import re
import json
import config
from blockchain_client import BlockchainClient
from phishing_detector import PhishingDetector
from js_analyzer import JSAnalyzer

# Tipos que son cuentas financieras tradicionales (no se consultan contra blockchain)
TIPOS_CUENTA_FINANCIERA = [
    "CBU/CVU", "CLABE", "IBAN", "PIX", "SWIFT"
]


class MotorFiltro:
    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)
        self.patrones = {
            nombre: re.compile(regex)
            for nombre, regex in datos.items()
            if regex and not nombre.startswith("=====")
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

    # =============================================================
    # 🧹 RUIDO / VALIDACIÓN
    # =============================================================
    @staticmethod
    def es_ruido_obvio(valor: str) -> bool:
        s = re.sub(r'[\s\-]+', '', valor)
        if len(set(s)) == 1:
            return True
        if s.count('0') > len(s) / 2:
            return True
        return False

    @staticmethod
    def validar_cbu(cbu: str) -> bool:
        """
        Valida CBU/CVU argentino (22 dígitos) con su algoritmo real de
        dígito verificador, para descartar los 21+ dígitos random que
        matchean el regex pero no son una cuenta real.
        Estructura: 3 (entidad) + 1 (DV entidad) + 3 (sucursal) + 1 (DV sucursal)
                    + 13 (cuenta) + 1 (DV cuenta)
        """
        cbu = re.sub(r'\D', '', cbu)
        if len(cbu) != 22:
            return False

        def _dv(bloque, pesos):
            suma = sum(int(d) * p for d, p in zip(bloque, pesos))
            resto = suma % 10
            return 0 if resto == 0 else 10 - resto

        # Primer bloque: entidad(3) + sucursal(3) + DV(1) = 8 dígitos, pesos 7-1-3-9-7-1-3
        bloque1 = cbu[0:7]
        dv1_esperado = int(cbu[7])
        pesos1 = [7, 1, 3, 9, 7, 1, 3]
        if _dv(bloque1, pesos1) != dv1_esperado:
            return False

        # Segundo bloque: cuenta(13) + DV(1) = 14 dígitos, pesos 3-9-7-1-3-9-7-1-3-9-7-1-3
        bloque2 = cbu[8:21]
        dv2_esperado = int(cbu[21])
        pesos2 = [3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3]
        if _dv(bloque2, pesos2) != dv2_esperado:
            return False

        return True

    @staticmethod
    def validar_iban(iban: str) -> bool:
        """Valida IBAN con el algoritmo mod-97 estándar (ISO 7064)."""
        iban = iban.replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            return False
        reordenado = iban[4:] + iban[:4]
        convertido = ""
        for ch in reordenado:
            convertido += str(int(ch, 36)) if ch.isalpha() else ch
        try:
            return int(convertido) % 97 == 1
        except ValueError:
            return False

    def _es_cuenta_financiera_valida(self, nombre, valor):
        if "CBU" in nombre:
            return self.validar_cbu(valor)
        if "IBAN" in nombre:
            return self.validar_iban(valor)
        # CLABE, PIX, SWIFT: por ahora solo validación de formato (ya la hace el regex)
        return True

    # =============================================================
    # 🔗 BLOCKCHAIN
    # =============================================================
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

    # =============================================================
    # 🔍 ESCANEO PRINCIPAL
    # =============================================================
    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        ya_encontrado = set()

        # --- 1. Patrones: email, cuentas financieras, cripto ---
        for nombre, regex in self.patrones.items():
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if not valor or len(valor) <= 5 or self.es_ruido_obvio(valor):
                    continue

                es_cuenta_financiera = any(t in nombre for t in TIPOS_CUENTA_FINANCIERA)
                if es_cuenta_financiera and not self._es_cuenta_financiera_valida(nombre, valor):
                    continue  # descarta CBU/IBAN con dígito verificador inválido

                clave_unica = f"{nombre}:{valor[:80]}"
                if clave_unica in ya_encontrado:
                    continue
                ya_encontrado.add(clave_unica)

                hallazgo = {"tipo": nombre, "valor": valor, "origen": origen, "peligro": "🔴 ALTO"}
                hallazgos.append(hallazgo)

                if nombre != "Correo Electrónico" and not es_cuenta_financiera:
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

        # --- 3. Análisis JS: endpoints + direcciones cripto ---
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

        # --- 4. PUENTE: cuenta financiera + wallet en el mismo origen ---
        self._detectar_puente(hallazgos, origen)

        return hallazgos

    def _detectar_puente(self, hallazgos, origen):
        """
        Si en el mismo origen aparecen una cuenta financiera (CBU/IBAN/etc.)
        Y una dirección cripto, arma un 'caso puente': la pista con dueño
        real (cuenta bancaria) conectada con el destino final del lavado.
        Esto es lo más accionable para un reporte a la policía/fiscalía.
        """
        cuentas = [h for h in hallazgos if any(t in h["tipo"] for t in TIPOS_CUENTA_FINANCIERA)]
        wallets = [h for h in hallazgos if h["tipo"] in (
            "Bitcoin (Legacy)", "Bitcoin (Native SegWit)", "Bitcoin (Taproot)",
            "Ethereum / EVM (Polygon, BNB, Arbitrum, etc.)", "Solana (SOL)",
            "Cardano (ADA)", "Ripple (XRP)", "Tron (TRX)", "Litecoin (Legacy)",
            "Litecoin (Native SegWit)", "Dogecoin", "Dash", "Monero",
            "Zcash (Transparent)", "Zcash (Shielded)", "Stellar (XLM)",
            "Tezos (XTZ)", "Cosmos (ATOM)", "Polkadot (DOT)",
            "Dirección Cripto (JS)"
        )]

        if not cuentas or not wallets:
            return

        for cuenta in cuentas:
            for wallet in wallets:
                caso = {
                    "origen": origen,
                    "cuenta_financiera": {"tipo": cuenta["tipo"], "valor": cuenta["valor"]},
                    "wallet_cripto": {"tipo": wallet["tipo"], "valor": wallet["valor"]},
                }
                self._guardar_caso_puente(caso)
                print(f"   🌉 CASO PUENTE: {cuenta['tipo']} {cuenta['valor']} ←→ {wallet['tipo']} {wallet['valor']}")

    @staticmethod
    def _guardar_caso_puente(caso):
        try:
            with open(config.CASOS_PUENTE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(caso, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"   ⚠️ Error guardando caso puente: {e}")

    def guardar_hallazgo(self, hallazgo):
        detalles = hallazgo.get('detalles', '')
        linea = f"{hallazgo['peligro']} | [{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}"
        if detalles:
            linea += f" (Detalles: {detalles})"
        linea += "\n"
        with open(config.HALLAZGOS_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
        print(f"✅ {hallazgo['peligro']} HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
