import requests
import json

with open(".token_cache.json") as f:
    data = json.load(f)
token = data["token"]

headers = {"Authorization": f"Bearer {token}"}

r = requests.get(
    "https://api.mercadolibre.com/categories/MLA1404/attributes",
    headers=headers
)

attrs = r.json()
for a in attrs:
    tags = a.get("tags", {})
    if tags.get("required") or tags.get("conditional_required"):
        print(f"REQUERIDO | {a['id']} | {a['name']}")
    else:
        print(f"opcional  | {a['id']} | {a['name']}")
