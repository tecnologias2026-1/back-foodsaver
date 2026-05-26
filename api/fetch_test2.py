import urllib.request
for path in ['/api/ingredients', '/api/ingredients/']:
    try:
        with urllib.request.urlopen('http://127.0.0.1:3000' + path) as r:
            print(path, r.status)
            print(r.read(300).decode('utf-8', errors='replace'))
    except Exception as e:
        print(path, 'ERROR', type(e).__name__, e)
