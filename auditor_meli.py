"""
NEXUS VINOS — Auditor de Publicaciones MeLi
============================================
Consulta todas tus publicaciones activas, detecta las que están "perdiendo"
y genera un reporte JSON + HTML con recomendaciones.

USO:
    1. Asegurate de tener tu access_token actualizado (el mismo que usás en carga_vinos_meli.py)
    2. Pegá tu access_token en la variable ACCESS_TOKEN de abajo
    3. Corré: python auditor_meli.py
    4. Se abre automáticamente el reporte en tu navegador

REQUIERE:
    pip install requests
"""

import requests
import json
import webbrowser
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURACIÓN — COMPLETÁ ESTOS VALORES
# ─────────────────────────────────────────────
ACCESS_TOKEN = "PEGA_TU_TOKEN_ACA"   # <-- pegá tu token acá
SELLER_ID    = None   # Si lo sabés ponelo, si no lo detectamos automático

# ─────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────
BASE_URL  = "https://api.mercadolibre.com"
HEADERS   = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

HEALTH_LABELS = {
    "good":    ("✅ Ganando",    "#22c55e"),
    "normal":  ("⚠️ Empatando", "#f59e0b"),
    "bad":     ("❌ Perdiendo", "#ef4444"),
    "without": ("➖ Sin datos",  "#94a3b8"),
}

# ─────────────────────────────────────────────
#  FUNCIONES DE API
# ─────────────────────────────────────────────

def get_seller_id():
    """Obtiene el user_id del token actual."""
    r = requests.get(f"{BASE_URL}/users/me", headers=HEADERS)
    r.raise_for_status()
    return r.json()["id"]


def get_all_items(seller_id):
    """Descarga todos los item_id del vendedor (paginado)."""
    items = []
    offset = 0
    limit  = 50
    print("📦 Descargando lista de publicaciones...")
    while True:
        url = f"{BASE_URL}/users/{seller_id}/items/search"
        params = {"limit": limit, "offset": offset, "status": "active"}
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data   = r.json()
        batch  = data.get("results", [])
        items += batch
        total  = data.get("paging", {}).get("total", 0)
        print(f"   {len(items)} / {total} publicaciones obtenidas")
        if len(items) >= total or not batch:
            break
        offset += limit
    return items


def get_items_details(item_ids):
    """Obtiene detalles en lote (hasta 20 por request)."""
    details = []
    chunk_size = 20
    print(f"🔍 Obteniendo detalles de {len(item_ids)} publicaciones...")
    for i in range(0, len(item_ids), chunk_size):
        chunk = item_ids[i:i+chunk_size]
        ids_str = ",".join(chunk)
        url = f"{BASE_URL}/items?ids={ids_str}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        for entry in r.json():
            if entry.get("code") == 200:
                details.append(entry["body"])
        print(f"   Procesados {min(i+chunk_size, len(item_ids))} / {len(item_ids)}")
    return details


def get_item_health(item_id):
    """Obtiene el health/posicionamiento de una publicación."""
    try:
        url = f"{BASE_URL}/items/{item_id}/health"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def get_visits(item_id):
    """Obtiene visitas de los últimos 30 días."""
    try:
        url = f"{BASE_URL}/visits/items"
        params = {"ids": item_id}
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                return data[0].get("total_visits", 0)
    except Exception:
        pass
    return 0


# ─────────────────────────────────────────────
#  ANÁLISIS Y RECOMENDACIONES
# ─────────────────────────────────────────────

