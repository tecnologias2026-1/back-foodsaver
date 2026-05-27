from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.parse import quote, urljoin

from utils.jsonld_utils import extract_products_from_jsonld
from utils.product_utils import extract_quantity
from utils.scraper_utils import (
    css,
    extract_first_number,
    get_candidate_pages,
)


TARGET_URL = "https://www.jumbocolombia.com/"


def _build_search_urls(search: str) -> list[str]:
    encoded = quote(search.strip(), safe="")

    return [
        f"https://www.jumbocolombia.com/{encoded}?_q={encoded}&map=ft&order=OrderByPriceASC",
    ]


def _extract_product_links_from_html(
    page: Any,
    base_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    fallback_products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for link in css(page, "a[class*='clearLink'][href*='/p']"):
        href = css(link, "::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        title = (
            css(link, "::attr(aria-label)").get()
            or css(link, "::attr(title)").get()
            or css(link, "::text").get()
            or ""
        ).strip()

        fallback_products.append(
            {
                "name": title or None,
                "url": absolute_url,
                "image": None,
                "seller": "Jumbo",
                "price": None,
                "quantity": None,
                "unit": None,
                "original_price": None,
                "discount_percent": None,
                "source": "html-link-jumbo",
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

    cards = css(page, "a[class*='clearLink'][href*='/p']")
    print("Cards encontradas:", len(cards))

    for card in cards:
        href = css(card, "::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        name = (
            css(card, "span[class*='brandName']::text").get()
            or css(card, "img::attr(alt)").get()
            or ""
        ).strip() or None

        quantity, unit, clean_name = extract_quantity(name or "")

        image = css(
            card,
            "img[class*='-image']::attr(src)",
        ).get()

        current_price_text = css(
            card,
            "#items-price div[class*='-price']::text",
        ).get()

        original_price_text = css(
            card,
            "div[class*='cencoPriceWithoutDiscount'] div[class*='-price']::text",
        ).get()

        discount_text = css(
            card,
            "span[class*='containerPercentageFlag']::text",
        ).get()

        products.append(
            {
                "name": clean_name,
                "url": absolute_url,
                "image": image,
                "seller": "Jumbo",
                "price": extract_first_number(current_price_text),
                "quantity": quantity,
                "unit": unit,
                "original_price": extract_first_number(original_price_text),
                "discount_percent": extract_first_number(discount_text),
                "source": "html-card-jumbo",
            }
        )

        if len(products) >= limit:
            break

    return products


def scrape_jumbo(
    search: str | None = None,
    max_items: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Scrape Jumbo products; optionally target search result pages."""

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
                seller="Jumbo",
                source="json-ld-jumbo",
            )

            print(f"Productos encontrados desde JSON-LD: {len(products)}")

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
        "Could not extract products from Jumbo with the current strategy"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape products from jumbocolombia.com"
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

    data, source_url = scrape_jumbo(
        search=args.search,
        max_items=args.max_items,
    )

    print(f"Collected {len(data)} product records from {source_url}")

    if ingredient:
        for product in data:
            product["ingredient"] = ingredient

        slug = "_".join(ingredient.lower().split())
        output_file = f"data/jumbo_{slug}_products.json"
    elif args.search:
        slug = "_".join(args.search.lower().split())
        output_file = f"data/jumbo_{slug}_products.json"
    else:
        output_file = "data/jumbo_products.json"

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