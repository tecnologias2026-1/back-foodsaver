from __future__ import annotations

import json
from typing import Any

from utils.product_utils import extract_quantity


# Verifica si el JSON-LD extraído del HTML corresponde
# a un producto real.
#
# Exito incluye información de productos dentro de bloques
# JSON-LD ocultos en el HTML, por ejemplo:
#
# {
#   "@type": "Product",
#   "name": "Arroz Diana",
#   "price": "4500"
# }

def is_product_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "product"

    if isinstance(value, list):
        return any(
            isinstance(item, str) and item.lower() == "product"
            for item in value
        )

    return False


# Recorre los bloques JSON-LD extraídos del HTML
# y construye una lista de productos válidos.
#
# Para cada bloque encontrado:
# - verifica si "@type" es "Product"
# - extrae nombre, precio, URL, imagen y marca
# - evita agregar productos repetidos
#
# Finalmente devuelve una lista limpia de productos obtenidos
# directamente desde el JSON-LD de la página.
def extract_products_from_jsonld(
    raw_json_blocks: list[str],
    seller: str,
    source: str,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    def add_product(item: dict[str, Any]) -> None:
        offers = item.get("offers")

        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        if not isinstance(offers, dict):
            offers = {}

        name = item.get("name")
        url = item.get("url") or item.get("@id") or ""

        price = (
            offers.get("price")
            or offers.get("lowPrice")
        )
        key = f"{name}|{url}"

        if key in seen_keys:
            return

        seen_keys.add(key)

        quantity, unit, clean_name = extract_quantity(name or "")

        products.append(
            {
                "name": clean_name,
                "url": url,
                "image": item.get("image"),
                "seller": seller,
                "price": price,
                "quantity": quantity,
                "unit": unit,
                "original_price": None,
                "discount_percent": None,
                "source": source,
            }
        )

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if is_product_type(node.get("@type")):
                add_product(node)

            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for value in node:
                walk(value)

    for raw in raw_json_blocks:
        try:
            payload = json.loads(raw)

        except json.JSONDecodeError:
            continue

        walk(payload)

    return products