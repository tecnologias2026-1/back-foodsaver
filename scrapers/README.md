# Scrapling sample (Python)

This project is a minimal web scraping example based on the Scrapling framework:
https://github.com/D4Vinci/Scrapling

It scrapes product-like data from:
https://www.exito.com/

## 1) Create and activate a virtual environment (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2) Install dependencies

```powershell
pip install -r requirements.txt
```

## 3) Run the scraper

```powershell
python sample_scrapling.py
```

Search for a specific product (example: banano):

```powershell
python sample_scrapling.py --search banano
```

Control number of results:

```powershell
python sample_scrapling.py --search banano --max-items 30
```

Expected output:
- Console summary with number of collected product records
- An `exito_products.json` file with extracted data
- If you use `--search`, output file will be `exito_<keyword>_products.json` (example: `exito_banano_products.json`)

## Notes

- This sample uses `Fetcher.get` (fast static HTTP scraping).
- The script first tries structured data (`application/ld+json`) and then falls back to product links from HTML.
- If you later need JavaScript rendering or anti-bot handling, check Scrapling `DynamicFetcher` and `StealthyFetcher` in the official docs.
