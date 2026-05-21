import random
import os
import json
import glob
from db import supabase

def obtener_ingredientes_usuario(user_id):
    response = supabase.table("user_ingredients") \
        .select("ingredient_id, ingredients(name, category_id, categories(name))") \
        .eq("user_id", user_id) \
        .execute()

    return response.data


def clasificar_ingredientes(data):
    categorias = {
        "proteina": [],
        "carbohidrato": [],
        "verdura": []
    }

    for item in data:
        ing = item["ingredients"]
        cat = ing["categories"]["name"]
        categorias[cat].append(ing["name"])

    return categorias


def _calcular_score(selecciones: dict) -> int:
    """Calcula el puntaje nutricional según la composición 50-25-25."""
    score = 0
    score += 50 if selecciones.get("verdura") else 0
    score += 25 if selecciones.get("proteina") else 0
    score += 25 if selecciones.get("carbohidrato") else 0
    return score


def generar_receta(selecciones: dict, user_id=None):
    """Genera una receta según la regla 50-25-25 y devuelve el objeto completo."""
    proteina = str(selecciones.get("proteina", "")).strip()
    carbo = str(selecciones.get("carbohidrato", "")).strip()
    verdura = str(selecciones.get("verdura", "")).strip()

    if not proteina or not carbo or not verdura:
        return None

    ingredientes = [verdura, verdura, proteina, carbo]
    nombre = f"{proteina} con {carbo} y {verdura}"
    score = _calcular_score(selecciones)

    receta = {
        "user_id": user_id,
        "nombre": nombre,
        "ingredientes": ingredientes,
        "score": score
    }

    disponibilidad = verificar_disponibilidad(ingredientes)
    receta["disponibilidad"] = disponibilidad

    return receta


def guardar_receta(user_id, receta):
    if not receta:
        return None

    receta_db = {
        "user_id": user_id,
        "nombre": receta["nombre"],
        "score": receta["score"]
    }

    res = None
    try:
        res = supabase.table("recetas").insert(receta_db).execute()
    except Exception:
        res = supabase.table("recipes").insert({
            "user_id": user_id,
            "name": receta["nombre"],
            "score": receta["score"]
        }).execute()

    if res and getattr(res, 'data', None):
        receta_id = res.data[0].get("id")
        receta["id"] = receta_id
        receta["user_id"] = user_id

    return receta


def guardar_usuario(nombre: str) -> dict:
    """Registra el usuario en Supabase y devuelve el registro creado."""
    nombre = str(nombre).strip()
    if not nombre:
        raise ValueError("El nombre del usuario no puede estar vacío.")

    try:
        usuario = supabase.table("usuarios").insert({
            "nombre": nombre
        }).execute()
        if usuario.data:
            return usuario.data[0]
    except Exception:
        pass

    # Si no existe la tabla `usuarios`, intenta crear en la tabla `users`.
    # Se genera un email válido de forma automática para cumplir con esquemas que lo requieran.
    sanitized = nombre.lower().replace(" ", ".")
    email = f"{sanitized}@example.com"

    usuario = supabase.table("users").insert({
        "full_name": nombre,
        "email": email
    }).execute()

    if usuario.data:
        return usuario.data[0]

    raise RuntimeError("No se pudo guardar el usuario en Supabase.")


def preguntar_ingredientes() -> dict:
    """Pregunta al usuario por una proteína, una verdura y un carbohidrato."""
    selections = {}
    preguntas = [
        ("proteina", "Proteína"),
        ("verdura", "Verdura"),
        ("carbohidrato", "Carbohidrato"),
    ]

    for key, label in preguntas:
        while True:
            valor = input(f"Ingrese {label}: ").strip()
            if valor:
                selections[key] = valor
                break
            print(f"{label} no puede estar vacío. Intenta de nuevo.")

    return selections


def guardar_ingredientes(ingredientes: dict) -> list:
    """Guarda ingredientes en la tabla `ingredientes` y devuelve los registros guardados."""
    guardados = []

    for categoria, nombre in ingredientes.items():
        nombre = str(nombre).strip()
        categoria = str(categoria).strip()

        if not nombre:
            continue

        existencia = supabase.table("ingredientes") \
            .select("id, nombre, categoria") \
            .eq("nombre", nombre) \
            .eq("categoria", categoria) \
            .execute()

        if existencia.data:
            guardados.append(existencia.data[0])
            continue

        res = supabase.table("ingredientes").insert({
            "nombre": nombre,
            "categoria": categoria
        }).execute()

        if res.data:
            guardados.append(res.data[0])

    return guardados


def main():
    print("Registro de usuario e ingredientes en Supabase")
    nombre_usuario = input("Ingrese el nombre del usuario: ").strip()
    usuario = guardar_usuario(nombre_usuario)
    user_id = usuario.get('id')
    print(f"Usuario guardado: id={user_id} nombre={usuario.get('nombre', usuario.get('full_name'))}")

    ingredientes = preguntar_ingredientes()
    guardados = guardar_ingredientes(ingredientes)

    if guardados:
        print("Ingredientes guardados:")
        for item in guardados:
            print(f"- id={item.get('id')} nombre={item.get('nombre')} categoria={item.get('categoria')}")
    else:
        print("No se guardó ningún ingrediente.")

    receta = generar_receta(ingredientes, user_id=user_id)
    if receta:
        receta_guardada = guardar_receta(user_id, receta)
        print("Receta generada:")
        print(f"- id: {receta_guardada.get('id')}")
        print(f"- user_id: {receta_guardada.get('user_id')}")
        print(f"- nombre: {receta_guardada.get('nombre')}")
        print(f"- score: {receta_guardada.get('score')}")
        print(f"- ingredientes: {', '.join(receta_guardada.get('ingredientes', []))}")
    else:
        print("No se pudo generar la receta porque faltan categorías válidas.")


if __name__ == "__main__":
    main()


def _load_products_from_data():
    """Carga los productos desde los archivos JSON específicos de D1 y Éxito."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(project_root, "data")

    products = []
    if not os.path.isdir(data_dir):
        return products

    file_names = [
        "d1_arroz_products.json",
        "exito_arroz_products.json"
    ]

    for filename in file_names:
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    products.extend(data)
        except Exception:
            continue

    return products


def verificar_disponibilidad(ingredientes: list) -> dict:
    """Para cada ingrediente, busca coincidencias en los datos de D1 y Éxito.
    Devuelve un mapping ingrediente -> lista de coincidencias con precio y url."""
    products = _load_products_from_data()

    disponibilidad = {}

    for ing in ingredientes:
        ing_lower = str(ing).lower()
        matches = []

        for p in products:
            name = str(p.get("name", "")).lower()
            if ing_lower in name:
                matches.append({
                    "product_name": p.get("name"),
                    "price": p.get("price"),
                    "url": p.get("url"),
                    "source": p.get("source")
                })

        disponibilidad[ing] = matches

    return disponibilidad