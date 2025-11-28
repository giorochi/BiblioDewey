import os
import pandas as pd
from flask import Flask, request, jsonify
from groq import Groq
import requests
from io import BytesIO

app = Flask(__name__)

# -----------------------
# 1. CARICA CATALOGO E ARGOMENTI DA DROPBOX
# -----------------------

CATALOGO_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?dl=1"
ARGOMENTI_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?dl=1"

def scarica_excel(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return pd.read_excel(BytesIO(resp.content))

try:
    catalogo = scarica_excel(CATALOGO_URL)
    argomenti = scarica_excel(ARGOMENTI_URL)
except Exception as e:
    print("Errore nel caricamento dei file Excel:", e)
    catalogo = pd.DataFrame()
    argomenti = pd.DataFrame()


# -----------------------
# 2. CONFIGURA GROQ
# -----------------------

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if GROQ_API_KEY is None:
    raise ValueError("La variabile d'ambiente GROQ_API_KEY non è impostata!")

client = Groq(api_key=GROQ_API_KEY)


# -----------------------
# 3. HOME ROUTE
# -----------------------

@app.route("/")
def home():
    return "Bot della Biblioteca attivo e funzionante."


# -----------------------
# 4. API: CONSIGLIA
# -----------------------

@app.route("/consiglia", methods=["POST"])
def consiglia():

    data = request.json
    if not data or "domanda" not in data:
        return jsonify({"errore": "Manca il campo 'domanda'"}), 400

    domanda = data["domanda"]

    # Se vuoi debug
    print("Domanda ricevuta:", domanda)

    try:
        # Costruisci prompt
        prompt = f"""
Sei il bibliotecario digitale. Rispondi alla domanda dell’utente
usando SOLO i dati del catalogo e degli argomenti.

CATALOGO:
{catalogo.to_string(index=False)}

ARGOMENTI:
{argomenti.to_string(index=False)}

Domanda utente: {domanda}
"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        testo = response.choices[0].message["content"]

        return jsonify({"risposta": testo})

    except Exception as e:
        print("Errore durante la richiesta a GROQ:", e)
        return jsonify({"errore": str(e)}), 500


# -----------------------
# 5. AVVIO COMPATIBILE CON RENDER
# -----------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
