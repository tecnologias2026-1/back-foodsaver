from __future__ import annotations

import argparse
import json
import requests
from typing import Any
from urllib.parse import quote_plus


TARGET_URL = "https://api.mercadolibre.com/sites/MCO"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-CO,es;q=0.9"
}

def _build_search_urls(search: str) -> list[str]:
    encoded = quote_plus(search.strip())
    return [
        f"https://api.mercadolibre.com/sites/MCO/search?q={encoded}&limit=20",
    ]


def scrape_mercadolibre(
    search: str | None = None,
    max_items: int = 20,
) -> tuple[list[dict[str, Any]], str]:
    """Scrape Mercado Libre Colombia products via API pública."""

    urls = _build_search_urls(search) if search else [TARGET_URL]

    for url in urls:
        try:
            response = requests.get(url, timeout=10, headers=HEADERS)
            data = response.json()

            results = data.get("results", [])
            print(f"Productos encontrados en API: {len(results)}")

            products = []
            for item in results[:max_items]:
                products.append({
                    "name": item.get("title"),
                    "url": item.get("permalink"),
                    "image": item.get("thumbnail"),
                    "seller": "Mercado Libre",
                    "price": item.get("price"),
                    "quantity": None,
                    "unit": None,
                    "original_price": item.get("original_price"),
                    "discount_percent": None,
                    "source": "api-mercadolibre",
                })

            if products:
                return products[:max_items], url

        except Exception as e:
            print(f"Error consultando Mercado Libre: {e}")

    raise RuntimeError("Could not extract products from Mercado Libre")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape products from Mercado Libre Colombia"
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


def main() -> None:
    args = _parse_args()

    data, source_url = scrape_mercadolibre(
        search=args.search,
        max_items=args.max_items,
    )

    print(f"Collected {len(data)} product records from {source_url}")

    if args.search:
        slug = "_".join(args.search.lower().split())
        output_file = f"data/mercadolibre_{slug}_products.json"
    else:
        output_file = "data/mercadolibre_products.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    main()