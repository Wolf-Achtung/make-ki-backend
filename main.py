from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json
import requests
from datetime import date

app = Flask(__name__)
CORS(app)
client = OpenAI()

def call_gpt(prompt, expect_json=False):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du bist ein zertifizierter KI-Berater. Antworte strukturiert, konkret und auf Deutsch."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content) if expect_json else content
    except json.JSONDecodeError:
        return [] if expect_json else "Fehler beim Parsen der GPT-Antwort."
    except Exception as e:
        print("❌ GPT-Fehler:", e)
        return [] if expect_json else "Fehler bei der GPT-Auswertung."

def generate_gpt_analysis(data):
    score = int(data.get("score", 0))
    branche = data.get("branche", "Allgemein")
    ziel = data.get("ziel", "nicht angegeben")
    tools = data.get("tools", "keine")
    herausforderung = data.get("herausforderung", "keine")

    prompts = {
        "executive_summary": f"Fasse die KI-Situation eines Unternehmens der Branche {branche} mit dem Ziel '{ziel}' und Score {score}/40 zusammen.",
        "analyse": f"Analysiere die aktuelle KI-Nutzung im Unternehmen ({branche}, Score {score}). Tools: {tools}, Herausforderung: {herausforderung}.",
        "empfehlungen": f"Gib 3 Empfehlungen für den KI-Einsatz (JSON mit titel, beschreibung, next_step, tool). Ziel: {ziel}, Score: {score}, Branche: {branche}.",
        "risikoprofil": f"Erstelle ein Risikoprofil inkl. risikoklasse, begruendung, pflichten (JSON) nach EU AI Act für Score {score}.",
        "compliance": f"Welche DSGVO- und EU-AI-Act-Pflichten gelten für ein Unternehmen mit Score {score} in der Branche {branche}? Nenne konkrete Sanktionen.",
        "branchenvergleich": f"Wie schneidet ein Unternehmen der Branche {branche} mit Score {score} im Branchendurchschnitt ab?",
        "trendreport": f"Nenne 3 relevante KI-Trends für {branche} als JSON mit titel, beschreibung, link.",
        "toolkompass": f"Empfiehl 3 Tools für Ziel '{ziel}' in der Branche {branche} als JSON mit titel, beschreibung, link.",
        "foerderung": f"Nenne 2-3 passende Förderprogramme (EU/DE) für Score {score}, Branche {branche}.",
        "ressourcen": f"Empfiehl 3 Ressourcen (Kurse, Leitfäden) für Einsteiger und Entscheider im Bereich KI für {branche}.",
        "zukunft": f"Wie könnte sich das Unternehmen in 12–24 Monaten weiterentwickeln, wenn es gezielt in KI investiert?",
        "vision": f"Gib eine visionäre Idee für KI-Nutzung in der Branche {branche}, die das Unternehmen transformieren könnte.",
        "beratungsempfehlung": f"Warum sollte das Unternehmen ({branche}, Ziel: {ziel}, Score: {score}) jetzt ein Beratungsgespräch starten?"
    }

    result = {
        "name": data.get("name"),
        "email": data.get("email"),
        "unternehmen": data.get("unternehmen"),
        "datum": date.today().isoformat(),
        "score": score,
        "status": "in Prüfung" if score < 25 else "aktiv",
        "bewertung": "kritisch" if score < 20 else "gut" if score > 30 else "ausbaufähig",
        "branche": branche,
        "ziel": ziel,
        "executive_summary": call_gpt(prompts["executive_summary"]),
        "analyse": call_gpt(prompts["analyse"]),
        "empfehlungen": call_gpt(prompts["empfehlungen"], expect_json=True),
        "risikoprofil": call_gpt(prompts["risikoprofil"], expect_json=True),
        "compliance": call_gpt(prompts["compliance"]),
        "branchenvergleich": call_gpt(prompts["branchenvergleich"]),
        "trendreport": call_gpt(prompts["trendreport"], expect_json=True),
        "toolkompass": call_gpt(prompts["toolkompass"], expect_json=True),
        "foerderung": call_gpt(prompts["foerderung"]),
        "ressourcen": call_gpt(prompts["ressourcen"]),
        "zukunft": call_gpt(prompts["zukunft"]),
        "vision": call_gpt(prompts["vision"]),
        "beratungsempfehlung": call_gpt(prompts["beratungsempfehlung"])
    }

    return result

@app.route("/")
def index():
    return "✅ KI-Backend aktiv – GPT & PDFMonkey bereit."

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    return jsonify(generate_gpt_analysis(data))

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    print("PDF-Daten empfangen:", data)

    api_key = os.environ.get("PDFMONKEY_API_KEY")
template_id = os.environ.get("PDFMONKEY_TEMPLATE_ID_PREVIEW") if data.get("template_variant") == "preview" else os.environ.get("PDFMONKEY_TEMPLATE_ID")

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
