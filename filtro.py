import re
import json
import config  # Importamos la configuración
from blockchain_client import BlockchainClient  # Nuestro nuevo módulo

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
        """✅ Valida si una tarjeta es matemáticamente correcta"""
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
        """✅ Descarta basura que no tiene sentido real"""
        s = re.sub(r'[\s\-]+', '', valor)
        
        # ❌ Todos los dígitos iguales → imposible
        if len(set(s)) == 1:
            return True
        
        # ❌ Muchos ceros seguidos o al final
        if "00000" in s or s.endswith("000000"):
            return True
        
        # ❌ Secuencias obvias
        if s in "0123456789" or s in "9876543210":
            return True
        
        # ❌ Más de la mitad son ceros
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

    def _nivel_peligro(self, nombre):
        """Clasifica automáticamente sin romper nada"""
        if any(peligro in nombre for peligro in self.ALTO_RIESGO):
            return "🔴 ALTO"
        if any(peligro in nombre for peligro in self.MEDIO_RIESGO):
            return "🟡 MEDIO"
        return "🟢 BAJO"

    def _detectar_blockchain(self, texto):
        """Detecta la blockchain según el prefijo de la dirección."""
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
            # Podría ser Solana (sin prefijo fijo, longitud 43-44)
            if 43 <= len(texto) <= 44 and re.match(r'^[A-Za-z0-9]{43,44}$', texto):
                return 'solana'
            return None

    def _enriquecer_direccion(self, direccion, blockchain):
        """Consulta la blockchain para enriquecer una dirección."""
        if not self.blockchain_client:
            return None
        try:
            # Solo soportamos tron, ethereum, bsc por ahora (las que tienen API)
            if blockchain in ['tron', 'ethereum', 'bsc']:
                return self.blockchain_client.analyze_address(direccion, blockchain)
            else:
                # Para otras cadenas, podríamos hacer consultas específicas (ej. Blockchair)
                return None
        except Exception as e:
            print(f"⚠️ Error en análisis blockchain para {direccion}: {e}")
            return None

    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        ya_encontrado = set()  # ✅ Evita duplicados SIN cambiar tu lógica
        ruido_descartado = 0
        
        for nombre, regex in self.patrones.items():
            # ✅ Tu lógica INTACTA: encontrar todas las coincidencias
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if not valor or len(valor) <= 5:
                    continue

                # 🧠 APLICAMOS LOS FILTROS INTELIGENTES
                es_valido = True

                if "Tarjeta" in nombre:
                    # Tarjetas → validar matemáticamente
                    if self.es_ruido_obvio(valor) or not self.validar_luhn(valor):
                        es_valido = False
                else:
                    # Lo demás → descartar ruido obvio
                    if self.es_ruido_obvio(valor):
                        es_valido = False

                if not es_valido:
                    ruido_descartado += 1
                    continue

                clave_unica = f"{nombre}:{valor[:80]}"
                if clave_unica not in ya_encontrado:
                    ya_encontrado.add(clave_unica)
                    # Creamos el hallazgo
                    hallazgo = {
                        "tipo": nombre,
                        "valor": valor,
                        "origen": origen,
                        "peligro": self._nivel_peligro(nombre)
                    }
                    hallazgos.append(hallazgo)

                    # Si es una dirección de criptomoneda, enriquecer
                    if "Billetera" in nombre or any(c in nombre for c in ["BTC", "ETH", "TRX", "SOL", "ADA", "XRP"]):
                        blockchain = self._detectar_blockchain(valor)
                        if blockchain:
                            enriquecido = self._enriquecer_direccion(valor, blockchain)
                            if enriquecido:
                                # Guardar el enriquecimiento en un archivo separado
                                try:
                                    with open(config.BLOCKCHAIN_INSIGHTS_FILE, "a", encoding="utf-8") as f:
                                        f.write(json.dumps(enriquecido, indent=2) + "\n")
                                    print(f"   🔗 Blockchain enriquecida: {valor} - Balance: {enriquecido.get('balance', 'N/A')}")
                                except Exception as e:
                                    print(f"   ⚠️ Error guardando insight blockchain: {e}")

        if ruido_descartado > 0:
            print(f"   🧹 {ruido_descartado} coincidencias descartadas en: {origen[:50]}")
        return hallazgos

    def guardar_hallazgo(self, hallazgo):
        # ✅ Tu formato original + nivel de peligro
        linea = f"{hallazgo['peligro']} | [{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}\n"
        with open("hallazgos.txt", "a", encoding="utf-8") as f:
            f.write(linea)
        # ✅ Tu mensaje original mejorado
        print(f"✅ {hallazgo['peligro']} HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
