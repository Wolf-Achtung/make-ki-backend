
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import openai

app = FastAPI()

# CORS
origins = [
    "https://check.ki-sicherheit.jetzt",
    "https://make.ki-sicherheit.jetzt",
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

class InputData(BaseModel):
    name: str
    unternehmen: Optional[str]
    email: str
    selbstständig: str
    antworten: dict
    template_variant: Optional[str] = "full"

@app.post("/generate-pdf")
async def generate_pdf(data: InputData):
    api_key = os.getenv("PDFMONKEY_API_KEY")
    template_id = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW") if data.template_variant == "preview" else os.getenv("PDFMONKEY_TEMPLATE_ID")
    webhook_url = os.getenv("MAKE_WEBHOOK_URL")
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or not template_id or not webhook_url or not openai.api_key:
        return {"error": "Fehlende Umgebungsvariablen"}

    # Analyse mit GPT
    messages = [
        {"role": "system", "content": "Du bist ein KI-Berater, der Unternehmen bei der Einführung von KI unterstützt."},
        {"role": "user", "content": f"Bitte analysiere folgende Antworten: {data.antworten} und gib Verbesserungsvorschläge, Tools und Tipps zur KI-Integration."}
    ]

    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    gpt_summary = gpt_response.choices[0].message.content.strip()

    # PDFMonkey Payload
    payload = {
        "document": {
            "document_template_id": template_id,
            "payload": {
                "name": data.name,
                "unternehmen": data.unternehmen or "",
                "email": data.email,
                "gpt_summary": gpt_summary,
                **data.antworten
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    pdf_response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=payload)
    if pdf_response.status_code != 201:
        return {"error": "PDFMonkey Error", "details": pdf_response.text}

    pdf_url = pdf_response.json()["data"]["attributes"]["download_url"]

    # Webhook
    try:
        requests.post(webhook_url, json={"name": data.name, "unternehmen": data.unternehmen, "email": data.email, "pdf_url": pdf_url})
    except Exception as e:
        return {"error": f"Webhook failed: {str(e)}"}

    return {"pdf_url": pdf_url}

@app.get("/")
async def root():
    return {"message": "Service läuft"}
