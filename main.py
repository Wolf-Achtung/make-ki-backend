import os
import requests
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

# Flask Setup
app = Flask(__name__)
CORS(app)

# ENV-Werte
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY


def run_gpt_analysis(user_payload):
    try:
        prompt = f"""
Analysiere die folgenden Unternehmensdaten und gib eine strukturierte, verständliche, praxisnahe Auswertung:
{user_payload}
        """
        print("🤖 GPT-Auswertung wird gestartet …")
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
    try:
        print(f"📄 PDF-Erstellung gestartet ({'Vorschau' if is_preview else 'Vollversion'}) …")
        response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "document": {
                    "document_template_id": template_id,
                    "payload": payload
                }
            }
        )
        response.raise_for_status()
        pdf_url = response.json()["data"]["download_url"]
        print(f"✅ PDF generiert: {pdf_url}")
        return pdf_url
    except Exception as e:
        print(f"❌ PDFMonkey-Fehler: {str(e)}")
        return None


@app.route("/generate-pdf", methods=["POST"])
def generate():
    try:
        user_data = request.json
        print("📥 Formulardaten empfangen:", user_data)

        gpt_result = run_gpt_analysis(user_data)

        # Zusammensetzen des Payloads für das PDF
        payload = {
            **user_data,
            "executive_summary": gpt_result,
            "analyse": "Vertiefende Analyse folgt basierend auf Ihren Antworten …",
            "empfehlung1": {
                "titel": "Automatisierung starten",
                "beschreibung": "Beginnen Sie mit einfachen Text-KI-Anwendungen.",
                "next_step": "Tool auswählen und testen",
                "tool": "ChatGPT"
            },
            "empfehlung2": {
                "titel": "Team befähigen",
                "beschreibung": "Schulen Sie Ihr Team für mehr KI-Kompetenz.",
                "next_step": "Weiterbildung starten",
                "tool": "KI-Campus"
            },
            "empfehlung3": {
                "titel": "Förderung nutzen",
                "beschreibung": "Beantragen Sie gezielte Unterstützung.",
                "next_step": "Programm evaluieren",
                "tool": "go-digital"
            },
            "roadmap": {
                "kurzfristig": "Testphase mit Prototypen",
                "mittelfristig": "Prozesse mit KI stützen",
                "langfristig": "KI als strategisches Asset"
            },
            "ressourcen": "Freie Tools, Beraternetzwerke",
            "foerdertipps": [
                {"programm": "go-digital", "nutzen": "Beratung", "zielgruppe": "KMU"},
                {"programm": "Digital Jetzt", "nutzen": "Investitionen", "zielgruppe": "mittelständische Unternehmen"}
            ],
            "risikoprofil": {
                "risikoklasse": "mittel",
                "begruendung": "Teilautomatisierte Entscheidungsprozesse",
                "pflichten": ["DSGVO-Konformität", "Transparenz", "Schulung"]
            },
            "tooltipps": [
                {"name": "ChatGPT", "einsatz": "Texterstellung", "warum": "Schnell & einfach"},
                {"name": "Make.com", "einsatz": "Automatisierung", "warum": "No-Code"}
            ],
            "branchenvergleich": "Sie liegen im oberen Drittel Ihrer Branche.",
            "trendreport": "Multimodale KI auf dem Vormarsch.",
            "vision": "Sie agieren KI-gestützt und zukunftsweisend."
        }

        # PDF generieren
        preview_url = generate_pdf(PDFMONKEY_TEMPLATE_ID_PREVIEW, payload, is_preview=True)
        generate_pdf(PDFMONKEY_TEMPLATE_ID, payload)

        # Webhook (Make) optional senden
        if WEBHOOK_URL:
            try:
                requests.post(WEBHOOK_URL, json=payload)
                print("📬 Webhook an Make gesendet.")
            except Exception as e:
                print(f"⚠️ Webhook-Fehler: {str(e)}")

        return jsonify({"preview": preview_url})

    except Exception as e:
        print(f"❌ Allgemeiner Fehler: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Railway-kompatibler Start
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
