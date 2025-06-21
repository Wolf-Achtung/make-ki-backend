
import os
import requests
import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# CORS-Konfiguration
origins = [
    "https://make.ki-sicherheit.jetzt",
    "https://check.ki-sicherheit.jetzt",
    "https://agent.ki-sicherheit.jetzt",
    "https://ki-sicherheit.jetzt",
    "https://ki-sicherheit.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionnaireData(BaseModel):
    name: str
    unternehmen: str
    email: str
    selbststaendig: str
    einsatzgebiet: str
    ziel: str
    kenntnisstand: str
    datenqualitaet: str
    datenverarbeitung: str
    tools: str
    dsgvo_ki: str
    risikobewertung: str
    dokumentation: str
    usecase_idee: str
    bereich: str
    tools_einsatz: str
    kurzziel: str
    hurdle: str
    massnahmen: str

@app.post("/generate-pdf")
async def generate_pdf(data: QuestionnaireData):
    try:
        # GPT-Zusammenfassung
        openai.api_key = os.getenv("OPENAI_API_KEY")
        prompt = (
            f"Erstelle eine individuelle, fachlich fundierte, kreative und praxisnahe Einschätzung für folgendes Unternehmen:\n"
            f"Name: {data.name}, Firma: {data.unternehmen}, Ziel: {data.ziel}, Tools: {data.tools_einsatz}, Hürde: {data.hurdle}\n"
            f"Gib konkrete Tipps und Empfehlungen zur rechtssicheren, effektiven Einführung und Nutzung von KI für Selbstständige oder kleine Unternehmen."
        )
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        gpt_text = gpt_response.choices[0].message.content.strip()

        # PDFMonkey
        pdf_api_key = os.getenv("PDFMONKEY_API_KEY")
        template_id = os.getenv("PDFMONKEY_TEMPLATE_ID")
        pdf_response = requests.post(
            "https://api.pdfmonkey.io/api/v1/documents",
            headers={
                "Authorization": f"Bearer {pdf_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "document": {
                    "document_template_id": template_id,
                    "payload": {
                        "name": data.name,
                        "unternehmen": data.unternehmen,
                        "email": data.email,
                        "einsatzgebiet": data.einsatzgebiet,
                        "ziel": data.ziel,
                        "tools_einsatz": data.tools_einsatz,
                        "hurdle": data.hurdle,
                        "gpt_text": gpt_text
                    }
                }
            }
        )

        if pdf_response.status_code != 201:
            return {"error": f"PDFMonkey Error: {pdf_response.text}"}

        pdf_url = pdf_response.json()["data"]["attributes"]["download_url"]

        # Make.com Webhook
        webhook_url = os.getenv("MAKE_WEBHOOK_URL")
        requests.post(webhook_url, json={**data.dict(), "pdf_url": pdf_url, "gpt_summary": gpt_text})

        return {"pdf_url": pdf_url}

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    return {"message": "KI-Auswertung Backend läuft."}
