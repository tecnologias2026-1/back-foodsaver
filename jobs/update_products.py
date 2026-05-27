from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INGREDIENTS = [
    "habichuela",
    "arroz",
    "pimenton",
    "cebolla",
    "pechuga",
    "arveja",
    "condimento",
    "ajo",
]
SCRAPERS = [
    "scrapers.d1_scraper",
    "scrapers.exito_scraper",
    "scrapers.jumbo_scraper",
]


def run_command(command: list[str], description: str) -> subprocess.CompletedProcess[str]:
    print(f"\n==> {description}")
    result = subprocess.run(
        command,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        print(result.stdout.rstrip())

    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)

    if result.returncode != 0:
        print(
            f"[ERROR] {description} falló con código {result.returncode}",
            file=sys.stderr,
        )

    return result


def extract_imported_count(output: str) -> int | None:
    match = re.search(r"Productos importados/actualizados:\s*(\d+)", output)
    if match:
        return int(match.group(1))
    return None


def main() -> None:
    print("Iniciando actualización centralizada de productos...")
    print(f"Directorio raíz: {ROOT_DIR}")

    for ingredient in INGREDIENTS:
        print(f"\nProcesando ingrediente: {ingredient}")

        for scraper in SCRAPERS:
            run_command(
                [
                    sys.executable,
                    "-m",
                    scraper,
                    "--search",
                    ingredient,
                    "--max-items",
                    "5",
                ],
                f"Ejecutando {scraper} para {ingredient}",
            )

    import_result = run_command(
        [sys.executable, "database/import_products.py"],
        "Importando productos a la base de datos",
    )

    imported_count = extract_imported_count(import_result.stdout)

    if imported_count is not None:
        print(f"\nProductos importados/actualizados: {imported_count}")
    else:
        print("\nNo se pudo determinar la cantidad importada desde el log de importación.")

    print("Proceso completado.")


if __name__ == "__main__":
    main()