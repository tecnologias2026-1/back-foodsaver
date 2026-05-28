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


def _page_text(page: Any) -> str:
    parts: list[str] = []

    for selector in ("body::text", "html::text"):
        try:
            values = css(page, selector).getall()
        except Exception:
            continue

        for value in values:
            if value:
                cleaned_value = str(value).strip()

                if cleaned_value:
                    parts.append(cleaned_value)

    return " ".join(parts).strip().lower()


def _looks_blocked_or_broken(page_text: str) -> bool:
    if len(page_text) < 80:
        return True

    blocked_signals = (
        "captcha",
        "access denied",
        "forbidden",
        "blocked",
        "verify you are human",
        "unusual traffic",
        "robot",
        "enable javascript",
    )

    return any(signal in page_text for signal in blocked_signals)


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
        title = (
            css(link, "::attr(title)").get()
            or css(link, "::text").get()
            or ""
        ).strip()
        image = css(link, "img::attr(src)").get()

        print(
            "Exito card link debug -> "
            f"nombre={title or None} | precio=None | url={href or None} | imagen={image or None}"
        )

        if not href:
            print("Exito card discarded -> reason=missing href")
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            print(f"Exito card discarded -> reason=duplicate url | url={absolute_url}")
            continue

        seen_urls.add(absolute_url)

        fallback_products.append(
            {
                "name": title or None,
                "brand": None,
                "url": absolute_url,
                "image": image,
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
) -> tuple[list[dict[str, Any]], int]:
    
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Busca todos los <article> que tengan una clase que
    # contenga: productCard_productCard.
    cards = css(page, "article[class*='productCard_productCard']")
    print("Cards encontradas:", len(cards))

    for card in cards:
        href = css(card, "a[data-testid='product-link']::attr(href)").get()
        raw_name = (
            css(card, "h3::text").get()
            or css(card, "img::attr(alt)").get()
            or ""
        ).strip()
        image = css(
            card,
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

        print(
            "Exito card debug -> "
            f"nombre={raw_name or None} | precio={current_price_text or None} | url={href or None} | imagen={image or None}"
        )

        if not href:
            print("Exito card discarded -> reason=missing href")
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            print(f"Exito card discarded -> reason=duplicate url | url={absolute_url}")
            continue

        seen_urls.add(absolute_url)

        name = raw_name or None

        if not name:
            print(f"Exito card discarded -> reason=missing name | url={absolute_url}")
            continue

        quantity, unit, clean_name = extract_quantity(name or "")
        price = extract_first_number(current_price_text)

        if price is None:
            print(f"Exito card discarded -> reason=missing price | url={absolute_url} | name={clean_name}")
            continue

        products.append(
            {
                "name": clean_name,
                "url": absolute_url,
                "image": image,
                "seller": "Exito",
                "price": price,
                "quantity": quantity,
                "unit": unit,
                "original_price": extract_first_number(original_price_text),
                "discount_percent": extract_first_number(discount_text),
                "source": "html-card-exito",
            }
        )

        if len(products) >= limit:
            break

    return products, len(cards)


def scrape_exito(
    search: str | None = None,
    max_items: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Scrape Exito products; optionally target search result pages."""

    urls = _build_search_urls(search) if search else [TARGET_URL]
    search_label = search or "esta búsqueda"
    found_any_page = False

    for url in urls:
        pages = get_candidate_pages(url)

        if not pages:
            continue

        for page in pages:
            found_any_page = True
            page_text = _page_text(page)

            if _looks_blocked_or_broken(page_text):
                raise RuntimeError(
                    f"Exito page blocked, empty, or too short for {search_label}"
                )
            
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

            if products:
                for product in products:
                    print(
                        "Exito product debug -> "
                        f"nombre={product.get('name')} | precio={product.get('price')} | url={product.get('url')} | imagen={product.get('image')}"
                    )
            

            # Busca las cards visibles del HTML, como los <article> de productos.
            if not products:
                products, cards_found = _extract_products_from_cards(
                    page,
                    url,
                    limit=max_items,
                )

                if cards_found > 0 and not products:
                    raise RuntimeError(
                        f"Exito structure looks broken for {search_label}: cards found but no valid products"
                    )


            # Rescata al menos links de productos, aunque tengan menos información.
            if not products:
                products = _extract_product_links_from_html(
                    page,
                    url,
                    limit=max_items,
                )

            valid_products = [product for product in products if product.get("price") is not None]

            if valid_products:
                return valid_products[:max_items], url

            if products:
                print(f"No se encontraron productos para {search_label} en Exito")
                return [], url

    if found_any_page:
        print(f"No se encontraron productos para {search_label} en Exito")
        return [], urls[0] if urls else TARGET_URL

    raise RuntimeError(f"Could not load any candidate pages for Exito search={search_label}")


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

    if not data:
        print(f"No se encontraron productos para {args.search or 'esta búsqueda'} en Exito")

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