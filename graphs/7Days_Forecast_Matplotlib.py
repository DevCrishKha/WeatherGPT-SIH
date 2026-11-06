# Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
#
# This source code and all associated materials are proprietary and
# confidential to [Dev Crish Kha]. Unauthorized copying, modification,
# distribution, publication, sublicensing, or use of this code, in whole
# or in part, is strictly prohibited without prior written permission
# from the copyright holder.

"""
Beautiful weather dashboard built with Matplotlib.

Usage as a module:
    from weather_dashboard import generate_dashboard
    generate_dashboard(my_dict, out_path="/mnt/user-data/outputs/weather_dashboard.png")

Renders, from a single weather-station record (dict):
  - A 7-day Max/Min temperature trend (today + forecast)
  - Info cards for current conditions (humidity, rainfall, sun/moon times)
  - A header with station identity
"""

import textwrap
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import io

# ---------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------

SUB = "#000000"
TXT = "#000000"
PANEL = "#f6f6f7"
BG = "#ffffff"
# BG = "#0f1220"
# PANEL = "#1a1e33"
# TXT = "#eef0fa"
# SUB = "#9aa0c4"
GRID = "#2a2f4a"
MAX_C = "#ff8a5c"
MIN_C = "#5cc9ff"
ACCENT = "#ffd166"
MOON_C = "#c6a8ff"


def _f(v, default=np.nan):
    """Safely convert a value to float, treating None/'NA'/missing as NaN."""
    if v is None or v == "NA":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _info_card(ax, title, value, subtitle, color):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    box = FancyBboxPatch((0.02, 0.05), 0.96, 0.9,
                          boxstyle="round,pad=0.02,rounding_size=0.06",
                          linewidth=0, facecolor=PANEL, zorder=1)
    ax.add_patch(box)
    ax.text(0.5, 0.72, title, fontsize=11.5, color=SUB, ha="center", va="center")
    ax.text(0.5, 0.42, value, fontsize=22, fontweight="bold", color=color, ha="center", va="center")
    ax.text(0.5, 0.16, subtitle, fontsize=9.5, color=SUB, ha="center", va="center")


