import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# CORS für alle Ursprünge
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manuelles Abfangen des OPTIONS-Preflight-Requests
@app.options("/generate-pdf")
async def options_handler(request: Request):
    return JSONResponse(status_code=200, content={"message": "CORS OK"})

class DummyData(BaseModel):
    name: str
    ziel: Optional[str] = "Prozesse automatisieren"
    template_variant: Optional[str] = "preview"

@app.post("/generate-pdf")
async def generate_pdf(data: DummyData):
    try:
        api_key = os.getenv("PDFMONKEY_API_KEY")
        template_id = os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW") if data.template_variant == "preview" else os.getenv("PDFMONKEY_TEMPLATE_ID")
        if not api_key or not template_id:
            return {"error": "PDFMonkey keys fehlen"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "document": {
                "document_template_id": template_id,
                "payload": {
                    "executive_summary": f"{data.name} möchte {data.ziel} mithilfe von KI erreichen.",
                    "analyse": "Die Organisation hat erste Voraussetzungen für den KI-Einsatz geschaffen.",
                    "vision": "Mit gezielter Automatisierung steigert das Unternehmen seine Effizienz deutlich."
                }
            }
        }

        response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=payload)
        if response.status_code != 201:
            return {"error": "PDFMonkey Error", "details": response.text}

        pdf_url = response.json()["data"]["attributes"]["download_url"]
        return {"pdf_url": pdf_url}

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Service läuft"}
