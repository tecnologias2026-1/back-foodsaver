import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from models.ingredient_model import get_all_ingredients

try:
    rows = get_all_ingredients()
    print('ROWS', type(rows), len(rows) if hasattr(rows, '__len__') else 'n/a')
    print(rows[0])
except Exception as e:
    import traceback
    print('EXC', e)
    traceback.print_exc()
