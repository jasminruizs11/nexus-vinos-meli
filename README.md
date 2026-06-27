# 🍷 NEXUS Vinos: Automatización y Data Analytics en E-commerce

¡Hola! Bienvenido/a a este proyecto. 👋 Este desarrollo nació directamente de una necesidad real como emprendedora: **optimizar, escalar y controlar mi propia tienda online de vinos premium en Mercado Libre Argentina**.

Llevar un negocio adelante implica tomar decisiones rápidas, por lo que mi objetivo principal fue **maximizar el tiempo y simplificar la operativa al extremo**. Quería pasar del trabajo manual propenso a errores a un sistema inteligente, **fácilmente modificable en cualquier momento a lo largo del tiempo**. Por eso, diseñé un flujo donde todo nace desde una carga limpia y organizada de datos en Excel hasta una estructura milimétrica de carpetas locales para el correcto etiquetado y subida masiva de fotos. ¡Acá te cuento cómo transformé la gestión de mi negocio con **Python**! 🚀

---

## 📂 Estructura del repositorio

```
nexus-vinos-meli/
│
├── carga_vinos_meli.py          # Script 1: carga masiva y publicación en MeLi
├── auditor_meli.py               # Script 2: auditoría y reporte de publicaciones
├── analizar_precios.py           # Script 4: inteligencia de precios (bloqueado por API, ver sección 4️⃣)
├── buscar_categoria.py           # Script utilitario: explora atributos de una categoría
├── catalogo_vinos_meli.xlsx      # Catálogo de vinos (fuente de datos del negocio)
├── requirements.txt              # Dependencias del proyecto (nuevo, agregar al repo)
├── .env.example                  # Plantilla de variables de entorno (nuevo, agregar al repo)
├── .gitignore                    # Excluye .env, .token_cache.json y archivos temporales
│
├── reporte_meli.json             # Salida de auditor_meli.py (datos estructurados)
├── reporte_meli.html             # Salida de auditor_meli.py (dashboard visual)
├── resultados_carga.json         # Salida de carga_vinos_meli.py (log de publicaciones creadas)
├── analisis_precios.json         # Salida vacía de analizar_precios.py (bloqueado por API)
│
├── documentos/                   # Capturas y material de apoyo del proyecto
│
├── vinos/                        # Carpeta local de fotos (no versionada)
│   ├── altocedro_malbec_ano_cero/
│   │   ├── 01_frontal.jpg
│   │   └── 02_contraetiqueta.jpg
│   └── ...
│
└── README.md                     # Este archivo
```

> 📌 La carpeta `vinos/` con las fotos **no se sube al repositorio** (son archivos de imagen pesados y de uso particular del negocio). Si querés probar el script de carga, creá tus propias subcarpetas siguiendo la convención de nombres que se explica en el paso 5.

> 📌 Los archivos `reporte_meli.*`, `resultados_carga.json` y `analisis_precios.json` son **salidas generadas por los scripts**, no archivos de entrada. Se incluyen en el repositorio a modo de evidencia de ejecuciones reales, pero se regeneran cada vez que corrés el script correspondiente.
---

## 🛠️ ¿Qué hace este proyecto? (Paso a Paso)

El sistema se divide en los siguientes scripts, que cubren todo el ciclo de vida de los datos y la logística comercial:

### 1️⃣ Carga Masiva y Configuración Estructurada (`carga_vinos_meli.py`)
Este script se encarga de toda la publicación masiva y controlada sin tener que tocar la plataforma web con las manos:
* **Conexión API y OAuth2:** Implementa la autenticación segura con la API de Mercado Libre mediante tokens dinámicos para proteger la cuenta.
* **Normalización de Datos en Excel (ETL):** Procesa automáticamente el catálogo (`catalogo_vinos_meli.xlsx`) donde gestiono las variables del negocio: marcas, varietales, cosechas, stock actual, precios de lista y tipos de publicación (Clásica, Premium, etc.).
* **Estructura Inteligente de Carpetas:** Recorre de forma programática el almacenamiento local de fotos. Diseñé un estándar de etiquetado de carpetas basado en la limpieza de strings y minúsculas para que el script asocie y suba cada imagen al vino correcto de manera automatizada.
* **Control de Atributos Técnicos:** Construye el payload en JSON estructurando títulos optimizados de hasta 60 caracteres y aplicando los atributos comerciales requeridos por la plataforma (Bodega, Varietal, Volumen de unidad, GTIN/Código de barras).

