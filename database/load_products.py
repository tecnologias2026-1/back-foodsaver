import json
import os
from pathlib import Path
from dotenv import load_dotenv
from database.db import get_connection

load_dotenv()

def load_products_from_json():
    """Load products from JSON files and insert into database"""
    # Get the data directory relative to the backend root
    data_dir = Path(__file__).parent.parent / "data"
    json_files = list(data_dir.glob("*.json"))
    
    if not json_files:
        print("No JSON files found in data directory")
        return
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            count = 0
            for json_file in json_files:
                print(f"Loading from {json_file.name}...")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        products = json.load(f)
                    
                    for product in products:
                        try:
                            nombre = str(product.get("name", "")).strip()
                            imagen = str(product.get("image", "")).strip()
                            tienda = str(product.get("seller", "")).strip()
                            url = str(product.get("url", "")).strip()
                            
                            # Parse price: handle Colombian format (9.350 = 9350, or 9,50 = 9.50)
                            precio_str = product.get("price", "").strip()
                            precio = 0
                            if precio_str:
                                try:
                                    # Replace comma with dot for decimal separator
                                    precio_clean = precio_str.replace(",", ".")
                                    # Split by dots to identify thousands separators vs decimal
                                    parts = precio_clean.split(".")
                                    if len(parts) > 1 and len(parts[-1]) == 2:
                                        # Last part has 2 digits = decimal separator
                                        precio = float(".".join(parts[:-1]).replace(".", "") + "." + parts[-1])
                                    else:
                                        # No decimal or different format
                                        precio = float(precio_clean.replace(".", ""))
                                except ValueError:
                                    precio = 0
                            
                            if not nombre or not tienda:
                                continue
                            
                            cur.execute(
                                """
                                INSERT INTO ingredientes_scraper (nombre, imagen, precio, tienda, url)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (url) DO NOTHING
                                """,
                                (nombre, imagen, precio, tienda, url)
                            )
                            count += 1
                        except Exception as e:
                            print(f"Error processing product: {e}")
                            continue
                except json.JSONDecodeError as e:
                    print(f"Error reading {json_file.name}: {e}")
                    continue
            
            conn.commit()
            print(f"\n✅ Loaded {count} products successfully!")

if __name__ == "__main__":
    load_products_from_json()
