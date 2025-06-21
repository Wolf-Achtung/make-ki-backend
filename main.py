
import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# Konfiguration
PDFMONKEY_API_KEY = os.environ.get("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.environ.get("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.environ.get("PDFMONKEY_TEMPLATE_ID_PREVIEW")
MAKE_WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "KI-Auswertung Backend aktiv"}), 200

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.json

        # GPT-Auswertung generieren
        gpt_input = f"""
        Unternehmensprofil:
        Branche: {data.get("branche")}
        Herausforderungen: {data.get("herausforderung")}
        Ziel: {data.get("ziel")}
        Bestehende Tools: {data.get("tools")}

        Formuliere eine prägnante Executive Summary mit konkreten Empfehlungen, Roadmap und Tooltipps für ein KMU.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": gpt_input}],
            temperature=0.7,
            max_tokens=800
        )

        summary = response.choices[0].message.content.strip()
        data["zusammenfassung"] = summary

        # Vorschau erzeugen
        preview_payload = {
            "document": {
                "template_id": PDFMONKEY_TEMPLATE_ID_PREVIEW,
                "payload": data
            }
        }
        preview_response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps(preview_payload)
        )
        preview_url = preview_response.json()["data"]["attributes"]["download_url"]

        # Vollversion erzeugen (async, für späteren Versand)
        full_payload = {
            "document": {
                "template_id": PDFMONKEY_TEMPLATE_ID,
                "payload": data
            }
        }
        requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps(full_payload)
        )

        # Make-WebHook auslösen
        if MAKE_WEBHOOK_URL:
            requests.post(MAKE_WEBHOOK_URL, json=data)

        return jsonify({"status": "success", "previewURL": preview_url})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Startblock für Railway-kompatiblen Flask-Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
