import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

HF_API_KEY = "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"
MODEL = "bigscience/bloomz-560m"

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&e=1&dl=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"


def download_excel(url):
    """Scarica Excel da Dropbox."""
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")


# Caricamento file all'avvio del server
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
            timeout=60
        )
        r.raise_for_status()
        data = r.json()

        # Modello in fase di loading
        if isinstance(data, dict) and data.get("error") and "loading" in data["error"]:
            return "Sto caricando il modello, riprova tra qualche secondo."

        # Risposta valida
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

        return "Non riesco a generare una risposta ora."

    except Exception as e:
        return f"Errore API: {e}"


@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")

    testo_ai = (
        f"Sei il bot della biblioteca. L’utente chiede: {richiesta}. "
        "Rispondi in modo naturale, utile e informativo."
    )

    risposta = ai_chat(testo_ai)

    return jsonify({"risposta": risposta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

