from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "✅ Flask läuft – API bereit."

@app.route("/analyze", methods=["POST"])
def analyze():
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    import datetime
    import json

    user_input = request.json["answers"]

    prompt_template = """
Du bist ein KI-Analyst für Unternehmen, die sich mit dem Thema Künstliche Intelligenz befassen. Analysiere die folgenden Angaben aus einem interaktiven KI-Check und gib eine umfassende Bewertung zurück. Deine Antwort soll **ausschließlich aus gültigem JSON** bestehen, das automatisch in ein PDF übertragen wird. Gib kein Fließtext und keine Vorbemerkung zurück.

Die Bewertung soll folgende Felder enthalten:

{{
  "name": "...",
  "unternehmen": "...",
  "datum": "TT.MM.JJJJ",
  "score": 0–100,
  "status": "Einsteiger | Fortgeschritten | Profi",
  "bewertung": "...",
  "executive_summary": "...",
  "analyse": "...",
  "empfehlungen": [
    {{
      "titel": "...",
      "beschreibung": "...",
      "next_step": "...",
      "tool": "..."
    }}
  ],
  "ressourcen": "...",
  "zukunft": "...",
  "gamechanger": {{
    "idee": "...",
    "begründung": "...",
    "potenzial": "..."
  }},
  "risikoprofil": {{
    "risikoklasse": "gering | mittel | hoch",
    "begruendung": "...",
    "pflichten": ["...", "..."]
  }},
  "tooltipps": [
    {{ "name": "...", "einsatz": "...", "warum": "..." }}
  ],
  "foerdertipps": [
    {{ "programm": "...", "zielgruppe": "...", "nutzen": "..." }}
  ],
  "branchenvergleich": "...",
  "trendreport": "...",
  "visionaer": "..."
}}

Nutze für Score & Status die Antworten auf die 10 Skalenfragen. Berücksichtige auch Branche, Selbstständigkeit und alle Freitexte. Die Gamechanger-Idee darf visionär sein und muss kein direkt logischer Vorschlag sein – z. B. ein neuartiges Produkt oder Modell mit KI.

Hier sind die Nutzerdaten (als JSON):

{user_input}
"""

    prompt = prompt_template.format(user_input=json.dumps(user_input, ensure_ascii=False))

    def ask_gpt(p):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": p}],
            temperature=0.7
        )
        return response.choices[0].message["content"]

    def try_parse(raw):
        try:
            return json.loads(raw), None
        except Exception as e:
            return None, str(e)

    result, error = try_parse(ask_gpt(prompt))

    if not result:
        repair_prompt = "Bitte gib das folgende JSON korrekt zurück, ohne Fließtext. Repariere es:\n\n" + ask_gpt(prompt)
        result, error = try_parse(ask_gpt(repair_prompt))

    if not result:
        return jsonify({"error": "JSON-Parsing fehlgeschlagen", "details": error}), 500

    result["datum"] = datetime.datetime.now().strftime("%d.%m.%Y")

    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

    while True:
        print("✅ Flask ist aktiv – Endlosschleife läuft")
        time.sleep(10)