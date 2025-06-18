from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import datetime
import requests

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "✅ KI-Backend aktiv – Dummy-Modus + PDFMonkey bereit."

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


@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    api_key = os.environ.get("PDFMONKEY_API_KEY")
    template_id = os.environ.get("PDFMONKEY_TEMPLATE_ID")
    if not api_key or not template_id:
        return jsonify({"error": "PDFMonkey-Konfiguration fehlt"}), 500

    payload = {
        "document": {
            "document_template_id": template_id,
            "payload": request.json or {},
            "meta": {
                "external_id": f"check-{int(time.time())}"
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.pdfmonkey.io/api/v1/documents", json=payload, headers=headers)
        if response.status_code != 201:
            return jsonify({"error": "PDFMonkey-Fehler", "details": response.text}), 500
        data = response.json()
        return jsonify({ "pdf_url": data["data"]["attributes"]["download_url"] })

    except Exception as e:
        return jsonify({"error": "PDF-Erzeugung fehlgeschlagen", "details": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

    while True:
        print("✅ Backend läuft mit /analyze und /generate-pdf")
        time.sleep(10)