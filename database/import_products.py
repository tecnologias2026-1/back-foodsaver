import json
import sys
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from models.ingredient_model import create_ingredient

load_dotenv()

DATA_DIR = BASE_DIR / "data"


def normalize_price(price):
    if price is None:
        return None

    if isinstance(price, (int, float)):
        return price

    return int(str(price).replace(".", ""))


def import_products():
    total = 0

    for file_path in DATA_DIR.glob("*.json"):
        print(f"Procesando archivo: {file_path.name}")

        with open(file_path, "r", encoding="utf-8") as file:
            products = json.load(file)

        # print(
        #     f"Nombre: {products[0]['name']}\n"
        #     f"Precio: {normalize_price(products[0]['price'])}\n"
        #     f"URL: {products[0]['url']}"
        # )
        # return
    
        for product in products:
            create_ingredient(
                nombre=product.get("name"),
                imagen=product.get("image"),
                precio=normalize_price(product.get("price")),
                tienda=product.get("seller"),
                url=product.get("url"),
            )

            total += 1

    print(f"Productos importados/actualizados: {total}")


if __name__ == "__main__":
    import_products()