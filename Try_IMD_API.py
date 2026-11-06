# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

# --- CONFIGURATION ---
IMD_API_KEY = os.getenv("API_KEY")
IMD_JWT_TOKEN = os.getenv("JWT_TOKEN")

IMD_ENDPOINT = "https://api.imd.gov.in/api/v1/cityforecastloc"

headers = {
    "X-API-KEY": IMD_API_KEY,
    "Authorization": f"Bearer {IMD_JWT_TOKEN}"
}

response = requests.get(
    IMD_ENDPOINT,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)

if response.ok:
    data = response.json()
    print(data)
    with open ("JSONs/IMD_API_JSON.json", 'w') as f:
        json.dump(data, f, indent=4)
else:
    print("Error:", response.text)