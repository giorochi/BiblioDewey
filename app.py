from flask import Flask, request, jsonify
import pandas as pd
import requests
from transformers import pipeline

app = Flask(__name__)

# IA di HuggingFace (gratis)
model = pipeline("text-generation", model="google/gemma-2b-it", max_new_tokens=250)

# Link al file Excel su Dropbox
DROPBOX_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&e=1&dl=0"

def load_catalogo():
    r = requests.get(DROPBOX_URL)
    with open("catalogo.xlsx", "wb") as f:
        f.write(r.content)
    return pd.read_excel("catalogo.xlsx")

@app.route("/consiglia", methods=["POST"])
def consiglia():
    dati = request.json
    bisogno = dati.get("richiesta", "")
    dewey = dati.get("dewey", "")

    df = load_catalogo()
    
    # Filtra per Dewey
    filtrati = df[df["Dewey"].astype(str).str.startswith(str(dewey))]
    
    if filtrati.empty:
        return jsonify({"risposta": "Nessun libro trovato per questa notazione Dewey."})

    # Crea prompt da dare alla IA
    testo = "Ecco i libri disponibili:\n"
    for _, row in filtrati.iterrows():
        testo += f"- {row['Titolo']} di {row['Autore']} ({row['Dewey']})\n"

    prompt = (
        f"L'utente cerca: {bisogno}. Qui sotto ci sono dei libri della biblioteca.\n"
        f"Consiglia i più adatti e spiega brevemente perché.\n\n"
        f"{testo}"
    )

    risposta = model(prompt)[0]["generated_text"]
    return jsonify({"risposta": risposta})

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"
