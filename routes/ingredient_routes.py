from flask import Blueprint

from controllers.ingredient_controller import (
    create_ingredient_handler,
    delete_ingredient_handler,
    list_ingredients,
    list_ingredients_by_name,
    update_ingredient_handler,
)


ingredient_bp = Blueprint("ingredients", __name__)


ingredient_bp.get("/")(list_ingredients)
ingredient_bp.get("/<ingrediente>")(list_ingredients_by_name)
ingredient_bp.post("/")(create_ingredient_handler)
ingredient_bp.put("/<int:ingredient_id>")(update_ingredient_handler)
ingredient_bp.delete("/<int:ingredient_id>")(delete_ingredient_handler)
