# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.


"""  
weather_image.py

Generates a "weather forecast app" style PNG image (current conditions +
7-day forecast) from a data dict shaped like the IMD-style station bulletin
described in the prompt.

Main entry point:

    generate_weather_image(data: dict) -> bytes

Returns raw PNG bytes, ready to be sent to a frontend
(e.g. `Response(img_bytes, mimetype="image/png")` in Flask,
or base64-encoded into a data URI).
"""

from __future__ import annotations

import io
import math
import datetime as dt
from typing import Optional
import requests

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------

FONT_DIR = "fonts"


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a DejaVu font, falling back to PIL's default bitmap font."""
    try:
        return ImageFont.truetype(f"{FONT_DIR}/{name}.ttf", size)
    except Exception:
        return ImageFont.load_default()


class Fonts:
    def __init__(self):
        self.city = _font("DejaVuSans-Bold", 30)
        self.subtitle = _font("DejaVuSans", 20)
        self.temp_big = _font("DejaVuSans-Bold", 92)
        self.temp_unit = _font("DejaVuSans-Bold", 36)
        self.desc = _font("DejaVuSans", 22)
        self.section = _font("DejaVuSans-Bold", 18)
        self.stat_label = _font("DejaVuSans", 15)
        self.stat_value = _font("DejaVuSans-Bold", 20)
        self.day_name = _font("DejaVuSans-Bold", 17)
        self.day_date = _font("DejaVuSans", 13)
        self.day_temp = _font("DejaVuSans-Bold", 18)
        self.day_temp_min = _font("DejaVuSans", 16)
        self.day_forecast = _font("DejaVuSans", 12)


# --------------------------------------------------------------------------
# Colour palette (dark "modern weather app" theme)
# --------------------------------------------------------------------------

BG_TOP = (20, 30, 65)
BG_BOTTOM = (55, 65, 110)
CARD_BG = (255, 255, 255, 22)
CARD_BG_HIGHLIGHT = (255, 255, 255, 38)
WHITE = (255, 255, 255, 255)
SOFT_WHITE = (225, 230, 245, 255)
MUTED = (185, 192, 220, 255)
ACCENT_YELLOW = (255, 205, 90, 255)
ACCENT_BLUE = (120, 180, 255, 255)
DIVIDER = (255, 255, 255, 35)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

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


def _weekday_short(d: dt.date) -> str:
    return d.strftime("%a").upper()


def _classify_condition(text: str) -> str:
    """Classify a free-text forecast string into an icon category."""
    t = (text or "").lower()
    if "thunder" in t:
        return "thunder"
    if "rain" in t or "shower" in t:
        return "rain"
    if "mist" in t or "fog" in t or "haze" in t:
        return "fog"
    if "generally cloudy" in t or "overcast" in t:
        return "cloudy"
    if "partly cloudy" in t or "cloud" in t:
        return "partly_cloudy"
    if "clear" in t or "sunny" in t:
        return "clear"
    return "partly_cloudy"


