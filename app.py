# app.py
from flask import Flask, request, jsonify
import pandas as pd
import requests
import io
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# ============================
# LINK DIRETTI DROPBOX (dl=1)
# ============================
DROPBOX_CATALOG_URL = "https://www.dropbox.com/s/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?dl=1"
DROPBOX_DEWEY_URL   = "https://www.dropbox.com/s/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?dl=1"
# ============================

# Parametri
TOP_K_DEWEY_MATCHES = 1
TOP_N_BOOKS = 6

# ----------------------------
# Funzione per scaricare Excel
# ----------------------------
def download_excel(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    # Controllo content-type per sicurezza
    if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' not in r.headers.get('Content-Type', ''):
        raise ValueError(f"Il file scaricato da {url} non è un Excel valido")
    return pd.read_excel(io.BytesIO(r.content), engine='openpyxl')

# ----------------------------
# Carica i file una sola volta
# ----------------------------
try:
    df_catalog = download_excel(DROPBOX_CATALOG_URL)
    df_dewey   = download_excel(DROPBOX_DEWEY_URL)
except Exception as e:
    print("Errore caricamento file Dropbox:", e)
    df_catalog, df_dewey = pd.DataFrame(), pd.DataFrame()

# Normalizza IDArgomento
df_catalog['IDArgomento'] = df_catalog['IDArgomento'].astype(str).str.replace(r'\.0$', '', regex=True)
df_dewey['IDArgomento'] = df_dewey['IDArgomento'].astype(str).str.replace(r'\.0$', '', regex=True)

# ----------------------------
# Funzione per trovare Dewey
# ----------------------------
def find_dewey_for_text(user_text, df_dewey):
    descr_col_candidates = ['Descrizione', 'DescrizioneArgomento', 'Nome', 'NomeArgomento', 'Argomento', 'Titolo']
    descr_col = None
    for c in descr_col_candidates:
        if c in df_dewey.columns:
            descr_col = c
            break
    if descr_col is None:
        cols = [c for c in df_dewey.columns if c != 'IDArgomento']
        descr_col = cols[0] if cols else 'IDArgomento'
        df_dewey['__descr__'] = df_dewey[descr_col].astype(str)
        descr_col = '__descr__'

    texts = df_dewey[descr_col].fillna('').astype(str).values
    vect = TfidfVectorizer(stop_words='italian', ngram_range=(1,2)).fit(texts.tolist() + [user_text])
    X = vect.transform(texts)
    q = vect.transform([user_text])
    sims = cosine_similarity(q, X)[0]
    top_idx = np.argsort(sims)[::-1][:TOP_K_DEWEY_MATCHES]
    best_ids = df_dewey.iloc[top_idx]['IDArgomento'].astype(str).tolist()
    return best_ids

# ----------------------------
# Genera spiegazione
# ----------------------------
def generate_explanation(user_text, selected_books, selected_dewey):
    explanation = f"Ho identificato la categoria Dewey: {selected_dewey}.\n"
    explanation += "Ecco i libri che ho trovato e perché li suggerisco:\n"
    for i, b in enumerate(selected_books[:TOP_N_BOOKS], start=1):
        titolo = b.get('Titolo', 'Titolo non disponibile')
        autore = b.get('Autore', 'Autore sconosciuto')
        dew = b.get('IDArgomento', '')
        motivo = "Buona corrispondenza alla categoria."
        if 'Descrizione' in b and isinstance(b['Descrizione'], str) and len(b['Descrizione'])>30:
            motivo = "Descrizione utile e pertinente."
        if i == 1:
            motivo = "Scelta consigliata: introduzione/approfondimento bilanciato adatto alla richiesta."
        explanation += f"{i}. {titolo} — {autore} (Dewey {dew}) → {motivo}\n"
    return explanation

# ----------------------------
# Route principale
# ----------------------------
@app.route("/consiglia", methods=["POST"])
def consiglia():
    data = request.get_json(force=True)
    user_text = data.get("richiesta", "").strip()
    given_dewey = data.get("dewey", "").strip()

    if not user_text:
        return jsonify({"error": "Nessuna richiesta fornita"}), 400

    if df_catalog.empty or df_dewey.empty:
        return jsonify({"error": "I file Excel non sono disponibili."}), 500

    if given_dewey:
        selected_dewey = str(given_dewey)
    else:
        best_ids = find_dewey_for_text(user_text, df_dewey)
        if not best_ids:
            return jsonify({"risposta": "Non sono riuscito a identificare una categoria Dewey dalla tua richiesta."})
        selected_dewey = best_ids[0]

    # Filtra catalogo per Dewey
    matches = df_catalog[df_catalog['IDArgomento'].astype(str).str.startswith(selected_dewey)]
    if matches.empty:
        return jsonify({"risposta": f"Nessun libro trovato per la categoria {selected_dewey}."})

    selected = matches.head(TOP_N_BOOKS).to_dict(orient='records')
    explanation = generate_explanation(user_text, selected, selected_dewey)

    return jsonify({
        "selected_dewey": selected_dewey,
        "n_results": len(matches),
        "books": selected,
        "risposta": explanation
    })

@app.route("/")
def home():
    return "Bot IA Biblioteca attivo!"

# ----------------------------
# Avvio server
# ----------------------------
if __name__ == "__main__":
    import os
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
