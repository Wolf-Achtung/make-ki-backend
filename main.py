from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import datetime

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "✅ KI-Backend aktiv – Dummy-Modus für Vorschau."

@app.route("/analyze", methods=["POST"])
def analyze():
    dummy_response = {
        "name": "Max Mustermann",
        "unternehmen": "Beispiel GmbH",
        "datum": datetime.datetime.now().strftime("%d.%m.%Y"),
        "score": 82,
        "status": "Fortgeschritten",
        "bewertung": "Gute strategische Ausgangslage.",
        "executive_summary": "Ihr Unternehmen ist gut vorbereitet auf KI-Anwendungen.",
        "analyse": "Sie nutzen bereits grundlegende Tools, aber es gibt Optimierungspotenzial.",
        "empfehlungen": [
            {
                "titel": "Einführung einer KI-Richtlinie",
                "beschreibung": "Definieren Sie klare Regeln für KI-Einsatz.",
                "next_step": "Rollen & Verantwortlichkeiten klären",
                "tool": "AI-Governance Guide"
            },
            {
                "titel": "Datenstrategie entwickeln",
                "beschreibung": "Strukturieren Sie Ihre Datenbasis für künftige KI-Anwendungen.",
                "next_step": "Dateninventur starten",
                "tool": "OneTrust"
            }
        ],
        "ressourcen": "Fokus auf interne Weiterbildung",
        "zukunft": "Ausbau von KI-gestützten Services",
        "gamechanger": {
            "idee": "Entwicklung eines KI-gestützten Kundenberaters",
            "begründung": "Hohe Serviceorientierung + starke Datenlage",
            "potenzial": "Skalierbarer Mehrwert & Differenzierung"
        },
        "risikoprofil": {
            "risikoklasse": "mittel",
            "begruendung": "Teilweise sensible Datenverarbeitung",
            "pflichten": ["DSGVO-Check", "Transparenzpflicht"]
        },
        "tooltipps": [
            { "name": "ChatGPT", "einsatz": "Textgenerierung", "warum": "Einfach, schnell einsetzbar" }
        ],
        "foerdertipps": [
            { "programm": "go-digital", "zielgruppe": "KMU", "nutzen": "Beratungsförderung bis 16.500€" }
        ],
        "branchenvergleich": "Sie liegen über dem Branchendurchschnitt.",
        "trendreport": "Automatisierung & Generative KI",
        "visionaer": "Sie könnten durch KI ein Abo-Modell einführen."
    }

    return jsonify(dummy_response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

    while True:
        print("✅ Dummy-Modus läuft – Vorschau sollte erreichbar sein.")
        time.sleep(10)