import importlib.util
spec = importlib.util.spec_from_file_location('app_module', 'app.py')
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

from controllers.ingredient_controller import list_ingredients

with app_module.app.test_request_context(path='/api/ingredients/'):
    try:
        res = list_ingredients()
        print('RESULT TYPE', type(res))
        try:
            print(res.get_data().decode())
        except Exception:
            print(res)
    except Exception as e:
        import traceback
        print('EXC', e)
        traceback.print_exc()
