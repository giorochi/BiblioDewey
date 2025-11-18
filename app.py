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
#  SOSTITUISCI QUI I LINK
# ============================
DROPBOX_CATALOG_URL = "https://www.dropbox.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=meiiqapmo6uzc1crf1b9kd2ct&dl=1"
"
DROPBOX_DEWEY_URL   = "https://www.dropbox.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=38lsti7r48xlehxccgdz21ive&dl=1"
"
# ============================

# Parametri
TOP_K_DEWEY_MATCHES = 1    # quanti IDArgomento considerare per filtrare (1 va bene)
TOP_N_BOOKS = 6            # quanti libri mostrare nel risultato

def download_excel(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content))

def load_dataframes():
    # Scarica i due file da Dropbox
    df_catalog = download_excel(DROPBOX_CATALOG_URL)
    df_dewey   = download_excel(DROPBOX_DEWEY_URL)
    return df_catalog, df_dewey

def find_dewey_for_text(user_text, df_dewey):
    """
    Prende il testo dell'utente e cerca la descrizione più simile
    nella tabella Dewey. Restituisce la lista di IDArgomento più rilevanti.
    """
    # Trova la colonna con la descrizione nella tabella Dewey (gestione flessibile)
    descr_col_candidates = ['Descrizione', 'DescrizioneArgomento', 'Nome', 'NomeArgomento', 'Argomento', 'Titolo']
    descr_col = None
    for c in descr_col_candidates:
        if c in df_dewey.columns:
            descr_col = c
            break
    if descr_col is None:
        # fallback: usa la seconda colonna utile se presente
        cols = [c for c in df_dewey.columns if c != 'IDArgomento']
        if len(cols) > 0:
            descr_col = cols[0]
        else:
            # se non c'è nulla, usa l'IDArgomento come stringa (pessimo ma evita crash)
            df_dewey['__descr__'] = df_dewey['IDArgomento'].astype(str)
            descr_col = '__descr__'

    texts = df_dewey[descr_col].fillna('').astype(str).values
    # Costruisci TF-IDF
    vect = TfidfVectorizer(stop_words='italian', ngram_range=(1,2)).fit(texts.tolist() + [user_text])
    X = vect.transform(texts)
    q = vect.transform([user_text])
    sims = cosine_similarity(q, X)[0]
    top_idx = np.argsort(sims)[::-1][:TOP_K_DEWEY_MATCHES]
    best_ids = df_dewey.iloc[top_idx]['IDArgomento'].astype(str).tolist()
    best_scores = sims[top_idx].tolist()
    return best_ids, best_scores

def generate_explanation(user_text, selected_books, selected_dewey):
    """
    Genera una spiegazione sintetica. Se transformers è installato,
    prova a creare una risposta 'più naturale' usando un modello.
    Altrimenti, genera un testo template.
    """
    try:
        from transformers import pipeline
        # Modello leggero: se non disponibile, transformers lancerà eccezione
        # ATTENZIONE: qui puoi cambiare il modello se preferisci uno italiano
        gen = pipeline("text-generation", model="bigscience/bloomz-560m", max_new_tokens=120)
        libro_str = "\n".join([f"- {b['Titolo']} di {b.get('Autore','Sconosciuto')} (Dewey: {b['IDArgomento']})" for b in selected_books])
        prompt = (
            f"L'utente ha chiesto: \"{user_text}\".\n"
            f"Categoria Dewey selezionata: {selected_dewey}.\n\n"
            f"Libri disponibili nel catalogo:\n{libro_str}\n\n"
            f"Consiglia i 2 libri migliori e spiega brevemente perché sono adatti alla richiesta."
        )
        out = gen(prompt)[0]['generated_text']
        # tronca se troppo lungo
        return out.strip()
    except Exception:
        # fallback: template semplice e robusto
        explanation = f"Ho identificato la categoria Dewey: {selected_dewey}.\n"
        explanation += "Ecco i libri che ho trovato e perché li suggerisco:\n"
        for i, b in enumerate(selected_books[:TOP_N_BOOKS], start=1):
            titolo = b.get('Titolo') if 'Titolo' in b else b.get('Titolo','Titolo non disponibile')
            autore = b.get('Autore', 'Autore sconosciuto')
            dew = b.get('IDArgomento', '')
            # semplice euristica: preferisci libri con descrizione se presente
            motivo = "Buona corrispondenza alla categoria."
            if 'Descrizione' in b and isinstance(b['Descrizione'], str) and len(b['Descrizione'])>30:
                motivo = "Descrizione utile e pertinente."
            if i == 1:
                motivo = "Scelta consigliata: introduzione/approfondimento bilanciato adatto alla richiesta."
            explanation += f"{i}. {titolo} — {autore} (Dewey {dew}) → {motivo}\n"
        return explanation

@app.route("/consiglia", methods=["POST"])
def consiglia():
    data = request.get_json(force=True)
    user_text = data.get("richiesta", "").strip()
    given_dewey = data.get("dewey", "")  # opzionale

    try:
        df_catalog, df_dewey = load_dataframes()
    except Exception as e:
        return jsonify({"error": "Errore scaricamento file", "details": str(e)}), 500

    # Normalizziamo le colonne IDArgomento in stringhe (evitiamo float .0)
    df_catalog['IDArgomento'] = df_catalog['IDArgomento'].astype(str).str.replace(r'\.0$','', regex=True)
    df_dewey['IDArgomento'] = df_dewey['IDArgomento'].astype(str).str.replace(r'\.0$','', regex=True)

    if given_dewey:
        selected_dewey = str(given_dewey).strip()
    else:
        # inferiamo la Dewey più adatta dalla tabella Dewey
        best_ids, scores = find_dewey_for_text(user_text, df_dewey)
        if len(best_ids) == 0:
            return jsonify({"risposta": "Non sono riuscito a identificare una categoria Dewey dalla tua richiesta."})
        selected_dewey = best_ids[0]

    # Filtra il catalogo: IDArgomento che iniziano con selected_dewey
    matches = df_catalog[df_catalog['IDArgomento'].astype(str).str.startswith(selected_dewey)]

    if matches.empty:
        return jsonify({"risposta": f"Nessun libro trovato per la categoria {selected_dewey}."})

    # Ordina e prendi i migliori top-N (qui semplice: i primi trovati)
    # Potresti migliorare con priorità, rating, etc.
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

