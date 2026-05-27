import requests
import json
import time

with open(".token_cache.json") as f:
    data = json.load(f)
token = data["token"]
user_id = data["user_id"]

headers = {"Authorization": f"Bearer {token}"}

vinos = [
    ("Año cero Altocedro", "Cabernet Sauvignon Altocedro"),
    ("Milamore Renacer", "Red Blend Renacer Milamore"),
    ("Manos Negras Stone Soil", "Blend blancas Manos Negras"),
    ("Santa Julia Reserva", "Chardonnay Santa Julia Reserva"),
    ("Magna Santa Julia", "Cabernet Sauvignon Santa Julia"),
    ("Pinot Noir Rose Alpataco", "Pinot Noir Rose Alpataco"),
    ("Semillon Losange", "Semillon Losange"),
    ("Riesling Losange", "Riesling Losange"),
    ("Zuccardi Q Cabernet Franc", "Cabernet Franc Zuccardi"),
    ("Brioso Susana Balbo", "Red Blend Susana Balbo Brioso"),
    ("Concrete Tank Alandes", "Concrete Tank Alandes"),
    ("La Consulta Select", "La Consulta Select Altocedro"),
    ("Osadia de Crear", "Espumante Susana Balbo Osadia"),
    ("Punto Final Renacer", "Cabernet Franc Renacer"),
    ("Crux Tempranillo", "Tempranillo Alfa Crux"),
    ("Año cero Malbec", "Malbec Altocedro"),
    ("Las Perdices Chardonnay", "Chardonnay Las Perdices"),
    ("Las Perdices Bonarda", "Bonarda Las Perdices"),
    ("Naranjo El Porvenir", "Vino Blanco El Porvenir"),
    ("Artesano Manos Negras", "Pinot Noir Manos Negras"),
    ("Zuccardi Q Cab Sauv", "Cabernet Sauvignon Zuccardi"),
    ("Merlot Reserva Alpataco", "Merlot Alpataco"),
    ("Crux Alfa Crux", "Cabernet Sauvignon Alfa Crux"),
    ("Gewurztraminer Alfa Crux", "Gewurztraminer Alfa Crux"),
    ("El Turco Karim Mussi", "Red Blend Karim Mussi"),
]

print(f"\n{'='*70}")
print(f"{'VINO':<30} {'SUGERIDO':>12} {'MÍN':>10} {'MÁX':>10} {'#':>4}")
print(f"{'='*70}")

resultados = []

for nombre, query in vinos:
    try:
        # Usar el endpoint de highlights que sí está permitido
        r = requests.get(
            f"https://api.mercadolibre.com/sites/MLA/search",
            headers=headers,
            params={
                "q": query,
                "category": "MLA1404",
                "limit": 5,
            }
        )

        if r.status_code == 403:
            # Fallback: buscar por precio referencial manual
            print(f"{nombre:<30} {'Sin acceso API':>12}")
            continue

        items = r.json().get("results", [])
        precios = [i["price"] for i in items if i.get("price", 0) > 500]

        if not precios:
            print(f"{nombre:<30} {'Sin resultados':>12}")
            continue

        minimo   = min(precios)
        maximo   = max(precios)
        promedio = sum(precios) / len(precios)
        sugerido = round(promedio * 0.90)

        print(f"{nombre:<30} ${sugerido:>10,.0f} ${minimo:>8,.0f} ${maximo:>8,.0f} {len(precios):>4}")
        resultados.append({
            "vino": nombre,
            "precio_sugerido": sugerido,
            "precio_minimo": round(minimo),
            "precio_maximo": round(maximo),
            "competidores": len(precios)
        })

        time.sleep(0.3)

    except Exception as e:
        print(f"{nombre:<30} Error: {e}")

print(f"{'='*70}")

with open("analisis_precios.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"\n✓ Guardado en analisis_precios.json")