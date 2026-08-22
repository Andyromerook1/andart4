# filtro.py
import re
import json
import hashlib
import config
from blockchain_client import BlockchainClient
from phishing_detector import PhishingDetector
from js_analyzer import JSAnalyzer

TIPOS_CUENTA_FINANCIERA = ["CBU/CVU", "CLABE", "IBAN", "PIX", "SWIFT"]

TIPOS_WALLET = (
    "Bitcoin (Legacy)", "Bitcoin (Native SegWit)", "Bitcoin (Taproot)",
    "Ethereum / EVM (Polygon, BNB, Arbitrum, etc.)", "Solana (SOL)",
    "Cardano (ADA)", "Ripple (XRP)", "Tron (TRX)", "Litecoin (Legacy)",
    "Litecoin (Native SegWit)", "Dogecoin", "Dash", "Monero",
    "Zcash (Transparent)", "Zcash (Shielded)", "Stellar (XLM)",
    "Tezos (XTZ)", "Cosmos (ATOM)", "Polkadot (DOT)", "Dirección Cripto (JS)"
)

TIPOS_BASE58CHECK = ("Bitcoin (Legacy)", "Litecoin (Legacy)", "Dogecoin", "Dash", "Tron (TRX)")
TIPOS_REGEX_DEBIL = ("Solana (SOL)", "Polkadot (DOT)", "Cosmos (ATOM)", "Ripple (XRP)")

TIPOS_ENTIDAD_NEUTRA = ("Correo Electrónico", "Usuario Telegram (link)",
                         "Usuario Telegram (mención)", "Número WhatsApp (con código país)")

CONTEXTO_WALLET = [
    "wallet", "billetera", "cartera", "deposit", "depósito", "enviar", "envío",
    "pay", "pago", "recibir", "transferencia", "usdt", "btc", "eth", "trx",
    "地址", "钱包", "转账", "充值",
    "address", "dirección",
]

CONTEXTO_CUENTA_FINANCIERA = [
    "cbu", "cvu", "clabe", "iban", "swift", "bic", "pix",
    "cuenta", "banco", "bancaria", "transferencia", "transferir",
    "deposit", "depósito", "pago", "pagar", "enviar dinero",
    "account", "bank", "transfer", "payment",
    "银行", "账户", "转账",
]

CONTEXTO_PIX = [
    "pix", "chave", "chave pix", "pagamento", "transferência",
    "banco", "conta", "depósito", "enviar dinheiro",
]

PATRONES_CONTEXTO_OPERATIVO = [
    r'\b(escrib[íi]nos|contact[áa]nos|escrib[íi]me|contact[áa]me)\b',
    r'\b(envi[áa]|deposit[áa]|transfer[íi])\w*\s+(a|al|a este)\b',
    r'\bpag[áa]\s+(aqu[íi]|ahora|ya)\b',
    r'\bpara\s+(invertir|participar|ingresar|unirte)\s+(contact|escrib|envi)',
    r'\bhac[ée]\s+tu\s+(pago|dep[oó]sito|transferencia)\b',
    r'\bclic[k]?\s+aqu[íi]\s+para\s+(pagar|invertir|depositar)\b',
]

PATRONES_CONTEXTO_DESCRIPTIVO = [
    r'\b(la\s+v[íi]ctima|las\s+v[íi]ctimas|el\s+denunciante)\b',
    r'\b(report[óo]|report[aá]ron|denunci[óo]|denunci[aá]ron)\b',
    r'\b(seg[úu]n\s+(la\s+)?(investigaci[óo]n|polic[íi]a|fuentes))\b',
    r'\b(fue\s+estafad|fueron\s+estafad|cay[óo]\s+en\s+la\s+estafa)\b',
    r'\b(los\s+delincuentes|los\s+estafadores|el\s+estafador)\s+(usaron|utilizaron|se\s+hac[íi]an)\b',
    r'\ben\s+este\s+caso\b',
]

