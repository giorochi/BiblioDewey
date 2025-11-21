import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

GROQ_API_KEY = "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"
MODEL = "llama-3.1-8b-instant"  # modello raccomandato da Groq

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&dl=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"

def download_excel(url):
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")

df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey   = download_excel(DROPBOX_DEWEY_URL)

def ai_chat(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Sei il bot intelligente della Biblioteca Parrocchiale."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 512
    }

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        return f"Errore API: {r.status_code} - {r.text}"
    data = r.json()
    return data["choices"][0]["message"]["content"]

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo con Groq!"

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")
    prompt = f"L’utente chiede: {richiesta}. Rispondi come un bibliotecario esperto."
    risposta = ai_chat(prompt)
    return jsonify({"risposta": risposta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
