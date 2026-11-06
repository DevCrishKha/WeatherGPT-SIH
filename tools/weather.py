# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.


"""Weather tools.

These are deliberately DEMO implementations.

Replace their internals with calls into services/ as you integrate
IMD, Open-Meteo, your own databases, retrieval systems, etc.
"""

from datetime import datetime


def get_current_weather(
    location: str,
    unit: str = "celsius",
):
    if not location.strip():
        raise ValueError("location must not be empty")

    if unit not in {"celsius", "fahrenheit"}:
        raise ValueError(
            "unit must be 'celsius' or 'fahrenheit'"
        )

    return {
        "location": location.strip(),
        "observation_time": datetime.now().astimezone().isoformat(),
        "temperature": 29,
        "unit": unit,
        "humidity": 78,
        "rain_probability": 70,
        "condition": "Partly cloudy",
        "source": "DEMO_DATA",
    }


def get_weather_alerts(location: str):
    if not location.strip():
        raise ValueError("location must not be empty")

    return {
        "location": location.strip(),
        "alerts": [
            {
                "type": "Heavy Rain",
                "severity": "Moderate",
                "valid_until": "2026-09-20T18:00:00+05:30",
                "description": (
                    "Moderate rainfall may occur in some areas."
                ),
            }
        ],
        "source": "DEMO_DATA",
    }
