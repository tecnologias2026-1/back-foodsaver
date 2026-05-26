import importlib.util
import os
spec = importlib.util.spec_from_file_location('app_module', 'app.py')
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
print('ROUTES:')
for rule in app_module.app.url_map.iter_rules():
    print(repr(str(rule)), 'methods=', rule.methods)
print('---')
client = app_module.app.test_client()
for path in ['/api/ingredients', '/api/ingredients/']:
    print('PATH', path)
    r = client.get(path, follow_redirects=False)
    print(' status', r.status_code)
    print(' headers', {k:v for k,v in r.headers.items() if k in ['Location','Content-Type']})
    print('body', r.get_data(as_text=True)[:400])
