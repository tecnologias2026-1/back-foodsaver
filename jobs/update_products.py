from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INGREDIENTS = [
    {"ingredient": "habichuela", "search": "habichuela"},
    {"ingredient": "arroz", "search": "arroz blanco"},
    {"ingredient": "pimenton", "search": "pimenton"},
    {"ingredient": "cebolla", "search": "cebolla"},
    {"ingredient": "pechuga", "search": "pechuga"},
    {"ingredient": "arveja", "search": "arveja"},
    {"ingredient": "condimento", "search": "condimento completo"},
    {"ingredient": "ajo", "search": "ajo malla"},
]
SCRAPERS = [
    "scrapers.d1_scraper",
    "scrapers.exito_scraper",
    "scrapers.jumbo_scraper",
]


def cleanup_data_files() -> None:
    data_dir = ROOT_DIR / "data"

    if not data_dir.exists():
        return

    removed_files = 0

    for json_file in data_dir.glob("*.json"):
        json_file.unlink(missing_ok=True)
        removed_files += 1

    print(f"Limpieza previa completada: {removed_files} archivos JSON eliminados")


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

    cleanup_data_files()

    for item in INGREDIENTS:
        ingredient = item["ingredient"]
        search = item["search"]

        print(f"\nProcesando ingrediente: {ingredient} | búsqueda: {search}")

        for scraper in SCRAPERS:
            run_command(
                [
                    sys.executable,
                    "-m",
                    scraper,
                    "--search",
                    search,
                    "--ingredient",
                    ingredient,
                    "--max-items",
                    "5",
                ],
                f"Ejecutando {scraper} para {ingredient} ({search})",
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