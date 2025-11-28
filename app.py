import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ===== API GROQ =====
GROQ_API_KEY = "TUO_TOKEN_GROQ"  # metti il token come variabile su Render
MODEL = "llama2-7b-chat"  # modello valido su Groq

# ===== LINK DROPBOX (link pubblico diretto) =====
DROPBOX_CATALOG_URL = "https://www.dropbox.com/s/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?raw=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/s/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?raw=1"


def download_excel(url):
    """Scarica Excel da Dropbox con engine specificato"""
    try:
        r = requests.get(url)
        r.raise_for_status()
        return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")
    except Exception as e:
        print("Errore nel caricamento dei file Excel:", e)
        return pd.DataFrame()  # ritorna vuoto se errore


# ===== CARICAMENTO DATI =====
df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey = download_excel(DROPBOX_DEWEY_URL)


def ai_chat(prompt):
    """Funzione per chiamata Groq API"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("Errore API:", e)
        return "Errore nella comunicazione con l'API AI."


@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")
    if richiesta == "":
        return jsonify({"risposta": "Richiesta vuota"})

    testo_ai = f"Sei il bot della biblioteca. L’utente chiede: {richiesta}. Rispondi in modo naturale e utile."

    risposta = ai_chat(testo_ai)
    return jsonify({"risposta": risposta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
