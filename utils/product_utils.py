import re


# Extrae el gramaje o cantidad desde el nombre del producto.
#
# Básicamente, busca patrones como:
# "2000 GRS", "1 KG", "500 ML", etc.
#
# Primero convierte todo el texto a mayúsculas usando .upper()
# para que funcione incluso si el producto viene como:
# "2000 gr", "1 kg" o "500 ml".
#
# Luego usa regex para separar:
# - la cantidad numérica
# - la unidad
#
# Ejemplo:
# "ARROZ ECONÓMICO ALBAR 2000 GRS"
#
# Resultado:
# ("2000", "GRS")

def extract_quantity(name: str) -> tuple[str | None, str | None]:

    # Si el nombre viene vacío, no hay nada que extraer.
    if not name:
        return None, None

    # Busca:
    # - uno o más números
    # - opcionalmente con decimal
    # - seguidos de unidades como GRS, KG, ML, etc.
    #
    # Ejemplos válidos:
    # 2000 GRS
    # 1 KG
    # 500 ML

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(GRS|G|GR|KG|ML|L)",
        name.upper()
    )

    # Si no encuentra coincidencias,
    # devuelve valores vacíos.
    if not match:
        return None, None

    # Primer grupo:
    # cantidad numérica.
    amount = match.group(1)

    # Segundo grupo:
    # unidad encontrada.
    unit = match.group(2)

    return amount, unit