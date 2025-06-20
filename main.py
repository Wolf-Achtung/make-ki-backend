from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

app = FastAPI()

# CORS setup for Netlify frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# PDF template mapping (dummy IDs)
PDFMONKEY_TEMPLATE_IDS = {
    "preview": "TEMPLATE_ID_PREVIEW",
    "full": "TEMPLATE_ID_FULL"
}

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

@app.post("/analyze")
async def analyze(data: FormData):
    scale_map = {
        "trifft nicht zu": 1,
        "teilweise": 2,
        "überwiegend": 3,
        "voll zutreffend": 4
    }

    def score(fields):
        return sum([scale_map.get(getattr(data, f), 0) for f in fields])

    readiness_fields = ["r1", "r2", "r3", "r4", "r5"]
    compliance_fields = ["c2", "c3", "c5"]

    score_readiness = score(readiness_fields)
    score_compliance = score(compliance_fields)
    score_total = score_readiness + score_compliance

    bewertung = (
        "kritisch" if score_total < 10 else
        "ausbaufähig" if score_total < 20 else
        "gut"
    )

    executive_summary = "Ihre Organisation zeigt solide Ansätze im Bereich KI." if bewertung == "gut" else                         "Es bestehen grundlegende Voraussetzungen für KI-Nutzung." if bewertung == "ausbaufähig" else                         "Wichtige Grundlagen für KI müssen noch geschaffen werden."

    analyse = "Sie verfügen über ein gewisses Maß an KI-Bereitschaft. Die Datenbasis und das Wissen sind ausbaufähig."

    result = {
        "executive_summary": executive_summary,
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
        "bewertung": bewertung
    }

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
