import importlib.util
spec = importlib.util.spec_from_file_location('app_module', 'app.py')
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

handlers = [
    ('index', lambda: app_module.index()),
    ('static_js', lambda: app_module.static_files('js/api.js')),
    ('routes', lambda: app_module.debug_routes()),
]

for name, fn in handlers:
    try:
        res = fn()
        print(name, 'OK ->', type(res))
        try:
            print(res.get_data().decode('utf-8') if hasattr(res, 'get_data') else str(res))
        except Exception:
            pass
    except Exception as e:
        import traceback
        print(name, 'EXCEPTION')
        traceback.print_exc()
