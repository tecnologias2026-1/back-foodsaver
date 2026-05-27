# import re

from flask import jsonify, request

from models.ingredient_model import (
    create_ingredient,
    delete_ingredient,
    get_all_ingredients,
    get_ingredients_by_name,
    update_ingredient,
)

# EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def validate_payload(data):
    nombre = str(data.get("nombre", "")).strip()
    imagen = str(data.get("imagen", "")).strip()
    precio = data.get("precio")
    tienda = str(data.get("tienda", "")).strip()
    url = str(data.get("url", "")).strip()
    ingrediente = str(data.get("ingrediente", "")).strip()

    if not nombre:
        return None, "nombre is required"

    return {
        "nombre": nombre,
        "imagen": imagen,
        "precio": precio,
        "tienda": tienda,
        "url": url,
        "ingrediente": ingrediente or None,
    }, None


def list_ingredients():
    ingredients = get_all_ingredients()
    return jsonify(ingredients), 200


def create_ingredient_handler():
    payload, error = validate_payload(request.get_json(silent=True) or {})

    if error:
        return jsonify({"error": error}), 400

    new_ingredient = create_ingredient(
        payload["nombre"],
        payload["imagen"],
        payload["precio"],
        payload["tienda"],
        payload["url"],
        payload["ingrediente"],
    )

    return jsonify(new_ingredient), 201


def update_ingredient_handler(ingredient_id: int):
    if ingredient_id <= 0:
        return jsonify({"error": "invalid id"}), 400

    payload, error = validate_payload(request.get_json(silent=True) or {})

    if error:
        return jsonify({"error": error}), 400

    updated = update_ingredient(
        ingredient_id,
        payload["nombre"],
        payload["imagen"],
        payload["precio"],
        payload["tienda"],
        payload["url"],
        payload["ingrediente"],
    )

    if not updated:
        return jsonify({"error": "ingredient not found"}), 404

    return jsonify(updated), 200


def delete_ingredient_handler(ingredient_id: int):
    if ingredient_id <= 0:
        return jsonify({"error": "invalid id"}), 400

    deleted = delete_ingredient(ingredient_id)

    if not deleted:
        return jsonify({"error": "ingredient not found"}), 404

    return "", 204


def list_ingredients_by_name(ingrediente: str):
    ingrediente = str(ingrediente).strip()

    if not ingrediente:
        return jsonify({"error": "ingrediente is required"}), 400

    ingredients = get_ingredients_by_name(ingrediente)
    return jsonify(ingredients), 200