### 2️⃣ Monitoreo Operativo y Data Storytelling (`auditor_meli.py`)
Una vez que los productos están online, este script actúa como mi propio "Analista de Salud" automatizado:
* **Descarga Paginada:** Consulta en lote (en bloques de hasta 20 ítems) todas las publicaciones activas del vendedor para monitorear su estado real.
* **Cálculo de KPIs de Rendimiento:** Extrae métricas clave de los últimos 30 días directas de la API, como el total de visitas y los niveles de posicionamiento en el buscador (*health levels*).
* **Lógica de Negocio Aplicada:** Evalúa cada publicación bajo reglas críticas. Detecta si el título es muy corto, si faltan fotos, si la descripción es escasa, si el stock está bajo o si la falta de envío gratis está afectando la conversión.
* **Reporting Dinámico (HTML/JSON):** Exporta un archivo JSON con los datos limpios y genera automáticamente un dashboard en HTML con diseño estético y badges de colores (`✅ Ganando`, `⚠️ Empatando`, `❌ Perdiendo`) junto con sugerencias automáticas para mejorar las ventas.

### 3️⃣ Exploración de Atributos de Categoría (`buscar_categoria.py`)
Script utilitario de soporte, pensado para consultar contra la API qué atributos exige Mercado Libre para una categoría puntual antes de armar el payload de publicación:
* **Consulta de Atributos:** Pega contra el endpoint `categories/{id}/attributes` y lista cada atributo de la categoría de vinos (`MLA1404`).
* **Clasificación Requerido/Opcional:** Distingue automáticamente qué atributos son obligatorios (o condicionalmente obligatorios) y cuáles son opcionales, evitando publicaciones rechazadas por faltar un campo clave.

### 4️⃣ Inteligencia Competitiva de Mercado (`analizar_precios.py`) — ⛔ Bloqueado por restricción de la API
Este script fue diseñado para resolver un problema de negocio concreto: identificar qué precios maneja la competencia para cada vino del catálogo y sugerir un precio de venta óptimo, filtrando desvíos y promediando publicaciones similares.

**Estado real:** al ejecutarlo, el script devuelve `403 Forbidden` para los 25 vinos consultados y no logra obtener ningún precio de competidores. La causa identificada es que el endpoint que utiliza, `GET /sites/MLA/search`, está restringido por Mercado Libre desde abril de 2025 y ya no responde con el token de acceso de la aplicación, incluso siendo válido para otros endpoints (ítems, visitas, categorías). El propio código contempla este escenario con un control `if r.status_code == 403`, que actualmente se activa para el 100% de las consultas.

Como consecuencia, `analisis_precios.json` se genera vacío (`[]`) en cada ejecución: no hay datos de producción asociados a este componente todavía.

**Próximo paso identificado para destrabarlo:** migrar la búsqueda de competidores a un endpoint que no esté afectado por esta restricción (por ejemplo, consultando por `category_id` a través de `GET /products/search` o explorando el alcance habilitado para aplicaciones de terceros en la documentación oficial de Mercado Libre), en lugar de `/sites/MLA/search`.

---

## 🧰 Stack Tecnológico Utilizado