def analyze_item(item, health_data, visits):
    """Genera un diagnóstico y recomendaciones para un ítem."""
    issues  = []
    tips    = []

    # Estado health
    level = "without"
    if health_data:
        level = health_data.get("level", "without")

    # Precio
    price = item.get("price", 0)
    if price == 0:
        issues.append("Sin precio configurado")

    # Fotos
    pics = item.get("pictures", [])
    if len(pics) < 3:
        issues.append(f"Pocas fotos ({len(pics)} — recomendado: mínimo 6)")
        tips.append("Agregá más fotos de alta calidad: etiqueta, copa servida, bodega")

    # Descripción
    desc = item.get("description") or {}
    desc_text = desc.get("plain_text", "") if isinstance(desc, dict) else ""
    if len(desc_text) < 200:
        issues.append("Descripción corta o vacía")
        tips.append("Escribí una descripción completa: varietal, añada, maridaje, bodega, notas de cata")

    # Título
    title = item.get("title", "")
    if len(title) < 40:
        issues.append("Título muy corto")
        tips.append("Optimizá el título: Vino + Varietal + Bodega + Región + ml (ej: 'Vino Tinto Malbec Zuccardi Valle 750ml Mendoza')")

    # Visitas
    if visits == 0:
        issues.append("Sin visitas registradas")
        tips.append("Activá Product Ads aunque sea con $200/día para generar tráfico inicial")
    elif visits < 10:
        issues.append(f"Pocas visitas ({visits} en 30 días)")
        tips.append("Revisá palabras clave en el título y considerá activar Product Ads")

    # Stock
    avail = item.get("available_quantity", 0)
    if avail == 0:
        issues.append("Sin stock disponible")
        tips.append("Actualizá el stock, MeLi penaliza las publicaciones sin inventario")
    elif avail < 3:
        issues.append(f"Stock bajo ({avail} unidades)")

    # Envío
    shipping = item.get("shipping", {})
    free_shipping = shipping.get("free_shipping", False)
    if not free_shipping:
        issues.append("Sin envío gratis")
        tips.append("El envío gratis mejora drásticamente el CTR — evaluá absorber el costo en el precio")

    # Garantía
    if not item.get("warranty"):
        tips.append("Agregá garantía del vendedor (aunque sea 'Satisfacción garantizada')")

    return {
        "id":           item.get("id"),
        "title":        title,
        "price":        price,
        "currency":     item.get("currency_id", "ARS"),
        "status":       item.get("status", ""),
        "health_level": level,
        "visits_30d":   visits,
        "stock":        avail,
        "pics_count":   len(pics),
        "free_ship":    free_shipping,
        "link":         item.get("permalink", ""),
        "issues":       issues,
        "tips":         tips,
        "category_id":  item.get("category_id", ""),
    }


# ─────────────────────────────────────────────
#  GENERADOR DE REPORTE HTML
# ─────────────────────────────────────────────

