from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json
import requests
from datetime import date

# Initialisierung
app = Flask(__name__)
CORS(app)
client = OpenAI()

# GPT-Hilfsfunktion

def call_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du bist ein zertifizierter KI-Berater. Antworte strukturiert und geschäftlich, aber klar verständlich."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# GPT-Auswertungsfunktion

def generate_gpt_analysis(data):
    score = int(data.get("score", 0))
    branche = data.get("branche", "Allgemein")
    ziel = data.get("ziel", "nicht angegeben")
    tools = data.get("tools", "keine")
    herausforderung = data.get("herausforderung", "keine")

    executive_prompt = f"""
    Erstelle eine kurze Executive Summary für ein Unternehmen der Branche {branche} mit folgendem Ziel: {ziel}. Der aktuelle Score im KI-Check beträgt {score}/40.
    """

    analyse_prompt = f"""
    Analysiere strategisch, wie ein Unternehmen in der Branche {branche} mit einem Score von {score} beim KI-Einsatz aufgestellt ist. Berücksichtige: Tools = {tools}, Herausforderung = {herausforderung}.
    """

    empfehlungen_prompt = f"""
    Gib drei konkrete Empfehlungen (je mit Titel, Beschreibung, next_step, tool) für den KI-Einsatz in einem Unternehmen der Branche {branche} mit Score {score} und Ziel: {ziel}.
    Antworte im JSON-Format: [{{"titel": ..., "beschreibung": ..., "next_step": ..., "tool": ...}}, ...]
    """

    risikoprofil_prompt = f"""
    Leite ein Risikoprofil für das Unternehmen mit Score {score} ab. Gib Risikoklasse, Begründung und 3 empfohlene Pflichten aus.
    Antworte im JSON-Format: {{"risikoklasse": ..., "begruendung": ..., "pflichten": ["...", "...", "..."]}}
    """

    executive_summary = call_gpt(executive_prompt)
    analyse = call_gpt(analyse_prompt)
    empfehlungen = json.loads(call_gpt(empfehlungen_prompt))
    risikoprofil = json.loads(call_gpt(risikoprofil_prompt))

    result = {
        "name": data.get("name"),
        "email": data.get("email"),
        "unternehmen": data.get("unternehmen"),
        "datum": date.today().isoformat(),
        "score": score,
        "status": "in Prüfung" if score < 25 else "aktiv",
        "bewertung": "kritisch" if score < 20 else "gut" if score > 30 else "ausbaufähig",
        "executive_summary": executive_summary,
        "analyse": analyse,
        "empfehlungen": empfehlungen,
        "risikoprofil": risikoprofil,
        "branche": branche,
        "ziel": ziel
    }

    return result

# Index-Test
@app.route("/")
def index():
    return "✅ KI-Backend aktiv – GPT & PDFMonkey bereit."

# GPT-Hauptanalyse
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    return jsonify(generate_gpt_analysis(data))

# PDF-Erzeugung
@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    print("PDF-Daten empfangen:", data)

    api_key = os.environ.get("PDFMONKEY_API_KEY")
    template_id = os.environ.get("PDFMONKEY_TEMPLATE_ID")

    if not api_key or not template_id:
        return jsonify({"error": "PDFMonkey-Konfiguration fehlt"}), 500

    try:
        response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "document": {
                    "document_template_id": template_id,
                    "payload": data,
                    "publish": True
                }
            }
        )

        if response.status_code != 201:
            print("❌ PDFMonkey-Fehler:", response.text)
            return jsonify({"error": "PDF konnte nicht erstellt werden"}), 500

        pdf_url = response.json().get("document", {}).get("download_url")
        return jsonify({"pdf_url": pdf_url})

    except Exception as e:
        print("❌ Ausnahmefehler:", e)
        return jsonify({"error": "Serverfehler"}), 500

# Startpunkt
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
