import re
import json

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

    def __init__(self, archivo_patrones="patrones.json"):
        with open(archivo_patrones, encoding="utf-8") as f:
            datos = json.load(f)

        self.patrones = {}
        for nombre, regex in datos.items():
            # ✅ Tu lógica INTACTA: aplica IGNORECASE solo a los que corresponda
            banderas = re.IGNORECASE if any(ignorado in nombre for ignorado in self.IGNORE_CASE) else 0
            self.patrones[nombre] = re.compile(regex, banderas)

    def _nivel_peligro(self, nombre):
        """Clasifica automáticamente sin romper nada"""
        if any(peligro in nombre for peligro in self.ALTO_RIESGO):
            return "🔴 ALTO"
        if any(peligro in nombre for peligro in self.MEDIO_RIESGO):
            return "🟡 MEDIO"
        return "🟢 BAJO"

    def escanear_texto(self, texto, origen="desconocido"):
        hallazgos = []
        ya_encontrado = set()  # ✅ Evita duplicados SIN cambiar tu lógica
        
        for nombre, regex in self.patrones.items():
            # ✅ Tu lógica INTACTA: encontrar todas las coincidencias
            for match in regex.finditer(texto):
                valor = match.group(0).strip()
                if valor and len(valor) > 5:
                    clave_unica = f"{nombre}:{valor[:80]}"
                    if clave_unica not in ya_encontrado:
                        ya_encontrado.add(clave_unica)
                        hallazgos.append({
                            "tipo": nombre,
                            "valor": valor,
                            "origen": origen,
                            "peligro": self._nivel_peligro(nombre)
                        })
        return hallazgos

    def guardar_hallazgo(self, hallazgo):
        # ✅ Tu formato original + nivel de peligro
        linea = f"{hallazgo['peligro']} | [{hallazgo['tipo']}] {hallazgo['valor']} → {hallazgo['origen']}\n"
        with open("hallazgos.txt", "a", encoding="utf-8") as f:
            f.write(linea)
        # ✅ Tu mensaje original mejorado
        print(f"{hallazgo['peligro']} HALLAZGO: {hallazgo['tipo']} → {hallazgo['valor'][:50]}...")
