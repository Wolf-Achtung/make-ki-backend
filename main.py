import os
import logging
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import requests

load_dotenv()

# Konfiguration
openai.api_key = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
WEBHOOK_URL = os.getenv("WEBHOOK_MAKE_URL")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask Setup
app = Flask(__name__)
CORS(app)

# GPT-Analyse
def gpt_auswertung(user_data):
    prompt = f"""
    Du bist ein KI-Berater. Analysiere folgende Unternehmensdaten und erstelle:
    1. Eine Zusammenfassung (Executive Summary)
    2. Eine fundierte Analyse
    3. Drei konkrete Empfehlungen (Titel, Beschreibung, Tool, Next Step)
    4. Eine KI-Roadmap (kurzfristig, mittelfristig, langfristig)
    5. Fördertipps (Programm, Nutzen, Zielgruppe)
    6. Ein Risikoprofil mit Risikoklasse, Begründung und Pflichten
    7. Tooltipps mit Name, Einsatz und Begründung
    8. Branchenvergleich & Trendreport
    9. Vision für die KI-Zukunft

    Daten: {user_data}
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Fehler bei GPT-Analyse: {e}")
        return "Analyse konnte nicht generiert werden."

# PDFMonkey-Erstellung
def erstelle_pdf(payload, template_id):
    url = "https://api.pdfmonkey.io/api/v1/documents"
    headers = {
        "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "document": {
            "document_template_id": template_id,
            "payload": payload
        }
    }
    try:
        res = requests.post(url, json=data, headers=headers)
        res.raise_for_status()
        doc_url = res.json().get("data", {}).get("attributes", {}).get("download_url", "")
        logger.info(f"PDF erstellt mit URL: {doc_url}")
        return doc_url
    except Exception as e:
        logger.error(f"Fehler bei PDFMonkey: {e}")
        return None

# Webhook an Make senden
def sende_webhook(data):
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        logger.info(f"Webhook gesendet: {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook-Fehler: {e}")

# Flask Route
@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        user_data = request.json
        logger.info("Empfangene Formulardaten:")
        logger.info(user_data)

        # GPT-Auswertung
        gpt_result = gpt_auswertung(user_data)
        logger.info("GPT-Auswertung erhalten.")

        # Dummy-Payload-Erweiterung mit GPT
        payload = {
            **user_data,
            "executive_summary": gpt_result,
            "analyse": "Erste Analyse basierend auf den Angaben.",
            "empfehlung1": {
                "titel": "KI sofort starten",
                "beschreibung": "Nutzen Sie ChatGPT für E-Mail-Antworten.",
                "tool": "ChatGPT",
                "next_step": "Login auf openai.com und testen."
            },
            "empfehlung2": {
                "titel": "Automatisierung ausbauen",
                "beschreibung": "Wiederkehrende Aufgaben automatisieren.",
                "tool": "Make",
                "next_step": "Erstelle ein Szenario für Rechnungsversand."
            },
            "empfehlung3": {
                "titel": "Mitarbeiter schulen",
                "beschreibung": "Onboarding zu KI-Tools.",
                "tool": "Lernplattform",
                "next_step": "Erstelle ein Lernprogramm für dein Team."
            },
            "roadmap": {
                "kurzfristig": "Testphase mit einfachen GPT-Aufgaben.",
                "mittelfristig": "Prozessautomatisierung mit Make.",
                "langfristig": "Individuelle KI-Anwendungen entwickeln."
            },
            "ressourcen": "Kostenlose Tools, YouTube-Kurse, Förderprogramme.",
            "foerdertipps": [
                {"programm": "go-digital", "nutzen": "Beratung", "zielgruppe": "KMU"},
                {"programm": "Digital Jetzt", "nutzen": "Investitionsförderung", "zielgruppe": "Mittelstand"}
            ],
            "risikoprofil": {
                "risikoklasse": "Mittel",
                "begruendung": "Kein Hochrisiko-KI-Einsatz.",
                "pflichten": ["Transparenz", "Datenmanagement"]
            },
            "tooltipps": [
                {"name": "Make", "einsatz": "Prozessautomatisierung", "warum": "Einfache Bedienung"},
                {"name": "ChatGPT", "einsatz": "Texterstellung", "warum": "Hohe Qualität"}
            ],
            "branchenvergleich": "Im Mittelfeld bei KI-Einführung.",
            "trendreport": "Multimodale KI auf dem Vormarsch.",
            "vision": "Individuelle KI-Lösungen, ganzheitlich integriert."
        }

        # Vorschau-PDF erstellen
        preview_link = erstelle_pdf(payload, TEMPLATE_ID_PREVIEW)
        if not preview_link:
            return jsonify({"error": "PDF-Vorschau fehlgeschlagen"}), 500

        # Vollversion-PDF erstellen
        voll_link = erstelle_pdf(payload, TEMPLATE_ID)

        # Webhook an Make
        sende_webhook(payload)

        logger.info("Fertig. Vorschau-Downloadlink zurückgegeben.")
        return jsonify({"preview_url": preview_link})

    except Exception as e:
        logger.error(f"Fehler in /generate-pdf: {e}")
        return jsonify({"error": str(e)}), 500

# Railway-Kompatibilität
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
