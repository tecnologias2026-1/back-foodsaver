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


TARGET_URL = "https://d1.com.co/"


def _build_search_urls(search: str) -> list[str]:
    encoded = quote_plus(search.strip())

    return [
        f"https://domicilios.tiendasd1.com/search?name={encoded}&sort=3",
    ]


def _extract_product_links_from_html(
    page: Any,
    base_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    fallback_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in css(page, "a.containerCard"):
        href = css(link, "::attr(href)").get()
        title = (
            css(link, "h3[data-testid='card-name']::text").get()
            or css(link, "img::attr(alt)").get()
            or ""
        ).strip()
        image = css(link, "img::attr(src)").get()

        print(
            "D1 card link debug -> "
            f"nombre={title or None} | precio=None | url={href or None} | imagen={image or None}"
        )

        if not href:
            print("D1 card discarded -> reason=missing href")
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            print(f"D1 card discarded -> reason=duplicate url | url={absolute_url}")
            continue

        seen_urls.add(absolute_url)

        fallback_products.append(
            {
                "name": title or None,
                "url": absolute_url,
                "image": image,
                "seller": "D1",
                "price": None,
                "quantity": None,
                "unit": None,
                "original_price": None,
                "discount_percent": None,
                "source": "html-link-d1",
            }
        )

        if len(fallback_products) >= limit:
            break

    return fallback_products


def _extract_products_from_cards(
    page: Any,
    base_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    cards = css(page, "div[class*='ProductWrapper_product-wrapper']")
    print("Cards encontradas:", len(cards))

    for card in cards:
        href = css(card, "a.containerCard::attr(href)").get()
        raw_name = (
            css(card, "h3[data-testid='card-name']::text").get()
            or css(card, "img::attr(alt)").get()
            or ""
        ).strip()
        image = css(
            card,
            "img[class*='prod__figure__img']::attr(src)",
        ).get()
        current_price_text = css(
            card,
            "p[data-testid='card-base-price']::text",
        ).get()

        print(
            "D1 card debug -> "
            f"nombre={raw_name or None} | precio={current_price_text or None} | url={href or None} | imagen={image or None}"
        )

        if not href:
            print("D1 card discarded -> reason=missing href")
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            print(f"D1 card discarded -> reason=duplicate url | url={absolute_url}")
            continue

        seen_urls.add(absolute_url)

        name = raw_name or None

        if not name:
            print(f"D1 card discarded -> reason=missing name | url={absolute_url}")
            continue

        quantity, unit, clean_name = extract_quantity(name or "")
        price = extract_first_number(current_price_text)

        if price is None:
            print(f"D1 card discarded -> reason=missing price | url={absolute_url} | name={clean_name}")
            continue

        products.append(
            {
                "name": clean_name,
                "url": absolute_url,
                "image": image,
                "seller": "D1",
                "price": price,
                "quantity": quantity,
                "unit": unit,
                "original_price": None,
                "discount_percent": None,
                "source": "html-card-d1",
            }
        )

        if len(products) >= limit:
            break

    return products


def scrape_d1(
    search: str | None = None,
    max_items: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Scrape D1 products; optionally target search result pages."""
    
    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:
        pages = get_candidate_pages(url)

        for page in pages:
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
                seller="D1",
                source="json-ld-d1",
            )

            print(f"Productos encontrados desde JSON-LD: {len(products)}")

            if products:
                for product in products:
                    print(
                        "D1 product debug -> "
                        f"nombre={product.get('name')} | precio={product.get('price')} | url={product.get('url')} | imagen={product.get('image')}"
                    )

            if not products:
                products = _extract_products_from_cards(
                    page,
                    url,
                    limit=max_items,
                )

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


def main() -> None:
    args = _parse_args()
    ingredient = (args.ingredient or args.search or "").strip() or None

    data, source_url = scrape_d1(
        search=args.search,
        max_items=args.max_items,
    )

    print(f"Collected {len(data)} product records from {source_url}")

    if ingredient:
        for product in data:
            product["ingredient"] = ingredient

    if ingredient:
        slug = "_".join(ingredient.lower().split())
        output_file = f"data/d1_{slug}_products.json"
    elif args.search:
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