import requests
from flask import Flask, render_template_string, request, Response, stream_with_context
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Diccionario real de SecLists (5000 palabras comunes)
WORDLIST_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-small.txt"

def check_url(target, path):
    path = path.strip()
    if not path or path.startswith("#"):
        return None
    
    url = f"{target.rstrip('/')}/{path}"
    try:
        # Petición real: HEAD es más rápido, pero si falla probamos GET
        r = requests.head(url, timeout=1.5, allow_redirects=True)
        if r.status_code in [200, 403, 301, 302]:
            return f"<tr><td><a href='{url}' target='_blank'>{url}</a></td><td>{r.status_code}</td></tr>"
    except:
        pass
    return None

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pro Path Scanner</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    </head>
    <body>
        <h1>🔍 Escáner de Directorios Real</h1>
        <p>Introduce una URL para buscar carpetas ocultas usando la lista <i>SecLists</i>.</p>
        <form action="/scan" method="get">
            <input type="text" name="url" placeholder="https://testphp.vulnweb.com" required>
            <button type="submit">Iniciar Auditoría Real</button>
        </form>
    </body>
    </html>
    '''

@app.route('/scan')
def scan():
    target = request.args.get('url')
    if not target.startswith('http'):
        return "Error: La URL debe empezar por http:// o https://"

    def generate():
        yield "<table><tr><th>Ruta Encontrada</th><th>Código HTTP</th></tr>"
        
        # Descarga la lista de palabras real
        r_list = requests.get(WORDLIST_URL, stream=True)
        words = (line.decode('utf-8') for line in r_list.iter_lines())

        # Usamos 15 hilos para que sea MUY rápido
        with ThreadPoolExecutor(max_workers=15) as executor:
            # Procesamos las primeras 500 palabras para que Render no te corte por tiempo
            futures = [executor.submit(check_url, target, next(words)) for _ in range(500)]
            for future in futures:
                result = future.result()
                if result:
                    yield result
        yield "</table><h3>Escaneo de las primeras 500 rutas completado.</h3>"

    return Response(stream_with_context(generate()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
