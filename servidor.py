from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_PLANTILLA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Panel de Control — Hallazgos en Vivo</title>
    <meta http-equiv="refresh" content="5">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#0a0f14;color:#00ff88;font-family:'Segoe UI',Consolas,monospace;padding:20px;line-height:1.6}
        .contenedor{max-width:900px;margin:0 auto}
        h1{color:#fff;margin-bottom:5px;font-size:22px}
        .estado{color:#8899a6;font-size:13px;margin-bottom:20px}
        .indicador{display:inline-block;width:10px;height:10px;background:#00ff88;border-radius:50%;margin-right:8px;animation:parpadeo 1s ease-in-out infinite}
        @keyframes parpadeo{0%,100%{opacity:1}50%{opacity:.3}}
        pre{background:#0f1a20;border:1px solid #1e3040;border-radius:10px;padding:20px;overflow-x:auto;color:#88ffbb;font-size:13px;white-space:pre-wrap;word-wrap:break-word}
        .vacio{color:#446655;text-align:center;padding:40px}
    </style>
</head>
<body>
    <div class="contenedor">
        <h1>🤖 Panel de Control — Hallazgos en Vivo</h1>
        <p class="estado"><span class="indicador"></span>Actualizando automáticamente cada 5 segundos...</p>
        <pre>{{ contenido }}</pre>
    </div>
</body>
</html>
"""

@app.route("/")
def panel():
    ruta = "hallazgos.txt"
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()
            if not contenido.strip():
                contenido = "🔍 El bot está analizando... aún no se registraron hallazgos."
    else:
        contenido = "🔍 Esperando que el bot encuentre coincidencias..."
    return render_template_string(HTML_PLANTILLA, contenido=contenido)

if __name__ == "__main__":
    print("\n🌐 Panel web activo → http://127.0.0.1:5000")
    print("📡 El archivo hallazgos.txt se actualizará automáticamente en pantalla\n")
    app.run(host="0.0.0.0", port=5000, debug=False)