def generate_dashboard(data, out_path="weather_dashboard.png", show=False):
    """
    Build the weather dashboard PNG from a station-record dict.

    Parameters
    ----------
    data : dict
        A single station record, using the same keys as the source
        MongoDB-style document (Date, Station_Name, Todays_Forecast_Max_Temp,
        Day_2_Max_Temp ... Day_7_Min_temp, Relative_Humidity_at_0830,
        Past_24_hrs_Rainfall, Sunrise_time, Sunset_time, etc.).
        Missing/None/'NA' values are handled gracefully.
    out_path : str
        Where to save the PNG.
    show : bool
        If True, also calls plt.show() (useful outside a headless run).

    Returns
    -------
    str
        The path the image was saved to.
    """
    g = data.get  # shorthand

    # -- 7-day series (Today + Day_2..Day_7) -----------------------------
    labels = ["Today"] + [f"Day {i}" for i in range(2, 8)]
    max_temps = [_f(g("Todays_Forecast_Max_Temp"))] + [_f(g(f"Day_{i}_Max_Temp")) for i in range(2, 8)]
    min_temps = [_f(g("Todays_Forecast_Min_temp"))] + [_f(g(f"Day_{i}_Min_temp")) for i in range(2, 8)]
    x = np.arange(len(labels))

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "text.color": TXT,
        "axes.edgecolor": GRID,
    })

    fig = plt.figure(figsize=(12, 9), facecolor=BG)
    gs = fig.add_gridspec(
        nrows=3, ncols=3,
        height_ratios=[0.9, 3.2, 1.4],
        width_ratios=[1, 1, 1],
        hspace=0.55, wspace=0.35,
        left=0.06, right=0.96, top=0.93, bottom=0.06,
    )

    # -- Header ------------------------------------------------------------
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.axis("off")
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)

    date_raw = g("Date")
    try:
        date_fmt = datetime.strptime(date_raw, "%Y-%m-%d").strftime("%A, %d %B %Y")
    except (TypeError, ValueError):
        date_fmt = date_raw or ""

    station_name = g("Station_Name") or "Unknown Station"
    district = (g("district") or "").title()
    state = (g("state") or "").title()

    ax_header.text(0, 0.75, station_name, fontsize=26, fontweight="bold", color=TXT, va="top")
    ax_header.text(0, 0.25, f"{district}, {state}   •   {date_fmt}".strip(" •"),
                   fontsize=12, color=SUB, va="top")

    prev_max = _f(g("Previous_Day_Max_temp"))
    today_min = _f(g("Today_Min_temp"))
    prev_max_str = f"{prev_max:.1f}°" if not np.isnan(prev_max) else "—"
    today_min_str = f"{today_min:.1f}°" if not np.isnan(today_min) else "—"
    ax_header.text(1, 0.75, prev_max_str, fontsize=30, fontweight="bold",
                   color=MAX_C, va="top", ha="right")
    ax_header.text(1, 0.25, f"Prev-day High  •  Today's Low {today_min_str}",
                   fontsize=11, color=SUB, va="top", ha="right")

    # -- Main temperature trend chart ---------------------------------------
    ax = fig.add_subplot(gs[1, :])
    ax.set_facecolor(PANEL)

    ax.fill_between(x, min_temps, max_temps, color=MAX_C, alpha=0.08, zorder=1)

    ax.plot(x, max_temps, color=MAX_C, lw=3, marker="o", markersize=8,
            markerfacecolor=BG, markeredgecolor=MAX_C, markeredgewidth=2.5,
            zorder=3, label="Max Temp (°C)")
    ax.plot(x, min_temps, color=MIN_C, lw=3, marker="o", markersize=8,
            markerfacecolor=BG, markeredgecolor=MIN_C, markeredgewidth=2.5,
            zorder=3, label="Min Temp (°C)")

    for xi, yv in zip(x, max_temps):
        if not np.isnan(yv):
            ax.annotate(f"{yv:.0f}°", (xi, yv), textcoords="offset points", xytext=(0, 12),
                        ha="center", fontsize=10.5, fontweight="bold", color=MAX_C)
    for xi, yv in zip(x, min_temps):
        if not np.isnan(yv):
            ax.annotate(f"{yv:.0f}°", (xi, yv), textcoords="offset points", xytext=(0, -18),
                        ha="center", fontsize=10.5, fontweight="bold", color=MIN_C)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11, color=SUB)
    finite_vals = [v for v in max_temps + min_temps if not np.isnan(v)]
    if finite_vals:
        ax.set_ylim(min(finite_vals) - 4, max(finite_vals) + 5)
    ax.set_yticks([])
    ax.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    ax.legend(loc="upper right", frameon=False, fontsize=11, labelcolor=TXT, ncol=2)
    ax.set_title("7-Day Temperature Outlook", fontsize=15, fontweight="bold",
                 color=TXT, loc="left", pad=14)

    todays_forecast = g("Todays_Forecast")
    if todays_forecast:
        wrapped = "\n".join(textwrap.wrap(todays_forecast, 26))
        # box around Today's Forecast text
        box_style = dict(
            boxstyle="round,pad=0.5",  #  (Round corners) 
            fc="white",                #  (Face color)
            ec="gray",                 # (Edge color) 
            lw=1                       # (Line width)
        )
        ax.text(0, ax.get_ylim()[0] + -4.5, wrapped, fontsize=10, color=MAX_C, ha="center", va="bottom", bbox=box_style)

    # -- Info cards row (Humidity, Rainfall, Sun/Moon) ----------------------
    ax_h = fig.add_subplot(gs[2, 0])
    rh0830 = g("Relative_Humidity_at_0830") or "—"
    prev_rh = g("Previous_Day_Relative_Humidity_at_1730") or "—"
    _info_card(ax_h, "HUMIDITY (08:30)", f"{rh0830}%", f"Prev 17:30 → {prev_rh}%", ACCENT)

    ax_r = fig.add_subplot(gs[2, 1])
    rain = g("Past_24_hrs_Rainfall") or "0"
    _info_card(ax_r, "RAINFALL (24H)", f"{rain} mm", "Past 24 hours", MIN_C)

    ax_s = fig.add_subplot(gs[2, 2])
    sunrise = g("Sunrise_time") or "—"
    sunset = g("Sunset_time") or "—"
    moonrise = g("Moonrise_time") or "—"
    moonset = g("Moonset_time") or "—"
    _info_card(ax_s, "SUN & MOON", f"{sunrise} / {sunset}", f"Moon  {moonrise} / {moonset}", MOON_C)

    # -- Save ----------------------------------------------------------------
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, facecolor=BG, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()   # raw PNG bytes


if __name__ == "__main__":
    # Sample record for standalone testing / demo
    sample_data = {
        "Date": "2026-09-24",
        "Station_Code": "53",
        "Station_Name": "Kanpur Airforce",
        "Today_Max_temp": None,
        "Previous_Day_Max_temp": "32.6",
        "Today_Min_temp": "25.0",
        "Past_24_hrs_Rainfall": "3.40",
        "Relative_Humidity_at_0830": "84",
        "Previous_Day_Relative_Humidity_at_1730": "81",
        "Sunset_time": "18:04",
        "Sunrise_time": "05:58",
        "Moonset_time": "03:29",
        "Moonrise_time": "16:39",
        "Todays_Forecast_Max_Temp": "31.0",
        "Todays_Forecast_Min_temp": "24.0",
        "Todays_Forecast": "Partly cloudy sky with one or two spells of rain or thundershowers",
        "Day_2_Max_Temp": "29.0", "Day_2_Min_temp": "24.0",
        "Day_3_Max_Temp": "30.0", "Day_3_Min_temp": "24.0",
        "Day_4_Max_Temp": "31.0", "Day_4_Min_temp": "24.0",
        "Day_5_Max_Temp": "32.0", "Day_5_Min_temp": "25.0",
        "Day_6_Max_Temp": "33.0", "Day_6_Min_temp": "25.0",
        "Day_7_Max_Temp": "33.0", "Day_7_Min_temp": "25.0",
        "city": "jajmau", "district": "kanpur nagar", "state": "uttar pradesh",
    }
    png_bytes = generate_dashboard(sample_data)
    with open("preview.png", "wb") as f:
        f.write(png_bytes)
    print("Saved preview.png — open it to view")