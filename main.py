
import os
import openai
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")

openai.api_key = OPENAI_API_KEY


@app.route("/")
def index():
    return jsonify({"message": "Service läuft"})


def run_gpt_analysis(data):
    prompt = f"""
    Du bist ein KI-Analyst. Analysiere folgende Unternehmensinformationen und gib eine strukturierte Einschätzung:
    - Unternehmen: {data.get("name_unternehmen")}
    - Branche: {data.get("branche")}
    - Teamgröße: {data.get("team")}
    - Ziel KI: {data.get("ziel_ki")}
    - KI-Verständnis: {data.get("tech_verstaendnis")}
    - Datenlage: {data.get("datenlage")}
    - Datenarten: {data.get("datenarten")}
    - Datenherausforderung: {data.get("daten_herausforderung")}
    - Ziel mit KI: {data.get("ziel_mit_ki")}
    - Maßnahmen: {data.get("massnahmen_geplant")}

    Gib zurück:
    - Executive Summary
    - Drei konkrete GPT-Empfehlungen (Titel, Beschreibung, nächster Schritt, Tool)
    - Compliance-Checkliste (Risikostufe, Begründung, Pflichten)
    - Tool-Tipps (2–3 Tools + Nutzen)
    - GPT-Bewertung (1–10 Prognose)
    - Branchenvergleich
    - Vision
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Fehler bei GPT: {str(e)}"


def send_to_pdfmonkey(template_id, payload):
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
    response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=data)
    return response.status_code


@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        body = request.get_json()
        gpt_result = run_gpt_analysis(body)

        payload = {
            "name": body.get("name_unternehmen"),
            "email": body.get("email"),
            "branche": body.get("branche"),
            "team": body.get("team"),
            "ziel_ki": body.get("ziel_ki"),
            "gpt_result": gpt_result
        }

        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_ID_PREVIEW, payload)
        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_ID, payload)

        return jsonify({"message": "PDF wird generiert"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
