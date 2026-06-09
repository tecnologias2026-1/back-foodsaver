# Backend Python + PostgreSQL (Render Ready)

API REST para consulta y gestión de ingredientes y productos alimenticios, conectada a PostgreSQL y preparada para actualización automática mediante scrapers.

## Stack

* Python 3.12
* Flask
* PostgreSQL (`psycopg2-binary`)
* Gunicorn para producción
* `python-dotenv` para variables de entorno
* Flask-CORS

## Estructura

* `api/app.py`: aplicación Flask
* `routes/ingredient_routes.py`: rutas `/api/ingredients`
* `controllers/ingredient_controller.py`: validaciones y respuestas HTTP
* `models/ingredient_model.py`: consultas SQL
* `database/db.py`: conexión a PostgreSQL
* `database/schema.sql`: esquema de base de datos
* `database/init_schema.py`: ejecuta el esquema
* `scrapers/`: extracción de productos desde supermercados
* `jobs/update_products.py`: actualización automática de productos
* `render.yaml`: blueprint para Render

## Endpoints

* `GET /api/ingredients` → listar ingredientes
* `GET /api/ingredients/<ingredient>` → buscar ingrediente
* `POST /api/ingredients` → crear registro
* `PUT /api/ingredients/<id>` → actualizar registro
* `DELETE /api/ingredients/<id>` → eliminar registro

## Ejecutar localmente

1. Crear y activar entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Crear `.env`:

```env
PORT=3000
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB_NAME
PYTHON_VERSION=3.12.3
```

4. Inicializar esquema:

```bash
python database/init_schema.py
```

5. Levantar la API:

```bash
python api/app.py
```

Servidor local: `http://localhost:3000`

## Actualizar productos

Ejecutar el proceso de scraping e importación:

```bash
python jobs/update_products.py
```

Este proceso obtiene productos desde las fuentes configuradas y actualiza la información almacenada en PostgreSQL.

## Despliegue en Render

### Opción 1: Blueprint (`render.yaml`) recomendado

1. Sube este repositorio a GitHub.
2. En Render: `New +` → `Blueprint`.
3. Selecciona el repositorio.
4. Render creará automáticamente los servicios definidos en `render.yaml`.
5. Cuando termine el primer despliegue, ejecuta una vez en la Shell del servicio:

```bash
python database/init_schema.py
```

### Opción 2: Manual

1. Crear una base de datos PostgreSQL en Render.

2. Crear un Web Service de Python conectado al repositorio.

3. Configurar las variables:

   * `DATABASE_URL=<connection string de PostgreSQL en Render>`

4. Build Command:

```bash
pip install -r requirements.txt
```

5. Start Command:

```bash
gunicorn api.app:app
```

6. Ejecutar el esquema una vez:

```bash
python database/init_schema.py
```
