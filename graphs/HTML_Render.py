# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.


"""
weather_html.py

Generates weather-app UI cards as self-contained HTML/CSS (with inline
SVG icons) instead of a rasterized image. Because the browser does the
rendering, text stays crisp at any zoom level, the card can be made
responsive, and it's trivial to re-skin via CSS variables -- all things
that are awkward with a baked PNG.

Two builders are provided:

    generate_current_weather_html(data: dict) -> str
        A single "current conditions" card (temperature, feels-like,
        humidity/wind/pressure/rainfall, cloud cover, sun & moon times)
        from a single-observation station dict.

    generate_weekly_forecast_html(data: dict) -> str
        A "today + 7-day" forecast card from a station-bulletin-style
        dict with Day_2_Max_Temp ... Day_7_Forecast fields.

Both return a full, self-contained `<div class="weather-card">...</div>`
plus a `<style>` block with a unique, scoped class prefix, so you can
drop the returned string directly into a page. Two ways to use it on
your frontend:

  1. Inject directly into the DOM (React/Vue/plain JS):
        container.innerHTML = html_string   // from your API response

  2. Isolate it completely in an iframe (no CSS collisions with the
     rest of your page):
        <iframe srcdoc="{{ html_string | escape }}" style="border:0; width:100%; height:700px;"></iframe>

Everything is escaped with `html.escape()` before being interpolated,
so it's safe to feed in raw station-bulletin strings.
"""

from __future__ import annotations

import html
import datetime as dt
from typing import Optional
import requests


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

def _e(value) -> str:
    """HTML-escape any value (coercing to str first)."""
    return html.escape(str(value)) if value is not None else ""


