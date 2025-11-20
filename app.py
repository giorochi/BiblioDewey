import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ==============================
#  CONFIGURAZIONE
# ==============================
HF_API_KEY = "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"  # Mettila come variabile d'ambiente in produzione
MODEL = "tiiuae/falcon-7b-instruct"  # modello gratuito e leggero per generazione testo

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&dl=1"
DROPBOX_DEWEY_URL   = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"


# ==============================
#  FUNZIONI
# ==============================

def download_excel(url):
    """Scarica Excel da Dropbox"""
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")


# carica dati catalogo e Dewey
df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey   = download_excel(DROPBOX_DEWEY_URL)


def ai_chat_hf(prompt):
    """Chiama Hugging Face Inference API per generare risposta AI"""
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}

    r = requests.post(
        f"https://api-inference.huggingface.co/models/{MODEL}",
        headers=headers,
        json=payload,
        timeout=30
    )
    r.raise_for_status()
    resp = r.json()
    # alcuni modelli restituiscono lista di dict, altri dict con 'generated_text'
    if isinstance(resp, list):
        return resp[0]["generated_text"]
    elif isinstance(resp, dict) and "generated_text" in resp:
        return resp["generated_text"]
    else:
        return str(resp)


# ==============================
#  ROUTE
# ==============================

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")
    if not richiesta:
        return jsonify({"risposta": "Devi fornire una richiesta!"}), 400

    # costruisci prompt per AI
    prompt_ai = f"L'utente chiede: {richiesta}. Rispondi in modo naturale e utile."
    
    try:
        risposta = ai_chat_hf(prompt_ai)
    except Exception as e:
        return jsonify({"risposta": f"Errore API: {str(e)}"}), 500

    return jsonify({"risposta": risposta})


if __name__ == "__main__":
    import os
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
