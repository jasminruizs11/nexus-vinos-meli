"""
╔══════════════════════════════════════════════════════════════════════╗
║         NEXUS VINOS — Carga Masiva Mercado Libre Argentina          ║
║         Lee el Excel, genera token OAuth2 y sube publicaciones      ║
╚══════════════════════════════════════════════════════════════════════╝

REQUISITOS:
    pip install requests openpyxl python-dotenv

ARCHIVOS NECESARIOS:
    - .env                          (credenciales, ver abajo)
    - catalogo_vinos_meli.xlsx      (tu Excel con los 25 vinos)
    - vinos/                        (carpeta con subcarpetas de fotos)

ESTRUCTURA DE CARPETAS:
    vinos/
        altocedro_malbec_ano_cero/
            01_frontal.jpg
            02_contraetiqueta.jpg
            ...

PASOS ANTES DE CORRER:
    1. Completá el archivo .env con tus credenciales
    2. Asegurate de tener el Excel con precios y stock completos
    3. Corré primero en modo TEST: python carga_vinos_meli.py --test
    4. Si todo está bien: python carga_vinos_meli.py
"""

import os
import sys
import json
import time
import base64
import webbrowser
import urllib.parse
import requests
import openpyxl
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# ── CONFIGURACIÓN ──────────────────────────────────────────────────────────
APP_ID        = os.getenv("MELI_APP_ID",      "ACA")
CLIENT_SECRET = os.getenv("MELI_SECRET",      "")   # NO pongas acá, usá .env
REDIRECT_URI  = 'https://httpbin.org/get'
BASE_URL      = "https://api.mercadolibre.com"
SITE_ID       = "MLA"

# Ruta al Excel y carpeta de fotos (ajustá si están en otro lugar)
EXCEL_PATH    = Path("catalogo_vinos_meli.xlsx")
FOTOS_DIR     = Path("vinos")

# Categoría de vinos en MeLi Argentina
CATEGORIA_VINOS = "MLA1404"   # Alimentos y Bebidas > Vinos

# Tipo de publicación por defecto
LISTING_TYPE_DEFAULT = "gold_special"  # gold_special = Gold

# ── COLORES PARA LA CONSOLA ────────────────────────────────────────────────
G = "\033[92m"   # verde
Y = "\033[93m"   # amarillo
R = "\033[91m"   # rojo
B = "\033[94m"   # azul
W = "\033[0m"    # reset
BOLD = "\033[1m"

def ok(msg):  print(f"{G}  ✓  {msg}{W}")
def warn(msg): print(f"{Y}  ⚠  {msg}{W}")
def err(msg):  print(f"{R}  ✗  {msg}{W}")
def info(msg): print(f"{B}  →  {msg}{W}")
def title(msg): print(f"\n{BOLD}{msg}{W}\n{'─'*60}")


# ══════════════════════════════════════════════════════════════════════════
# PASO 1 — AUTENTICACIÓN OAUTH2
# ══════════════════════════════════════════════════════════════════════════

auth_code_received = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code_received
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            auth_code_received = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body style='font-family:Arial;text-align:center;padding:60px;'>"
                "<h2 style='color:#00a650'>&#10003; Autenticacion exitosa</h2>"
                "<p>Podes cerrar esta ventana y volver a la consola.</p>"
                "</body></html>"
            ).encode("utf-8")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, *args):
        pass  # silenciar logs del servidor