DENYLIST_TELEGRAM = {
    "context", "graph", "type", "media", "keyframes", "supports",
    "toprimitive", "charset", "import", "page", "namespace", "document",
    "viewport", "font-face", "value", "id", "container", "scope",
}

BASE58_ALFABETO = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

CODIGOS_PAIS_ISO_SWIFT = {
    "AR", "US", "GB", "BR", "MX", "ES", "DE", "FR", "IT", "CN", "JP",
    "IN", "CA", "AU", "CH", "NL", "BE", "SE", "NO", "DK", "FI", "PT",
    "PL", "AT", "IE", "RU", "TR", "SA", "AE", "IL", "ZA", "KR", "SG",
    "HK", "TW", "TH", "VN", "ID", "MY", "PH", "NZ", "CL", "CO", "PE",
    "UY", "PY", "BO", "EC", "VE", "CR", "PA", "GT", "HN", "SV", "NI",
    "DO", "CU", "JM", "TT",
}


class MotorFiltro:
    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)
        self.patrones = {
            nombre: re.compile(regex)
            for nombre, regex in datos.items()
            if regex and not nombre.startswith("=====")
        }

        self._patrones_operativo = [re.compile(p, re.IGNORECASE) for p in PATRONES_CONTEXTO_OPERATIVO]
        self._patrones_descriptivo = [re.compile(p, re.IGNORECASE) for p in PATRONES_CONTEXTO_DESCRIPTIVO]

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
        self.indice_correlacion = self._cargar_indice_correlacion()
        self._hallazgos_guardados = {}

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
    def validar_base58check(direccion: str) -> bool:
        try:
            if not direccion or any(c not in BASE58_ALFABETO for c in direccion):
                return False
            num = 0
            for char in direccion:
                num = num * 58 + BASE58_ALFABETO.index(char)
            combinado = num.to_bytes((num.bit_length() + 7) // 8, 'big') if num else b''
            ceros_iniciales = len(direccion) - len(direccion.lstrip('1'))
            decodificado = b'\x00' * ceros_iniciales + combinado
            if len(decodificado) < 5:
                return False
            payload, checksum = decodificado[:-4], decodificado[-4:]
            checksum_calculado = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
            return checksum_calculado == checksum
        except Exception:
            return False

    @staticmethod
    def validar_cbu(cbu: str) -> bool:
        cbu = re.sub(r'\D', '', cbu)
        if len(cbu) != 22:
            return False

        def _dv(bloque, pesos):
            suma = sum(int(d) * p for d, p in zip(bloque, pesos))
            resto = suma % 10
            return 0 if resto == 0 else 10 - resto

        if _dv(cbu[0:7], [7, 1, 3, 9, 7, 1, 3]) != int(cbu[7]):
            return False
        if _dv(cbu[8:21], [3, 9, 7, 1, 3, 9, 7, 1, 3, 9, 7, 1, 3]) != int(cbu[21]):
            return False
        return True

    @staticmethod
    def validar_iban(iban: str) -> bool:
        iban = iban.replace(" ", "").upper()
        if len(iban) < 15 or len(iban) > 34:
            return False
        reordenado = iban[4:] + iban[:4]
        convertido = "".join(str(int(ch, 36)) if ch.isalpha() else ch for ch in reordenado)
        try:
            return int(convertido) % 97 == 1
        except ValueError:
            return False

    @staticmethod
    def validar_swift(codigo: str) -> bool:
        codigo = codigo.strip().upper()
        if len(codigo) not in (8, 11):
            return False
        pais = codigo[4:6]
        return pais in CODIGOS_PAIS_ISO_SWIFT

    def _es_cuenta_financiera_valida(self, nombre, valor):
        if "CBU" in nombre:
            return self.validar_cbu(valor)
        if "IBAN" in nombre:
            return self.validar_iban(valor)
        if "SWIFT" in nombre:
            return self.validar_swift(valor)
        return True

    def _confianza_por_contexto(self, texto, pos_inicio, pos_fin, palabras_clave):
        inicio = max(0, pos_inicio - 60)
        fin = min(len(texto), pos_fin + 60)
        ventana = texto[inicio:fin].lower()
        return "🟢 ALTA" if any(kw in ventana for kw in palabras_clave) else "🟡 MEDIA"

    def _clasificar_contexto(self, texto, pos_inicio, pos_fin):
        inicio = max(0, pos_inicio - 150)
        fin = min(len(texto), pos_fin + 150)
        ventana = texto[inicio:fin]

        es_operativo = any(p.search(ventana) for p in self._patrones_operativo)
        es_descriptivo = any(p.search(ventana) for p in self._patrones_descriptivo)

        if es_operativo and not es_descriptivo:
            return "operativo"
        if es_descriptivo and not es_operativo:
            return "descriptivo"
        if es_operativo and es_descriptivo:
            return "mixto"
        return "neutro"

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
    # 🕸️ CORRELACIÓN
    # =============================================================
    def _cargar_indice_correlacion(self):
        try:
            with open(config.CORRELACION_INDEX_FILE, encoding="utf-8") as f:
                data = json.load(f)
                return {k: set(v) for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _guardar_indice_correlacion(self):
        try:
            serializable = {k: list(v) for k, v in self.indice_correlacion.items()}
            with open(config.CORRELACION_INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando índice de correlación: {e}")

    def _registrar_correlacion(self, tipo, valor, origen):
        clave = f"{tipo}:{valor}"
        origenes_previos = self.indice_correlacion.get(clave, set())

        if origen not in origenes_previos and origenes_previos:
            caso = {
                "tipo": tipo, "valor": valor,
                "origenes": list(origenes_previos) + [origen],
                "cantidad_apariciones": len(origenes_previos) + 1,
            }
            self._guardar_correlacion(caso)
            print(f"   🕸️ CORRELACIÓN: {tipo} '{valor[:40]}' reaparece en {caso['cantidad_apariciones']} orígenes distintos")

        origenes_previos.add(origen)
        self.indice_correlacion[clave] = origenes_previos
        self._guardar_indice_correlacion()

    @staticmethod
    def _guardar_correlacion(caso):
        try:
            with open(config.CORRELACION_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(caso, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"   ⚠️ Error guardando correlación: {e}")

    # =============================================================
    # 🔍 ESCANEO PRINCIPAL
    # =============================================================
    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        ya_encontrado = set()

        for nombre, regex in self.patrones.items():
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if not valor or len(valor) <= 5 or self.es_ruido_obvio(valor):
                    continue

                if "Telegram" in nombre:
                    usuario = valor.lstrip("@").split("/")[-1].lower()
                    if usuario in DENYLIST_TELEGRAM:
                        continue

                es_cuenta_financiera = any(t in nombre for t in TIPOS_CUENTA_FINANCIERA)
                if es_cuenta_financiera and not self._es_cuenta_financiera_valida(nombre, valor):
                    continue

                if "PIX" in nombre:
                    confianza_pix = self._confianza_por_contexto(texto, match.start(), match.end(), CONTEXTO_PIX)
                    if confianza_pix != "🟢 ALTA":
                        continue

                if nombre in TIPOS_BASE58CHECK and not self.validar_base58check(valor):
                    continue

                clave_unica = f"{nombre}:{valor[:80]}"
                if clave_unica in ya_encontrado:
                    continue
                ya_encontrado.add(clave_unica)

                es_wallet = nombre in TIPOS_WALLET
                es_entidad_neutra = nombre in TIPOS_ENTIDAD_NEUTRA
                peligro = "🔴 ALTO"
                confianza = None

                if es_wallet:
                    confianza = self._confianza_por_contexto(texto, match.start(), match.end(), CONTEXTO_WALLET)
                    if nombre in TIPOS_REGEX_DEBIL and confianza != "🟢 ALTA":
                        continue
                    if confianza == "🟡 MEDIA":
                        peligro = "🟡 MEDIO"

                if es_cuenta_financiera and "PIX" not in nombre:
                    confianza = self._confianza_por_contexto(texto, match.start(), match.end(), CONTEXTO_CUENTA_FINANCIERA)
                    if confianza == "🟡 MEDIA":
                        peligro = "🟡 MEDIO"

                if es_entidad_neutra:
                    tipo_contexto = self._clasificar_contexto(texto, match.start(), match.end())
                    if tipo_contexto in ("operativo", "mixto"):
                        peligro = "🔴 ALTO"
                        confianza = f"🟢 ALTA (contexto {tipo_contexto})"
                    else:
                        peligro = "ℹ️ ENTIDAD"
                        confianza = f"contexto {tipo_contexto}, no operativo"

                hallazgo = {"tipo": nombre, "valor": valor, "origen": origen, "peligro": peligro}
                if confianza:
                    hallazgo["confianza"] = confianza
                hallazgos.append(hallazgo)

                if nombre == "Correo Electrónico" or es_cuenta_financiera or es_wallet:
                    self._registrar_correlacion(nombre, valor, origen)

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
                        self._registrar_correlacion("Dominio Clonado", dominio, origen)
                        print(f"   🚨 DOMINIO CLONADO: {dominio} → imita a {legitimo}")
                except Exception:
                    pass

        if config.ENABLE_JS_ANALYSIS and self.js_analyzer:
            if origen.endswith('.js') or ('function' in texto and 'var' in texto and '=' in texto):
                resultados_js = self.js_analyzer.analizar_js(texto, origen)

                for endpoint in resultados_js.get('endpoints', []):
                    if not endpoint or "archive.org" in endpoint.lower():
                        continue
                    # Un endpoint técnico (login, register, admin-ajax.php,
                    # xmlrpc.php...) es infraestructura NORMAL en millones
                    # de sitios legítimos. Encontrarlo es informativo, no
                    # una señal de riesgo por sí solo — igual que ya
                    # hicimos con email/Telegram/WhatsApp.
                    h = {"tipo": "Endpoint API (JS)", "valor": endpoint, "origen": origen, "peligro": "ℹ️ ENDPOINT"}
                    hallazgos.append(h)
                    self.guardar_hallazgo(h)

                for addr in resultados_js.get('crypto_addresses', []):
                    if not addr:
                        continue
                    h = {"tipo": "Dirección Cripto (JS)", "valor": addr, "origen": origen, "peligro": "🔴 ALTO"}
                    hallazgos.append(h)
                    self.guardar_hallazgo(h)
                    self._registrar_correlacion("Dirección Cripto (JS)", addr, origen)
                    blockchain = self._detectar_blockchain(addr)
                    if blockchain:
                        enriquecido = self._enriquecer_direccion(addr, blockchain)
                        if enriquecido:
                            try:
                                with open(config.BLOCKCHAIN_INSIGHTS_FILE, "a", encoding="utf-8") as f:
                                    f.write(json.dumps(enriquecido, indent=2) + "\n")
                            except Exception as e:
                                print(f"   ⚠️ Error guardando insight blockchain: {e}")

        self._detectar_puente(hallazgos, origen)
        return hallazgos

    def _detectar_puente(self, hallazgos, origen):
        cuentas = [h for h in hallazgos if any(t in h["tipo"] for t in TIPOS_CUENTA_FINANCIERA)]
        wallets = [h for h in hallazgos if h["tipo"] in TIPOS_WALLET]
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
        clave = (hallazgo['tipo'], hallazgo['valor'], hallazgo['origen'])
        if clave in self._hallazgos_guardados:
            self._hallazgos_guardados[clave] += 1
            return
        self._hallazgos_guardados[clave] = 1

        detalles = hallazgo.get('detalles', '')
        confianza = f" (Confianza: {hallazgo['confianza']})" if 'confianza' in hallazgo else ""
        linea = f"{hallazgo['peligro']} | [{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}{confianza}"
        if detalles:
            linea += f" (Detalles: {detalles})"
        linea += "\n"
        with open(config.HALLAZGOS_FILE, "a", encoding="utf-8") as f:
            f.write(linea)
        print(f"✅ {hallazgo['peligro']} HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
