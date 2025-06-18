from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return "✅ KI-Backend aktiv – GPT-Dummy & PDFMonkey einsatzbereit."

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    print("Fragebogen empfangen:", data)

    result = {
        "name": data.get("name", "Max Mustermann"),
        "email": data.get("email"),
        "unternehmen": data.get("unternehmen", "Muster GmbH"),
        "datum": data.get("datum"),
        "score": 85,
        "status": "aktiv",
        "bewertung": "gut",
        "executive_summary": "Dieses KI-Briefing zeigt die wichtigsten Chancen und Risiken...",
        "analyse": "Die Muster GmbH befindet sich in einem dynamischen Marktumfeld...",
        "emp": [
            {
                "titel": "Dringende Hebelmaßnahme",
                "beschreibung": "Automatisierung interner Workflows mit Make starten.",
                "next_step": "Pilot-Workflow identifizieren und aufsetzen.",
                "tool": "Make"
            },
            {
                "titel": "Potenzial entfesseln",
                "beschreibung": "Content-Erstellung durch Notion AI und DeepL Pro unterstützen.",
                "next_step": "Redaktionsprozesse analysieren und KI integrieren.",
                "tool": "Notion AI, DeepL Pro"
            },
            {
                "titel": "Zukunft sichern",
                "beschreibung": "Strategische Weiterbildung im Bereich KI für Schlüsselmitarbeiter.",
                "next_step": "Online-Kurse bei aiCampus starten.",
                "tool": "aiCampus"
            }
        ],
        "roadmap": {
            "kurzfristig": "Mindestens einen Prozess automatisieren.",
            "mittelfristig": "KI-Standards im Unternehmen definieren.",
            "langfristig": "KI als festen Bestandteil der Unternehmenskultur etablieren."
        },
        "ressourcen": "Plattformen wie aiCampus, Bundesförderprogramme...",
        "zukunft": "Mit einem klaren KI-Fahrplan kann die Muster GmbH zum Branchenvorbild werden...",
        "risikoprofil": {
            "risikoklasse": "Moderat",
            "begruendung": "Nutzung generativer Tools mit sensiblen Daten.",
            "pflichten": ["Transparenzpflichten", "DSFA", "Mitarbeiterschulung"]
        },
        "tooltipps": [
            {"name": "Make", "einsatz": "Workflow-Automatisierung", "warum": "Intuitiv und vielseitig"},
            {"name": "Notion AI", "einsatz": "Content-Optimierung", "warum": "Smarte Textvorschläge"}
        ],
        "foerdertipps": [
            {"programm": "go-digital", "zielgruppe": "KMU", "nutzen": "Bis zu 50% Förderung"}
        ],
        "branchenvergleich": "Die IT-Branche liegt beim KI-Einsatz vorn...",
        "trendreport": "Multimodale Systeme & datensichere Private-AI-Lösungen kommen.",
        "visionaer": "Ihre Agentur schafft doppelt so viel bei halbem Aufwand durch KI."
    }

    return jsonify(result)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    print("PDF-Daten empfangen:", data)

    api_key = os.environ.get("PDFMONKEY_API_KEY")
    template_id = os.environ.get("PDFMONKEY_TEMPLATE_ID")

    if not api_key or not template_id:
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
                    "payload": data,
                    "publish": True
                }
            }
        )

        if response.status_code != 201:
            print("❌ PDFMonkey-Fehler:", response.text)
            return jsonify({"error": "PDF konnte nicht erstellt werden"}), 500

        pdf_url = response.json().get("document", {}).get("download_url")
        return jsonify({"pdf_url": pdf_url})

    except Exception as e:
        print("❌ Ausnahmefehler:", e)
        return jsonify({"error": "Serverfehler"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
