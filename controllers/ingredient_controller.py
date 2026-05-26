# import re

from flask import jsonify, request

from models.ingredient_model import (
    create_ingredient,
    delete_ingredient,
    get_all_ingredients,
    update_ingredient,
)
from scrapers.exito_scraper import scrape_exito
from scrapers.d1_scraper import scrape_d1
from scrapers.jumbo_scraper import scrape_jumbo


def normalize_scraped_product(product):
    nombre = (
        product.get("nombre")
        or product.get("name")
        or product.get("title")
        or product.get("titleText")
        or "Sin nombre"
    )
    imagen = product.get("imagen") or product.get("image") or ""
    precio = product.get("precio") if product.get("precio") is not None else product.get("price")
    if isinstance(precio, str):
        precio_clean = precio.replace(".", "").replace(",", ".").strip()
        try:
            precio = int(float(precio_clean))
        except ValueError:
            try:
                precio = float(precio_clean)
            except ValueError:
                precio = 0
    elif precio is None:
        precio = 0

    tienda = (
        product.get("tienda")
        or product.get("seller")
        or product.get("market")
        or product.get("store")
        or "Tienda"
    )

    return {
        "nombre": nombre,
        "imagen": imagen,
        "precio": precio,
        "tienda": tienda,
        "url": product.get("url") or product.get("link") or "",
    }


def scrape_and_normalize(search=None, max_items=20):
    normalized = []
    seen = set()

    scrapers = [
        scrape_exito,
        scrape_d1,
        scrape_jumbo,
    ]

    for scraper_fn in scrapers:
        try:
            products, source_url = scraper_fn(search=search, max_items=max_items)
        except Exception as e:
            print(f"WARNING: scraper {scraper_fn.__name__} failed: {e}")
            continue

        for product in products:
            item = normalize_scraped_product(product)
            key = item["url"] or f"{item['nombre']}|{item['tienda']}"
            if key in seen:
                continue
            seen.add(key)
            normalized.append(item)
            if len(normalized) >= max_items:
                return normalized

    if not normalized:
        raise RuntimeError("No scraped products were found from the available scrapers.")

    return normalized


# EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def validate_payload(data):
    nombre = str(data.get("nombre", "")).strip()
    imagen = str(data.get("imagen", "")).strip()
    precio = data.get("precio")
    tienda = str(data.get("tienda", "")).strip()
    url = str(data.get("url", "")).strip()

    if not nombre:
        return None, "nombre is required"

    return {
        "nombre": nombre,
        "imagen": imagen,
        "precio": precio,
        "tienda": tienda,
        "url": url,
    }, None


def list_ingredients():
    try:
        print('DEBUG: list_ingredients invoked')
        if request.args.get('scrape', '').lower() in ('1', 'true', 'yes'):
            search_term = request.args.get('search', 'arroz')
            print(f"DEBUG: scraping ingredients for search={search_term}")
            ingredients = scrape_and_normalize(search=search_term, max_items=20)
        else:
            ingredients = get_all_ingredients()

        print('DEBUG: got ingredients count', len(ingredients) if hasattr(ingredients, '__len__') else 'n/a')
        return jsonify(ingredients), 200
    except Exception as e:
        print('ERROR in list_ingredients:', e)
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def create_ingredient_handler():
    payload, error = validate_payload(request.get_json(silent=True) or {})

    if error:
        return jsonify({"error": error}), 400

    new_ingredient = create_ingredient(
        payload["nombre"],
        payload["imagen"],
        payload["precio"],
        payload["tienda"],
        payload["url"],
    )

    return jsonify(new_ingredient), 201


def update_ingredient_handler(ingredient_id: int):
    if ingredient_id <= 0:
        return jsonify({"error": "invalid id"}), 400

    payload, error = validate_payload(request.get_json(silent=True) or {})

    if error:
        return jsonify({"error": error}), 400

    updated = update_ingredient(
        ingredient_id,
        payload["nombre"],
        payload["imagen"],
        payload["precio"],
        payload["tienda"],
        payload["url"],
    )

    if not updated:
        return jsonify({"error": "ingredient not found"}), 404

    return jsonify(updated), 200


def delete_ingredient_handler(ingredient_id: int):
    if ingredient_id <= 0:
        return jsonify({"error": "invalid id"}), 400

    deleted = delete_ingredient(ingredient_id)

    if not deleted:
        return jsonify({"error": "ingredient not found"}), 404

    return "", 204
