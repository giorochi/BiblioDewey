import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Link modificati per il download diretto
DROPBOX_CATALOG_URL = "https://dl.dropboxusercontent.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=3wcn05kwsusu3vnnwf5nqg5on&st=xp2813pp&dl=1"
DROPBOX_DEWEY_URL = "https://dl.dropboxusercontent.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=kjgt8etgum3w72mo5c9gzkqvp&st=3fclbbjy&dl=1"

def download_excel(url):
    """Scarica Excel da Dropbox"""
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")

df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey = download_excel(DROPBOX_DEWEY_URL)

def ai_chat(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    try:
        r = requests.post(
            f"https://api-inference.huggingface.co/models/{MODEL}",
            headers=headers,
            json=payload,
        )

        # Log the response for debugging
        if r.status_code == 200:
            data = r.json()
            return data[0]["generated_text"]
        else:
            return f"Errore API: {r.status_code} - {r.text}"

    except requests.exceptions.RequestException as e:
        return f"Errore nella richiesta API: {str(e)}"

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json["richiesta"]
    testo_ai = f"Sei il bot della biblioteca. L’utente chiede: {richiesta}. Rispondi in modo naturale e utile."

    risposta = ai_chat(testo_ai)

    return jsonify({"risposta": risposta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
