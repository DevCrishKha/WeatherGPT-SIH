# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

"""
current_weather_image.py

Generates a "current weather conditions" style PNG image (a single
point-in-time observation, not a multi-day forecast) from a data dict
shaped like an IMD/AWS station observation, e.g.:

{
    'Station Id': '42724',
    'Station': 'Agartala',
    'Date of Observation': '2026-09-24',
    'Time': '21',
    'Mean Sea Level Pressure': '1009',
    'Wind Direction': '50',
    'Wind Speed KMPH': '1.9',
    'Temperature': '27',
    'Weather Code': '10',
    'Nebulosity': '6',
    'Humidity': '89',
    'Last 24 hrs Rainfall': '0',
    'Feel Like': '30.9',
    'WEATHER_ICON': 500,
    'WEATHER_MESSAGE': 'Mist',
    'Sunrise': '05:14',
    'Sunset': '17:19',
    'Moonrise': '16:25',
    'Moonset': '03:42',
    'city': 'agartala',
    'district': 'west tripura',
    'state': 'tripura',
}

Main entry point:

    generate_current_weather_image(data: dict) -> bytes

Returns raw PNG bytes, ready to be sent to a frontend
(e.g. `Response(img_bytes, mimetype="image/png")` in Flask,
or base64-encoded into a data URI).
"""

from __future__ import annotations

import io
import math
import datetime as dt
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests


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
        self.city = _font("DejaVuSans-Bold", 54)
        self.subtitle = _font("DejaVuSans", 23)
        self.temp_big = _font("DejaVuSans-Bold", 118)
        self.temp_unit = _font("DejaVuSans-Bold", 48)
        self.desc = _font("DejaVuSans", 25)
        self.section = _font("DejaVuSans-Bold", 21)
        self.stat_label = _font("DejaVuSans", 17)
        self.stat_value = _font("DejaVuSans-Bold", 20)
        self.small_value = _font("DejaVuSans", 16)


# --------------------------------------------------------------------------
# Colour palette (dark "modern weather app" theme -- matches
# weather_image.py's 7-day forecast card so both can be used together)
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


def _format_hour(hour_str: str) -> str:
    """'21' -> '9:00 PM', '5' -> '5:00 AM'."""
    h = _safe_float(hour_str)
    if h is None:
        return str(hour_str)
    h = int(h) % 24
    period = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
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
    """Classify a free-text weather message into an icon category."""
    t = (text or "").lower()
    if "thunder" in t:
        return "thunder"
    if "rain" in t or "shower" in t or "drizzle" in t:
        return "rain"
    if "mist" in t or "fog" in t or "haze" in t or "smoke" in t:
        return "fog"
    if "overcast" in t or "cloudy" in t and "partly" not in t:
        return "cloudy"
    if "partly" in t or "cloud" in t:
        return "partly_cloudy"
    if "clear" in t or "sunny" in t or "fair" in t:
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
    transparent RGBA layer -- drawing translucent fills directly onto an
    already-opaque RGBA image paints a flat opaque colour instead of
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
# Weather icon drawing (simple flat vector icons on a transparent layer --
# no external icon/emoji font required)
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


