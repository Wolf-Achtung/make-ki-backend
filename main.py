import os
import json
import logging
import traceback
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# Logging-Setup
logging.basicConfig(level=logging.INFO)

# Flask-Setup
app = Flask(__name__)
CORS(app)

# API-Schlüssel und IDs
openai.api_key = os.getenv("OPENAI_API_KEY")
pdfmonkey_api_key = os.getenv("PDFMONKEY_API_KEY")
pdfmonkey_template_id = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
make_webhook_url = os.getenv("MAKE_WEBHOOK_URL")

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    logging.info("📥 POST /generate-pdf gestartet")

    try:
        data = request.get_json()
        logging.info(f"📦 Erhaltene Formulardaten:\n{json.dumps(data, indent=2)}")

        # Pflichtfelder prüfen
        for field in ["name", "unternehmen", "branche"]:
            if field not in data or not data[field]:
                error_msg = f"❌ Fehlendes Pflichtfeld: {field}"
                logging.error(error_msg)
                return jsonify({"error": error_msg}), 400

        # GPT-Auswertung vorbereiten
        prompt = (
            f"Unternehmen: {data['unternehmen']}\n"
            f"Branche: {data['branche']}\n"
            f"Ziel mit KI: {data.get('ziel_ki', 'Nicht angegeben')}\n"
            f"Herausforderung: {data.get('herausforderung', 'Nicht angegeben')}\n"
            f"Vorwissen: {data.get('verständnis', 'Unklar')}\n"
            "Bitte erstelle eine kurze Zusammenfassung zur KI-Reife."
        )
        logging.info("🧠 Sende Anfrage an OpenAI ...")

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein KI-Berater."},
                {"role": "user", "content": prompt}
            ]
        )

        zusammenfassung = completion['choices'][0]['message']['content']
        logging.info(f"✅ GPT-Antwort erhalten:\n{zusammenfassung}")

        # Vorschau-PDF generieren
        payload = {
            "document": {
                "payload": {
                    "name": data["name"],
                    "unternehmen": data["unternehmen"],
                    "branche": data["branche"],
                    "zusammenfassung": zusammenfassung
                },
                "template_id": pdfmonkey_template_id,
                "webhook_url": make_webhook_url
            }
        }

        headers = {
            "Authorization": f"Bearer {pdfmonkey_api_key}",
            "Content-Type": "application/json"
        }

        logging.info("📄 Erzeuge PDF über PDFMonkey ...")
        response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers=headers,
            json=payload
        )

        if response.status_code == 201:
            doc = response.json()
            preview_url = doc.get("data", {}).get("attributes", {}).get("download_url", "")
            logging.info(f"🎉 PDF-Vorschau erstellt: {preview_url}")
            return jsonify({"preview": preview_url})
        else:
            logging.error(f"❌ PDFMonkey Fehler: {response.status_code} - {response.text}")
            return jsonify({"error": "Fehler bei PDFMonkey"}), 502

    except Exception as e:
        logging.exception("❌ Unerwarteter Fehler:")
        return jsonify({"error": f"Fehler bei der Auswertung: {str(e)}"}), 500


# Railway-kompatibler Start
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
