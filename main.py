
import os
import requests
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY


def send_to_pdfmonkey(template_id, payload):
    print(f"[PDFMONKEY] Sending document to template {template_id}...")
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
    try:
        res = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=data)
        print(f"[PDFMONKEY] Status: {res.status_code}, Response: {res.text}")
        res.raise_for_status()
    except Exception as e:
        print(f"[ERROR] PDFMonkey request failed: {e}")


@app.route("/")
def index():
    return "Service läuft!"


@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        body = request.json
        print("[BACKEND] Request empfangen:", body)

        name = body.get("name")
        email = body.get("email")
        data = body.get("data", {})

        prompt = f"""
Du bist ein KI-Analyst. Analysiere die folgenden Informationen und gib eine strukturierte Empfehlung.
Daten: {data}
"""

        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        gpt_result = gpt_response.choices[0].message.content.strip()
        print("[GPT] Ergebnis:", gpt_result)

        payload = {
            "name": name,
            "email": email,
            "unternehmen": body.get("unternehmen"),
            "branche": body.get("branche"),
            "antworten": data,
            "gpt": gpt_result
        }

        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_ID_PREVIEW, payload)
        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_ID, payload)

        if MAKE_WEBHOOK_URL:
            print("[MAKE] Webhook wird gesendet...")
            try:
                res = requests.post(MAKE_WEBHOOK_URL, json=payload)
                print(f"[MAKE] Status: {res.status_code}, Response: {res.text}")
                res.raise_for_status()
            except Exception as e:
                print(f"[ERROR] Make request failed: {e}")

        return jsonify({"message": "Auswertung erfolgreich generiert."})

    except Exception as e:
        print(f"[ERROR] Allgemeiner Fehler: {e}")
        return jsonify({"error": str(e)}), 500
