import json
import sys
from pathlib import Path
import unicodedata
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from models.ingredient_model import create_ingredient

load_dotenv()

DATA_DIR = BASE_DIR / "data"


def normalize_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()
    normalized = unicodedata.normalize("NFKD", text)

    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_price(price):
    if price is None:
        return None

    if isinstance(price, (int, float)):
        return price

    try:
        cleaned_price = str(price).replace(".", "").strip()

        if not cleaned_price:
            return None

        return int(cleaned_price)
    except (TypeError, ValueError):
        return None


def is_relevant_product(ingredient, product_name):
    normalized_name = normalize_text(product_name)
    normalized_ingredient = normalize_text(ingredient)

    if not normalized_name or not normalized_ingredient:
        return False

    aliases = {
        "pechuga": ["pechuga", "pollo"],
    }

    terms = aliases.get(normalized_ingredient, [normalized_ingredient])

    return any(term in normalized_name for term in terms)


def import_products():
    best_products: dict[tuple[str, str], dict[str, object]] = {}
    scanned_products = 0
    skipped_products = 0
    irrelevant_products = 0

    for file_path in DATA_DIR.glob("*.json"):
        print(f"Procesando archivo: {file_path.name}")

        with open(file_path, "r", encoding="utf-8") as file:
            products = json.load(file)

        for product in products:
            scanned_products += 1

            ingredient = str(product.get("ingredient", "")).strip()

            if not ingredient:
                skipped_products += 1
                print(
                    f"  -> Omitido sin ingrediente válido: {product.get('name')} | {product.get('seller')} | {product.get('url')}"
                )
                continue

            price = normalize_price(product.get("price"))

            if price is None:
                skipped_products += 1
                print(
                    f"  -> Omitido sin precio válido: {product.get('name')} | {product.get('seller')} | {product.get('url')}"
                )
                continue

            store = str(product.get("seller", "")).strip()

            if not store:
                skipped_products += 1
                print(
                    f"  -> Omitido sin tienda válida: {product.get('name')} | {product.get('url')}"
                )
                continue

            if not is_relevant_product(ingredient, product.get("name")):
                irrelevant_products += 1
                print(
                    f"  -> Descartado por irrelevante: ingrediente={ingredient} | tienda={store} | nombre={product.get('name')}"
                )
                continue

            key = (ingredient, store.lower())
            current_best = best_products.get(key)

            if current_best is None or price < current_best["precio"]:
                best_products[key] = {
                    "nombre": product.get("name"),
                    "imagen": product.get("image"),
                    "precio": price,
                    "tienda": store,
                    "url": product.get("url"),
                    "ingrediente": ingredient,
                }
                print(f"  -> Mejor precio actualizado para {ingredient} / {store}: {price}")

    print(
        f"\nResumen de filtrado: {scanned_products} productos revisados, {skipped_products} omitidos, {irrelevant_products} irrelevantes descartados, {len(best_products)} registros finales por insertar"
    )

    imported_total = 0

    for ingredient_name, store_name in sorted(best_products.keys()):
        product = best_products[(ingredient_name, store_name)]

        create_ingredient(
            nombre=product["nombre"],
            imagen=product["imagen"],
            precio=product["precio"],
            tienda=product["tienda"],
            url=product["url"],
            ingrediente=product["ingrediente"],
        )

        imported_total += 1
        print(
            f"  -> Insertado: {product['ingrediente']} / {product['tienda']} / {product['precio']}"
        )

    print(f"Productos importados/actualizados: {imported_total}")


if __name__ == "__main__":
    import_products()