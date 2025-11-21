import requests
import pandas as pd
import io
from flask import Flask, request, jsonify, render_template
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

GROQ_API_KEY = "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"
MODEL = "llama-3.1-8b-instant"

DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?dl=1"
DROPBOX_DEWEY_URL = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?dl=1"

TOP_K_DEWEY_MATCHES = 1
TOP_N_BOOKS = 6

def download_excel(url):
    url = url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), engine="openpyxl")

df_catalog = download_excel(DROPBOX_CATALOG_URL)
df_dewey   = download_excel(DROPBOX_DEWEY_URL)

# Normalizziamo IDArgomento
df_catalog['IDArgomento'] = df_catalog['IDArgomento'].astype(str).str.replace(r'\.0$', '', regex=True)
df_dewey['IDArgomento'] = df_dewey['IDArgomento'].astype(str).str.replace(r'\.0$', '', regex=True)

def find_dewey(user_text):
    # Trova descrizione più simile
    descr_col_candidates = ['Descrizione', 'Nome', 'Argomento', 'Titolo']
    descr_col = next((c for c in descr_col_candidates if c in df_dewey.columns), None)
    if not descr_col:
        df_dewey['__descr__'] = df_dewey['IDArgomento'].astype(str)
        descr_col = '__descr__'

    texts = df_dewey[descr_col].fillna('').astype(str).values
    vect = TfidfVectorizer(stop_words='italian', ngram_range=(1,2)).fit(texts.tolist() + [user_text])
    X = vect.transform(texts)
    q = vect.transform([user_text])
    sims = cosine_similarity(q, X)[0]
    top_idx = np.argsort(sims)[::-1][:TOP_K_DEWEY_MATCHES]
    return df_dewey.iloc[top_idx]['IDArgomento'].astype(str).tolist()[0]

def ai_chat(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Sei il bot intelligente della Biblioteca. Rispondi solo con libri presenti nel catalogo e indica collocazione/ID Dewey."},
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
    return "Bot IA Biblioteca attivo!"

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/consiglia", methods=["POST"])
def consiglia():
    richiesta = request.json.get("richiesta", "")
    if not richiesta:
        return jsonify({"risposta": "Devi inserire una richiesta!"})

    # Trova la categoria Dewey più pertinente
    selected_dewey = find_dewey(richiesta)

    # Filtra il catalogo per Dewey
    matches = df_catalog[df_catalog['IDArgomento'].astype(str).str.startswith(selected_dewey)]
    if matches.empty:
        return jsonify({"risposta": f"Nessun libro trovato per la categoria {selected_dewey}."})

    # Prendi top N libri
    selected_books = matches.head(TOP_N_BOOKS).to_dict(orient='records')

    # Costruisci prompt per AI
    libro_str = "\n".join([f"- {b.get('Titolo','Sconosciuto')} di {b.get('Autore','Sconosciuto')} (ID Dewey: {b.get('IDArgomento','')})" for b in selected_books])
    prompt = f"L’utente ha chiesto: '{richiesta}'. Libri disponibili nel catalogo:\n{libro_str}\nRispondi consigliando libri presenti solo in questa lista, indicando collocazione e spiegando brevemente perché sono adatti."

    risposta = ai_chat(prompt)
    return jsonify({"selected_dewey": selected_dewey, "books": selected_books, "risposta": risposta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
