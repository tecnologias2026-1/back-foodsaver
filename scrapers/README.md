# Scrapers FoodSaver (Python)

Colección de scrapers utilizados para extraer información de productos de supermercados colombianos y generar los datos consumidos por el backend de FoodSaver.

Fuentes actualmente soportadas:

* Éxito
* Jumbo
* D1

## 1) Crear y activar un entorno virtual (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 2) Instalar dependencias

```powershell
pip install -r requirements.txt
```

## 3) Instalar navegadores de Playwright

Algunos scrapers requieren automatización de navegador y renderizado de JavaScript.

Instala los navegadores con:

```powershell
python -m playwright install
```

## 4) Ejecutar un scraper

### Éxito

```powershell
python -m scrapers.exito_scraper --search arroz
```

### Jumbo

```powershell
python -m scrapers.jumbo_scraper --search arroz
```

### D1

```powershell
python -m scrapers.d1_scraper --search arroz
```

Controlar la cantidad de resultados:

```powershell
python -m scrapers.exito_scraper --search arroz --max-items 30
```

## Salida

Cada scraper genera un archivo JSON con los productos recolectados.

Ejemplos:

```text
exito_arroz_products.json
jumbo_arroz_products.json
d1_arroz_products.json
```

Cada registro contiene información como:

* Nombre del producto
* Precio
* URL del producto
* URL de la imagen
* Tienda de origen

## Integración con el Backend

El backend puede ejecutar todos los scrapers y actualizar automáticamente la base de datos PostgreSQL mediante:

```powershell
python jobs/update_products.py
```

Este proceso:

* Ejecuta los scrapers configurados
* Recolecta información de productos
* Genera archivos intermedios
* Actualiza los registros en PostgreSQL

## Notas

* Los scrapers fueron desarrollados con fines académicos y de investigación.
* La disponibilidad de productos y la estructura de los sitios web pueden cambiar sin previo aviso.
* Algunas fuentes requieren renderizado de JavaScript mediante Playwright.
* Si un scraper deja de funcionar, se recomienda revisar la estructura del sitio objetivo antes de actualizar los selectores.
