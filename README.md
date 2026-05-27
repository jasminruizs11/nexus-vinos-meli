# 🍷 NEXUS Vinos: Automatización y Data Analytics en E-commerce

¡Hola! Bienvenido/a a este proyecto. 👋 Este desarrollo nació directamente de una necesidad real como emprendedora: **optimizar, escalar y controlar mi propia tienda online de vinos premium en Mercado Libre Argentina**. 

Llevar un negocio adelante implica tomar decisiones rápidas, por lo que mi objetivo principal fue **maximizar el tiempo y simplificar la operativa al extremo**. Quería pasar del trabajo manual propenso a errores a un sistema inteligente, **fácilmente modificable en cualquier momento a lo largo del tiempo**. Por eso, diseñé un flujo donde todo nace desde una carga limpia y organizada de datos en Excel hasta una estructura milimétrica de carpetas locales para el correcto etiquetado y subida masiva de fotos. ¡Acá te cuento cómo transformé la gestión de mi negocio con **Python**! 🚀

---

## 🛠️ ¿Qué hace este proyecto? (Paso a Paso)

El sistema se divide en tres scripts principales que cubren todo el ciclo de vida de los datos y la logística comercial:

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

### 3️⃣ Inteligencia Competitiva de Mercado (`analizar_precios.py`)
Para mantener márgenes saludables y reaccionar rápido a las fluctuaciones del mercado, el sistema analiza el entorno:
* **Scraping y Búsqueda de Competidores:** Realiza consultas automáticas utilizando la categoría específica de vinos para identificar qué precios está manejando la competencia para cada etiqueta.
* **Cálculo de Precios Sugeridos:** Extrae los valores de los competidores directos, filtra desvíos, calcula precios mínimos/máximos y promedia las publicaciones para sugerir un precio de venta óptimo con un margen competitivo ajustado.

---

## 🧰 Stack Tecnológico Utilizado

* **Lenguaje Principal:** Python 🐍
* **Conectividad:** API de Mercado Libre (Endpoints de Users, Items, Visits, Health, Categories)
* **Librerías Clave:** `requests` (para el consumo de APIs), `openpyxl` (para la manipulación del catálogo en Excel), `json`, `time` y `webbrowser`.
* **Visualización:** HTML5 y CSS3 personalizado para el reporte analítico local.

---

## 📈 Resultados del Proyecto

* **Eficiencia al Máximo:** Se eliminó el error humano en el registro de atributos técnicos, reduciendo tareas de horas de carga manual a solo segundos.
* **Decisiones Basadas en Datos:** Permite auditar el catálogo completo en tiempo real, detectando de un vistazo qué productos necesitan atención urgente para no perder relevancia en el algoritmo de Mercado Libre.

---
## 📸 Visualización y Resultados

### Sincronización en Producción (Mercado Libre)
Catálogo e inventario impactados correctamente y de manera masiva en la plataforma pública:

![Panel de Control Mercado Libre](docs/panel_meli.png)

---
*Nota de Seguridad: Por cuestiones de privacidad y cumplimiento de políticas de seguridad, las credenciales reales (`.env`) y los tokens de acceso (`.token_cache.json`) se encuentran estrictamente ocultos mediante `.gitignore`.*