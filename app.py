import requests
import random
from flask import Flask, render_template_string, request, Response, stream_with_context
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Lista más pequeña para evitar el error de memoria
WORDLIST_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt"

def check_url(target, path):
    path = path.strip()
    if not path or path.startswith("#"): return None
    url = f"{target.rstrip('/')}/{path}"
    try:
        # Usamos timeout corto para no bloquear el servidor
        r = requests.get(url, headers={'User-Agent': random.choice(USER_AGENTS)}, timeout=2, allow_redirects=False)
        if r.status_code in [200, 301, 302, 403]:
            return {"url": url, "status": r.status_code}
    except:
        pass
    return None

@app.route('/')
def index():
    return '''
    <html><body style="background:#000;color:#00ff00;font-family:monospace;padding:50px;">
    <h1>[ TERMINAL V4 ]</h1>
    <form action="/scan" method="get">
        <input type="text" name="url" placeholder="http://testphp.vulnweb.com" style="background:#111;color:#0f0;border:1px solid #0f0;padding:10px;">
        <button type="submit" style="background:#0f0;color:#000;padding:10px;cursor:pointer;">SCAN</button>
    </form>
    </body></html>
    '''

@app.route('/scan')
def scan():
    target = request.args.get('url')
    if not target.startswith('http'): target = "http://" + target

    def generate():
        yield "<pre style='color:#0f0;background:#000;padding:20px;'>"
        yield f"DEBUG: Iniciando escaneo en {target}...<br>"
        
        try:
            # Cargamos solo las primeras 100 palabras para no saturar la RAM
            r_list = requests.get(WORDLIST_URL, timeout=5)
            words = r_list.text.split('\n')[:100]

            # BAJAMOS A 3 TRABAJADORES PARA EVITAR EL SIGKILL
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(check_url, target, w) for w in words]
                for future in futures:
                    res = future.result()
                    if res:
                        yield f"<span style='color:white;'>[+] {res['url']} (CODE:{res['status']})</span><br>"
                    else:
                        # Esto es para que veas que está trabajando
                        yield "." 
        except Exception as e:
            yield f"<br>ERROR CRÍTICO: {str(e)}"
        
        yield "<br>--- ESCANEO FINALIZADO ---</pre>"

    return Response(stream_with_context(generate()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