def _vertical_gradient(size, top, bottom):
    w, h = size
    base = Image.new("RGB", (1, h), color=0)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        ratio = y / max(h - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        draw.point((0, y), fill=(r, g, b))
    return base.resize((w, h))


def _rounded_rect_on_layer(layer_draw, box, radius, fill=None, outline=None, width=1):
    """Draw a (possibly semi-transparent) rounded rect onto a dedicated
    transparent RGBA layer. Drawing translucent fills directly onto an
    already-opaque RGBA base paints a flat opaque color instead of
    blending, so cards must be drawn on their own layer and then
    alpha-composited onto the background."""
    layer_draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _text_centered(draw, cx, y, text, font, fill, anchor_top=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    if anchor_top:
        draw.text((cx - w / 2, y), text, font=font, fill=fill)
    else:
        h = bbox[3] - bbox[1]
        draw.text((cx - w / 2, y - h / 2), text, font=font, fill=fill)
    return w


# --------------------------------------------------------------------------
# Weather icon drawing (simple flat vector icons, drawn on a transparent
# RGBA layer so no external icon/emoji font is required)
# --------------------------------------------------------------------------

def _draw_sun(draw, cx, cy, r, color=ACCENT_YELLOW):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    ray_len = r * 0.55
    for i in range(8):
        angle = math.radians(i * 45)
        x1 = cx + math.cos(angle) * (r + 4)
        y1 = cy + math.sin(angle) * (r + 4)
        x2 = cx + math.cos(angle) * (r + 4 + ray_len)
        y2 = cy + math.sin(angle) * (r + 4 + ray_len)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=max(2, r // 8))


def _draw_cloud(draw, cx, cy, scale=1.0, color=(255, 255, 255, 235)):
    r = 16 * scale
    draw.ellipse([cx - r * 2.2 - r, cy - r * 0.2, cx - r * 0.2, cy + r * 1.8], fill=color)
    draw.ellipse([cx - r * 0.9, cy - r * 1.3, cx + r * 1.5, cy + r * 1.3], fill=color)
    draw.ellipse([cx + r * 0.4, cy - r * 0.1, cx + r * 2.6, cy + r * 1.9], fill=color)
    draw.rectangle([cx - r * 2.2, cy + r * 0.9, cx + r * 2.2, cy + r * 1.8], fill=color)


def _draw_rain(draw, cx, cy, scale=1.0, color=ACCENT_BLUE):
    r = 16 * scale
    for i, dx in enumerate([-r * 1.3, 0, r * 1.3]):
        offset = (i % 2) * 6
        x = cx + dx
        y0 = cy + r * 2.0 + offset
        y1 = y0 + r * 1.1
        draw.line([(x, y0), (x - 4, y1)], fill=color, width=max(2, int(3 * scale)))


def _draw_bolt(draw, cx, cy, scale=1.0, color=ACCENT_YELLOW):
    r = 16 * scale
    pts = [
        (cx + r * 0.2, cy + r * 1.7),
        (cx - r * 0.6, cy + r * 1.7),
        (cx + r * 0.1, cy + r * 2.6),
        (cx - r * 0.3, cy + r * 2.6),
        (cx + r * 0.7, cy + r * 3.6),
        (cx + r * 0.35, cy + r * 2.7),
        (cx + r * 0.75, cy + r * 2.7),
    ]
    draw.polygon(pts, fill=color)


def _draw_fog(draw, cx, cy, scale=1.0, color=(210, 218, 235, 220)):
    r = 16 * scale
    _draw_cloud(draw, cx, cy - r * 0.4, scale=scale * 0.9, color=(230, 235, 245, 200))
    for i, dy in enumerate([r * 1.6, r * 2.2, r * 2.8]):
        w = r * (2.4 - i * 0.3)
        draw.line([(cx - w, cy + dy), (cx + w, cy + dy)], fill=color, width=max(2, int(2.5 * scale)))


def draw_weather_icon(condition: str, size: int) -> Image.Image:
    """Return an RGBA icon image of the given pixel size for a condition."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size / 2, size / 2 - size * 0.05
    scale = size / 90.0

    if condition == "clear":
        _draw_sun(draw, cx, cy, r=size * 0.28)
    elif condition == "partly_cloudy":
        _draw_sun(draw, cx - size * 0.12, cy - size * 0.05, r=size * 0.20)
        _draw_cloud(draw, cx + size * 0.08, cy + size * 0.06, scale=scale * 1.05)
    elif condition == "cloudy":
        _draw_cloud(draw, cx, cy, scale=scale * 1.25)
    elif condition == "rain":
        _draw_cloud(draw, cx, cy - size * 0.12, scale=scale * 1.1)
        _draw_rain(draw, cx, cy - size * 0.12, scale=scale)
    elif condition == "thunder":
        _draw_cloud(draw, cx, cy - size * 0.16, scale=scale * 1.1)
        _draw_bolt(draw, cx, cy - size * 0.16, scale=scale)
    elif condition == "fog":
        _draw_fog(draw, cx, cy, scale=scale)
    else:
        _draw_sun(draw, cx, cy, r=size * 0.25)

    return img


# --------------------------------------------------------------------------
# Main image builder
# --------------------------------------------------------------------------

WIDTH, HEIGHT = 900, 700
MARGIN = 32


def generate_weather_image(data: dict) -> bytes:
    """
    Build a 7-day weather forecast UI image from a station-bulletin-style
    dict and return it as PNG-encoded bytes.
    """
    fonts = Fonts()

    base = _vertical_gradient((WIDTH, HEIGHT), BG_TOP, BG_BOTTOM).convert("RGBA")

    # subtle decorative glow circles in background
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse([WIDTH - 260, -160, WIDTH + 140, 220], fill=(255, 255, 255, 14))
    glow_draw.ellipse([-180, 260, 160, 620], fill=(255, 255, 255, 10))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(40))
    base = Image.alpha_composite(base, glow_layer)

    # ---------------------------------------------------------------
    # Pre-compute all card geometry, then draw every semi-transparent
    # card background onto one dedicated overlay layer and composite it
    # onto the gradient base in a single pass (see _rounded_rect_on_layer
    # docstring for why this can't be drawn directly onto `base`).
    # ---------------------------------------------------------------
    hero_top = 120
    hero_h = 170
    stats_top = hero_top + hero_h + 20
    stats_h = 90
    forecast_top = stats_top + stats_h + 22
    forecast_h = HEIGHT - forecast_top - MARGIN

    n_days = 7
    strip_top = forecast_top + 50
    strip_h = forecast_h - 66
    col_w2 = (WIDTH - 2 * MARGIN - 20) / n_days
    start_x = MARGIN + 10

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    _rounded_rect_on_layer(overlay_draw, [MARGIN, hero_top, WIDTH - MARGIN, hero_top + hero_h],
                           radius=24, fill=CARD_BG_HIGHLIGHT)
    _rounded_rect_on_layer(overlay_draw, [MARGIN, stats_top, WIDTH - MARGIN, stats_top + stats_h],
                           radius=20, fill=CARD_BG)
    _rounded_rect_on_layer(overlay_draw, [MARGIN, forecast_top, WIDTH - MARGIN, forecast_top + forecast_h],
                           radius=20, fill=CARD_BG)
    today_col_left = start_x
    _rounded_rect_on_layer(
        overlay_draw,
        [today_col_left + 4, strip_top - 8, today_col_left + col_w2 - 4, strip_top + strip_h - 4],
        radius=16, fill=CARD_BG_HIGHLIGHT,
    )

    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    # ---------------------------------------------------------------
    # Header: location + date
    # ---------------------------------------------------------------
    city = (data.get("city") or "").strip().title()
    district = (data.get("district") or "").strip().title()
    state = (data.get("state") or "").strip().title()
    station = (data.get("Station_Name") or "").strip()

    location_main = city or station or "Unknown location"
    location_sub_parts = [p for p in [station if station != location_main else None,
                                       district, state] if p]
    location_sub = ", ".join(location_sub_parts)

    date_obj = _parse_date(data.get("Date", ""))
    date_str = date_obj.strftime("%A, %d %b %Y")

    draw.text((MARGIN, 28), location_main, font=fonts.city, fill=WHITE)
    if location_sub:
        draw.text((MARGIN, 76), location_sub, font=fonts.subtitle, fill=MUTED)
    date_w = draw.textbbox((0, 0), date_str, font=fonts.subtitle)[2]
    draw.text((WIDTH - MARGIN - date_w, 40), date_str, font=fonts.subtitle, fill=SOFT_WHITE)

    # ---------------------------------------------------------------
    # "Today" hero card: big current temp + condition + icon
    # ---------------------------------------------------------------
    today_forecast_text = data.get("Todays_Forecast") or ""
    condition = _classify_condition(today_forecast_text)

    # temperature: prefer today's forecast max, else today's max temp,
    # else previous day's max as a last resort
    current_temp = (
        _safe_float(data.get("Todays_Forecast_Max_Temp"))
        or _safe_float(data.get("Today_Max_temp"))
        or _safe_float(data.get("Previous_Day_Max_temp"))
    )
    today_min = _safe_float(data.get("Todays_Forecast_Min_temp")) or _safe_float(data.get("Today_Min_temp"))
    today_max = _safe_float(data.get("Todays_Forecast_Max_Temp")) or _safe_float(data.get("Today_Max_temp"))

    temp_text = f"{current_temp:.0f}" if current_temp is not None else "--"
    draw.text((MARGIN + 30, hero_top + 25), temp_text, font=fonts.temp_big, fill=WHITE)
    temp_num_w = draw.textbbox((0, 0), temp_text, font=fonts.temp_big)[2]
    draw.text((MARGIN + 30 + temp_num_w + 4, hero_top + 40), "\u00b0C",
               font=fonts.temp_unit, fill=SOFT_WHITE)

    minmax_text = f"H:{today_max:.0f}\u00b0  L:{today_min:.0f}\u00b0" if today_max is not None and today_min is not None else ""
    draw.text((MARGIN + 30, hero_top + 130), minmax_text, font=fonts.stat_value, fill=MUTED)

    # wrap the forecast description text to a couple of lines on the right
    desc_x = 380
    desc_max_w = WIDTH - MARGIN - 20 - desc_x - 90  # leave room for icon
    words = today_forecast_text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textbbox((0, 0), trial, font=fonts.desc)[2] <= desc_max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lines = lines[:3]

    icon_size = 100
    icon_img = draw_weather_icon(condition, icon_size)
    base.paste(icon_img, (desc_x, hero_top + 20), icon_img)

    text_y = hero_top + 20
    label = condition.replace("_", " ").title()
    draw.text((desc_x + icon_size + 15, text_y), label, font=fonts.section, fill=WHITE)
    ty = text_y + 30
    for line in lines:
        draw.text((desc_x + icon_size + 15, ty), line, font=fonts.desc, fill=SOFT_WHITE)
        ty += 26

    # ---------------------------------------------------------------
    # Stats row: humidity, rainfall, sunrise/sunset, moonrise/moonset
    # ---------------------------------------------------------------
    rh = data.get("Relative_Humidity_at_0830") or data.get("Previous_Day_Relative_Humidity_at_1730")
    rainfall = data.get("Past_24_hrs_Rainfall")
    sunrise = data.get("Sunrise_time") or "--"
    sunset = data.get("Sunset_time") or "--"
    moonrise = data.get("Moonrise_time") or "--"
    moonset = data.get("Moonset_time") or "--"

    stat_items = [
        ("HUMIDITY", f"{rh}%" if rh not in (None, "NA") else "--"),
        ("RAINFALL (24H)", f"{rainfall} mm" if rainfall not in (None, "NA") else "0 mm"),
        ("SUNRISE / SUNSET", f"{sunrise} / {sunset}"),
        ("MOONRISE / MOONSET", f"{moonrise} / {moonset}"),
    ]
    col_w = (WIDTH - 2 * MARGIN) / len(stat_items)
    for i, (label_txt, value_txt) in enumerate(stat_items):
        x = MARGIN + i * col_w
        draw.text((x + 24, stats_top + 20), label_txt, font=fonts.stat_label, fill=MUTED)
        draw.text((x + 24, stats_top + 44), value_txt, font=fonts.stat_value, fill=WHITE)
        if i > 0:
            draw.line([(x, stats_top + 16), (x, stats_top + stats_h - 16)], fill=DIVIDER, width=1)

    # ---------------------------------------------------------------
    # 7-day forecast strip
    # ---------------------------------------------------------------
    draw.text((MARGIN + 20, forecast_top + 14), "7-DAY FORECAST", font=fonts.section, fill=MUTED)

    days = []
    days.append({
        "label": "TODAY",
        "date": date_obj,
        "max": today_max,
        "min": today_min,
        "forecast": today_forecast_text,
    })
    for n in range(2, 8):
        d_max = _safe_float(data.get(f"Day_{n}_Max_Temp"))
        d_min = _safe_float(data.get(f"Day_{n}_Min_temp"))
        d_forecast = data.get(f"Day_{n}_Forecast") or ""
        d_date = date_obj + dt.timedelta(days=n - 1)
        days.append({
            "label": _weekday_short(d_date),
            "date": d_date,
            "max": d_max,
            "min": d_min,
            "forecast": d_forecast,
        })

    # find overall min/max across the week for a small temp-range bar
    all_temps = [d["max"] for d in days if d["max"] is not None] + \
                [d["min"] for d in days if d["min"] is not None]
    week_min = min(all_temps) if all_temps else 0
    week_max = max(all_temps) if all_temps else 1
    span = max(week_max - week_min, 1)

    for i, d in enumerate(days):
        cx = start_x + col_w2 * i + col_w2 / 2

        _text_centered(draw, cx, strip_top, d["label"], fonts.day_name, WHITE)
        date_lbl = d["date"].strftime("%d %b")
        _text_centered(draw, cx, strip_top + 22, date_lbl, fonts.day_date, MUTED)

        cond = _classify_condition(d["forecast"])
        icon = draw_weather_icon(cond, 46)
        base.paste(icon, (int(cx - 23), int(strip_top + 44)), icon)

        max_t = d["max"]
        min_t = d["min"]
        max_txt = f"{max_t:.0f}\u00b0" if max_t is not None else "--"
        min_txt = f"{min_t:.0f}\u00b0" if min_t is not None else "--"

        temps_y = strip_top + 100
        _text_centered(draw, cx, temps_y, max_txt, fonts.day_temp, WHITE)

        # mini range bar
        bar_w = col_w2 * 0.55
        bar_y = temps_y + 26
        bx0, bx1 = cx - bar_w / 2, cx + bar_w / 2
        draw.line([(bx0, bar_y), (bx1, bar_y)], fill=DIVIDER, width=4)
        if max_t is not None and min_t is not None:
            rel_min = (min_t - week_min) / span
            rel_max = (max_t - week_min) / span
            hx0 = bx0 + rel_min * bar_w
            hx1 = bx0 + rel_max * bar_w
            draw.line([(hx0, bar_y), (hx1, bar_y)], fill=ACCENT_YELLOW, width=4)

        _text_centered(draw, cx, bar_y + 12, min_txt, fonts.day_temp_min, MUTED)

    # ---------------------------------------------------------------
    # Encode to PNG bytes
    # ---------------------------------------------------------------
    out = base.convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------------
# Demo / manual test
# --------------------------------------------------------------------------

if __name__ == "__main__":
    sample = {
        "Date": "2026-09-24",
        "Station_Code": "53",
        "Station_Name": "Kanpur Airforce",
        "Today_Max_temp": None,
        "Today_Max_Departure_from_Normal": None,
        "Previous_Day_Max_temp": "32.6",
        "Previous_Day_Max_Departure_from_Normal": "NA",
        "Today_Min_temp": "25.0",
        "Today_Min_Departure_from_Normal": "NA",
        "Past_24_hrs_Rainfall": "3.40",
        "Relative_Humidity_at_0830": "84",
        "Relative_Humidity_at_1730": None,
        "Previous_Day_Relative_Humidity_at_1730": "81",
        "Sunset_time": "18:04",
        "Sunrise_time": "05:58",
        "Moonset_time": "03:29",
        "Moonrise_time": "16:39",
        "Todays_Forecast_Max_Temp": "31.0",
        "Todays_Forecast_Min_temp": "24.0",
        "Todays_Forecast": "Partly cloudy sky with one or two spells of rain or thundershowers",
        "Day_2_Max_Temp": "29.0",
        "Day_2_Min_temp": "24.0",
        "Day_2_Forecast": "Generally cloudy sky with a few spells of rain or thundershowers",
        "Day_3_Max_Temp": "30.0",
        "Day_3_Min_temp": "24.0",
        "Day_3_Forecast": "Generally cloudy sky with one or two spells of rain or thundershowers",
        "Day_4_Max_Temp": "31.0",
        "Day_4_Min_temp": "24.0",
        "Day_4_Forecast": "Partly cloudy sky",
        "Day_5_Max_Temp": "32.0",
        "Day_5_Min_temp": "25.0",
        "Day_5_Forecast": "Partly cloudy sky",
        "Day_6_Max_Temp": "33.0",
        "Day_6_Min_temp": "25.0",
        "Day_6_Forecast": "Partly cloudy sky",
        "Day_7_Max_Temp": "33.0",
        "Day_7_Min_temp": "25.0",
        "Day_7_Forecast": "Partly cloudy sky",
        "Latitude": "26.416666666",
        "Longitude": "80.383333333",
        "city": "Delhi",
        "village": None,
        "district": "kanpur nagar",
        "state": "uttar pradesh",
    }

    img_bytes = generate_weather_image(sample)
    
    
    URL = "http://localhost:5000/get_tool_images"
    # 1. Prepare your custom internal authorization token header
    headers = {
        "Authorization": "Bearer YOUR_INTERNAL_TOKEN_HERE"  # Update this to match your _internal_token_ok() logic
    }

    # 2. Add your text form fields
    form_data = {
        "user_id": "Devin",
        "conversation_id": "aef183b5cc11"  # Optional, but accepted by your endpoint
    }
    
    file_payload = {
        "image":img_bytes
    }
    
    response = requests.post(URL, headers=headers, data=form_data, files=file_payload)
    
    # 5. Handle the server response
    if response.status_code == 200:
        print("Success!")
        print(response.json())
    else:
        print(f"Failed with status code {response.status_code}: {response.text}")
    # with open("weather_preview.png", "wb") as f:
    #     f.write(img_bytes)
    # print(f"Wrote {len(img_bytes)} bytes to weather_preview.png")