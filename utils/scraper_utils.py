import re
from typing import Any
from scrapling.fetchers import Fetcher, StealthyFetcher


def css(node: Any, selector: str) -> Any:
    return node.css(selector)


# Básicamente, intenta abrir la página usando dos métodos:
# uno más avanzado para páginas dinámicas y otro más simple
# por si el primero falla.
def get_candidate_pages(url: str) -> list[Any]:
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


# Recibe un texto extraído del HTML, por ejemplo:
# "$ 4.500" o "20% OFF", y obtiene únicamente
# el número para poder trabajar mejor el precio o descuento.
def extract_first_number(value: str | None) -> str | None:
    if not value:
        return None

    match = re.search(r"\d[\d\.,]*", value)

    return match.group(0) if match else None