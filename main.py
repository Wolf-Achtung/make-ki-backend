import os
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Setup
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# API-Keys aus Umgebungsvariablen
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

client = OpenAI(api_key=OPENAI_API_KEY)

def analyse_mit_gpt(daten):
    prompt = f"""
    Du bist ein KI-Analyst. Analysiere folgende Unternehmensdaten:

    - Name: {daten.get('name')}
    - Unternehmen: {daten.get('unternehmen')}
    - Branche: {daten.get('branche')}
    - Ziel KI: {daten.get('ziel_ki')}
    - Tools: {daten.get('tools')}
    - Herausforderung: {daten.get('herausforderung')}
    - Geplante Maßnahmen: {daten.get('massnahmen_geplant')}

    Gib zurück:
    1. Executive Summary
    2. Empfehlungen (3 klare Punkte)
    3. Tool-Tipps & Roadmap
    4. Trends & Vision
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        ergebnis = response.choices[0].message.content.strip()
        logging.info("✅ GPT-Antwort erhalten.")
        return ergebnis
    except Exception as e:
        logging.error(f"❌ Fehler bei GPT-Abfrage: {e}")
        return "Fehler bei der GPT-Auswertung."

def sende_an_pdfmonkey(template_id, payload):
    try:
        headers = {
            "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "document": {
                "template_id": template_id,
                "payload": payload
            }
        }
        res = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=data)
        logging.info(f"📄 PDFMonkey Status {res.status_code}")
        if res.status_code == 201:
            return res.json()["data"]["attributes"]["download_url"]
        else:
            logging.warning("⚠️ PDFMonkey kein Dokument erstellt.")
            return None
    except Exception as e:
        logging.error(f"❌ Fehler bei PDFMonkey: {e}")
        return None

def sende_webhook(payload):
    try:
        res = requests.post(MAKE_WEBHOOK_URL, json=payload)
        logging.info(f"📡 Webhook gesendet – Status: {res.status_code}")
        return res.status_code
    except Exception as e:
        logging.error(f"❌ Webhook-Fehler: {e}")
        return 500

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()
        logging.info("📩 Anfrage erhalten: %s", data)

        if not data:
            return jsonify({"error": "Kein JSON erhalten."}), 400

        gpt_resultat = analyse_mit_gpt(data)

        payload = {
            "name": data.get("name"),
            "unternehmen": data.get("unternehmen"),
            "branche": data.get("branche"),
            "zusammenfassung": gpt_resultat
        }

        preview_url = sende_an_pdfmonkey(PDFMONKEY_TEMPLATE_ID_PREVIEW, payload)
        full_url = sende_an_pdfmonkey(PDFMONKEY_TEMPLATE_ID, payload)
        webhook_status = sende_webhook(payload)

        if preview_url and full_url and webhook_status in [200, 201]:
            return jsonify({
                "message": "✅ Auswertung erfolgreich generiert.",
                "preview": preview_url,
                "full": full_url
            })
        else:
            return jsonify({"error": "Ein Dienst hat versagt."}), 500

    except Exception as e:
        logging.exception("❌ Fehler in /generate-pdf")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ Backend läuft"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
