import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ==============================
#  CONFIGURAZIONE
# ==============================
OPENROUTER_API_KEY = "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"  # Mettila come variabile d'ambiente in produzione!
OPENROUTER_MODEL = "tngtech/deepseek-r1t2-chimera:free"  # verifica il modello free disponibile

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&dl=1"
DROPBOX_DEWEY_URL   = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"


# ==============================
#  FUNZIONI
# ==============================

def download_excel(url):
    """Scarica Excel da Dropbox"""
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")


# carica dati catalogo e Dewey
df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey   = download_excel(DROPBOX_DEWEY_URL)


def ai_chat_openrouter(prompt):
    """Chiama OpenRouter API per generare risposta AI"""
    url = "https://api.openrouter.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Sei un assistente virtuale della biblioteca."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 256
    }
    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()
    resp = r.json()
    return resp["choices"][0]["message"]["content"]


# ==============================
#  ROUTE
# ==============================

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")
    if not richiesta:
        return jsonify({"risposta": "Devi fornire una richiesta!"}), 400

    # costruisci prompt per AI
    prompt_ai = f"L'utente chiede: {richiesta}. Rispondi in modo naturale e utile."
    
    try:
        risposta = ai_chat_openrouter(prompt_ai)
    except Exception as e:
        return jsonify({"risposta": f"Errore API: {str(e)}"}), 500

    return jsonify({"risposta": risposta})


if __name__ == "__main__":
    import os
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
