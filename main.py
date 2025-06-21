import os
import requests
import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from starlette.responses import JSONResponse

app = FastAPI()

# CORS-Konfiguration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion: spezifische Domains setzen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Umgebungsvariablen laden
openai.api_key = os.getenv("OPENAI_API_KEY")
PDFMONKEY_TEMPLATE_FULL = os.getenv("PDFMONKEY_TEMPLATE_ID")
PDFMONKEY_TEMPLATE_PREVIEW = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

# Validierung der Schlüssel
if not openai.api_key:
    raise RuntimeError("Fehlender OPENAI_API_KEY in Umgebungsvariablen.")

# Eingabemodell definieren
class InputData(BaseModel):
    name: Optional[str]
    unternehmen: Optional[str]
    email: Optional[str]
    branche: Optional[str]
    ist_selbststaendig: Optional[str]
    datenqualitaet: Optional[str]
    datennutzung: Optional[str]
    ist_ki_tools: Optional[str]
    ki_tools: Optional[str]
    ist_ki_doku: Optional[str]
    ziel_ki: Optional[str]
    daten_herausforderung: Optional[str]
    daten_massnahmen_geplant: Optional[str]

# GPT-Analysefunktion
def gpt_analysis(data: InputData) -> str:
    prompt = (
        "Du bist ein KI-Analyst. Analysiere folgende Unternehmensinformationen und gib eine strukturierte Einschätzung:\n"
        f"- Name: {data.name}\n"
        f"- Branche: {data.branche}\n"
        f"- Datenqualität: {data.datenqualitaet}\n"
        f"- Tools im Einsatz: {data.ist_ki_tools}, {data.ki_tools}\n"
        f"- Herausforderung: {data.daten_herausforderung}\n"
        f"- Ziel mit KI: {data.ziel_ki}\n"
        f"- Geplante Maßnahmen: {data.daten_massnahmen_geplant}\n\n"
        "Gib zurück:\n"
        "- Executive Summary\n"
        "- Drei konkrete GPT-Empfehlungen\n"
        "- Compliance-Risiko\n"
        "- Tool-Tipps\n"
        "- Branchenvergleich\n"
        "- Trendreport\n"
        "- Vision"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Fehler bei GPT-Auswertung: {str(e)}"

# PDFMonkey-Aufruf
def send_to_pdfmonkey(template_id, payload):
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
        response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=data)
        print("PDFMonkey Response:", response.status_code, response.text)
        return response
    except Exception as e:
        print("PDFMonkey Fehler:", str(e))
        return None

@app.get("/")
async def root():
    return {"message": "Service läuft"}

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    body = await request.json()
    data = InputData(**body)

    gpt_result = gpt_analysis(data)
    payload = {
        "name": data.name,
        "unternehmen": data.unternehmen,
        "email": data.email,
        "branche": data.branche,
        "gpt_result": gpt_result
    }

    if PDFMONKEY_TEMPLATE_PREVIEW:
        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_PREVIEW, payload)
    if PDFMONKEY_TEMPLATE_FULL:
        send_to_pdfmonkey(PDFMONKEY_TEMPLATE_FULL, payload)

    return JSONResponse({"pdf_status": "generating", "message": "PDF wird generiert", "gpt_preview": gpt_result})