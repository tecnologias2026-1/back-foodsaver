import importlib.util
spec = importlib.util.spec_from_file_location('app_module', 'app.py')
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
for rule in app_module.app.url_map.iter_rules():
    print(rule)
