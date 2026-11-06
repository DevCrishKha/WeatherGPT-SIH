import os
from datetime import datetime
import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import json
from save_district import jsonToDict

load_dotenv("../.env")

app = Flask(__name__)

IMD_API_KEY = os.getenv("API_KEY")
IMD_JWT_TOKEN = os.getenv("JWT_TOKEN")

IMD_ENDPOINT = "https://api.imd.gov.in/api/v1/districtnowcast"

headers = {
    "X-API-KEY": IMD_API_KEY,
    "Authorization": f"Bearer {IMD_JWT_TOKEN}"
}

CATEGORY_DESCRIPTIONS = {
    "cat1": "No Weather",
    "cat2": "Light rain: < 5 mm/hr",
    "cat3": "Light snow: < 5 cm/hr",
    "cat4": "Light Thunderstorms with maximum surface wind speed less than 40 kmph (in gusts)",
    "cat5": "Slight dust storm: wind speed up to 41 kmph and visibility less than 1000 m but more than 500 m",
    "cat6": "Low cloud to ground Lightning probability (< 30%)",
    "cat7": "Moderate rain: 5-15 mm/hr",
    "cat8": "Moderate snow: 5-15 cm/hr",
    "cat9": "Moderate Thunderstorms with maximum surface wind speed between 41 - 61 kmph (in gusts)",
    "cat10": "Moderate dust storm: wind speed between 41-61 kmph and visibility between 200 and 500 m due to dust",
    "cat11": "Moderate cloud to ground Lightning probability (30 - 60%)",
    "cat12": "Heavy rain: > 15 mm/hr",
    "cat13": "Heavy snow: > 15 cm/hr",
    "cat14": "Severe Thunderstorms with maximum surface wind speed 62 - 87 kmph (in gusts)",
    "cat15": "Very Severe Thunderstorms with maximum surface wind speed > 87 kmph (in gusts)",
    "cat16": "Other Warnings",
    "cat17": "Thunderstorms with Hail",
    "cat18": "Severe dust storm: surface wind speed exceeding 61 kmph and visibility less than 200 m",
    "cat19": "High cloud to ground Lightning probability (> 60%)",
}

def active_categories(record):
    active = []

    for key, description in CATEGORY_DESCRIPTIONS.items():
        value = str(record.get(key, "")).strip()

        # cat16 contains text, while the other categories normally contain 0/1.
        if key == "cat16":
            if value and value not in {"0", "None", "null"}:
                active.append({
                    "code": key,
                    "value": value,
                    "description": description,
                    "text": value
                })
        elif value not in {"", "0", "None", "null"}:
            active.append({
                "code": key,
                "value": value,
                "description": description,
                "text": description
            })

    return active

def make_warning_html(record, categories):
    district = record.get("State_District", "Unknown district")
    date = record.get("Date", "")
    message = str(record.get("message", "")).strip()

    lines = [
        f"<strong>{district}</strong>",
        f"<br>Date: {date}" if date else ""
    ]

    if categories:
        lines.append("<br><strong>Warnings:</strong><ul>")
        for category in categories:
            lines.append(f"<li>{category['text']}</li>")
        lines.append("</ul>")
    else:
        lines.append("<br>No active warning category reported.")

    if message:
        safe_message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"<br><strong>Message:</strong> {safe_message}")

    toi = record.get("toi", "")
    vupto = record.get("vupto", "")
    if toi or vupto:
        lines.append(f"<br><strong>Time:</strong> {toi or 'N/A'} - {vupto or 'N/A'}")

    return "".join(lines)

def transform_record(record):
    categories = active_categories(record)

    return {
        "object_id": record.get("Obj_id"),
        "district": str(record.get("State_District", "")).strip().upper(),
        "date": record.get("Date"),
        "categories": categories,
        "message": record.get("message", ""),
        "toi": record.get("toi", ""),
        "vupto": record.get("vupto", ""),
        "color_code": str(record.get("color", "")),
        "warning_html": make_warning_html(record, categories)
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/nowcast")
def nowcast():
    try:
        response = requests.get(
            IMD_ENDPOINT,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        payload = response.json()
        with open ("IMD_API_JSON.json", 'w') as f:
            json.dump(payload, f, indent=4)

        if not isinstance(payload, list):
            return jsonify({"error": "Expected the IMD response to be a JSON array."}), 502

        result = [transform_record(item) for item in payload if isinstance(item, dict)]
        return jsonify({
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "districts": result
        })

    except requests.RequestException as exc:
        return jsonify({"error": f"Could not request IMD API: {exc}"}), 502
    except ValueError:
        return jsonify({"error": "IMD response was not valid JSON."}), 502

@app.route("/save/district_table", methods=["POST"])
def save_district_table():
    table = request.get_json()
    jsonToDict(table)
    return "Saved Successfully"

if __name__ == "__main__":
    app.run(debug=True, port=8080)
