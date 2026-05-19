from __future__ import annotations

import argparse
import json
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from scrapling.fetchers import Fetcher, StealthyFetcher


# Página a scrapear
TARGET_URL = "https://d1.com.co/"

StealthyFetcher.adaptive = True


def _css(node: Any, selector: str) -> Any:
    return node.css(selector)


# Básicamente, intenta abrir la página usando dos métodos:
# uno más avanzado para páginas dinámicas y otro más simple
# por si el primero falla.

def _get_candidate_pages(url: str) -> list[Any]:
    pages: list[Any] = []

    try:
        # Primer intento: usa StealthyFetcher para abrir la página como si fuera
        # un navegador real. Esto ayuda cuando los productos se cargan con JavaScript.

        stealth_page = StealthyFetcher.fetch(
            url,
            headless=True,
            network_idle=True,
            adaptive=True,
        )

        if getattr(stealth_page, "status", 200) == 200:
            pages.append(stealth_page)

    except Exception:
        pass

    try:
        # Segundo intento: usa Fetcher para traer el HTML directamente.
        # Es más rápido, pero puede fallar si la página depende mucho de JavaScript.

        static_page = Fetcher.get(url)

        if getattr(static_page, "status", 0) == 200:
            pages.append(static_page)

    except Exception:
        pass

    return pages


# Extrae el primer número encontrado en un texto.
# Se usa para limpiar precios obtenidos del HTML.
#
# Ejemplo:
# "$ 7.450" -> "7.450"

def _extract_first_number(value: str | None) -> str | None:
    if not value:
        return None

    match = re.search(r"\d[\d\.,]*", value)

    return match.group(0) if match else None


# Construye URLs de búsqueda para D1.
#
# Convierte el texto ingresado por el usuario
# a un formato válido para URL.
#
# Ejemplo:
# "arveja verde" -> "arveja+verde"

def _build_search_urls(search: str) -> list[str]:

    encoded = quote_plus(search.strip())

    return [
        f"https://domicilios.tiendasd1.com/search?name={encoded}",
    ]


# Estrategia de respaldo:
# si no se logran obtener productos completos desde las cards HTML,
# intenta recuperar al menos los links encontrados en la página.

def _extract_product_links_from_html(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    fallback_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in _css(page, "a.containerCard"):

        href = _css(link, "::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        title = (
            _css(link, "h3[data-testid='card-name']::text").get()
            or _css(link, "img::attr(alt)").get()
            or ""
        ).strip()

        fallback_products.append(
            {
                "name": title or None,
                "url": absolute_url,
                "source": "html-link",
            }
        )

        if len(fallback_products) >= limit:
            break

    return fallback_products


# Extrae productos desde las cards HTML visibles de D1.

def _extract_products_from_cards(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:

    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Básicamente, busca las cards HTML que representan
    # cada producto dentro de la página de D1.

    cards = _css(page, "div[class*='ProductWrapper_product-wrapper']")

    print("Cards encontradas:", len(cards))

    # Recorre cada producto encontrado.
    # Cada card representa 1 producto.

    for card in cards:

        # Extrae el link del producto.

        href = _css(card, "a.containerCard::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        # Extrae nombre del producto.

        name = (
            _css(card, "h3[data-testid='card-name']::text").get()
            or _css(card, "img::attr(alt)").get()
            or ""
        ).strip() or None

        # Extrae imagen.

        image = _css(card, "img::attr(src)").get()

        # Extrae precio actual.

        current_price_text = _css(
            card,
            "p[data-testid='card-base-price']::text"
        ).get()

        products.append(
            {
                "name": name,
                "url": absolute_url,
                "image": image,
                "seller": "D1",
                "price": _extract_first_number(current_price_text),
                "original_price": None,
                "discount_percent": None,
                "source": "html-card-d1",
            }
        )

        if len(products) >= limit:
            break

    return products


# Intenta varias estrategias hasta encontrar productos válidos.

def scrape_d1(search: str | None = None, max_items: int = 20) -> tuple[list[dict[str, Any]], str]:

    # Función principal:
    # recibe una búsqueda como "arroz" o "banano",
    # prueba URLs de D1 y devuelve productos encontrados.

    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:

        pages = _get_candidate_pages(url)

        for page in pages:

            # Primera estrategia:
            # intenta extraer productos desde las cards HTML.

            products = _extract_products_from_cards(
                page,
                url,
                limit=max_items,
            )

            # Segunda estrategia:
            # si no encontró cards completas,
            # intenta rescatar links de productos.

            if not products:

                products = _extract_product_links_from_html(
                    page,
                    url,
                    limit=max_items,
                )

            if products:
                return products[:max_items], url

    raise RuntimeError(
        "Could not extract products from D1 with the current strategy"
    )


def _parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description="Scrape products from D1"
    )

    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Product keyword to search, for example: arroz",
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
# Ejemplo:
#
# python scrapers/d1_scraper.py --search arroz --max-items 3

def main() -> None:

    args = _parse_args()

    data, source_url = scrape_d1(
        search=args.search,
        max_items=args.max_items,
    )

    print(
        f"Collected {len(data)} product records from {source_url}"
    )

    if args.search:

        slug = "_".join(args.search.lower().split())

        output_file = f"data/d1_{slug}_products.json"

    else:

        output_file = "data/d1_products.json"

    with open(output_file, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    main()