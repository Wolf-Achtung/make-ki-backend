
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import openai

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# Init Flask
app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

def gpt_generate_analysis(payload):
    prompt = f"""
    Du bist ein KI-Berater. Analysiere folgenden Kundenfragebogen als Grundlage für einen Executive Summary und drei Empfehlungen:

    {payload}

    Antworte in folgendem JSON Format:
    {{
        "executive_summary": "...",
        "analyse": "...",
        "empfehlung1": "...",
        "empfehlung2": "...",
        "empfehlung3": "...",
        "vision": "..."
    }}
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    logger.info("✅ GPT-Antwort empfangen")
    content = response.choices[0].message.content.strip()
    try:
        return eval(content)
    except Exception as e:
        logger.error("⚠️ Fehler beim Parsen der GPT-Antwort: %s", e)
        return {}

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        payload = request.json
        logger.info("📥 Formulardaten empfangen:")
        logger.info(payload)

        preview_mode = payload.pop("preview", False)
        template_id = PDFMONKEY_TEMPLATE_ID_PREVIEW if preview_mode else PDFMONKEY_TEMPLATE_ID
        logger.info("📄 Verwende Template-ID: %s", template_id)

        # GPT-Auswertung
        logger.info("🧠 GPT-Auswertung wird gestartet ...")
        gpt_data = gpt_generate_analysis(payload)
        payload.update(gpt_data)

        # PDFMonkey: PDF erzeugen
        logger.info("📤 Sende Daten an PDFMonkey ...")
        response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "document": {
                    "template_id": template_id,
                    "payload": payload
                }
            }
        )

        pdfmonkey_response = response.json()
        document_id = pdfmonkey_response["data"]["id"]
        logger.info("✅ PDFMonkey Dokument-ID: %s", document_id)

        preview_url = f"https://app.pdfmonkey.io/preview/{document_id}"
        logger.info("🔗 Vorschau-Link: %s", preview_url)

        # Trigger Make
        logger.info("📬 Trigger Make Webhook ...")
        if MAKE_WEBHOOK_URL:
            requests.post(MAKE_WEBHOOK_URL, json=payload)

        return jsonify({"success": True, "preview": preview_url})

    except Exception as e:
        logger.error("❌ Ausnahme beim Verarbeiten der Anfrage:")
        logger.exception(e)
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
