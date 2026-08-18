# 🕵️ ANDART — Rastreador OSINT de Phishing, Estafas y Lavado de Cripto

Herramienta de código abierto para detectar sitios de phishing, campañas de
estafa (incluido spam de apuestas ilegales) y trazar el flujo de fondos
—tanto en cuentas financieras tradicionales como en criptomonedas— a partir
de **fuentes públicas**.

---

## ⚠️ Aviso legal y alcance

- **Fuentes públicas únicamente.** El bot solo lee contenido accesible sin
  autenticación (páginas web, repos públicos de GitHub, exploradores de
  blockchain públicos) y consulta APIs oficiales dentro de sus límites
  publicados.
- **No escanea redes ni rangos de IP.** No hace port scanning, no intenta
  acceder a sistemas ajenos, no explota vulnerabilidades.
- **No cosecha credenciales.** No busca ni guarda claves de API, contraseñas
  ni tokens de terceros — solo indicadores de estafa: dominios clonados,
  direcciones de criptomonedas y cuentas financieras (CBU/CVU, IBAN, etc.)
  que el propio estafador publica para que la víctima le pague.
- **Los hallazgos pueden incluir datos personales reales** (ej. una cuenta
  bancaria vinculada a una identidad). Tratalos con cuidado: no los subas a
  ningún repo público ni los compartas fuera del canal correspondiente
  (policía / fiscalía).
- Esta herramienta no reemplaza asesoramiento legal. Si vas a presentar
  hallazgos ante una autoridad, consultá cómo documentar la cadena de
  custodia para que sean válidos como evidencia.

---

## 📁 Estructura del proyecto

```text
andart4/
 ├─ app.py                 ← Menú principal
 ├─ servidor.py            ← Panel web en vivo
 ├─ network_client.py      ← Cliente HTTP (rotación de User-Agent, reintentos)
 ├─ fuentes.py             ← Semillas: dorks, feeds de threat intel, sitios de investigación
 ├─ rastreador.py          ← Recorre las semillas y sigue enlaces
 ├─ filtro.py              ← Motor de detección (patrones + phishing + JS + puente)
 ├─ patrones.json          ← Reglas: email, cuentas financieras, direcciones cripto
 ├─ phishing_detector.py   ← Detección de dominios clonados (typosquatting)
 ├─ js_analyzer.py         ← Extrae endpoints y direcciones cripto de archivos JS
 ├─ blockchain_client.py   ← Consulta Tronscan/Etherscan/BscScan + heurística de lavado
 ├─ github_hunter.py       ← Caza de repos de spam en GitHub (Search API oficial)
 ├─ config.py              ← Configuración centralizada
 └─ README.md              ← Esta guía
```

---

## 🚀 Instalación en Termux

```bash
# 1. Actualizar sistema
pkg update && pkg upgrade -y

# 2. Instalar dependencias del sistema
pkg install python git -y

# 3. Instalar librerías de Python
pip install requests beautifulsoup4 flask

# 4. Clonar el repositorio
git clone https://github.com/Andyromerook1/andart4.git
cd andart4

# 5. Dar permiso de almacenamiento (para guardar los hallazgos en Descargas)
termux-setup-storage
```


## ▶️ Ejecución

### Opción recomendada: 2 terminales en Termux

Deslizá el dedo desde el borde izquierdo de la pantalla para abrir una
segunda sesión y dejá las dos corriendo al mismo tiempo.

**Terminal 1 — el bot rastrea:**

```bash
python app.py
```

Se abrirá el menú:

- `1` ➔ **Rastreo web** — recorre dorks, feeds de threat intel y sitios de
  investigación en busca de phishing, dominios clonados, cuentas financieras
  y wallets.
- `2` ➔ **Caza en GitHub** — busca repos de spam (como campañas de apuestas
  ilegales en chino) usando la API oficial de búsqueda de GitHub.
- `0` ➔ Salir.

**Terminal 2 — panel web en vivo:**

```bash
python servidor.py
```

Abrí `http://127.0.0.1:5000` en el navegador del celular/PC. El panel se
actualiza solo cada 5 segundos, sin recargar.

---

## 🔄 ¿Qué hace el bot en segundo plano?

```text
[INICIAR]
   ↓
📡 Carga semillas: dorks de Google, feeds de threat intel (urlhaus,
   phishstats, openphish), sitios de investigación, semillas.txt (opcional)
   ↓
🌐 Visita cada URL con network_client (rotación de User-Agent normal)
   ↓
🔍 filtro.py analiza el contenido:
     - Dominios clonados (phishing)
     - Direcciones de criptomonedas → se enriquecen contra blockchain_client
     - Cuentas financieras (CBU/CVU, IBAN...) → se validan con su dígito verificador
     - Si aparecen ambas en el mismo origen → se guarda como "caso puente"
   ↓
💾 hallazgos.txt / blockchain_insights.txt / casos_puente.jsonl
   ↓
📊 servidor.py muestra hallazgos.txt en vivo
```

---

## 📋 Archivos de salida

Todo se guarda en `~/storage/downloads/andart_output/`:

| Archivo                     | Contenido                                                        |
|------------------------------|--------------------------------------------------------------------|
| `hallazgos.txt`             | Todos los hallazgos individuales (dominios, wallets, cuentas, etc.)|
| `blockchain_insights.txt`   | Balance, volumen y patrones de lavado detectados por wallet        |
| `casos_puente.jsonl`        | Cuenta financiera + wallet vinculadas en el mismo origen (⚠️ sensible) |
| `checkpoint.json`           | Progreso del rastreo, si se implementa                             |

`casos_puente.jsonl` es el archivo más sensible: cruza un dato con
identidad real con el destino final de los fondos. No lo subas a git.

---

## 🔒 Antes de subir cambios al repo

Agregá un `.gitignore` con al menos:

```gitignore
*.env
hallazgos.txt
blockchain_insights.txt
casos_puente.jsonl
checkpoint.json
__pycache__/
*.pyc
```

Y nunca commitees una API key en `config.py` — siempre por variable de
entorno.

---

## 🌐 Opcional: acceso remoto al panel

Si además de correrlo en tu celular querés ver el panel desde otro
dispositivo fuera de tu red:

```bash
pkg install cloudflared -y
cloudflared tunnel --url http://127.0.0.1:5000
```

Te va a dar un link público temporal. Cambia cada vez que reiniciás el
túnel.
