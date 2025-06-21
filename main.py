import os
import requests
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

def generate_gpt_analysis(form_data):
    prompt = f"""
Du bist ein KI-Experte. Analysiere auf Basis der folgenden Angaben das KI-Potenzial und gib Empfehlungen für ein kleines oder mittleres Unternehmen:

Name: {form_data.get("name")}
Unternehmen: {form_data.get("unternehmen")}
Branche: {form_data.get("branche")}
Selbstständig: {form_data.get("ist_selbststaendig")}
Ziel mit KI: {form_data.get("ziel_ki")}
Technisches Verständnis: {form_data.get("tech_verstaendnis")}
Datenqualität: {form_data.get("datenqualitaet")}
Verwendet bereits KI-Tools: {form_data.get("verwendet_ki_tools")}
Risiken bekannt: {form_data.get("kennt_risiken")}
Dokumentation vorhanden: {form_data.get("hat_ki_dokumentation")}
Konkrete Maßnahmen geplant: {form_data.get("massnahmen_geplant")}
Tools im Einsatz: {form_data.get("tools")}
Größte Herausforderung: {form_data.get("daten_herausforderung")}
Geschäftsbereich: {form_data.get("geschaeftsbereich")}
Anwendungsfall: {form_data.get("anwendungsfall")}

Strukturiere deine Antwort bitte in folgende Abschnitte:
- Executive Summary
- Analyse
- Drei Empfehlungen mit Titel, Beschreibung, Tool, Next Step
- Compliance-Risiko (mit Risikoklasse, Begründung, Pflichten)
- Roadmap (kurz-, mittel-, langfristig)
- Tool-Tipps
- Fördertipps
- Branchenvergleich
- Trendreport
- Vision
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1500
    )

    return response["choices"][0]["message"]["content"]

@app.route("/analyze", methods=["POST"])
def analyze():
    form_data = request.json
    gpt_output = generate_gpt_analysis(form_data)

    result = {
        "name": form_data.get("name"),
        "unternehmen": form_data.get("unternehmen"),
        "email": form_data.get("email"),
        "branche": form_data.get("branche"),
        "analyse": gpt_output,
        "template_variant": form_data.get("template_variant", "preview")
    }

    headers = {
        "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
        "Content-Type": "application/json"
    }

    document_payload = {
        "document": {
            "template_id": PDFMONKEY_TEMPLATE_ID_PREVIEW if result["template_variant"] == "preview" else PDFMONKEY_TEMPLATE_ID,
            "payload": result
        }
    }

    pdf_response = requests.post("https://api.pdfmonkey.io/api/v1/documents", json=document_payload, headers=headers)

    if MAKE_WEBHOOK_URL:
        try:
            requests.post(MAKE_WEBHOOK_URL, json=result, timeout=4)
        except Exception:
            pass

    return jsonify({"message": "Analyse abgeschlossen", "pdf_response": pdf_response.status_code})