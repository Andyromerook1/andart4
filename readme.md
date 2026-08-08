# 🛡️ ANDY TECHNOLOGY SYSTEMS

## 🤖 BOT RASTREADOR AUTÓNOMO

### 🔍 Reconocimiento Automático desde Fuentes Públicas + Panel en Vivo

---

## ⚠️ AVISO LEGAL Y DESLINDE DE RESPONSABILIDAD

* 🎯 **FINES EXCLUSIVAMENTE EDUCATIVOS:** Esta herramienta ha sido desarrollada únicamente para demostrar cómo funcionan los sistemas de rastreo automatizado utilizados en reconocimiento de fuentes públicas.
* ⚖️ **USO RESPONSABLE:** El escaneo de redes, rangos IP o propiedades ajenas sin autorización escrita expresa constituye un delito informático. Esta herramienta no debe ser utilizada contra objetivos que no sean de tu propiedad o sobre los que no cuentes con permiso formal.
* 📜 **LIMITACIÓN DE DISEÑO:** El módulo de rastreo web consulta únicamente APIs públicas y contenido accesible por cualquier navegador sin autenticación. No realiza ataques, inyecciones ni intentos de explotar vulnerabilidades.

---

## ✅ ¿CÓMO FUNCIONA?

El bot se alimenta solo al encenderse, sin que tengas que escribir ninguna dirección manualmente:

* 🔗 **GitHub API:** Trae repositorios creados o actualizados recientemente.
* 📚 **Wikipedia API:** Trae artículos al azar como semillas de navegación.
* 📂 **Archivo local:** Si existe `semillas.txt`, carga URLs adicionales automáticamente.
* 🌐 **Generador automático de rangos IP:** Crea direcciones al azar para el módulo de red.

**Flujo completo:**

> Descubre enlaces ➔ Lee páginas ➔ Filtra por patrones ➔ Guarda hallazgos en `hallazgos.txt` ➔ Se muestran en vivo en el panel web.

---

## 📁 ESTRUCTURA DEL PROYECTO

```plaintext
andart4/
 ├─ app.py              ← Menú principal y coordinación
 ├─ servidor.py         ← Panel web en tiempo real ✅
 ├─ fuentes.py          ← Obtención automática de semillas desde APIs
 ├─ rastreador.py       ← Navegación automática y descubrimiento de enlaces
 ├─ filtro.py           ← Búsqueda por patrones RegEx definidos
 ├─ escaner_red.py      ← Escaneo de rangos IP y detección de puertos abiertos
 ├─ patrones.json       ← Moldes de búsqueda (claves, tokens, correos...)
 └─ README.md           ← Esta guía

```

---

## 🚀 INSTALACIÓN EN TERMUX

Abrí Termux y ejecutá paso a paso:

```bash
# 1. Actualizar sistema
pkg update && pkg upgrade -y

# 2. Instalar dependencias
pkg install python git cloudflared -y

# 3. Instalar librerías de Python
pip install requests beautifulsoup4

# 4. Clonar el repositorio
git clone https://github.com/Andyromerook1/andart4.git

# 5. Entrar a la carpeta
cd andart4

```

---

## ▶️ EJECUCIÓN — INSTRUCCIONES COMPLETAS

### 🔹 Opción recomendada: 2 Terminales en Termux

Deslizá el dedo desde el borde izquierdo de la pantalla para abrir una segunda sesión y dejá las dos funcionando al mismo tiempo:

#### 🟢 Terminal 1 — El bot trabaja y busca:

```bash
python app.py

```

Se abrirá el menú. Elegí:

* `1` ➔ Rastreo web (APIs automáticas + búsqueda de claves)
* `2` ➔ Escaneo de red (genera rango IP automáticamente)
* `3` ➔ AMBOS al mismo tiempo
* `0` ➔ Salir

#### 🔵 Terminal 2 — Panel web en vivo desde cualquier dispositivo:

```bash
python servidor.py &
cloudflared tunnel --url http://127.0.0.1:5000

```

> ✅ Cloudflared imprimirá en pantalla un enlace público en color verde, por ejemplo: `[https://palabras-aleatorias.trycloudflare.com](https://palabras-aleatorias.trycloudflare.com)`
> Entrá a ese enlace desde tu celular, PC o cualquier navegador del mundo. Verás los hallazgos apareciendo automáticamente cada 5 segundos sin que tengas que recargar la página.

---

## 🔄 ¿QUÉ OCURRE EN SEGUNDO PLANO?

```plaintext
[ENCENDER BOT]
      ↓
🔗 Consultar GitHub API → trae repositorios nuevos automáticamente
      ↓
📚 Consultar Wikipedia API → trae artículos al azar
      ↓
📂 Cargar semillas.txt (si existe)
      ↓
🌐 Generar rango IP aleatorio
      ↓
🔁 Llenar cola → navegar → descubrir enlaces → filtrar por patrones
      ↓
💾 Guardar coincidencias en hallazgos.txt
      ↓
📡 Servidor web lee el archivo cada 5 segundos y lo muestra en pantalla
      ↓
🌍 Cualquier dispositivo ve los resultados en vivo

```

---

## 📋 RESUMEN DE CARACTERÍSTICAS

| Característica | Detalle |
| --- | --- |
| **Semillas automáticas** | GitHub + Wikipedia + Archivo local |
| **Sin escribir URLs** | El bot se alimenta solo al iniciar |
| **Búsqueda por patrones** | Claves AWS, tokens, correos, contraseñas, billeteras |
| **Escaneo de red** | Genera rangos IP automáticamente |
| **Panel en vivo** | Se actualiza cada 5 segundos |
| **Acceso remoto** | Cloudflared ➔ enlace público desde cualquier lugar |
| **Todo guardado** | `hallazgos.txt` persiste todos los resultados |

---

## ⚠️ NOTAS IMPORTANTES

* El archivo `hallazgos.txt` se crea automáticamente al primer hallazgo. No necesitas crearlo.
* El escaneo de red prueba puertos comunes (`22`, `80`, `443`, `3306`, `5432`, `27017`).
* Si usás la opción `2` o `3`, el rango IP se genera aleatoriamente en cada ejecución.
* El enlace de Cloudflared cambia cada vez que reiniciás el túnel.
