from flask import Flask, request, jsonify
import pandas as pd
import requests
import io
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?dl=1"
DROPBOX_DEWEY_URL   = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?dl=1"

TOP_K_DEWEY_MATCHES = 1
TOP_N_BOOKS = 6

def download_excel(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine='openpyxl')


# 🔹 Carica una volta sola al deploy
df_catalog, df_dewey = download_excel(DROPBOX_CATALOG_URL), download_excel(DROPBOX_DEWEY_URL)

@app.route("/consiglia", methods=["POST"])
def consiglia():
    data = request.get_json(force=True)
    user_text = data.get("richiesta", "").strip()
    if not user_text:
        return jsonify({"error": "Nessuna richiesta fornita"}), 400

    # Conversione IDArgomento
    df_catalog['IDArgomento'] = df_catalog['IDArgomento'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_dewey['IDArgomento'] = df_dewey['IDArgomento'].astype(str).str.replace(r'\.0$', '', regex=True)

    # Esempio semplice: prendi il primo libro
    selected = df_catalog.head(TOP_N_BOOKS).to_dict(orient='records')

    return jsonify({
        "books": selected,
        "risposta": f"Trovati {len(selected)} libri per la tua richiesta."
    })

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"

if __name__ == "__main__":
    import os
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)

