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
                {"role": "system", "content": "Du bist ein zertifizierter KI-Berater. Antworte strukturiert, aber klar verständlich. Antworte auf Deutsch."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        if expect_json:
            return json.loads(content)
        return content
    except json.JSONDecodeError as e:
        print("❌ JSON-Parsing-Fehler:", e)
        return [] if 'empfehlungen' in prompt else {}
    except Exception as e:
        print("❌ GPT-Fehler:", e)
        return "Fehler bei der GPT-Auswertung."

def generate_gpt_analysis(data):
    score = int(data.get("score", 0))
    branche = data.get("branche", "Allgemein")
    ziel = data.get("ziel", "nicht angegeben")
    tools = data.get("tools", "keine")
    herausforderung = data.get("herausforderung", "keine")

    prompts = {
        "executive_summary": f"Erstelle eine kurze Executive Summary für ein Unternehmen der Branche {branche} mit dem Ziel: {ziel}. Der aktuelle KI-Check-Score beträgt {score}/40.",
        "analyse": f"Analysiere, wie ein Unternehmen der Branche {branche} mit einem Score von {score} beim KI-Einsatz aktuell aufgestellt ist. Berücksichtige: Tools = {tools}, Herausforderung = {herausforderung}.",
        "empfehlungen": f"Gib drei konkrete Empfehlungen (je mit Titel, Beschreibung, next_step, tool) für den KI-Einsatz in einem Unternehmen der Branche {branche} mit Score {score} und Ziel: {ziel}. Antworte im JSON-Format.",
        "risikoprofil": f"Leite ein Risikoprofil ab (Score: {score}). Gib Risikoklasse, Begründung und 3 empfohlene Pflichten laut AI Act. Antworte im JSON-Format.",
        "branchenvergleich": f"Wie schneidet ein Unternehmen der Branche {branche} mit Score {score} im Vergleich zum Branchendurchschnitt ab? Gib Bewertung, Abweichung und Einschätzung.",
        "trendreport": f"Welche 3 relevanten KI-Trends betreffen aktuell besonders die Branche {branche}? Gib Titel und Beschreibung. Format: JSON.",
        "toolkompass": f"Welche 3 konkreten Tools oder Plattformen könnten für das Ziel '{ziel}' in der Branche {branche} hilfreich sein? Beschreibe kurz Nutzen & Einsatzbereich. Format: JSON.",
        "foerderung": f"Welche 2–3 aktuellen Förderprogramme auf EU- oder Bundesebene könnten für ein KMU mit Score {score} in der Branche {branche} relevant sein? Kurzbeschreibung + ggf. Link.",
        "ressourcen": f"Empfiehl 3 hochwertige Ressourcen (Weiterbildung, Leitfäden oder Kurse) für Unternehmen der Branche {branche}, die sich mit KI beschäftigen wollen.",
        "zukunft": f"Wie könnte sich der KI-Reifegrad dieses Unternehmens mit Ziel '{ziel}' in 12–24 Monaten weiterentwickeln – abhängig vom aktuellen Score {score}?",
        "vision": f"Gib eine innovative, visionäre Idee (Gamechanger), wie ein Unternehmen der Branche {branche} KI auf neuartige Weise nutzen könnte."
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
        "branchenvergleich": call_gpt(prompts["branchenvergleich"]),
        "trendreport": call_gpt(prompts["trendreport"], expect_json=True),
        "toolkompass": call_gpt(prompts["toolkompass"], expect_json=True),
        "foerderung": call_gpt(prompts["foerderung"]),
        "ressourcen": call_gpt(prompts["ressourcen"]),
        "zukunft": call_gpt(prompts["zukunft"]),
        "vision": call_gpt(prompts["vision"])
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