* **Lenguaje Principal:** Python 🐍
* **Conectividad:** API de Mercado Libre (Endpoints de Users, Items, Visits, Health, Categories)
* **Librerías Clave:** `requests` (para el consumo de APIs), `openpyxl` (para la manipulación del catálogo en Excel), `python-dotenv` (gestión de credenciales), `json`, `time` y `webbrowser`.
* **Visualización:** HTML5 y CSS3 personalizado para el reporte analítico local.

---

## 🚀 Instalación y Ejecución Local

A continuación se detallan los pasos para clonar el repositorio y correr el proyecto en tu propia máquina.

### Requisitos previos

* Python 3.10 o superior instalado.
* Una cuenta de vendedor en Mercado Libre Argentina.
* Una aplicación creada en [Mercado Libre Developers](https://developers.mercadolibre.com.ar/) para obtener tu propio `App ID` y `Client Secret`.

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/jasminruizs11/nexus-vinos-meli.git
cd nexus-vinos-meli
```

### Paso 2 — Crear un entorno virtual (recomendado)

```bash
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Mac / Linux
source venv/bin/activate
```

### Paso 3 — Instalar las dependencias

```bash
pip install -r requirements.txt
```

### Paso 4 — Configurar las credenciales (`.env`)

Por seguridad, **las credenciales reales nunca se suben al repositorio**. En su lugar, se incluye un archivo `.env.example` a modo de plantilla. Para configurarlo:

1. Copiá el archivo de ejemplo y renombralo:

   ```bash
   cp .env.example .env
   ```

2. Abrí `.env` y completá tus propios valores, obtenidos desde tu aplicación en Mercado Libre Developers:

   ```env
   MELI_APP_ID=tu_app_id_aca
   MELI_SECRET=tu_client_secret_aca
   ```

3. Verificá que `.env` y `.token_cache.json` figuren en el `.gitignore` (ya vienen incluidos por defecto) para que nunca se suban accidentalmente al repositorio.

> ⚠️ **Nunca compartas tu `Client Secret` ni tus tokens de acceso.** Si se filtran, regenerá las credenciales desde el panel de Mercado Libre Developers de inmediato.

### Paso 5 — Preparar el catálogo y las fotos

1. Completá `catalogo_vinos_meli.xlsx` con tus productos: nombre, bodega, varietal, año, región, volumen, GTIN, precio y stock.
2. Creá la carpeta `vinos/` en la raíz del proyecto y, dentro, una subcarpeta por cada vino, siguiendo esta convención de nombres (minúsculas, sin tildes, espacios reemplazados por guion bajo):

   ```
   vinos/
       altocedro_malbec_ano_cero/
           01_frontal.jpg
           02_contraetiqueta.jpg
   ```

   El nombre de la carpeta debe derivarse del nombre del vino tal como figura en el Excel (el script lo normaliza automáticamente, así que alcanza con respetar el formato de minúsculas y guiones bajos).

### Paso 6 — Ejecutar la carga masiva en modo de prueba

Antes de publicar nada real, corré siempre primero el modo `--test`, que simula todo el proceso sin escribir en Mercado Libre:

```bash
python carga_vinos_meli.py --test
```

Revisá la salida en consola: te muestra qué publicaciones se crearían, con qué precio, stock y fotos, sin tocar la plataforma.

### Paso 7 — Ejecutar la carga real

Si el modo de prueba se vio correcto, corré el script sin la bandera `--test`:

```bash
python carga_vinos_meli.py
```

* La primera vez, el script abrirá el navegador para que inicies sesión con tu cuenta de Mercado Libre y autorices la aplicación. Vas a tener que copiar el código de autorización (`TG-...`) que aparece en la URL y pegarlo en la consola cuando se te solicite.
* El token se guarda en caché (`.token_cache.json`) para no tener que repetir el login en cada ejecución, hasta que expire.
* Al finalizar, se genera un archivo `resultados_carga.json` con el ID y la URL pública de cada publicación creada.

### Paso 8 — Ejecutar el auditor de publicaciones

Este script usa el mismo token de acceso. Pegalo en la variable `ACCESS_TOKEN` dentro de `auditor_meli.py` (o adaptá el script para que lo lea desde `.token_cache.json`, como hace `buscar_categoria.py`) y luego ejecutá:

```bash
python auditor_meli.py
```

El script va a:
1. Descargar todas tus publicaciones activas.
2. Analizar cada una bajo las reglas de negocio (fotos, descripción, título, stock, envío, visitas).
3. Generar `reporte_meli.json` (datos estructurados) y `reporte_meli.html` (dashboard visual).
4. Abrir automáticamente el dashboard HTML en tu navegador.

### Paso 9 — Explorar atributos de una categoría (opcional)

Si necesitás conocer los atributos requeridos de otra categoría de Mercado Libre, usá el script utilitario:

```bash
python buscar_categoria.py
```

Por defecto consulta la categoría de vinos (`MLA1404`); para otra categoría, editá el ID dentro del script.

### Paso 10 — Script de análisis de precios (opcional, actualmente bloqueado)

```bash
python analizar_precios.py
```

⛔ Al día de hoy, este script devuelve `403 Forbidden` para todas las consultas, porque el endpoint que utiliza (`/sites/MLA/search`) está restringido por Mercado Libre desde abril de 2025. Podés ejecutarlo para verificar el comportamiento, pero vas a ver `"Sin acceso API"` en cada vino y `analisis_precios.json` se va a generar vacío (`[]`). No es un error de configuración local: es una limitación vigente de la API contra la que no hay workaround simple desde el lado del cliente.

---

## 📈 Resultados del Proyecto

* **Eficiencia al Máximo:** Se eliminó el error humano en el registro de atributos técnicos, reduciendo tareas de horas de carga manual a solo segundos.
* **Decisiones Basadas en Datos:** Permite auditar el catálogo completo en tiempo real, detectando de un vistazo qué productos necesitan atención urgente para no perder relevancia en el algoritmo de Mercado Libre.

---

## 📸 Visualización y Resultados

> 🚧 Esta sección incluirá próximamente una captura del panel de Mercado Libre con el catálogo sincronizado en producción. Cuando tengas la imagen, guardala en `documentos/panel_meli.png` y agregá aquí:
>
> `![Panel de Control Mercado Libre](documentos/panel_meli.png)`

---

## 🔐 Nota de Seguridad

Por cuestiones de privacidad y cumplimiento de políticas de seguridad:
* Las credenciales reales (`.env`) y los tokens de acceso (`.token_cache.json`) se encuentran estrictamente ocultos mediante `.gitignore` y **nunca se suben al repositorio**.
* Este repositorio solo incluye `.env.example` como plantilla, sin valores reales.
* Si vas a clonar y probar este proyecto, deberás generar tus propias credenciales en Mercado Libre Developers; las que figuran en cualquier ejemplo de este documento son solo ilustrativas.

---

## 🧯 Problemas Frecuentes (Troubleshooting)

| Problema | Causa probable | Solución |
|---|---|---|
| `CLIENT_SECRET no encontrado` | El archivo `.env` no existe o está vacío | Verificá que copiaste `.env.example` a `.env` y completaste los valores |
| El código de autorización no empieza con `TG-` | Se copió mal la URL de redirección | Volvé a iniciar el proceso de login y copiá el parámetro `code` completo |
| `Error creando publicación: 400` | Falta un atributo obligatorio de la categoría | Corré `buscar_categoria.py` para revisar qué atributos son requeridos |
| No se encuentran las fotos de un vino | El nombre de la carpeta no coincide con el nombre del vino | Revisá que la carpeta esté en minúsculas, sin tildes y con guiones bajos |
| El token expiró | Pasaron más de ~6 horas desde el último login | Borrá `.token_cache.json` y volvé a correr el script para reautenticarte |

---

*Proyecto desarrollado por Jasmin Ruiz como parte de NEXUS Vinos, una operación real de e-commerce en Mercado Libre Argentina.*
