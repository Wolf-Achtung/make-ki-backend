from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ KI-Backend aktiv – Dummy-Modus + PDFMonkey bereit."

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    print("📥 Formular-Daten erhalten:", data)

    # Dummy-Antwort für Testphase
    result = {
        "unternehmen": data.get("unternehmen", "Demo GmbH"),
        "score": 82,
        "status": "fortgeschritten",
        "analyse": "Sie sind bereits gut aufgestellt, aber es gibt Optimierungspotenzial.",
        "bewertung": "gut",
        "empfehlungen": [
            {"kategorie": "Transparenz", "text": "Führen Sie eine Modellkarte ein."},
            {"kategorie": "Schulung", "text": "Mitarbeitende sollten KI-Richtlinien kennen."}
        ],
        "gamechanger": {
            "titel": "KI-gestützter Mitarbeiter-Coach",
            "warum": "hilft bei Onboarding und Weiterbildung",
            "nutzen": "schnellere Einarbeitung",
            "potenzial": "hoch"
        },
        "trendreport": "Personalisierte KI-Assistenz wird zum Standard.",
        "zukunft": "In 5 Jahren ist KI Teil jeder Arbeitsbeschreibung.",
        "visionaer": "Nutzen Sie KI zur Identifikation neuer Geschäftsmodelle."
    }

    return jsonify(result)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    print("📥 PDF-Anfrage erhalten")
    data = request.json or {}
    print("📦 Daten für PDFMonkey:", data)

    api_key = os.environ.get("PDFMONKEY_API_KEY")
    template_id = os.environ.get("PDFMONKEY_TEMPLATE_ID")

    if not api_key or not template_id:
        print("❌ API-Key oder Template-ID fehlen")
        return jsonify({"error": "PDFMonkey-Konfiguration fehlt"}), 500

    try:
        response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "document": {
                    "document_template_id": template_id,
                    "payload": data
                }
            }
        )
        print("📤 Antwort von PDFMonkey:", response.status_code, response.text)
        if response.status_code != 201:
            return jsonify({"error": "PDF konnte nicht erstellt werden"}), 500

        pdf_url = response.json().get("document", {}).get("download_url")
        return jsonify({"pdf_url": pdf_url})

    except Exception as e:
        print("❌ Fehler bei PDF-Erstellung:", e)
        return jsonify({"error": "Serverfehler"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
