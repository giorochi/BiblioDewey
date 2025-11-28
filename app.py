import os
import io
import requests
import pandas as pd
from flask import Flask, request, jsonify, render_template

# --- CONFIG ---
app = Flask(__name__)

# API key (da impostare come variabile d'ambiente su Render)
AI_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "openrouter/airoboros-mini-1"  # Modello gratuito di esempio

# Link Excel Dropbox (con dl=1 per download diretto)
DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?dl=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?dl=1"

# --- FUNZIONI ---
def download_excel(url):
    """Scarica Excel da Dropbox e legge con pandas"""
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")

try:
    df_catalog = download_excel(DROPBOX_CATALOG_URL)
    df_dewey = download_excel(DROPBOX_DEWEY_URL)
except Exception as e:
    print(f"Errore nel caricamento dei file Excel: {e}")
    df_catalog = pd.DataFrame()
    df_dewey = pd.DataFrame()

def ai_chat(prompt):
    """Interroga l'API OpenRouter/Groq"""
    headers = {"Authorization": f"Bearer {AI_API_KEY}"}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }
    try:
        r = requests.post("https://api.openrouter.ai/v1/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Errore API: {e}")
        return "Si è verificato un errore durante la richiesta al bot AI."

# --- ROUTE ---
@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"

@app.route("/chat")
def chat_page():
    # Assicurati di avere chat.html nella cartella templates
    return render_template("chat.html")

@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")
    if not richiesta:
        return jsonify({"risposta": "Richiesta vuota."})

    # Prompt personalizzato con catalogo e collocazione
    prompt = f"Sei un assistente della biblioteca. L'utente chiede: {richiesta}. " \
             f"Rispondi solo con libri presenti nel catalogo e indica la collocazione."

    risposta = ai_chat(prompt)
    return jsonify({"risposta": risposta})

# --- AVVIO ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