def _safe_float(value, default=None) -> Optional[float]:
    try:
        if value in (None, "", "NA", "N/A"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(date_str: str) -> dt.date:
    try:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return dt.date.today()


def _format_hour(hour_str) -> str:
    h = _safe_float(hour_str)
    if h is None:
        return str(hour_str)
    h = int(h) % 24
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:00 {period}"


def _degrees_to_compass(deg) -> str:
    d = _safe_float(deg)
    if d is None:
        return "--"
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((d % 360) / 22.5 + 0.5) % 16
    return dirs[idx]


def _classify_condition(text: str) -> str:
    t = (text or "").lower()
    if "thunder" in t:
        return "thunder"
    if "rain" in t or "shower" in t or "drizzle" in t:
        return "rain"
    if "mist" in t or "fog" in t or "haze" in t or "smoke" in t:
        return "fog"
    if "overcast" in t or ("cloudy" in t and "partly" not in t):
        return "cloudy"
    if "partly" in t or "cloud" in t:
        return "partly_cloudy"
    if "clear" in t or "sunny" in t or "fair" in t:
        return "clear"
    return "partly_cloudy"


# --------------------------------------------------------------------------
# Inline SVG weather icons (currentColor-free -- explicit fills so they
# look right regardless of surrounding CSS)
# --------------------------------------------------------------------------

def _icon_svg(condition: str, size: int = 64) -> str:
    s = size
    sun = f'''<circle cx="{s*0.5}" cy="{s*0.46}" r="{s*0.22}" fill="#ffcd5a"/>
        {"".join(
            f'<line x1="{s*0.5 + (s*0.30)*_c}" y1="{s*0.46 + (s*0.30)*_sn}" '
            f'x2="{s*0.5 + (s*0.42)*_c}" y2="{s*0.46 + (s*0.42)*_sn}" '
            f'stroke="#ffcd5a" stroke-width="{max(2, s*0.035)}" stroke-linecap="round"/>'
            for _c, _sn in [
                (1, 0), (0.707, 0.707), (0, 1), (-0.707, 0.707),
                (-1, 0), (-0.707, -0.707), (0, -1), (0.707, -0.707),
            ]
        )}'''

    cloud = f'''<path d="M {s*0.18} {s*0.62}
        a {s*0.16} {s*0.16} 0 0 1 {s*0.02}-{s*0.32}
        a {s*0.20} {s*0.20} 0 0 1 {s*0.37}-{s*0.09}
        a {s*0.17} {s*0.17} 0 0 1 {s*0.24} {s*0.20}
        a {s*0.14} {s*0.14} 0 0 1 -{s*0.03} {s*0.28}
        Z" fill="#ffffff" opacity="0.92"/>'''

    rain = "".join(
        f'<line x1="{s*(0.34+i*0.16)}" y1="{s*0.70}" x2="{s*(0.30+i*0.16)}" y2="{s*0.86}" '
        f'stroke="#78b4ff" stroke-width="{max(2, s*0.035)}" stroke-linecap="round"/>'
        for i in range(3)
    )

    bolt = f'''<path d="M {s*0.52} {s*0.64} L {s*0.40} {s*0.80} L {s*0.49} {s*0.80}
        L {s*0.43} {s*0.94} L {s*0.60} {s*0.74} L {s*0.51} {s*0.74} Z" fill="#ffcd5a"/>'''

    fog = "".join(
        f'<line x1="{s*(0.20+i*0.02)}" y1="{s*(0.68+i*0.09)}" x2="{s*(0.80-i*0.05)}" y2="{s*(0.68+i*0.09)}" '
        f'stroke="#d2dbeb" stroke-width="{max(2, s*0.03)}" stroke-linecap="round"/>'
        for i in range(3)
    )

    if condition == "clear":
        body = sun
    elif condition == "partly_cloudy":
        body = (
            f'<g transform="translate(-{s*0.08},-{s*0.05})">{sun}</g>'
            f'<g transform="translate({s*0.04},{s*0.06}) scale(0.95)">{cloud}</g>'
        )
    elif condition == "cloudy":
        body = f'<g transform="scale(1.15) translate(-{s*0.07},-{s*0.06})">{cloud}</g>'
    elif condition == "rain":
        body = cloud + rain
    elif condition == "thunder":
        body = cloud + bolt
    elif condition == "fog":
        body = (
            f'<g transform="translate(0,-{s*0.08}) scale(0.85)" opacity="0.9">{cloud}</g>' + fog
        )
    else:
        body = sun

    return f'<svg viewBox="0 0 {s} {s}" width="{s}" height="{s}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def _wind_arrow_svg(direction_deg: float, size: int = 34) -> str:
    s = size
    return f'''<svg viewBox="0 0 {s} {s}" width="{s}" height="{s}" xmlns="http://www.w3.org/2000/svg">
        <circle cx="{s/2}" cy="{s/2}" r="{s*0.38}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="2"/>
        <g transform="rotate({direction_deg} {s/2} {s/2})">
            <line x1="{s/2}" y1="{s*0.14}" x2="{s/2}" y2="{s*0.68}" stroke="#78b4ff" stroke-width="{max(2, s*0.09)}" stroke-linecap="round"/>
            <polygon points="{s/2},{s*0.06} {s*0.38},{s*0.28} {s*0.62},{s*0.28}" fill="#78b4ff"/>
        </g>
    </svg>'''


# --------------------------------------------------------------------------
# Shared CSS (scoped under .wx-card so it can't leak into / clash with
# the host page's own styles)
# --------------------------------------------------------------------------

_SHARED_CSS = """
.wx-card {
    --wx-bg-top: #141e41;
    --wx-bg-bottom: #37416e;
    --wx-card-bg: rgba(255,255,255,0.08);
    --wx-card-bg-hi: rgba(255,255,255,0.14);
    --wx-white: #ffffff;
    --wx-soft-white: #e1e6f5;
    --wx-muted: #b9c0dc;
    --wx-divider: rgba(255,255,255,0.14);
    --wx-accent: #ffcd5a;

    box-sizing: border-box;
    max-width: 1000px;
    width: 100%;
    margin: 0 auto;
    padding: 28px;
    border-radius: 28px;
    background: linear-gradient(160deg, var(--wx-bg-top), var(--wx-bg-bottom));
    color: var(--wx-white);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    box-shadow: 0 20px 50px rgba(10, 15, 35, 0.45);
}
.wx-card * { box-sizing: border-box; }

.wx-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
}
.wx-location h1 {
    margin: 0;
    font-size: 34px;
    font-weight: 800;
    line-height: 1.15;
}
.wx-location p {
    margin: 4px 0 0;
    font-size: 15px;
    color: var(--wx-muted);
}
.wx-when { text-align: right; }
.wx-when .wx-date { font-size: 16px; color: var(--wx-soft-white); }
.wx-when .wx-time { font-size: 13px; color: var(--wx-muted); margin-top: 2px; }

.wx-panel {
    background: var(--wx-card-bg);
    border-radius: 20px;
    backdrop-filter: blur(6px);
}
.wx-panel.wx-hi { background: var(--wx-card-bg-hi); }

.wx-hero {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    padding: 26px 28px;
    margin-bottom: 18px;
}
.wx-temp-block { display: flex; align-items: baseline; gap: 4px; }
.wx-temp { font-size: 76px; font-weight: 800; line-height: 1; }
.wx-temp-unit { font-size: 30px; font-weight: 800; color: var(--wx-soft-white); }
.wx-feels { margin-top: 10px; font-size: 18px; font-weight: 700; color: var(--wx-muted); }
.wx-condition { display: flex; align-items: center; gap: 14px; text-align: left; }
.wx-condition .wx-cond-text .label {
    font-size: 19px; font-weight: 700; margin: 0 0 4px;
}
.wx-condition .wx-cond-text .desc {
    font-size: 16px; color: var(--wx-soft-white); margin: 0; max-width: 320px;
}

.wx-stats-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
    padding: 18px 4px;
    margin-bottom: 18px;
}
.wx-stat {
    flex: 1 1 0;
    min-width: 140px;
    padding: 4px 20px;
    border-left: 1px solid var(--wx-divider);
}
.wx-stat:first-child { border-left: none; }
.wx-stat .wx-label {
    font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase;
    color: var(--wx-muted); margin: 0 0 6px;
}
.wx-stat .wx-value {
    font-size: 18px; font-weight: 700; margin: 0;
    display: flex; align-items: center; gap: 8px;
}

.wx-days {
    padding: 18px 20px 22px;
}
.wx-days-title {
    font-size: 13px; letter-spacing: 0.04em; text-transform: uppercase;
    color: var(--wx-muted); font-weight: 700; margin: 0 0 14px;
}
.wx-days-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.wx-day {
    flex: 1 1 0;
    min-width: 90px;
    text-align: center;
    padding: 14px 6px;
    border-radius: 14px;
}
.wx-day.today { background: var(--wx-card-bg-hi); }
.wx-day .name { font-size: 14px; font-weight: 700; margin: 0; }
.wx-day .date { font-size: 11px; color: var(--wx-muted); margin: 2px 0 8px; }
.wx-day .icon { margin: 0 auto 6px; width: 40px; height: 40px; }
.wx-day .max { font-size: 15px; font-weight: 700; margin: 0; }
.wx-day .bar {
    height: 4px; border-radius: 2px; background: var(--wx-divider);
    margin: 6px auto; width: 70%; position: relative; overflow: hidden;
}
.wx-day .bar span {
    position: absolute; top: 0; bottom: 0; background: var(--wx-accent);
}
.wx-day .min { font-size: 13px; color: var(--wx-muted); margin: 0; }

@media (max-width: 640px) {
    .wx-temp { font-size: 56px; }
    .wx-hero { flex-direction: column; align-items: flex-start; }
    .wx-stat { flex: 1 1 45%; border-left: none !important; }
    .wx-day { flex: 1 1 22%; }
}
"""


def _header_html(location_main, location_sub, date_str, time_str: Optional[str] = None) -> str:
    when_time = f'<p class="wx-time">Observed {_e(time_str)}</p>' if time_str else ""
    return f"""
    <div class="wx-header">
        <div class="wx-location">
            <h1>{_e(location_main)}</h1>
            {f'<p>{_e(location_sub)}</p>' if location_sub else ''}
        </div>
        <div class="wx-when">
            <p class="wx-date">{_e(date_str)}</p>
            {when_time}
        </div>
    </div>
    """


def _location_parts(data: dict, station_key: str):
    city = (data.get("city") or "").strip().title()
    district = (data.get("district") or "").strip().title()
    state = (data.get("state") or "").strip().title()
    station = (data.get(station_key) or "").strip()

    location_main = city or station or "Unknown location"
    sub_parts = [p for p in [station if station != location_main else None,
                              district, state] if p]
    return location_main, ", ".join(sub_parts)


# --------------------------------------------------------------------------
# Current conditions card
# --------------------------------------------------------------------------

def generate_current_weather_html(data: dict) -> str:
    """Return a self-contained HTML snippet for a current-conditions card."""
    location_main, location_sub = _location_parts(data, "Station")

    date_obj = _parse_date(data.get("Date of Observation") or data.get("date") or "")
    date_str = date_obj.strftime("%A, %d %b %Y")
    time_str = _format_hour(data.get("Time")) if data.get("Time") is not None else None

    temp = _safe_float(data.get("Temperature"))
    feels_like = _safe_float(data.get("Feel Like"))
    weather_message = data.get("WEATHER_MESSAGE") or ""
    condition = _classify_condition(weather_message)

    humidity = data.get("Humidity")
    wind_speed = _safe_float(data.get("Wind Speed KMPH"))
    wind_dir_deg = _safe_float(data.get("Wind Direction"))
    pressure = data.get("Mean Sea Level Pressure")
    rainfall = data.get("Last 24 hrs Rainfall")
    nebulosity = data.get("Nebulosity")
    sunrise = data.get("Sunrise") or "--"
    sunset = data.get("Sunset") or "--"
    moonrise = data.get("Moonrise") or "--"
    moonset = data.get("Moonset") or "--"

    wind_html = ""
    if wind_speed is not None:
        arrow = _wind_arrow_svg(wind_dir_deg or 0, size=26)
        compass = _degrees_to_compass(wind_dir_deg)
        wind_html = f'{arrow}<span>{wind_speed:.1f} km/h {_e(compass)}</span>'
    else:
        wind_html = "--"

    stats = [
        ("Humidity", f"{humidity}%" if humidity not in (None, "NA") else "--"),
        ("Wind", wind_html),
        ("Pressure", f"{pressure} hPa" if pressure not in (None, "NA") else "--"),
        ("Rainfall (24h)", f"{rainfall} mm" if rainfall not in (None, "NA") else "0 mm"),
    ]
    stats2 = [
        ("Cloud cover", f"{nebulosity}/8 oktas" if nebulosity not in (None, "NA") else "--"),
        ("Sunrise / Sunset", f"{sunrise} / {sunset}"),
        ("Moonrise / Moonset", f"{moonrise} / {moonset}"),
    ]

    def _stat_cells(items):
        return "".join(
            f'<div class="wx-stat"><p class="wx-label">{_e(label)}</p>'
            f'<p class="wx-value">{value}</p></div>'
            for label, value in items
        )

    temp_html = f'{temp:.0f}' if temp is not None else "--"
    feels_html = f'Feels like {feels_like:.0f}&deg;' if feels_like is not None else ""

    return f"""<div class="wx-card">
<style>{_SHARED_CSS}</style>
{_header_html(location_main, location_sub, date_str, time_str)}
<div class="wx-panel wx-hi wx-hero">
    <div>
        <div class="wx-temp-block">
            <span class="wx-temp">{temp_html}</span><span class="wx-temp-unit">&deg;C</span>
        </div>
        <p class="wx-feels">{feels_html}</p>
    </div>
    <div class="wx-condition">
        <span class="icon">{_icon_svg(condition, 88)}</span>
        <div class="wx-cond-text">
            <p class="label">{_e(condition.replace('_', ' ').title())}</p>
            <p class="desc">{_e(weather_message) or '--'}</p>
        </div>
    </div>
</div>
<div class="wx-panel wx-stats-row" style="margin-bottom: 14px;">
    {_stat_cells(stats)}
</div>
<div class="wx-panel wx-stats-row">
    {_stat_cells(stats2)}
</div>
</div>"""


# --------------------------------------------------------------------------
# 7-day forecast card
# --------------------------------------------------------------------------

def generate_weekly_forecast_html(data: dict) -> str:
    """Return a self-contained HTML snippet for a today + 7-day forecast card."""
    location_main, location_sub = _location_parts(data, "Station_Name")

    date_obj = _parse_date(data.get("Date", ""))
    date_str = date_obj.strftime("%A, %d %b %Y")

    today_forecast_text = data.get("Todays_Forecast") or ""
    condition = _classify_condition(today_forecast_text)

    current_temp = (
        _safe_float(data.get("Todays_Forecast_Max_Temp"))
        or _safe_float(data.get("Today_Max_temp"))
        or _safe_float(data.get("Previous_Day_Max_temp"))
    )
    today_min = _safe_float(data.get("Todays_Forecast_Min_temp")) or _safe_float(data.get("Today_Min_temp"))
    today_max = _safe_float(data.get("Todays_Forecast_Max_Temp")) or _safe_float(data.get("Today_Max_temp"))

    rh = data.get("Relative_Humidity_at_0830") or data.get("Previous_Day_Relative_Humidity_at_1730")
    rainfall = data.get("Past_24_hrs_Rainfall")
    sunrise = data.get("Sunrise_time") or "--"
    sunset = data.get("Sunset_time") or "--"
    moonrise = data.get("Moonrise_time") or "--"
    moonset = data.get("Moonset_time") or "--"

    stats = [
        ("Humidity", f"{rh}%" if rh not in (None, "NA") else "--"),
        ("Rainfall (24h)", f"{rainfall} mm" if rainfall not in (None, "NA") else "0 mm"),
        ("Sunrise / Sunset", f"{sunrise} / {sunset}"),
        ("Moonrise / Moonset", f"{moonrise} / {moonset}"),
    ]
    stats_html = "".join(
        f'<div class="wx-stat"><p class="wx-label">{_e(label)}</p><p class="wx-value">{_e(value)}</p></div>'
        for label, value in stats
    )

    minmax_html = f"H:{today_max:.0f}&deg;  L:{today_min:.0f}&deg;" if today_max is not None and today_min is not None else ""
    temp_html = f"{current_temp:.0f}" if current_temp is not None else "--"

    days = [{
        "label": "Today",
        "date": date_obj,
        "max": today_max,
        "min": today_min,
        "forecast": today_forecast_text,
    }]
    for n in range(2, 8):
        d_max = _safe_float(data.get(f"Day_{n}_Max_Temp"))
        d_min = _safe_float(data.get(f"Day_{n}_Min_temp"))
        d_forecast = data.get(f"Day_{n}_Forecast") or ""
        d_date = date_obj + dt.timedelta(days=n - 1)
        days.append({
            "label": d_date.strftime("%a"),
            "date": d_date,
            "max": d_max,
            "min": d_min,
            "forecast": d_forecast,
        })

    all_temps = [d["max"] for d in days if d["max"] is not None] + \
                [d["min"] for d in days if d["min"] is not None]
    week_min = min(all_temps) if all_temps else 0
    week_max = max(all_temps) if all_temps else 1
    span = max(week_max - week_min, 1)

    day_cards = []
    for i, d in enumerate(days):
        cond = _classify_condition(d["forecast"])
        max_t, min_t = d["max"], d["min"]
        max_txt = f'{max_t:.0f}&deg;' if max_t is not None else "--"
        min_txt = f'{min_t:.0f}&deg;' if min_t is not None else "--"

        bar_fill = ""
        if max_t is not None and min_t is not None:
            left = (min_t - week_min) / span * 100
            width = max((max_t - min_t) / span * 100, 4)
            bar_fill = f'<span style="left:{left:.1f}%; width:{width:.1f}%;"></span>'

        day_cards.append(f"""
        <div class="wx-day{' today' if i == 0 else ''}">
            <p class="name">{_e(d['label'])}</p>
            <p class="date">{d['date'].strftime('%d %b')}</p>
            <div class="icon">{_icon_svg(cond, 40)}</div>
            <p class="max">{max_txt}</p>
            <div class="bar">{bar_fill}</div>
            <p class="min">{min_txt}</p>
        </div>""")

    return f"""<div class="wx-card">
<style>{_SHARED_CSS}</style>
{_header_html(location_main, location_sub, date_str)}
<div class="wx-panel wx-hi wx-hero">
    <div>
        <div class="wx-temp-block">
            <span class="wx-temp">{temp_html}</span><span class="wx-temp-unit">&deg;C</span>
        </div>
        <p class="wx-feels">{minmax_html}</p>
    </div>
    <div class="wx-condition">
        <span class="icon">{_icon_svg(condition, 88)}</span>
        <div class="wx-cond-text">
            <p class="label">{_e(condition.replace('_', ' ').title())}</p>
            <p class="desc">{_e(today_forecast_text) or '--'}</p>
        </div>
    </div>
</div>
<div class="wx-panel wx-stats-row" style="margin-bottom: 14px;">
    {stats_html}
</div>
<div class="wx-panel wx-days">
    <p class="wx-days-title">7-Day Forecast</p>
    <div class="wx-days-strip">
        {''.join(day_cards)}
    </div>
</div>
</div>"""


# --------------------------------------------------------------------------
# Demo / manual test
# --------------------------------------------------------------------------

if __name__ == "__main__":
    current_sample = {
        "Station Id": "42724", "Station": "Agartala",
        "Date of Observation": "2026-09-24", "Time": "21",
        "Mean Sea Level Pressure": "1009", "Wind Direction": "50",
        "Wind Speed KMPH": "1.9", "Temperature": "27",
        "Weather Code": "10", "Nebulosity": "6", "Humidity": "89",
        "Last 24 hrs Rainfall": "0", "Feel Like": "30.9",
        "WEATHER_ICON": 500, "WEATHER_MESSAGE": "Mist",
        "Sunrise": "05:14", "Sunset": "17:19",
        "Moonrise": "16:25", "Moonset": "03:42",
        "city": "agartala", "district": "west tripura", "state": "tripura",
        "date": "2026-09-24",
    }

    weekly_sample = {
        "Date": "2026-09-29", "Station_Name": "Kanpur Airforce",
        "Previous_Day_Max_temp": "32.6", "Today_Min_temp": "25.0",
        "Past_24_hrs_Rainfall": "3.40", "Relative_Humidity_at_0830": "84",
        "Sunset_time": "18:04", "Sunrise_time": "05:58",
        "Moonset_time": "03:29", "Moonrise_time": "16:39",
        "Todays_Forecast_Max_Temp": "31.0", "Todays_Forecast_Min_temp": "24.0",
        "Todays_Forecast": "Partly cloudy sky with one or two spells of rain or thundershowers",
        "Day_2_Max_Temp": "29.0", "Day_2_Min_temp": "24.0",
        "Day_2_Forecast": "Generally cloudy sky with a few spells of rain or thundershowers",
        "Day_3_Max_Temp": "30.0", "Day_3_Min_temp": "24.0",
        "Day_3_Forecast": "Generally cloudy sky with one or two spells of rain or thundershowers",
        "Day_4_Max_Temp": "31.0", "Day_4_Min_temp": "24.0", "Day_4_Forecast": "Partly cloudy sky",
        "Day_5_Max_Temp": "32.0", "Day_5_Min_temp": "25.0", "Day_5_Forecast": "Partly cloudy sky",
        "Day_6_Max_Temp": "33.0", "Day_6_Min_temp": "25.0", "Day_6_Forecast": "Partly cloudy sky",
        "Day_7_Max_Temp": "33.0", "Day_7_Min_temp": "25.0", "Day_7_Forecast": "Partly cloudy sky",
        "city": "jajmau", "district": "kanpur nagar", "state": "uttar pradesh",
    }

    Current_weather_HTML = generate_current_weather_html(current_sample)
    
    # with open("current_preview.html", "w") as f:
    #     f.write(f"<html><body style='margin:0;background:#0b1020;padding:30px;'>{Current_weather_HTML}</body></html>")

    # with open("weekly_preview.html", "w") as f:
    #     f.write(f"<html><body style='margin:0;background:#0b1020;padding:30px;'>{generate_weekly_forecast_html(weekly_sample)}</body></html>")

    print("Wrote /HTML/current_preview.html and /HTML/weekly_preview.html")
    
    URL = "http://localhost:5000/get_tool_html"
    # 1. Prepare your custom internal authorization token header
    headers = {
        "Authorization": "Bearer YOUR_INTERNAL_TOKEN_HERE"  # Update this to match your _internal_token_ok() logic
    }

    # 2. The backend receives the json data and takes user_id, conversation_id, html from there
    payload_data = {
        "user_id": "Devin",
        "conversation_id": "b132f829a998",  # Optional, but accepted by your endpoint
        "html":generate_weekly_forecast_html(weekly_sample)
    }
    
    # form_data = {
    #     "user_id": "Devin",
    #     "conversation_id": "ac7c2b4c1677"  # Optional, but accepted by your endpoint
    # }
    
    response = requests.post(URL, headers=headers, json=payload_data)
    
    # 5. Handle the server response
    if response.status_code == 200:
        print("---------------------------------------------------------------\nSuccess!")
        print(response.json())
    else:
        print(f"--------------------------------------------------------------\nFailed with status code {response.status_code}: {response.text}")