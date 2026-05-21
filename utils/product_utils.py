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

def extract_quantity(name: str) -> tuple[str | None, str | None, str]:

    # Si el nombre viene vacío, no hay nada que extraer.
    if not name:
        return None, None, name

    # Regex reutilizable
    pattern = r"(?:x\s*)?\(?\s*(\d+(?:[.,]\d+)?)\s*(GRS|GR|KG|ML|G|L)\s*\)?"

    match = re.search(
        pattern,
        name.upper()
    )

    # Si no encuentra coincidencias,
    # devuelve valores vacíos.
    if not match:
        return None, None, name

    # Primer grupo:
    # cantidad numérica.
    amount = match.group(1)

    # Segundo grupo:
    # unidad encontrada.
    unit = match.group(2)

    # Elimina el gramaje del nombre
    clean_name = re.sub(
        pattern,
        "",
        name,
        flags=re.IGNORECASE
    )

    # Limpia espacios sobrantes
    clean_name = " ".join(clean_name.split())

    return amount, unit, clean_name