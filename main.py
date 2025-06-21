
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.get_json()

        # GPT-Analyse (optional)
        gpt_api_key = os.getenv("OPENAI_API_KEY")
        if gpt_api_key:
            openai.api_key = gpt_api_key
            gpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Analysiere die übermittelten Unternehmensdaten aus einem Fragebogen zur KI-Readiness, KI-Compliance und Anwendungsfällen. Formuliere eine verständliche und praxisnahe Zusammenfassung mit Handlungsempfehlungen, Tools, Fördermöglichkeiten und Risiken."
                    },
                    {
                        "role": "user",
                        "content": str(data)
                    }
                ]
            )
            analysis = gpt_response.choices[0].message["content"]
        else:
            analysis = "Keine GPT-Analyse durchgeführt (API-Key fehlt)."

        api_key = os.getenv("PDFMONKEY_API_KEY")
        template_id = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW") if data.get("template_variant") == "preview" else os.getenv("PDFMONKEY_TEMPLATE_ID")
        if not api_key or not template_id:
            return jsonify({"error": "PDFMonkey keys fehlen."}), 500

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "document": {
                "document_template_id": template_id,
                "payload": {
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "unternehmen": data.get("unternehmen"),
                    "ziel": data.get("ziel"),
                    "branche": data.get("branche"),
                    "antworten": data,
                    "analyse": analysis
                }
            }
        }

        response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=payload)
        if response.status_code != 201:
            return jsonify({"error": "PDFMonkey Error", "details": response.text}), 500

        pdf_url = response.json()["data"]["attributes"]["download_url"]

        # Optionale Weiterleitung an Make
        make_url = os.getenv("MAKE_WEBHOOK_URL")
        if make_url:
            try:
                requests.post(make_url, json={"pdf_url": pdf_url, "email": data.get("email")})
            except Exception as err:
                print(f"Fehler beim Make-Webhook: {err}")

        return jsonify({"pdf_url": pdf_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Service läuft"})
