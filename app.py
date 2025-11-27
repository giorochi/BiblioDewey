import os
import requests
from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CATALOGO_URL = "https://www.dl.dropboxusercontent.com/scl/fi/zkp7eo8f2tnlsneemqvjx/catalogo.xlsx?rlkey=3wcn05kwsusu3vnnwf5nqg5on&st=xp2813pp&dl=1"
ARGOMENTI_URL = "https://www.dl.dropboxusercontent.com/scl/fi/wynic8v2mt51cfk0es5m4/Argomenti.xlsx?rlkey=kjgt8etgum3w72mo5c9gzkqvp&st=3fclbbjy&dl=1"

def load_xlsx(url):
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_excel(r.content)

catalogo = load_xlsx(CATALOGO_URL)
argomenti = load_xlsx(ARGOMENTI_URL)

def ask_groq(prompt):
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    data = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(endpoint, json=data, headers=headers)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

@app.route("/consiglia", methods=["POST"])
def consiglia():
    try:
        query = request.json.get("query")

        # Filtro super semplice per trovare titoli rilevanti
        results = catalogo[catalogo.apply(lambda row:
            query.lower() in str(row).lower(), axis=1)]

        if results.empty:
            return jsonify({"risposta": "Nessun libro trovato nel catalogo."})

        libri = []
        for _, row in results.iterrows():
            libri.append({
                "titolo": row.get("Titolo", "Sconosciuto"),
                "autore": row.get("Autore", "Sconosciuto"),
                "collocazione": row.get("Collocazione", "N/A"),
            })

        testo = "Ecco i libri trovati:\n" + "\n".join(
            [f"{l['titolo']} – {l['autore']} (Collocazione: {l['collocazione']})" for l in libri]
        )

        answer = ask_groq(f"Utente chiede: {query}\nLibri disponibili:\n{testo}\nRispondi solo usando questi.")

        return jsonify({"risposta": answer})

    except Exception as e:
        return jsonify({"errore": str(e)}), 500

if __name__ == "__main__":
    app.run()
