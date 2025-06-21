import os
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests

app = Flask(__name__)
CORS(app)

# API-Keys aus Umgebungsvariablen
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# GPT-Antwort generieren
def generate_gpt_summary(data):
    prompt = f"""
    Du bist ein KI-Analyst. Analysiere folgende Unternehmensinformationen und gib eine strukturierte Einschätzung zurück:

    Unternehmen: {data.get("unternehmen")}
    Branche: {data.get("branche")}
    Tech-Verständnis: {data.get("tech_verstaendnis")}
    Ziel mit KI: {data.get("ziel_ki_kurzfristig")}
    Herausforderung: {data.get("data_herausforderung")}
    Maßnahmen: {data.get("massnahmen_geplant")}

    Gib ein Executive Summary zurück (2–4 Sätze) auf Deutsch.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        api_key=OPENAI_API_KEY
    )
    return response.choices[0].message["content"]

# PDFMonkey-API-Aufruf
def send_to_pdfmonkey(template_id, payload):
    headers = {
        "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "document": {
            "template_id": template_id,
            "payload": payload
        }
    }
    response = requests.post("https://api.pdfmonkey.io/api/v1/documents", json=body, headers=headers)
    if response.ok:
        return response.json()["data"]["attributes"]["download_url"]
    else:
        raise Exception(f"PDFMonkey-Fehler: {response.status_code} – {response.text}")

# Hauptroute
@app.route("/generate-pdf", methods=["POST", "OPTIONS"])
def generate_pdf():
    if request.method == "OPTIONS":
        # Handle CORS preflight
        return jsonify({"message": "CORS preflight OK"}), 200

    try:
        data = request.get_json()
        print("Empfangene Daten:", data)

        zusammenfassung = generate_gpt_summary(data)
        payload = {
            "name": data.get("name"),
            "unternehmen": data.get("unternehmen"),
            "branche": data.get("branche"),
            "zusammenfassung": zusammenfassung
        }

        preview_url = send_to_pdfmonkey(PDFMONKEY_TEMPLATE_ID_PREVIEW, payload)
        full_url = send_to_pdfmonkey(PDFMONKEY_TEMPLATE_ID, payload)

        # Optional: Trigger Webhook (Make/Integromat)
        if MAKE_WEBHOOK_URL:
            requests.post(MAKE_WEBHOOK_URL, json=payload)

        return jsonify({
            "preview": preview_url,
            "full": full_url
        })

    except Exception as e:
        print("Fehler beim Generieren:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
