from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.parse import quote_plus, urljoin

from utils.jsonld_utils import extract_products_from_jsonld
from utils.product_utils import extract_quantity
from utils.scraper_utils import (
    css,
    extract_first_number,
    get_candidate_pages,
)


# Página a scrapear
TARGET_URL = "https://www.exito.com/"


# Recibe un término de búsqueda, lo codifica para URL
# y genera varias URLs de búsqueda en Exito que podrían contener
# los productos relacionados con ese término.
def _build_search_urls(search: str) -> list[str]:
    # Convierte el texto de búsqueda a un formato que pueda usarse
    # dentro de una URL.
    encoded = quote_plus(search.strip())

    return [
        f"https://www.exito.com/s?q={encoded}&sort=price_asc",
        f"https://www.exito.com/search?q={encoded}",
        f"https://www.exito.com/buscar?ft={encoded}",
    ]


# Intenta recuperar al menos
# los links de productos encontrados en la página.
def _extract_product_links_from_html(
    page: Any,
    base_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    
    fallback_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in css(page, "a[href*='/p/']"):
        href = css(link, "::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        title = (
            css(link, "::attr(title)").get()
            or css(link, "::text").get()
            or ""
        ).strip()

        fallback_products.append(
            {
                "name": title or None,
                "brand": None,
                "url": absolute_url,
                "image": None,
                "seller": "Exito",
                "price": None,
                "quantity": None,
                "unit": None,
                "original_price": None,
                "discount_percent": None,
                "source": "html-link-exito",
            }
        )

        if len(fallback_products) >= limit:
            break

    return fallback_products


# Extrae productos de las cards visibles del HTML
def _extract_products_from_cards(
    page: Any,
    base_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Busca todos los <article> que tengan una clase que
    # contenga: productCard_productCard.
    cards = css(page, "article[class*='productCard_productCard']")
    print("Cards encontradas:", len(cards))

    for card in cards:
        href = css(card, "a[data-testid='product-link']::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        name = (
            css(card, "h3::text").get()
            or css(card, "img::attr(alt)").get()
            or ""
        ).strip() or None

        quantity, unit, clean_name = extract_quantity(name or "")

        image = css(card,
            "a[data-testid='product-link'] img::attr(src)"
        ).get()

        current_price_text = css(
            card,
            "p[data-fs-container-price-otros='true']::text",
        ).get()

        if not current_price_text:
            current_price_text = css(
                card,
                "[data-fs-container-price-otros='true']::text",
            ).get()

        original_price_text = css(
            card,
            "p[class*='price-dashed']::text",
        ).get()

        discount_text = css(
            card,
            "span[data-percentage='true']::text",
        ).get()

        products.append(
            {
                "name": clean_name,
                "url": absolute_url,
                "image": image,
                "seller": "Exito",
                "price": extract_first_number(current_price_text),
                "quantity": quantity,
                "unit": unit,
                "original_price": extract_first_number(original_price_text),
                "discount_percent": extract_first_number(discount_text),
                "source": "html-card-exito",
            }
        )

        if len(products) >= limit:
            break

    return products


def scrape_exito(
    search: str | None = None,
    max_items: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Scrape Exito products; optionally target search result pages."""

    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:
        pages = get_candidate_pages(url)

        for page in pages:
            
            # Con JSON-LD primero
            raw_json_blocks = css(
                page,
                "script[type='application/ld+json']::text",
            ).getall()

            if not raw_json_blocks:
                print("No se encontró ningún bloque JSON-LD")
            else:
                print(f"Se encontraron {len(raw_json_blocks)} bloques JSON-LD")

            products = extract_products_from_jsonld(
                raw_json_blocks, 
                seller="Exito", 
                source="json-ld-exito"
            )

            print(f"Productos encontrados desde JSON-LD: {len(products)}")
            

            # Busca las cards visibles del HTML, como los <article> de productos.
            if not products:
                products = _extract_products_from_cards(
                    page,
                    url,
                    limit=max_items,
                )


            # Rescata al menos links de productos, aunque tengan menos información.
            if not products:
                products = _extract_product_links_from_html(
                    page,
                    url,
                    limit=max_items,
                )

            if products:
                return products[:max_items], url

    raise RuntimeError("Could not extract products from Exito with the current strategy")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape products from exito.com")

    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Product keyword to search, for example: banano",
    )

    parser.add_argument(
        "--ingredient",
        type=str,
        default=None,
        help="Clean ingredient category to store in the JSON output",
    )

    parser.add_argument(
        "--max-items",
        type=int,
        default=5,
        help="Maximum number of products to store",
    )

    return parser.parse_args()


# Ejecuta el scraper usando los parámetros recibidos
# desde terminal, guarda los productos encontrados
# en un archivo JSON y muestra el resultado por consola.
#
# Ejemplo de ejecución:
#
# python -m scrapers.exito_scraper --search arroz --max-items 3
def main() -> None:
    args = _parse_args()
    ingredient = (args.ingredient or args.search or "").strip() or None

    data, source_url = scrape_exito(
        search=args.search,
        max_items=args.max_items,
    )

    print(f"Collected {len(data)} product records from {source_url}")

    if ingredient:
        for product in data:
            product["ingredient"] = ingredient

        slug = "_".join(ingredient.lower().split())
        output_file = f"data/exito_{slug}_products.json"
    elif args.search:
        slug = "_".join(args.search.lower().split())
        output_file = f"data/exito_{slug}_products.json"  # Para cambiar la ruta de salida, modificar esta línea.
    else:
        output_file = "data/exito_products.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    main()