def draw_wind_arrow(size: int, direction_deg: float, color=ACCENT_BLUE) -> Image.Image:
    """
    Return an RGBA icon of a compass arrow rotated to point in the
    direction the wind is blowing FROM (meteorological convention: 0
    degrees / arrow pointing up = wind from the north).
    """
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    cx, cy = size / 2, size / 2
    r = size * 0.38

    # faint compass ring
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 70), width=2)
    # arrow pointing "up" (north) before rotation
    draw.line([(cx, cy - r), (cx, cy + r * 0.5)], fill=color, width=max(2, size // 18))
    draw.polygon(
        [(cx, cy - r - size * 0.06), (cx - size * 0.09, cy - r * 0.45),
         (cx + size * 0.09, cy - r * 0.45)],
        fill=color,
    )
    # rotate: image rotation is counter-clockwise for positive angles,
    # and wind direction is measured clockwise from north, so negate.
    rotated = base.rotate(-direction_deg, resample=Image.BICUBIC, center=(cx, cy))
    return rotated


# --------------------------------------------------------------------------
# Main image builder
# --------------------------------------------------------------------------

WIDTH = 900
MARGIN = 32
HERO_H = 170
ROW_H = 100
GAP = 20


def generate_current_weather_image(data: dict) -> bytes:
    """
    Build a "current conditions" weather UI image from a single-observation
    station dict and return it as PNG-encoded bytes.
    """
    fonts = Fonts()

    header_h = 118
    hero_top = header_h
    row1_top = hero_top + HERO_H + GAP
    row2_top = row1_top + ROW_H + GAP
    height = row2_top + ROW_H + MARGIN

    base = _vertical_gradient((WIDTH, height), BG_TOP, BG_BOTTOM).convert("RGBA")

    # subtle decorative glow circles in background
    glow_layer = Image.new("RGBA", (WIDTH, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.ellipse([WIDTH - 260, -160, WIDTH + 140, 220], fill=(255, 255, 255, 14))
    glow_draw.ellipse([-180, height - 340, 160, height + 20], fill=(255, 255, 255, 10))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(40))
    base = Image.alpha_composite(base, glow_layer)

    # ---------------------------------------------------------------
    # Card backgrounds go on one overlay layer, composited once (see
    # _rounded_rect_on_layer docstring for why).
    # ---------------------------------------------------------------
    overlay = Image.new("RGBA", (WIDTH, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    _rounded_rect_on_layer(overlay_draw, [MARGIN, hero_top, WIDTH - MARGIN, hero_top + HERO_H],
                           radius=24, fill=CARD_BG_HIGHLIGHT)
    _rounded_rect_on_layer(overlay_draw, [MARGIN, row1_top, WIDTH - MARGIN, row1_top + ROW_H],
                           radius=20, fill=CARD_BG)
    _rounded_rect_on_layer(overlay_draw, [MARGIN, row2_top, WIDTH - MARGIN, row2_top + ROW_H],
                           radius=20, fill=CARD_BG)
    base = Image.alpha_composite(base, overlay)
    draw = ImageDraw.Draw(base)

    # ---------------------------------------------------------------
    # Header: location + date/time
    # ---------------------------------------------------------------
    city = (data.get("city") or "").strip().title()
    district = (data.get("district") or "").strip().title()
    state = (data.get("state") or "").strip().title()
    station = (data.get("Station") or "").strip()

    location_main = city or station or "Unknown location"
    location_sub_parts = [p for p in [station if station != location_main else None,
                                       district, state] if p]
    location_sub = ", ".join(location_sub_parts)

    date_obj = _parse_date(data.get("Date of Observation") or data.get("date") or "")
    date_str = date_obj.strftime("%A, %d %b %Y")
    time_str = _format_hour(data.get("Time"))

    draw.text((MARGIN, 24), location_main, font=fonts.city, fill=WHITE)
    if location_sub:
        draw.text((MARGIN, 88), location_sub, font=fonts.subtitle, fill=MUTED)

    date_w = draw.textbbox((0, 0), date_str, font=fonts.subtitle)[2]
    draw.text((WIDTH - MARGIN - date_w, 34), date_str, font=fonts.subtitle, fill=SOFT_WHITE)
    time_w = draw.textbbox((0, 0), f"Observed {time_str}", font=fonts.stat_label)[2]
    draw.text((WIDTH - MARGIN - time_w, 66), f"Observed {time_str}", font=fonts.stat_label, fill=MUTED)

    # ---------------------------------------------------------------
    # Hero card: current temp, "feels like", condition icon + message
    # ---------------------------------------------------------------
    temp = _safe_float(data.get("Temperature"))
    feels_like = _safe_float(data.get("Feel Like"))
    weather_message = data.get("WEATHER_MESSAGE") or ""
    condition = _classify_condition(weather_message)

    temp_text = f"{temp:.0f}" if temp is not None else "--"
    draw.text((MARGIN + 30, hero_top + 8), temp_text, font=fonts.temp_big, fill=WHITE)
    temp_num_w = draw.textbbox((0, 0), temp_text, font=fonts.temp_big)[2]
    draw.text((MARGIN + 30 + temp_num_w + 6, hero_top + 26), "\u00b0C",
               font=fonts.temp_unit, fill=SOFT_WHITE)

    feels_text = f"Feels like {feels_like:.0f}\u00b0" if feels_like is not None else ""
    draw.text((MARGIN + 30, hero_top + 138), feels_text, font=fonts.stat_value, fill=MUTED)

    desc_x = 380
    desc_max_w = WIDTH - MARGIN - 20 - desc_x - 90
    words = weather_message.split()
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
    lines = lines[:3] or ["--"]

    icon_size = 100
    icon_img = draw_weather_icon(condition, icon_size)
    base.paste(icon_img, (desc_x, hero_top + 20), icon_img)

    text_y = hero_top + 16
    label = condition.replace("_", " ").title()
    draw.text((desc_x + icon_size + 15, text_y), label, font=fonts.section, fill=WHITE)
    ty = text_y + 34
    for line in lines:
        draw.text((desc_x + icon_size + 15, ty), line, font=fonts.desc, fill=SOFT_WHITE)
        ty += 30

    # ---------------------------------------------------------------
    # Stats row 1: Humidity | Wind | Pressure | Rainfall (24h)
    # ---------------------------------------------------------------
    humidity = data.get("Humidity")
    wind_speed = _safe_float(data.get("Wind Speed KMPH"))
    wind_dir_deg = _safe_float(data.get("Wind Direction"))
    pressure = data.get("Mean Sea Level Pressure")
    rainfall = data.get("Last 24 hrs Rainfall")

    wind_compass = _degrees_to_compass(wind_dir_deg)
    wind_text = f"{wind_speed:.1f} km/h {wind_compass}" if wind_speed is not None else "--"

    row1_items = [
        ("HUMIDITY", f"{humidity}%" if humidity not in (None, "NA") else "--"),
        ("WIND", wind_text),
        ("PRESSURE", f"{pressure} hPa" if pressure not in (None, "NA") else "--"),
        ("RAINFALL (24H)", f"{rainfall} mm" if rainfall not in (None, "NA") else "0 mm"),
    ]
    col_w = (WIDTH - 2 * MARGIN) / len(row1_items)
    for i, (label_txt, value_txt) in enumerate(row1_items):
        x = MARGIN + i * col_w
        draw.text((x + 24, row1_top + 16), label_txt, font=fonts.stat_label, fill=MUTED)
        if label_txt == "WIND" and wind_dir_deg is not None:
            arrow = draw_wind_arrow(34, wind_dir_deg)
            base.paste(arrow, (int(x + 24), int(row1_top + 42)), arrow)
            draw.text((x + 24 + 42, row1_top + 48), value_txt, font=fonts.stat_value, fill=WHITE)
        else:
            draw.text((x + 24, row1_top + 40), value_txt, font=fonts.stat_value, fill=WHITE)
        if i > 0:
            draw.line([(x, row1_top + 16), (x, row1_top + ROW_H - 16)], fill=DIVIDER, width=1)

    # ---------------------------------------------------------------
    # Stats row 2: Cloud cover | Sunrise/Sunset | Moonrise/Moonset
    # ---------------------------------------------------------------
    nebulosity = data.get("Nebulosity")
    neb_text = f"{nebulosity}/8 oktas" if nebulosity not in (None, "NA") else "--"
    sunrise = data.get("Sunrise") or "--"
    sunset = data.get("Sunset") or "--"
    moonrise = data.get("Moonrise") or "--"
    moonset = data.get("Moonset") or "--"

    row2_items = [
        ("CLOUD COVER", neb_text),
        ("SUNRISE / SUNSET", f"{sunrise} / {sunset}"),
        ("MOONRISE / MOONSET", f"{moonrise} / {moonset}"),
    ]
    col_w2 = (WIDTH - 2 * MARGIN) / len(row2_items)
    for i, (label_txt, value_txt) in enumerate(row2_items):
        x = MARGIN + i * col_w2
        draw.text((x + 24, row2_top + 16), label_txt, font=fonts.stat_label, fill=MUTED)
        draw.text((x + 24, row2_top + 40), value_txt, font=fonts.stat_value, fill=WHITE)
        if i > 0:
            draw.line([(x, row2_top + 16), (x, row2_top + ROW_H - 16)], fill=DIVIDER, width=1)

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
        "Station Id": "42724",
        "Station": "Agartala",
        "Date of Observation": "2026-09-24",
        "Time": "21",
        "Mean Sea Level Pressure": "1009",
        "Wind Direction": "50",
        "Wind Speed KMPH": "1.9",
        "Temperature": "27",
        "Weather Code": "10",
        "Nebulosity": "6",
        "Humidity": "89",
        "Last 24 hrs Rainfall": "0",
        "Feel Like": "30.9",
        "WEATHER_ICON": 500,
        "WEATHER_MESSAGE": "Mist",
        "BACKGROUND": None,
        "BACKGROUND_URL": None,
        "Sunrise": "05:14",
        "Sunset": "17:19",
        "Moonrise": "16:25",
        "Moonset": "03:42",
        "city": "Delhi",
        "village": None,
        "district": "west tripura",
        "state": "tripura",
        "date": "2026-09-24",
    }

    img_bytes = generate_current_weather_image(sample)
    
    URL = "http://localhost:5000/get_tool_image"
    # 1. Prepare your custom internal authorization token header
    headers = {
        "Authorization": "Bearer YOUR_INTERNAL_TOKEN_HERE"  # Update this to match your _internal_token_ok() logic
    }

    # 2. Add your text form fields
    form_data = {
        "user_id": "Devin",
        "conversation_id": "d95190810858"  # Optional, but accepted by your endpoint
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
    
    # with open("current_weather_preview.png", "wb") as f:
    #     f.write(img_bytes)
    # print(f"Wrote {len(img_bytes)} bytes to current_weather_preview.png")