def generate_html(results, seller_id, timestamp):
    losing   = [r for r in results if r["health_level"] == "bad"]
    normal   = [r for r in results if r["health_level"] == "normal"]
    good     = [r for r in results if r["health_level"] == "good"]
    no_data  = [r for r in results if r["health_level"] == "without"]

    def card(item):
        label, color = HEALTH_LABELS.get(item["health_level"], ("➖", "#94a3b8"))
        issues_html = "".join(f'<li class="issue">{i}</li>' for i in item["issues"]) if item["issues"] else "<li class='ok'>Sin problemas críticos detectados</li>"
        tips_html   = "".join(f'<li class="tip">💡 {t}</li>' for t in item["tips"]) if item["tips"] else ""
        price_fmt   = f"${item['price']:,.0f}"
        return f"""
        <div class="card" data-level="{item['health_level']}">
          <div class="card-header">
            <span class="badge" style="background:{color}">{label}</span>
            <a href="{item['link']}" target="_blank" class="item-link">Ver en MeLi ↗</a>
          </div>
          <h3 class="item-title">{item['title']}</h3>
          <div class="meta-row">
            <span>💰 {price_fmt}</span>
            <span>👁 {item['visits_30d']} visitas</span>
            <span>📦 Stock: {item['stock']}</span>
            <span>🖼 {item['pics_count']} fotos</span>
            <span>{'🚚 Envío gratis' if item['free_ship'] else '💸 Sin envío gratis'}</span>
          </div>
          <ul class="issues-list">{issues_html}</ul>
          {f'<ul class="tips-list">{tips_html}</ul>' if tips_html else ""}
          <div class="item-id">ID: {item['id']} · Cat: {item['category_id']}</div>
        </div>
        """

    all_cards = "".join(card(r) for r in sorted(results, key=lambda x: ["bad","normal","without","good"].index(x["health_level"])))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NEXUS Vinos — Auditoría MeLi</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;600;700&display=swap');

  :root {{
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1e1e2e;
    --text: #e2e8f0;
    --muted: #64748b;
    --red: #ef4444;
    --yellow: #f59e0b;
    --green: #22c55e;
    --accent: #c084fc;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; min-height: 100vh; }}

  header {{
    padding: 2.5rem 2rem 1.5rem;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
  }}
  header h1 {{ font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; }}
  header h1 span {{ color: var(--accent); }}
  header .ts {{ font-family: 'DM Mono', monospace; font-size: 0.72rem; color: var(--muted); }}

  .summary {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;
    padding: 1.5rem 2rem;
  }}
  .stat {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.2rem 1.5rem;
    display: flex; flex-direction: column; gap: 0.3rem;
  }}
  .stat .num {{ font-size: 2rem; font-weight: 700; font-family: 'DM Mono', monospace; }}
  .stat .lbl {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}

  .filters {{
    padding: 0 2rem 1rem;
    display: flex; gap: 0.75rem; flex-wrap: wrap;
  }}
  .filter-btn {{
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text); padding: 0.45rem 1rem; border-radius: 999px;
    cursor: pointer; font-size: 0.82rem; font-family: 'DM Sans', sans-serif;
    transition: all 0.2s;
  }}
  .filter-btn:hover, .filter-btn.active {{ border-color: var(--accent); color: var(--accent); }}

  .grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1rem; padding: 0 2rem 3rem;
  }}

  .card {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.25rem;
    transition: border-color 0.2s;
  }}
  .card:hover {{ border-color: #2e2e42; }}
  .card[data-level="bad"]    {{ border-left: 3px solid var(--red); }}
  .card[data-level="normal"] {{ border-left: 3px solid var(--yellow); }}
  .card[data-level="good"]   {{ border-left: 3px solid var(--green); }}

  .card-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.75rem;
  }}
  .badge {{
    font-size: 0.72rem; font-weight: 600; padding: 0.3rem 0.75rem;
    border-radius: 999px; color: #000;
  }}
  .item-link {{
    font-size: 0.75rem; color: var(--muted); text-decoration: none;
    transition: color 0.2s;
  }}
  .item-link:hover {{ color: var(--accent); }}

  .item-title {{
    font-size: 0.95rem; font-weight: 600; line-height: 1.4;
    margin-bottom: 0.75rem; color: var(--text);
  }}

  .meta-row {{
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    font-size: 0.75rem; color: var(--muted);
    margin-bottom: 1rem; font-family: 'DM Mono', monospace;
  }}
  .meta-row span {{
    background: var(--bg); padding: 0.2rem 0.5rem;
    border-radius: 4px; border: 1px solid var(--border);
  }}

  .issues-list, .tips-list {{
    list-style: none; display: flex; flex-direction: column; gap: 0.4rem;
    margin-bottom: 0.75rem;
  }}
  .issues-list li {{ font-size: 0.8rem; padding: 0.35rem 0.6rem; border-radius: 5px; }}
  li.issue {{ background: rgba(239,68,68,0.08); color: #fca5a5; border-left: 2px solid var(--red); }}
  li.ok    {{ background: rgba(34,197,94,0.08);  color: #86efac; border-left: 2px solid var(--green); }}
  li.tip   {{ font-size: 0.78rem; background: rgba(192,132,252,0.07); color: #d8b4fe; border-left: 2px solid var(--accent); padding: 0.35rem 0.6rem; border-radius: 5px; }}

  .item-id {{
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    color: #334155; margin-top: 0.5rem;
  }}

  .hidden {{ display: none; }}
</style>
</head>
<body>
<header>
  <h1>NEXUS <span>Vinos</span> — Auditoría MeLi</h1>
  <span class="ts">Seller ID: {seller_id} · Generado: {timestamp}</span>
</header>

<div class="summary">
  <div class="stat">
    <span class="num" style="color:var(--red)">{len(losing)}</span>
    <span class="lbl">Perdiendo</span>
  </div>
  <div class="stat">
    <span class="num" style="color:var(--yellow)">{len(normal)}</span>
    <span class="lbl">Empatando</span>
  </div>
  <div class="stat">
    <span class="num" style="color:var(--green)">{len(good)}</span>
    <span class="lbl">Ganando</span>
  </div>
  <div class="stat">
    <span class="num">{len(results)}</span>
    <span class="lbl">Total publicaciones</span>
  </div>
</div>

<div class="filters">
  <button class="filter-btn active" onclick="filter('all',this)">Todas</button>
  <button class="filter-btn" onclick="filter('bad',this)">❌ Perdiendo</button>
  <button class="filter-btn" onclick="filter('normal',this)">⚠️ Empatando</button>
  <button class="filter-btn" onclick="filter('good',this)">✅ Ganando</button>
  <button class="filter-btn" onclick="filter('without',this)">➖ Sin datos</button>
</div>

<div class="grid" id="grid">
  {all_cards}
</div>

<script>
function filter(level, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.card').forEach(card => {{
    if (level === 'all' || card.dataset.level === level) {{
      card.classList.remove('hidden');
    }} else {{
      card.classList.add('hidden');
    }}
  }});
}}
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    global SELLER_ID

    print("\n🚀 NEXUS VINOS — Auditor de Publicaciones MeLi")
    print("=" * 50)

    if ACCESS_TOKEN == "TU_ACCESS_TOKEN_AQUI":
        print("\n❌ ERROR: Pegá tu access_token en la variable ACCESS_TOKEN del script")
        return

    # 1. Obtener seller_id
    if not SELLER_ID:
        print("🔑 Detectando Seller ID...")
        SELLER_ID = get_seller_id()
        print(f"   Seller ID: {SELLER_ID}")

    # 2. Obtener todos los items
    item_ids = get_all_items(SELLER_ID)
    if not item_ids:
        print("⚠️ No se encontraron publicaciones activas.")
        return

    # 3. Obtener detalles en lote
    details = get_items_details(item_ids)

    # 4. Para cada item obtener health + visitas
    results = []
    print(f"\n📊 Analizando {len(details)} publicaciones (esto puede tardar un minuto)...")
    for i, item in enumerate(details, 1):
        item_id = item.get("id")
        health  = get_item_health(item_id)
        visits  = get_visits(item_id)
        analyzed = analyze_item(item, health, visits)
        results.append(analyzed)
        status_icon = HEALTH_LABELS.get(analyzed["health_level"], ("➖",""))[0]
        print(f"   [{i:02d}/{len(details):02d}] {status_icon} {item['title'][:55]}")

    # 5. Guardar JSON
    json_path = "reporte_meli.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON guardado: {json_path}")

    # 6. Generar HTML
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = generate_html(results, SELLER_ID, timestamp)
    html_path = "reporte_meli.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📄 Reporte HTML generado: {html_path}")

    # 7. Resumen en consola
    losing = [r for r in results if r["health_level"] == "bad"]
    print(f"\n{'='*50}")
    print(f"📉 Perdiendo:   {len(losing)}")
    print(f"⚠️  Empatando:  {len([r for r in results if r['health_level'] == 'normal'])}")
    print(f"✅ Ganando:     {len([r for r in results if r['health_level'] == 'good'])}")
    print(f"➖ Sin datos:   {len([r for r in results if r['health_level'] == 'without'])}")
    print(f"{'='*50}")

    if losing:
        print(f"\n🔴 TOP publicaciones perdiendo:")
        for r in losing[:5]:
            print(f"   • {r['title'][:50]} — {len(r['issues'])} problemas")

    # 8. Abrir en navegador
    abs_path = os.path.abspath(html_path)
    webbrowser.open(f"file://{abs_path}")
    print(f"\n✅ Reporte abierto en tu navegador.")
    print(f"   Si no abrió automáticamente, abrí el archivo: {abs_path}\n")


if __name__ == "__main__":
    main()
