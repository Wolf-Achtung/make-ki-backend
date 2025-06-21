import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import requests

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY

# Hilfsfunktion: Dummy-Auswertung (ersetzt echte GPT-Analyse temporär)
def generate_dummy_payload(data):
    return {
        "name": data.get("name"),
        "unternehmen": data.get("unternehmen"),
        "branche": data.get("branche"),
        "email": data.get("email"),
        "selbststaendig": data.get("selbststaendig"),
        "readiness_fragen": "Technisch solide, aber ohne strategischen Plan.",
        "compliance_fragen": "DSGVO teils beachtet, keine explizite KI-Governance.",
        "usecase_fragen": "Textgenerierung geplant, geringe Toolintegration.",
        "executive_summary": "Ihr Unternehmen zeigt KI-Bereitschaft, aber es fehlen klare Strukturen und Prozesse.",
        "analyse": "Der Status ist experimentell. Chancen bestehen in der schnellen Umsetzung und im Marketing.",
        "empfehlung1": "Einführung eines KI-Piloten mit definierten KPIs.",
        "empfehlung2": "Aufbau eines internen KI-Teams mit Fortbildungsbudget.",
        "empfehlung3": "Verankerung der KI-Governance in der Datenschutzstruktur.",
        "roadmap": "3 Monate: Schulung. 6 Monate: Pilot. 12 Monate: Integration.",
        "ressourcen": "Externe Beratung, interne Schulung, Fördermittel beantragen.",
        "zukunft": "Automatisierung und multimodale KI-Integration möglich.",
        "risikoprofil": "Moderat – Datenverarbeitung ohne volle Kontrolle.",
        "tooltipps": "Nutzen Sie Tools wie ChatGPT, Notion AI, Midjourney.",
        "foerdertipps": "BMWK-Innovationsgutscheine, Digital Jetzt.",
        "branchenvergleich": "Sie liegen leicht über dem Durchschnitt der Branche.",
        "trendreport": "2025: Sprach-KI, Agenten, Edge AI im Vormarsch.",
        "vision": "Ihr Unternehmen als Vorreiter in kreativer KI-Nutzung."
    }

# Haupt-Route
@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        logging.info("✅ Formulardaten empfangen:")
        logging.info(data)

        # GPT- oder Dummy-Auswertung
        payload = generate_dummy_payload(data)

        # Auswahl Template
        is_preview = data.get("preview", False)
        template_id = PDFMONKEY_TEMPLATE_ID_PREVIEW if is_preview else PDFMONKEY_TEMPLATE_ID
        logging.info(f"📄 Verwende Template-ID: {template_id}")

        # Sende an PDFMonkey
        pdfmonkey_response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "document": {
                    "document_template_id": template_id,
                    "payload": payload,
                    "webhook_url": MAKE_WEBHOOK_URL
                }
            }
        )

        if pdfmonkey_response.status_code != 201:
            logging.error(f"❌ Fehler bei PDFMonkey: {pdfmonkey_response.text}")
            return jsonify({"error": "PDF-Erstellung fehlgeschlagen"}), 500

        document_id = pdfmonkey_response.json()["data"]["id"]
        logging.info(f"📄 PDFMonkey-Dokument ID: {document_id}")

        return jsonify({"success": True, "preview": is_preview, "pdf_id": document_id})

    except Exception as e:
        logging.exception("❌ Ausnahme beim Verarbeiten der Anfrage:")
        return jsonify({"error": f"Interner Fehler: {str(e)}"}), 500

# Railway-kompatibler Start
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
