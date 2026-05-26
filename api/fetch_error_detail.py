import urllib.request
from urllib.error import HTTPError
for path in ['/api/ingredients/', '/__routes__']:
    try:
        with urllib.request.urlopen('http://127.0.0.1:3000' + path) as r:
            print(path, r.status)
            print(r.read(2000).decode('utf-8', errors='replace'))
    except HTTPError as e:
        print(path, 'STATUS', e.code)
        print(e.read().decode('utf-8', errors='replace'))
    except Exception as e:
        print(path, 'ERROR', type(e).__name__, e)
