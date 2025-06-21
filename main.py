import os
import requests
import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")
PDFMONKEY_TEMPLATE_ID = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_ID_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

class InputData(BaseModel):
    name: str
    unternehmen: Optional[str]
    email: str
    branche: Optional[str]
    ist_selbststaendig: Optional[str]
    ziel_ki: Optional[str]
    tech_verstaendnis: Optional[str]
    datenqualitaet: Optional[str]
    hat_daten: Optional[str]
    verwendet_ki_tools: Optional[str]
    kennt_risiken: Optional[str]
    hat_ki_dokumentation: Optional[str]
    anwendungsfall: Optional[str]
    geschaeftsbereich: Optional[str]
    tools: Optional[str]
    ki_kurzfrist: Optional[str]
    daten_herausforderung: Optional[str]
    massnahmen_geplant: Optional[str]
    template_variant: Optional[str] = "preview"

def gpt_analysis(data: InputData) -> str:
    prompt = f"""
Du bist ein KI-Analyst. Analysiere folgende Unternehmensinformationen und gib eine strukturierte Einschätzung:
Name: {data.name}
Branche: {data.branche}
Ziel mit KI: {data.ziel_ki}
Technisches Verständnis: {data.tech_verstaendnis}
Datenqualität: {data.datenqualitaet}
Hat Daten: {data.hat_daten}
Verwendet KI-Tools: {data.verwendet_ki_tools}
Risiken bekannt: {data.kennt_risiken}
Dokumentation: {data.hat_ki_dokumentation}
Anwendungsfall: {data.anwendungsfall}
Geschäftsbereich: {data.geschaeftsbereich}
Tools: {data.tools}
Ziel mit KI (kurzfristig): {data.ki_kurzfrist}
Herausforderung: {data.daten_herausforderung}
Geplante Maßnahmen: {data.massnahmen_geplant}

Gib zurück:
- Executive Summary
- Drei konkrete GPT-Empfehlungen
- Compliance-Risiko
- Tool-Tipps
- Prioritäten
- Branchenvergleich
- Trendreport
- Vision
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1200
    )
    return response["choices"][0]["message"]["content"]

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
    return requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=data)

@app.get("/")
def root():
    return {"message": "Service läuft"}

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    data = await request.json()
    input_data = InputData(**data)
    gpt_result = gpt_analysis(input_data)
    payload = {
        "name": input_data.name,
        "unternehmen": input_data.unternehmen,
        "email": input_data.email,
        "branche": input_data.branche,
        "analyse": gpt_result
    }
    template_id = PDFMONKEY_TEMPLATE_ID_PREVIEW if input_data.template_variant == "preview" else PDFMONKEY_TEMPLATE_ID
    response = send_to_pdfmonkey(template_id, payload)
    return {"pdf_url": response.json()["data"]["attributes"]["download_url"]}