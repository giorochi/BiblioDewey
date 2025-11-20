import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

HF_API_KEY = "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"
MODEL = "mistralai/Mistral-Nemo-Instruct-2407"

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&e=1&dl=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"


def download_excel(url):
    """Scarica Excel da Dropbox"""
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")


df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey = download_excel(DROPBOX_DEWEY_URL)


def ai_chat(prompt):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}

    r = requests.post(
        f"https://api-inference.huggingface.co/models/{MODEL}",
        headers=headers,
        json=payload,
    )

    data = r.json()
    return data[0]["generated_text"]


@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json["richiesta"]

    testo_ai = (
        f"Sei il bot della biblioteca. L’utente chiede: {richiesta}. "
        "Rispondi in modo naturale e utile."
    )

    risposta = ai_chat(testo_ai)

    return jsonify({"risposta": risposta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

