import requests
import random
import time
from flask import Flask, render_template_string, request, Response, stream_with_context
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
]

# Usaremos una lista pequeña para que el test sea instantáneo
WORDLIST_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt"

def check_url(target, path):
    path = path.strip()
    if not path or path.startswith("#"): return None
    
    url = f"{target.rstrip('/')}/{path}"
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    try:
        # Petición real
        r = requests.get(url, headers=headers, timeout=3, allow_redirects=False)
        
        # Si encuentra algo interesante (200, 301, 403)
        if r.status_code in [200, 301, 302, 403]:
            return {"url": url, "status": r.status_code, "log": f"CHECKING: /{path} -> FOUND!"}
        return {"log": f"CHECKING: /{path} -> 404"}
    except:
        return {"log": f"CHECKING: /{path} -> ERROR"}

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>TERMINAL SCANNER v3.0</title>
        <style>
            body { background: #050505; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
            .container { display: flex; gap: 20px; }
            .panel { border: 1px solid #00ff00; padding: 15px; height: 500px; overflow-y: scroll; flex: 1; font-size: 12px; }
            h2 { color: #fff; border-bottom: 1px solid #fff; }
            input { background: #000; border: 1px solid #00ff00; color: #00ff00; padding: 10px; width: 250px; }
            button { background: #00ff00; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>[ SYSTEM AUDIT TOOL ]</h1>
        <form action="/scan" method="get">
            <input type="text" name="url" value="http://testphp.vulnweb.com" required>
            <button type="submit">INICIAR ESCANEO</button>
        </form>
    </body>
    </html>
    '''

@app.route('/scan')
def scan():
    target = request.args.get('url')
    if not target.startswith('http'): target = "http://" + target

    def generate():
        yield '''<style>
            body { background: #050505; color: #00ff00; font-family: monospace; }
            .box { display: flex; gap: 10px; height: 90vh; }
            .log { flex: 1; border: 1px solid #333; padding: 10px; overflow-y: scroll; color: #888; }
            .res { flex: 1; border: 1px solid #00ff00; padding: 10px; overflow-y: scroll; }
            .found { color: #00ff00; font-weight: bold; }
        </style>
        <div class="box">
            <div class="log"><h3>-- CONSOLA DE TRABAJO --</h3>'''
        
        # Marcador para cerrar el div de log y empezar el de resultados
        yield '</div><div class="res"><h3>-- RESULTADOS ENCONTRADOS --</h3>'

        try:
            r_list = requests.get(WORDLIST_URL, timeout=10)
            words = r_list.text.split('\n')[:150]
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(check_url, target, w) for w in words]
                for future in futures:
                    data = future.result()
                    if data:
                        # Enviamos un script de JS para meter el log en su sitio
                        yield f"<script>document.querySelector('.log').innerHTML += '<br>{data['log']}';</script>"
                        if 'url' in data:
                            yield f"<div class='found'>[MATCH] {data['url']} (Status: {data['status']})</div>"
                        # Forzamos al navegador a bajar el scroll automáticamente
                        yield "<script>document.querySelector('.log').scrollTop = document.querySelector('.log').scrollHeight;</script>"
        except Exception as e:
            yield f"<div>ERROR: {str(e)}</div>"
            
        yield "</div></div>"

    return Response(stream_with_context(generate()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
