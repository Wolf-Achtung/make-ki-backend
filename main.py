import os
import requests
import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

openai.api_key = os.getenv("OPENAI_API_KEY")
PDFMONKEY_API_KEY = os.getenv("PDFMONKEY_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
PDFMONKEY_TEMPLATE_IDS = {
    "preview": os.getenv("PDFMONKEY_TEMPLATE_ID_PREVIEW"),
    "full": os.getenv("PDFMONKEY_TEMPLATE_ID")
}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class FormData(BaseModel):
    name: str
    unternehmen: str
    email: str
    branche: str
    selbststaendig: Optional[str]
    branche_sonstige: Optional[str] = ""
    r1: Optional[str]
    r2: Optional[str]
    r3: Optional[str]
    r4: Optional[str]
    r5: Optional[str]
    c1: Optional[str]
    c2: Optional[str]
    c3: Optional[str]
    c4: Optional[str]
    c5: Optional[str]
    u1: Optional[str]
    u2: Optional[str]
    ziel: Optional[str]
    herausforderung: Optional[str]
    tools: Optional[str]
    massnahmen: Optional[str]
    template_variant: Optional[str] = "preview"
    logo_url: Optional[str] = ""

def score_fields(data, fields):
    scale = {
        "trifft nicht zu": 1,
        "teilweise": 2,
        "überwiegend": 3,
        "voll zutreffend": 4
    }
    return sum(scale.get(getattr(data, f), 0) for f in fields)

def gpt_summary(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Du bist ein KI-Experte für Mittelstandsberatung."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"].strip()

@app.post("/analyze")
async def analyze(data: FormData):
    score_readiness = score_fields(data, ["r1", "r2", "r3", "r4", "r5"])
    score_compliance = score_fields(data, ["c2", "c3", "c5"])
    score_total = score_readiness + score_compliance
    bewertung = "kritisch" if score_total < 10 else "ausbaufähig" if score_total < 20 else "gut"

    gpt_input = (
        f"Firma: {data.unternehmen}\n"
        f"Branche: {data.branche}\n"
        f"Tools: {data.tools}\n"
        f"Ziel: {data.ziel}\n"
        f"Maßnahmen: {data.massnahmen}\n"
        f"Herausforderung: {data.herausforderung}\n"
        "Bitte formuliere eine Executive Summary, Analyse, 3 Empfehlungen und eine Vision für den KI-Einsatz."
    )

    gpt_text = gpt_summary(gpt_input)
    executive_summary = f"{data.unternehmen} zeigt Bereitschaft zum KI-Einsatz in der Branche {data.branche}."
    analyse = "Es gibt Potenziale in Strategie, Tools und Umsetzung."

    return {
        "executive_summary": gpt_text or executive_summary,
        "analyse": analyse,
        "empfehlung1": {
            "titel": "Dringende Hebelmaßnahme",
            "beschreibung": "Automatisierung interner Workflows mit Make starten.",
            "next_step": "Pilot-Workflow identifizieren und aufsetzen.",
            "tool": "Make"
        },
        "empfehlung2": {
            "titel": "Potenzial entfesseln",
            "beschreibung": "Content-Erstellung durch Notion AI und DeepL Pro unterstützen.",
            "next_step": "Redaktionsprozesse analysieren und KI integrieren.",
            "tool": "Notion AI, DeepL Pro"
        },
        "empfehlung3": {
            "titel": "Zukunft sichern",
            "beschreibung": "Strategische Weiterbildung im Bereich KI für Schlüsselmitarbeiter.",
            "next_step": "Online-Kurse bei aiCampus starten.",
            "tool": "aiCampus"
        },
        "roadmap": {
            "kurzfristig": "Mindestens einen Prozess automatisieren.",
            "mittelfristig": "KI-Standards im Unternehmen definieren.",
            "langfristig": "KI als festen Bestandteil der Unternehmenskultur etablieren."
        },
        "ressourcen": "Plattformen wie aiCampus, Bundesförderprogramme (z. B. go-digital), Branchennetzwerke.",
        "zukunft": "Mit einem klaren KI-Fahrplan kann die Organisation zum Vorbild werden.",
        "risikoprofil": {
            "risikoklasse": "Moderat",
            "begruendung": "Nutzung generativer Tools mit sensiblen Daten.",
            "pflichten": ["Transparenzpflichten", "Datenschutzfolgeabschätzung", "Mitarbeiterschulung"]
        },
        "tooltipps": [
            {"name": "Make", "einsatz": "Workflow-Automatisierung", "warum": "Intuitiv und vielseitig"},
            {"name": "Notion AI", "einsatz": "Content-Optimierung", "warum": "Smarte Textvorschläge"}
        ],
        "foerdertipps": [
            {"programm": "go-digital", "zielgruppe": "KMU", "nutzen": "Bis zu 50% Förderung für Digitalisierung"}
        ],
        "branchenvergleich": "Die IT-Branche liegt beim KI-Einsatz vor anderen Sektoren.",
        "trendreport": "Multimodale KI-Systeme gewinnen an Bedeutung.",
        "vision": "Ihre Agentur schafft doppelt so viele Projekte mit halbem Zeitaufwand.",
        "score_readiness": score_readiness,
        "score_compliance": score_compliance,
        "score_total": score_total,
        "bewertung": bewertung,
        "logo_url": data.logo_url or ""
    }

class PDFRequest(BaseModel):
    template_variant: str
    executive_summary: str
    analyse: str
    empfehlung1: dict
    empfehlung2: dict
    empfehlung3: dict
    roadmap: dict
    ressourcen: str
    zukunft: str
    risikoprofil: dict
    tooltipps: list
    foerdertipps: list
    branchenvergleich: str
    trendreport: str
    vision: str
    score_total: Optional[int] = 0
    bewertung: Optional[str] = ""
    logo_url: Optional[str] = ""

@app.post("/generate-pdf")
async def generate_pdf(payload: PDFRequest):
    template_id = PDFMONKEY_TEMPLATE_IDS.get(payload.template_variant, PDFMONKEY_TEMPLATE_IDS["preview"])
    headers = {
        "Authorization": f"Bearer {PDFMONKEY_API_KEY}",
        "Content-Type": "application/json"
    }
    pdf_data = {
        "document": {
            "document_template_id": template_id,
            "payload": payload.dict()
        }
    }

    response = requests.post("https://api.pdfmonkey.io/api/v1/documents", headers=headers, json=pdf_data)

    if response.status_code != 201:
        return {"error": "PDFMonkey-Fehler", "details": response.text}

    document = response.json()["data"]
    pdf_url = document["attributes"]["download_url"]

    if MAKE_WEBHOOK_URL:
        requests.post(MAKE_WEBHOOK_URL, json=payload.dict())

    return {"pdf_url": pdf_url}
