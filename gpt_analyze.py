from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import json
from datetime import date

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

def call_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du bist ein zertifizierter KI-Berater. Antworte strukturiert und geschäftlich, aber klar verständlich."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_gpt_analysis(data):
    score = int(data.get("score", 0))
    branche = data.get("branche", "Allgemein")
    ziel = data.get("ziel", "nicht angegeben")
    tools = data.get("tools", "keine")
    herausforderung = data.get("herausforderung", "keine")

    executive_prompt = f"""
    Erstelle eine kurze Executive Summary für ein Unternehmen der Branche {branche} mit folgendem Ziel: {ziel}. Der aktuelle Score im KI-Check beträgt {score}/40.
    """

    analyse_prompt = f"""
    Analysiere strategisch, wie ein Unternehmen in der Branche {branche} mit einem Score von {score} beim KI-Einsatz aufgestellt ist. Berücksichtige: Tools = {tools}, Herausforderung = {herausforderung}.
    """

    empfehlungen_prompt = f"""
    Gib drei konkrete Empfehlungen (je mit Titel, Beschreibung, next_step, tool) für den KI-Einsatz in einem Unternehmen der Branche {branche} mit Score {score} und Ziel: {ziel}.
    Antworte im JSON-Format: [{{"titel": ..., "beschreibung": ..., "next_step": ..., "tool": ...}}, ...]
    """

    risikoprofil_prompt = f"""
    Leite ein Risikoprofil für das Unternehmen mit Score {score} ab. Gib Risikoklasse, Begründung und 3 empfohlene Pflichten aus.
    Antworte im JSON-Format: {{"risikoklasse": ..., "begruendung": ..., "pflichten": ["...", "...", "..."]}}
    """

    executive_summary = call_gpt(executive_prompt)
    analyse = call_gpt(analyse_prompt)
    empfehlungen = json.loads(call_gpt(empfehlungen_prompt))
    risikoprofil = json.loads(call_gpt(risikoprofil_prompt))

    result = {
        "executive_summary": executive_summary,
        "analyse": analyse,
        "empfehlungen": empfehlungen,
        "risikoprofil": risikoprofil,
        "score": score,
        "branche": branche,
        "ziel": ziel
    }

    return result

@app.route("/gpt-analyze", methods=["POST"])
def gpt_analyze():
    data = request.json
    return jsonify(generate_gpt_analysis(data))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
