from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.parse import quote_plus, urljoin

from utils.product_utils import extract_quantity
from utils.scraper_utils import (
    css,
    extract_first_number,
    get_candidate_pages,
)


TARGET_URL = "https://www.olimpica.com/"


def _build_search_urls(search: str) -> list[str]:
    encoded = quote_plus(search.strip())
    return [
        f"https://www.olimpica.com/search?q={encoded}",
    ]


def _extract_products_from_cards(
    page: Any,
    base_url: str,
    limit: int,
) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    cards = css(page, "div[class*='vtex-product-summary-2-x-container']")
    print("Cards encontradas:", len(cards))

    for card in cards:
        href = css(card, "a::attr(href)").get()

        if not href:
            continue

        absolute_url = urljoin(base_url, href)

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)

        name = (
            css(card, "span[class*='vtex-product-summary-2-x-brandName']::text").get()
            or css(card, "img::attr(alt)").get()
            or ""
        ).strip() or None

        quantity, unit, clean_name = extract_quantity(name or "")

        image = css(
            card,
            "img[class*='vtex-product-summary-2-x-imageNormal']::attr(src)",
        ).get()

        current_price_text = css(
            card,
            "span[class*='olimpica-dinamic-flags-0-x-currencyInteger']::text",
        ).get()

        products.append(
            {
                "name": clean_name,
                "url": absolute_url,
                "image": image,
                "seller": "Olímpica",
                "price": extract_first_number(current_price_text),
                "quantity": quantity,
                "unit": unit,
                "original_price": None,
                "discount_percent": None,
                "source": "html-card-olimpica",
            }
        )

        if len(products) >= limit:
            break

    return products


def scrape_olimpica(
    search: str | None = None,
    max_items: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Scrape Olímpica products; optionally target search result pages."""

    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:
        pages = get_candidate_pages(url)

        for page in pages:
            products = _extract_products_from_cards(page, url, limit=max_items)

            if products:
                return products[:max_items], url

    raise RuntimeError("Could not extract products from Olímpica with the current strategy")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape products from olimpica.com")
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


def main() -> None:
    args = _parse_args()

    data, source_url = scrape_olimpica(
        search=args.search,
        max_items=args.max_items,
    )

    print(f"Collected {len(data)} product records from {source_url}")

    if args.search:
        slug = "_".join(args.search.lower().split())
        output_file = f"data/olimpica_{slug}_products.json"
    else:
        output_file = "data/olimpica_products.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    main()