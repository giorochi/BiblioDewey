import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ============================
# CONFIG
# ============================
GROQ_API_KEY = "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"
MODEL = "llama3-8b-8192"

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&e=1&dl=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"


# ==========================================
# FUNZIONE DOWNLOAD EXCEL DA DROPBOX
# ==========================================
def download_excel(url):
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")


# Scarico i file all'avvio
df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey = download_excel(DROPBOX_DEWEY_URL)


# ==========================================
# FUNZIONE AI GROQ
# ==========================================
def ai_chat(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Sei il bot intelligente della Biblioteca Parrocchiale."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        r.raise_for_status()

        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Errore API: {e}"


# ==========================================
# ROUTES
# ==========================================
@app.route("/")
def home():
    return "Bot IA Biblioteca attivo con GROQ!"


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json["richiesta"]

    testo_ai = (
        f"L’utente chiede: {richiesta}. "
        "Rispondi come un bibliotecario esperto."
    )

    risposta = ai_chat(testo_ai)

    return jsonify({"risposta": risposta})


# ==========================================
# AVVIO
# ==========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
