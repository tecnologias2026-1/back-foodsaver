import urllib.request
urls = ['http://127.0.0.1:3000/', 'http://127.0.0.1:3000/js/api.js', 'http://127.0.0.1:3000/api', 'http://127.0.0.1:3000/api/ingredients/', 'http://127.0.0.1:3000/__routes__']
for u in urls:
    try:
        with urllib.request.urlopen(u, timeout=5) as r:
            print(u, r.status)
            print(r.read(400).decode('utf-8', errors='replace'))
    except Exception as e:
        print(u, 'ERROR', type(e), e)
