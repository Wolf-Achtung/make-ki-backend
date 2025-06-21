
import os
import openai
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from starlette.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Empfehlung: spezifische Domains in Produktion
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")
PDFMONKEY_TEMPLATE_FULL = os.getenv("PDFMONKEY_TEMPLATE_FULL")
PDFMONKEY_TEMPLATE_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_PREVIEW")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

class InputData(BaseModel):
    name: str
    unternehmen: Optional[str]
    email: str
    branche: Optional[str]
    digital_level: Optional[str]
    datenqualitaet: Optional[str]
    ziel_ki: Optional[str]
    tools_im_einsatz: Optional[str]
    herausforderung: Optional[str]
    ziel_ki_kurzfristig: Optional[str]
    massnahmen_geplant: Optional[str]

def gpt_analysis(data: InputData):
    prompt = f'''
Du bist ein KI-Analyst. Analysiere folgende Unternehmensinformationen und gib eine strukturierte Einschätzung:
Name: {data.name}
Branche: {data.branche}
Digitalisierungsgrad: {data.digital_level}
Datenqualität: {data.datenqualitaet}
Geplanter KI-Einsatz: {data.ziel_ki}
Tools im Einsatz: {data.tools_im_einsatz}
Herausforderung: {data.herausforderung}
Ziel mit KI: {data.ziel_ki_kurzfristig}
Geplante Maßnahmen: {data.massnahmen_geplant}

Gib zurück:
- Executive Summary
- Drei konkrete Empfehlungen (Titel, Beschreibung, nächster Schritt, Tool)
- Compliance-Risiko (Risikostufe, Begründung, Pflichten)
- Tooltipps (2-3 Tools + Nutzen)
- Fördertipps (1-2 Programme)
- Branchenvergleich
- Trendreport
- Vision
'''
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
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
async def root():
    return {"message": "Service läuft"}

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    try:
        body = await request.json()
        data = InputData(**body)
        gpt_result = gpt_analysis(data)
        payload = {
            "name": data.name,
            "unternehmen": data.unternehmen,
            "email": data.email,
            "branche": data.branche,
            "zusammenfassung": gpt_result
        }

        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_PREVIEW, payload)
        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_FULL, payload)

        if MAKE_WEBHOOK_URL:
            try:
                requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=5)
            except:
                pass

        return JSONResponse(content={"message": "PDFs generiert"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
