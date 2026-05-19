from __future__ import annotations

import argparse
import json
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from scrapling.fetchers import Fetcher, StealthyFetcher

# Página a Scrapear
TARGET_URL = "https://www.exito.com/"
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

        stealth_page = StealthyFetcher.fetch(url, headless=True, network_idle=True, adaptive=True)
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
# Se usa para limpiar precios y descuentos obtenidos del HTML.

# Recibe un texto extraído del HTML, por ejemplo:
# "$ 4.500" o "20% OFF", y obtiene únicamente
# el número para poder trabajar mejor el precio o descuento.

def _extract_first_number(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\d[\d\.,]*", value)
    return match.group(0) if match else None


# Construye múltiples URLs de búsqueda para aumentar las 
# posibilidades de obtener resultados relevantes.

# Esta función recibe un término de búsqueda, lo codifica para URL 
# y genera varias URLs de búsqueda en Exito que podrían contener 
# los productos relacionados con ese término. Por ejemplo, para la búsqueda 
# "banano", generaría URLs como:

def _build_search_urls(search: str) -> list[str]:

    # Convierte el texto de búsqueda# a un formato que pueda usarse 
    # dentro de una URL
    encoded = quote_plus(search.strip())
    return [
        f"https://www.exito.com/s?q={encoded}&sort=price_asc",
        f"https://www.exito.com/search?q={encoded}",
        f"https://www.exito.com/buscar?ft={encoded}",
    ]


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
#
# Esto permite extraer datos directamente desde el JSON
# sin depender tanto de etiquetas HTML como <article>, <h3> o clases CSS.
#
# La función filtra únicamente los bloques cuyo "@type"
# sea "Product" para trabajar solo con productos válidos.

def _is_product_type(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "product"
    if isinstance(value, list):
        return any(isinstance(item, str) and item.lower() == "product" for item in value)
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

def _extract_products_from_jsonld(raw_json_blocks: list[str]) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    def add_product(item: dict[str, Any]) -> None:
        offers = item.get("offers")
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if not isinstance(offers, dict):
            offers = {}

        name = item.get("name")
        url = item.get("url")
        key = f"{name}|{url}"
        if key in seen_keys:
            return
        seen_keys.add(key)

        products.append(
            {
                "name": name,
                "sku": item.get("sku"),
                "brand": item.get("brand", {}).get("name") if isinstance(item.get("brand"), dict) else item.get("brand"),
                "price": offers.get("price"),
                "currency": offers.get("priceCurrency"),
                "availability": offers.get("availability"),
                "url": url,
                "image": item.get("image"),
                "source": "json-ld",
            }
        )

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if _is_product_type(node.get("@type")):
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


# Estrategia de respaldo:
# si no se logran obtener productos completos desde JSON-LD
# o desde las cards HTML, intenta recuperar al menos
# los links de productos encontrados en la página.
#
# Esto permite no perder completamente la información
# incluso si cambia la estructura visual del sitio.

def _extract_product_links_from_html(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    fallback_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in _css(page, "a[href*='/p/']"):
        href = _css(link, "::attr(href)").get()
        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        title = (_css(link, "::attr(title)").get() or _css(link, "::text").get() or "").strip()

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


def _extract_products_from_cards(page: Any, base_url: str, limit: int) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    #Busca todos los <article>que tengan una clase que 
    # contenga:productCard_productCard

    # Básicamente, busca las cards HTML que representan
    # cada producto dentro de la página de Exito.
    cards = _css(page, "article[class*='productCard_productCard']")

    # Recorre cada producto encontrado.
    # Aquí sucede el Scraping. Cada card es 1 producto de supermercado....
    for card in cards:
        href = _css(card, "a[data-testid='product-link']::attr(href)").get()
        if not href:
            continue

        absolute_url = urljoin(base_url, href)
        if absolute_url in seen_urls:
            continue
        seen_urls.add(absolute_url)

        # Extrae dentro de esa card el nombre, imagen, vendedor, precio actual, precio original y descuento...
        name = (_css(card, "h3::text").get() or _css(card, "img::attr(alt)").get() or "").strip() or None
        image = _css(card, "img::attr(src)").get()
        seller = _css(card, "[data-fs-product-details-seller__name]::text").get()

        current_price_text = _css(card, "p[data-fs-container-price-otros='true']::text").get()
        if not current_price_text:
            current_price_text = _css(card, "[data-fs-container-price-otros='true']::text").get()

        original_price_text = _css(card, "p[class*='price-dashed']::text").get()
        discount_text = _css(card, "span[data-percentage='true']::text").get()

        products.append(
            {
                "name": name,
                "url": absolute_url,
                "image": image,
                "seller": seller.strip() if isinstance(seller, str) else None,
                "price": _extract_first_number(current_price_text),
                "original_price": _extract_first_number(original_price_text),
                "discount_percent": _extract_first_number(discount_text),
                "source": "html-card",
            }
        )

        if len(products) >= limit:
            break

    return products

# Intenta varias estrategias hasta encontrar productos válidos.

def scrape_exito(search: str | None = None, max_items: int = 20) -> tuple[list[dict[str, Any]], str]:
    """Scrape Exito products; optionally target search result pages."""

    # Función principal: recibe una búsqueda como "arroz o banano",
    # prueba varias URLs de Exito y devuelve una lista de productos encontrados.

    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:
        pages = _get_candidate_pages(url)

        for page in pages:

            # Primera estrategia: busca productos en bloques JSON-LD.
            # Estos son datos estructurados ocultos en el HTML que pueden tener nombre, precio, URL e imagen.

            raw_json_blocks = _css(page, "script[type='application/ld+json']::text").getall()
            products = _extract_products_from_jsonld(raw_json_blocks)

            # Segunda estrategia: si JSON-LD no encontró productos,
            # busca las cards visibles del HTML, como los <article> de productos.

            if not products:
                products = _extract_products_from_cards(page, url, limit=max_items)

            # Tercera estrategia: si tampoco encontró cards completas,
            # intenta rescatar al menos links de productos, aunque tengan menos información.

            if not products:
                products = _extract_product_links_from_html(page, url, limit=max_items)

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
# python scrapers/exito_scraper.py --search arroz --max-items 3

def main() -> None:
    args = _parse_args()
    data, source_url = scrape_exito(search=args.search, max_items=args.max_items)
    print(f"Collected {len(data)} product records from {source_url}")

    if args.search:
        slug = "_".join(args.search.lower().split())
        output_file = f"exito_{slug}_products.json"
    else:
        output_file = "exito_products.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    main()
