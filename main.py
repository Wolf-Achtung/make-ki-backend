import os
import requests
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# API-Keys & Template-IDs aus ENV
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY


def run_gpt_analysis(user_payload):
    try:
        prompt = f"""
Analysiere die folgenden Unternehmensdaten und gib Empfehlungen, Roadmap, Risiken, Fördertipps und Tool-Einsatz zurück:
{user_payload}
        """

        print("📡 GPT wird aufgerufen …")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein KI-Berater für Unternehmen."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        print("✅ GPT-Antwort empfangen.")
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ GPT-Fehler: {str(e)}")
        return "Analyse konnte nicht durchgeführt werden."


def generate_pdf(template_id, payload, is_preview=False):
    url = "https://api.pdfmonkey.io/api/v1/documents"
    headers = {
        "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "document": {
            "document_template_id": template_id,
            "payload": payload
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        document = response.json().get("data")
        pdf_url = document.get("download_url")

        print(f"📄 PDF ({'Vorschau' if is_preview else 'Vollversion'}) erstellt: {pdf_url}")
        return pdf_url

    except Exception as e:
        print(f"❌ PDFMonkey-Fehler: {str(e)}")
        return None


@app.route("/generate-pdf", methods=["POST"])
def generate():
    try:
        user_data = request.json
        print("📥 Eingehende Daten:", user_data)

        # GPT-Auswertung
        gpt_output = run_gpt_analysis(user_data)

        # Dummystruktur + GPT-Ergebnisse integrieren
        payload = {
            **user_data,
            "executive_summary": gpt_output,
            "analyse": "Analyse folgt...",
            "empfehlung1": {
                "titel": "Automatisierung starten",
                "beschreibung": "Beginnen Sie mit einem KI-Tool für Texterstellung.",
                "next_step": "Tool auswählen und testen",
                "tool": "ChatGPT"
            },
            "empfehlung2": {
                "titel": "Prozesse analysieren",
                "beschreibung": "KI-Potenziale im Rechnungswesen analysieren.",
                "next_step": "Workflows mappen",
                "tool": "Make.com"
            },
            "empfehlung3": {
                "titel": "Weiterbildung starten",
                "beschreibung": "Ihr Team fit für KI machen.",
                "next_step": "Online-Kurs buchen",
                "tool": "ki-campus.org"
            },
            "roadmap": {
                "kurzfristig": "Einstieg durch einfache KI-Tools",
                "mittelfristig": "Integration in Kernprozesse",
                "langfristig": "KI-gestützte Entscheidungen"
            },
            "ressourcen": "Open Source Tools, Förderprogramme",
            "foerdertipps": [
                {
                    "programm": "go-digital",
                    "nutzen": "Beratung und Umsetzung",
                    "zielgruppe": "KMU"
                },
                {
                    "programm": "Digital Jetzt",
                    "nutzen": "Investitionen in KI",
                    "zielgruppe": "mittelständische Unternehmen"
                }
            ],
            "risikoprofil": {
                "risikoklasse": "mittel",
                "begruendung": "Teilautomatisierte Kundendatenverarbeitung",
                "pflichten": [
                    "KI-Kennzeichnung",
                    "Datenschutzprüfung",
                    "Mitarbeiterschulung"
                ]
            },
            "tooltipps": [
                {"name": "ChatGPT", "einsatz": "Texte & E-Mails", "warum": "effizient & schnell"},
                {"name": "Fireflies", "einsatz": "Meeting-Protokolle", "warum": "automatisch & DSGVO-freundlich"}
            ],
            "branchenvergleich": "Ihr KI-Niveau liegt über dem Branchendurchschnitt.",
            "trendreport": "Multimodale KI wird in Ihrer Branche wichtig.",
            "vision": "Ihr Unternehmen wird KI-getrieben innovativ agieren."
        }

        # Vorschau erstellen
        preview_link = generate_pdf(PDFMONKEY_TEMPLATE_ID_PREVIEW, payload, is_preview=True)

        # Vollversion vorbereiten
        generate_pdf(PDFMONKEY_TEMPLATE_ID, payload)

        # Optional: Make-WebHook senden
        if WEBHOOK_URL:
            try:
                requests.post(WEBHOOK_URL, json=payload)
                print("📬 Webhook an Make gesendet.")
            except Exception as e:
                print(f"⚠️ Webhook-Fehler: {str(e)}")

        # Rückgabe für Frontend
        return jsonify({"preview": preview_link})

    except Exception as e:
        print(f"❌ Allgemeiner Fehler: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Für Railway / Docker
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
