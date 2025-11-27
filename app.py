import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# ================
# CONFIGURAZIONE
# ================

GROQ_API_KEY = "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"
MODEL = "llama3-8b-70k"  # modello stabile suggerito da Groq

DROPBOX_CATALOG_URL = "https://dl.dropboxusercontent.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=3wcn05kwsusu3vnnwf5nqg5on&st=xp2813pp&dl=1"
DROPBOX_DEWEY_URL = "https://dl.dropboxusercontent.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=kjgt8etgum3w72mo5c9gzkqvp&st=3fclbbjy&dl=1"

# ================
# DOWNLOAD FILE
# ================

def download_excel(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")
    except Exception as e:
        logging.error(f"Errore download {url}: {e}")
        raise

df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey = download_excel(DROPBOX_DEWEY_URL)

# ================
# AI (GROQ)
# ================

def ai_chat(prompt):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Sei il bot della biblioteca e devi dare risposte utili, sintetiche e precise."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        logging.error(f"Errore API GROQ: {e}")
        return f"Errore API: {e}"

# ================
# ROUTES
# ================

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/consiglia", methods=["POST"])
def consiglia():
    try:
        richiesta = request.json["richiesta"]
        logging.debug(f"Richiesta ricevuta: {richiesta}")

        testo_ai = f"L'utente chiede: {richiesta}. Rispondi usando SOLO i dati del catalogo e delle collocazioni."

        risposta = ai_chat(testo_ai)

        return jsonify({"risposta": risposta})

    except Exception as e:
        logging.error(f"Errore durante il processamento: {e}")
        return jsonify({"risposta": "Errore interno durante l'elaborazione."})

# ================
# RUN
# ================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
