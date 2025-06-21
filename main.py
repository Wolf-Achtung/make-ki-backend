
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import openai

app = FastAPI()

origins = [
    "https://check.ki-sicherheit.jetzt",
    "https://make.ki-sicherheit.jetzt",
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
    allow_headers=["*"]
)

class InputData(BaseModel):
    name: str
    unternehmen: str
    email: str
    selbststaendig: str
    modul_1_antworten: list
    modul_2_antworten: list
    use_case: str
    geschaeftsbereich: str
    tools: str
    ziel: str
    herausforderung: str
    massnahmen: str
    branche: str

@app.post("/generate-pdf")
async def generate_pdf(data: InputData):
    api_key = os.getenv("PDFMONKEY_API_KEY")
    template_id = os.getenv("PDFMONKEY_TEMPLATE_ID")
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")

    if not api_key or not template_id:
        return {"error": "PDFMonkey keys fehlen."}

    # GPT-Auswertung
    openai.api_key = os.getenv("OPENAI_API_KEY")
    gpt_prompt = f"""Analysiere die Antworten eines KI-Checks.
Name: {data.name}
Unternehmen: {data.unternehmen}
Branche: {data.branche}
Selbstständig: {data.selbststaendig}
Modul 1: {data.modul_1_antworten}
Modul 2: {data.modul_2_antworten}
Use Case: {data.use_case}
Geschäftsbereich: {data.geschaeftsbereich}
Tools: {data.tools}
Ziel: {data.ziel}
Herausforderung: {data.herausforderung}
Maßnahmen: {data.massnahmen}

Bitte gib eine Bewertung, Tipps, Risiken und Empfehlungen für den KI-Einsatz zurück."""

    try:
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist KI-Experte für Unternehmen."},
                {"role": "user", "content": gpt_prompt}
            ],
            max_tokens=800
        )
        gpt_auswertung = gpt_response.choices[0].message.content.strip()
    except Exception as e:
        gpt_auswertung = f"GPT-Analyse fehlgeschlagen: {str(e)}"

    payload = {
        "document": {
            "document_template_id": template_id,
            "payload": {
                "name": data.name,
                "unternehmen": data.unternehmen,
                "email": data.email,
                "branche": data.branche,
                "selbststaendig": data.selbststaendig,
                "modul_1_antworten": data.modul_1_antworten,
                "modul_2_antworten": data.modul_2_antworten,
                "use_case": data.use_case,
                "geschaeftsbereich": data.geschaeftsbereich,
                "tools": data.tools,
                "ziel": data.ziel,
                "herausforderung": data.herausforderung,
                "massnahmen": data.massnahmen,
                "gpt_auswertung": gpt_auswertung
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=payload)

    if response.status_code != 201:
        return {"error": "PDFMonkey Error", "details": response.text}

    pdf_url = response.json()["data"]["attributes"]["download_url"]

    if webhook_url:
        requests.post(webhook_url, json={
            "name": data.name,
            "unternehmen": data.unternehmen,
            "email": data.email,
            "pdf_url": pdf_url
        })

    return {"pdf_url": pdf_url}


@app.get("/")
async def root():
    return {"message": "Service läuft"}