def obtener_token():
    title("PASO 1 — Autenticación con Mercado Libre")

    secret = os.getenv("MELI_SECRET", "")
    if not secret:
        err("CLIENT_SECRET no encontrado. Configurá el archivo .env")
        sys.exit(1)

    auth_url = (
        f"https://auth.mercadolibre.com.ar/authorization"
        f"?response_type=code"
        f"&client_id={APP_ID}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    )

    info("Abriendo el navegador...")
    print(f"\n  {auth_url}\n")
    webbrowser.open(auth_url)

    print(f"\n{Y}Cuando se abra httpbin.org, buscá el valor de 'code' y pegalo acá:{W}")
    print(f"{Y}Ejemplo: TG-69abc123...{W}")
    print(f"\n{Y}Código: {W}", end="")
    code = input().strip()

    if not code.startswith("TG-"):
        err("El código no parece válido. Debe empezar con TG-")
        sys.exit(1)

    r = requests.post(f"{BASE_URL}/oauth/token", data={
        "grant_type":    "authorization_code",
        "client_id":     APP_ID,
        "client_secret": secret,
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
    })

    if r.status_code != 200:
        err(f"Error al obtener token: {r.text}")
        sys.exit(1)

    data = r.json()
    token = data["access_token"]
    user_id = data["user_id"]
    ok(f"Token obtenido para usuario {user_id}")

    with open(".token_cache.json", "w") as f:
        json.dump({"token": token, "user_id": user_id,
                   "expires": time.time() + 21000}, f)

    return token, user_id

def cargar_token():
    """Carga token desde cache si todavía es válido."""
    try:
        with open(".token_cache.json") as f:
            data = json.load(f)
        if data["expires"] > time.time() + 300:
            info(f"Token en cache válido (usuario {data['user_id']})")
            return data["token"], data["user_id"]
    except Exception:
        pass
    return None, None


def get_token():
    token, user_id = cargar_token()
    if token:
        return token, user_id
    return obtener_token()


# ══════════════════════════════════════════════════════════════════════════
# PASO 2 — LEER EXCEL
# ══════════════════════════════════════════════════════════════════════════

def leer_excel():
    """Lee el catálogo de vinos desde el Excel."""
    title("PASO 2 — Leyendo Excel")

    if not EXCEL_PATH.exists():
        err(f"No se encontró el archivo: {EXCEL_PATH}")
        err("Asegurate de que el Excel esté en la misma carpeta que este script.")
        sys.exit(1)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb["🍷 Catálogo de Vinos"]

    vinos = []
    for row in ws.iter_rows(min_row=5, values_only=True):
        nombre = row[1]   # col B
        if not nombre:
            continue

        bodega    = row[2]   # col C
        varietal  = row[3]   # col D
        anio      = row[4]   # col E
        region    = row[5]   # col F
        ml        = row[6]   # col G
        gtin      = row[7]   # col H
        precio    = row[8]   # col I
        stock     = row[11]  # col L
        tipo_pub  = row[12]  # col M

        if not precio or not stock:
            warn(f"Saltando '{nombre}': falta precio o stock")
            continue

        # Mapear tipo publicación
        tipo_map = {
            "Gold":         "gold_special",
            "Gold Premium": "gold_pro",
            "Clásica":      "bronze",
            "Gratuita":     "free",
        }
        listing_type = tipo_map.get(str(tipo_pub or ""), LISTING_TYPE_DEFAULT)

        vinos.append({
            "nombre":       str(nombre).strip(),
            "bodega":       str(bodega or "").strip(),
            "varietal":     str(varietal or "").strip(),
            "anio":         str(anio or "").strip(),
            "region":       str(region or "").strip(),
            "ml":           int(ml) if ml else 750,
            "gtin":         str(gtin or "").strip(),
            "precio":       float(precio),
            "stock":        int(stock),
            "listing_type": listing_type,
        })

    ok(f"{len(vinos)} vinos cargados desde el Excel")
    return vinos


# ══════════════════════════════════════════════════════════════════════════
# PASO 3 — SUBIR FOTOS
# ══════════════════════════════════════════════════════════════════════════

def nombre_a_carpeta(nombre_vino):
    """Convierte nombre del vino al formato de carpeta."""
    import unicodedata
    s = nombre_vino.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace(" ", "_")
    s = "".join(c for c in s if c.isalnum() or c == "_")
    return s


def subir_foto(ruta_foto, token):
    """Sube una foto a MeLi y retorna el picture_id."""
    with open(ruta_foto, "rb") as f:
        contenido = f.read()

    ext = ruta_foto.suffix.lower().replace(".", "")
    media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

    r = requests.post(
        f"{BASE_URL}/pictures/items/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (ruta_foto.name, contenido, media_type)},
    )

    if r.status_code == 201:
        return r.json().get("id")
    else:
        warn(f"Error subiendo {ruta_foto.name}: {r.status_code} {r.text[:100]}")
        return None


def obtener_fotos(nombre_vino, token, test_mode=False):
    """Busca las fotos del vino y las sube a MeLi."""
    carpeta_nombre = nombre_a_carpeta(nombre_vino)
    carpeta = FOTOS_DIR / carpeta_nombre

    if not carpeta.exists():
        # Intentar con coincidencia parcial
        matches = [d for d in FOTOS_DIR.iterdir()
                   if d.is_dir() and carpeta_nombre[:10] in d.name]
        if matches:
            carpeta = matches[0]
            warn(f"Usando carpeta aproximada: {carpeta.name}")
        else:
            warn(f"No se encontró carpeta de fotos para: {nombre_vino}")
            warn(f"  Buscando: {carpeta_nombre}")
            return []

    fotos = sorted(carpeta.glob("*.jpg")) + sorted(carpeta.glob("*.png"))
    fotos = fotos[:12]  # MeLi acepta máximo 12 fotos

    if not fotos:
        warn(f"No hay fotos en: {carpeta}")
        return []

    if test_mode:
        info(f"  [TEST] Se subirían {len(fotos)} fotos de {carpeta.name}")
        return ["TEST_PICTURE_ID"] * len(fotos)

    picture_ids = []
    for foto in fotos:
        pid = subir_foto(foto, token)
        if pid:
            picture_ids.append({"id": pid})
    return picture_ids


# ══════════════════════════════════════════════════════════════════════════
# PASO 4 — CREAR PUBLICACIÓN
# ══════════════════════════════════════════════════════════════════════════

def construir_descripcion(vino):
    """Construye descripción básica si no hay una personalizada."""
    return (
        f"{vino['nombre']}. "
        f"Bodega {vino['bodega']}. "
        f"Varietal: {vino['varietal']}. "
        f"Cosecha {vino['anio']}. "
        f"Región: {vino['region']}. "
        f"Botella {vino['ml']}ml. "
        f"Vino tinto premium argentino. "
        f"Ideal para maridar con carnes rojas, asado y quesos estacionados. "
        f"Temperatura de servicio entre 16 y 18 grados."
    )


def crear_publicacion(vino, picture_ids, token, test_mode=False):
    """Crea la publicación en MeLi."""

    titulo = (
        f"{vino['varietal']} {vino['bodega']} {vino['anio']} "
        f"{vino['region']} {vino['ml']}ml Vino Premium Argentina"
    )[:60]  # MeLi tiene límite de 60 caracteres en el título

    atributos = [
        {"id": "BRAND",                "value_name": vino["bodega"]},
        {"id": "UNIT_VOLUME",          "value_name": "750 mL"},
        {"id": "UNITS_PER_PACK",       "value_name": "1"},
        {"id": "IS_NON_ALCOHOLIC_DRINK", "value_name": "No"},
        {"id": "VALUE_ADDED_TAX",      "value_name": "10.5%"},
        {"id": "IMPORT_DUTY",          "value_name": "0%"},
        {"id": "CELLAR",               "value_name": vino["bodega"]},
        {"id": "VARIETAL",             "value_name": vino["varietal"]},
        {"id": "REGIONS",              "value_name": vino["region"]},
        {"id": "ORIGIN",               "value_name": "Argentina"},
        {"id": "WINE_TYPE",            "value_name": "Tinto"},
    ]

    if vino["anio"]:
        atributos.append({"id": "YEAR", "value_name": vino["anio"]})

    if vino["gtin"]:
        atributos.append({"id": "GTIN", "value_name": vino["gtin"]})
    else:
        atributos.append({"id": "EMPTY_GTIN_REASON", "value_name": "No tiene código"})

    payload = {
        "category_id":  CATEGORIA_VINOS,
        "family_name":  titulo,
        "price":        vino["precio"],
        "currency_id":  "ARS",
        "available_quantity": vino["stock"],
        "buying_mode":  "buy_it_now",
        "condition":    "new",
        "listing_type_id": vino["listing_type"],
        "description":  {"plain_text": construir_descripcion(vino)},
        "attributes":   atributos,
        "shipping": {
            "mode": "me2",
            "local_pick_up": False,
            "free_shipping": False,
        },
    }

    # Agregar fotos si las hay
    if picture_ids and picture_ids[0] != "TEST_PICTURE_ID":
        payload["pictures"] = picture_ids

    # Agregar GTIN si existe
    if vino["gtin"]:
        payload["attributes"].append({
            "id": "GTIN", "value_name": vino["gtin"]
        })

    if test_mode:
        info(f"  [TEST] Payload construido para: {titulo}")
        return {"id": "TEST_MLA000000000", "permalink": "https://test.mercadolibre.com.ar"}

    r = requests.post(
        f"{BASE_URL}/items",
        headers={
            "Authorization":  f"Bearer {token}",
            "Content-Type":   "application/json",
        },
        json=payload,
    )

    if r.status_code == 201:
        data = r.json()
        return {"id": data["id"], "permalink": data["permalink"]}
    else:
        err(f"Error creando publicación: {r.status_code}")
        err(r.text[:300])
        return None


# ══════════════════════════════════════════════════════════════════════════
# MAIN — ORQUESTADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

def main():
    test_mode = "--test" in sys.argv

    print(f"""
{BOLD}╔══════════════════════════════════════════════════════════╗
║       NEXUS VINOS — Carga Masiva Mercado Libre           ║
║       APP ID: {APP_ID[:20]}...                  ║
║       Modo: {"TEST (sin subir nada real)" if test_mode else "PRODUCCIÓN — subiendo a MeLi"}        ║
╚══════════════════════════════════════════════════════════╝{W}
""")

    if test_mode:
        warn("MODO TEST activado. No se subirá nada real a MeLi.")
        warn("Para subir de verdad: python carga_vinos_meli.py\n")

    # 1. Autenticación
    if test_mode:
        token, user_id = "TEST_TOKEN", "TEST_USER"
        info("Modo test: omitiendo autenticación real")
    else:
        token, user_id = get_token()

    # 2. Leer Excel
    vinos = leer_excel()

    if not vinos:
        err("No se encontraron vinos con precio y stock en el Excel.")
        sys.exit(1)

    # 3. Confirmar antes de subir
    title(f"PASO 3 — Subir {len(vinos)} vinos a MeLi")
    for i, v in enumerate(vinos):
        info(f"{i+1:2}. {v['nombre'][:45]:<45} | ${v['precio']:>10,.0f} | stock: {v['stock']}")

    if not test_mode:
        print(f"\n{Y}¿Confirmar la carga de {len(vinos)} publicaciones? (s/n): {W}", end="")
        if input().strip().lower() != "s":
            warn("Carga cancelada.")
            sys.exit(0)

    # 4. Procesar cada vino
    title("PASO 4 — Cargando publicaciones")
    resultados = []
    errores = []

    for i, vino in enumerate(vinos):
        print(f"\n[{i+1}/{len(vinos)}] {vino['nombre']}")

        # Subir fotos
        picture_ids = obtener_fotos(vino["nombre"], token, test_mode)
        if picture_ids:
            ok(f"Fotos: {len(picture_ids)} listas")
        else:
            warn("Sin fotos, se creará la publicación igual")

        # Crear publicación
        resultado = crear_publicacion(vino, picture_ids, token, test_mode)

        if resultado:
            ok(f"Publicación creada: {resultado['id']}")
            info(f"URL: {resultado['permalink']}")
            resultados.append({
                "vino":    vino["nombre"],
                "item_id": resultado["id"],
                "url":     resultado["permalink"],
            })
        else:
            errores.append(vino["nombre"])

        # Pausa entre publicaciones para no saturar la API
        if not test_mode and i < len(vinos) - 1:
            time.sleep(2)

    # 5. Resumen final
    title("RESUMEN FINAL")
    ok(f"{len(resultados)} publicaciones creadas exitosamente")
    if errores:
        err(f"{len(errores)} errores:")
        for e in errores:
            print(f"   - {e}")

    # Guardar log de resultados
    log_path = Path("resultados_carga.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    ok(f"Log guardado en: {log_path}")

    if not test_mode and resultados:
        print(f"\n{G}{BOLD}¡Listo! Tus {len(resultados)} vinos ya están en Mercado Libre.{W}")
        print(f"{B}Revisá las publicaciones en tu panel de vendedor.{W}\n")


if __name__ == "__main__":
    main()
