import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import textwrap
from streamlit.components.v1 import html as components_html


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# SAFE HTML RENDER
# =========================
def render_html(html: str):
    html = textwrap.dedent(html).strip()
    html = " ".join(line.strip() for line in html.splitlines())
    st.markdown(html, unsafe_allow_html=True)


# =========================
# LOAD ICON PACK
# =========================
st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">',
    unsafe_allow_html=True
)


# =========================
# CSS
# =========================
render_html("""
<style>
:root {
    --bg: #eef0f3;
    --card: #f3eee8;
    --card2: #f8f5f0;
    --text: #2f3341;
    --muted: #74777f;
    --orange: #f5a623;
    --green: #43b36a;
    --blue: #5b83ff;
    --purple: #9a7dff;
    --red: #ff7c4d;
    --line: #ded8d1;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1280px;
    padding-top: 1.8rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background: #e6e9ed;
}

.main-title {
    font-size: 32px;
    font-weight: 850;
    color: var(--text);
    margin-bottom: 6px;
}

.sub-title {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 20px;
}

.section-title {
    font-size: 24px;
    font-weight: 850;
    color: var(--text);
    margin: 22px 0 14px 0;
}

.metric-card {
    background: var(--card);
    border-radius: 24px;
    padding: 18px 20px;
    min-height: 166px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.05);
    margin-bottom: 16px;
}

.metric-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.metric-title {
    font-size: 16px;
    font-weight: 850;
    color: var(--text);
}

.metric-icon-box {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    background: rgba(255,255,255,0.8);
    display: flex;
    align-items: center;
    justify-content: center;
}

.metric-icon-box i {
    font-size: 25px;
}

.metric-value {
    font-size: 31px;
    font-weight: 850;
    color: var(--text);
    margin-top: 14px;
}

.metric-desc {
    color: var(--muted);
    font-size: 14px;
    margin-top: 4px;
}

.progress-wrap {
    width: 100%;
    height: 9px;
    background: var(--line);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 14px;
}

.progress-fill {
    height: 100%;
    border-radius: 999px;
}
</style>
""")


# =========================
# HELPERS
# =========================
def weather_code_to_text(code):
    mapping = {
        0: ("Clear sky", "wi wi-day-sunny"),
        1: ("Mainly clear", "wi wi-day-sunny-overcast"),
        2: ("Partly cloudy", "wi wi-day-cloudy"),
        3: ("Overcast", "wi wi-cloudy"),

        45: ("Fog", "wi wi-fog"),
        48: ("Rime fog", "wi wi-fog"),

        51: ("Light drizzle", "wi wi-sprinkle"),
        53: ("Moderate drizzle", "wi wi-sprinkle"),
        55: ("Dense drizzle", "wi wi-rain"),
        56: ("Freezing drizzle", "wi wi-rain-mix"),
        57: ("Freezing drizzle", "wi wi-rain-mix"),

        61: ("Slight rain", "wi wi-rain"),
        63: ("Moderate rain", "wi wi-rain"),
        65: ("Heavy rain", "wi wi-rain-wind"),
        66: ("Freezing rain", "wi wi-rain-mix"),
        67: ("Freezing rain", "wi wi-rain-mix"),

        71: ("Slight snow", "wi wi-snow"),
        73: ("Moderate snow", "wi wi-snow"),
        75: ("Heavy snow", "wi wi-snowflake-cold"),
        77: ("Snow grains", "wi wi-snow"),

        80: ("Rain showers", "wi wi-showers"),
        81: ("Rain showers", "wi wi-showers"),
        82: ("Violent rain showers", "wi wi-storm-showers"),

        85: ("Snow showers", "wi wi-snow"),
        86: ("Snow showers", "wi wi-snow"),

        95: ("Thunderstorm", "wi wi-thunderstorm"),
        96: ("Thunderstorm with hail", "wi wi-thunderstorm"),
        99: ("Thunderstorm with hail", "wi wi-thunderstorm"),
    }
    return mapping.get(int(code), ("Unknown", "wi wi-na"))


def fahrenheit(c):
    return c * 9 / 5 + 32


def wind_direction_text(deg):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(deg / 45) % 8]


def clamp(x, min_val=0, max_val=100):
    return max(min_val, min(x, max_val))


def metric_card(title, value, desc, icon_class, color, percent):
    percent = clamp(percent)

    return f"""
<div class="metric-card">
    <div class="metric-head">
        <div class="metric-title">{title}</div>
        <div class="metric-icon-box">
            <i class="{icon_class}" style="color:{color};"></i>
        </div>
    </div>
    <div class="metric-value">{value}</div>
    <div class="metric-desc">{desc}</div>
    <div class="progress-wrap">
        <div class="progress-fill" style="width:{percent}%; background:{color};"></div>
    </div>
</div>
"""


# =========================
# BING STYLE MAIN CARD
# =========================
def bing_main_weather_card(
    display_city,
    current,
    daily,
    hourly,
    temp_now,
    feels,
    unit,
    weather_text,
    weather_icon
):
    daily_rows = []

    for i, row in daily.head(6).reset_index(drop=True).iterrows():
        _, icon = weather_code_to_text(row["weather_code"])

        if i == 0:
            day_label = "Today"
        else:
            day_label = row["time"].strftime("%a %d")

        daily_rows.append(f"""
        <div class="bing-day">
            <div class="bing-day-name">{day_label}</div>
            <div class="bing-day-icon"><i class="{icon}"></i></div>
            <div class="bing-day-temp">
                {row["temp_max_show"]:.0f}° {row["temp_min_show"]:.0f}°
            </div>
        </div>
        """)

    daily_html = "".join(daily_rows)

    chart_data = hourly.head(8).copy().reset_index(drop=True)

    temps = chart_data["temperature_show"].tolist()
    rains = chart_data["precipitation_probability"].tolist()
    times = [t.strftime("%I %p").lstrip("0") for t in chart_data["time"]]

    min_t = min(temps)
    max_t = max(temps)
    temp_range = max(max_t - min_t, 1)

    width = 720
    height = 160
    left_pad = 38
    right_pad = 28
    top_pad = 22
    bottom_pad = 52

    usable_w = width - left_pad - right_pad
    usable_h = height - top_pad - bottom_pad

    points = []
    temp_labels_html = ""
    rain_labels_html = ""

    for i, temp in enumerate(temps):
        x = left_pad + i * usable_w / (len(temps) - 1)
        y = top_pad + (max_t - temp) / temp_range * usable_h
        points.append((x, y))

        temp_labels_html += f"""
        <div class="temp-label" style="left:{x - 10}px; top:{y - 24}px;">
            {temp:.0f}°
        </div>
        """

        rain_labels_html += f"""
        <div class="rain-label" style="left:{x - 20}px;">
            <span class="drop">💧</span>{rains[i]:.0f}%
            <div class="time-label">{times[i]}</div>
        </div>
        """

    polyline_points = " ".join([f"{x},{y}" for x, y in points])
    area_points = (
        f"{left_pad},{height-bottom_pad} "
        + polyline_points
        + f" {width-right_pad},{height-bottom_pad}"
    )

    wind_dir = wind_direction_text(current["wind_direction_10m"])

    if unit == "°C":
        active_c = "unit-active"
        active_f = "unit-off"
    else:
        active_c = "unit-off"
        active_f = "unit-active"

    html_code = f"""
    <html>
    <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">

        <style>
            body {{
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                background: transparent;
                color: #2f2f35;
            }}

            .bing-card {{
                width: 100%;
                background: #f3eee8;
                border-radius: 26px;
                overflow: hidden;
                box-shadow: 0 8px 24px rgba(0,0,0,0.06);
            }}

            .top {{
                padding: 22px 24px 10px 24px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}

            .place {{
                font-size: 18px;
                font-weight: 800;
            }}

            .updated {{
                margin-top: 6px;
                font-size: 13px;
                color: #777;
            }}

            .unit-switch {{
                display: flex;
                gap: 8px;
                font-weight: 700;
                font-size: 14px;
            }}

            .unit-active {{
                background: #6c6c6c;
                color: white;
                border-radius: 6px;
                padding: 7px 10px;
            }}

            .unit-off {{
                color: #555;
                padding: 7px 2px;
            }}

            .main-weather {{
                padding: 4px 24px 12px 24px;
                display: flex;
                align-items: center;
                gap: 22px;
            }}

            .main-icon {{
                font-size: 82px;
                color: #f6a623;
                width: 92px;
                text-align: center;
            }}

            .weather-text-area {{
                display: flex;
                flex-direction: column;
                flex: 1;
            }}

            .temp-condition-row {{
                display: flex;
                align-items: center;
                gap: 24px;
            }}

            .main-temp {{
                font-size: 58px;
                font-weight: 850;
                line-height: 1;
            }}

            .condition {{
                font-size: 22px;
                font-weight: 800;
            }}

            .hi-lo {{
                margin-top: 8px;
                color: #555;
                font-size: 15px;
            }}

            .mini-info {{
                display: flex;
                gap: 10px;
                margin-top: 12px;
                flex-wrap: wrap;
            }}

            .mini-pill {{
                background: white;
                border-radius: 999px;
                padding: 7px 11px;
                font-size: 13px;
                color: #444;
            }}

            .mini-pill i {{
                color: #f6a623;
                margin-right: 6px;
            }}

            .daily-row {{
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                margin: 8px 0 0 0;
                background: rgba(255,255,255,0.44);
            }}

            .bing-day {{
                padding: 13px 8px 12px 8px;
                text-align: center;
                border-right: 1px solid rgba(0,0,0,0.035);
            }}

            .bing-day:first-child {{
                background: rgba(255,255,255,0.75);
                border-radius: 12px 12px 0 0;
            }}

            .bing-day-name {{
                font-size: 14px;
                font-weight: 800;
                margin-bottom: 8px;
            }}

            .bing-day-icon {{
                font-size: 31px;
                color: #f6a623;
                margin-bottom: 7px;
            }}

            .bing-day-temp {{
                font-size: 14px;
                color: #555;
            }}

            .chart-wrap {{
                position: relative;
                height: 178px;
                background: #f8f6f3;
                padding-top: 4px;
            }}

            .chart-svg {{
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
            }}

            .temp-label {{
                position: absolute;
                font-size: 13px;
                color: #666;
            }}

            .rain-label {{
                position: absolute;
                bottom: 16px;
                font-size: 13px;
                color: #0076b6;
                text-align: center;
                min-width: 42px;
            }}

            .time-label {{
                color: #555;
                margin-top: 9px;
                font-size: 13px;
            }}

            .drop {{
                font-size: 10px;
                margin-right: 2px;
            }}
        </style>
    </head>

    <body>
        <div class="bing-card">
            <div class="top">
                <div>
                    <div class="place">{display_city}, Vietnam</div>
                    <div class="updated">Updated a few minutes ago</div>
                </div>

                <div class="unit-switch">
                    <div class="{active_f}">°F</div>
                    <div class="{active_c}">°C</div>
                </div>
            </div>

            <div class="main-weather">
                <div class="main-icon">
                    <i class="{weather_icon}"></i>
                </div>

                <div class="weather-text-area">
                    <div class="temp-condition-row">
                        <div class="main-temp">{temp_now:.0f}{unit}</div>
                        <div class="condition">{weather_text}</div>
                    </div>

                    <div class="hi-lo">
                        Feels like {feels:.0f}{unit} · Humidity {current["relative_humidity_2m"]}% · Wind {current["wind_speed_10m"]:.0f} km/h {wind_dir}
                    </div>

                    <div class="mini-info">
                        <div class="mini-pill"><i class="wi wi-humidity"></i>{current["relative_humidity_2m"]}% humidity</div>
                        <div class="mini-pill"><i class="wi wi-strong-wind"></i>{current["wind_speed_10m"]:.0f} km/h wind</div>
                        <div class="mini-pill"><i class="wi wi-raindrop"></i>{current["rain"]:.1f} mm rain</div>
                        <div class="mini-pill"><i class="wi wi-cloudy"></i>{current["cloud_cover"]}% cloud</div>
                    </div>
                </div>
            </div>

            <div class="daily-row">
                {daily_html}
            </div>

            <div class="chart-wrap">
                <svg class="chart-svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
                    <polygon points="{area_points}" fill="rgba(255, 138, 138, 0.25)"></polygon>
                    <polyline points="{polyline_points}" fill="none" stroke="rgba(245, 155, 155, 0.70)" stroke-width="3"></polyline>
                    <line x1="{left_pad}" y1="{height-bottom_pad}" x2="{width-right_pad}" y2="{height-bottom_pad}" stroke="#ddd" stroke-width="1"></line>
                </svg>

                {temp_labels_html}
                {rain_labels_html}
            </div>
        </div>
    </body>
    </html>
    """

    components_html(html_code, height=575)


# =========================
# API
# =========================
@st.cache_data(ttl=1800)
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "is_day",
            "precipitation",
            "rain",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m"
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "rain",
            "weather_code",
            "cloud_cover",
            "visibility",
            "uv_index",
            "wind_speed_10m"
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "uv_index_max",
            "wind_speed_10m_max"
        ]),
        "timezone": "Asia/Bangkok",
        "forecast_days": 7
    }

    res = requests.get(url, params=params, timeout=15)
    res.raise_for_status()
    return res.json()


# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Cài đặt")

city = st.sidebar.selectbox(
    "Chọn khu vực",
    ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Thanh Xuân - Hà Nội", "Tùy chỉnh"]
)

locations = {
    "Hà Nội": (21.0285, 105.8542),
    "TP. Hồ Chí Minh": (10.7769, 106.7009),
    "Đà Nẵng": (16.0544, 108.2022),
    "Thanh Xuân - Hà Nội": (20.9957, 105.8099)
}

if city == "Tùy chỉnh":
    lat = st.sidebar.number_input("Latitude", value=21.0285, format="%.6f")
    lon = st.sidebar.number_input("Longitude", value=105.8542, format="%.6f")
    display_city = "Custom Location"
else:
    lat, lon = locations[city]
    display_city = city

unit = st.sidebar.radio("Đơn vị nhiệt độ", ["°C", "°F"])

st.sidebar.markdown("---")
st.sidebar.write("Dữ liệu lấy từ Open-Meteo API")


# =========================
# LOAD DATA
# =========================
try:
    data = get_weather(lat, lon)
    current = data["current"]
    hourly = pd.DataFrame(data["hourly"])
    daily = pd.DataFrame(data["daily"])
except Exception as e:
    st.error(f"Lỗi lấy dữ liệu thời tiết: {e}")
    st.stop()

hourly["time"] = pd.to_datetime(hourly["time"])
daily["time"] = pd.to_datetime(daily["time"])

temp_now_c = current["temperature_2m"]
feels_c = current["apparent_temperature"]

if unit == "°F":
    temp_now = fahrenheit(temp_now_c)
    feels = fahrenheit(feels_c)
    hourly["temperature_show"] = hourly["temperature_2m"].apply(fahrenheit)
    daily["temp_max_show"] = daily["temperature_2m_max"].apply(fahrenheit)
    daily["temp_min_show"] = daily["temperature_2m_min"].apply(fahrenheit)
else:
    temp_now = temp_now_c
    feels = feels_c
    hourly["temperature_show"] = hourly["temperature_2m"]
    daily["temp_max_show"] = daily["temperature_2m_max"]
    daily["temp_min_show"] = daily["temperature_2m_min"]

weather_text, weather_icon = weather_code_to_text(current["weather_code"])
next_24h = hourly.head(24)


# =========================
# HEADER
# =========================
render_html(f"""
<div class="main-title">Weather Dashboard - {display_city}</div>
<div class="sub-title">Cập nhật theo API: {current["time"]} | Tọa độ: {lat}, {lon}</div>
""")


# =========================
# LAYOUT
# =========================
left, right = st.columns([1.35, 1])

with left:
    bing_main_weather_card(
        display_city=display_city,
        current=current,
        daily=daily,
        hourly=hourly,
        temp_now=temp_now,
        feels=feels,
        unit=unit,
        weather_text=weather_text,
        weather_icon=weather_icon
    )

with right:
    visibility_km = hourly["visibility"].iloc[0] / 1000
    wind_speed = current["wind_speed_10m"]
    wind_dir = wind_direction_text(current["wind_direction_10m"])
    gust = current["wind_gusts_10m"]
    pressure = current["pressure_msl"]
    humidity = current["relative_humidity_2m"]
    uv = hourly["uv_index"].iloc[0]
    cloud = current["cloud_cover"]

    c1, c2 = st.columns(2)

    with c1:
        render_html(metric_card(
            "Visibility",
            f"{visibility_km:.1f} km",
            "Tầm nhìn hiện tại",
            "wi wi-fog",
            "#43b36a",
            visibility_km * 12
        ))

    with c2:
        render_html(metric_card(
            "Wind",
            f"{wind_speed:.0f} km/h",
            f"Hướng {wind_dir} - Gust {gust:.0f} km/h",
            "wi wi-strong-wind",
            "#43b36a",
            wind_speed * 3
        ))

    c3, c4 = st.columns(2)

    with c3:
        render_html(metric_card(
            "Pressure",
            f"{pressure:.0f} hPa",
            "Áp suất mực nước biển",
            "wi wi-barometer",
            "#9a7dff",
            (pressure - 950) * 2
        ))

    with c4:
        render_html(metric_card(
            "Humidity",
            f"{humidity}%",
            "Độ ẩm không khí",
            "wi wi-humidity",
            "#5b83ff",
            humidity
        ))

    c5, c6 = st.columns(2)

    with c5:
        render_html(metric_card(
            "UV Index",
            f"{uv:.1f}",
            "Chỉ số UV theo giờ",
            "wi wi-hot",
            "#f5a623",
            uv / 12 * 100
        ))

    with c6:
        render_html(metric_card(
            "Cloud Cover",
            f"{cloud}%",
            "Mức độ mây che phủ",
            "wi wi-cloudy",
            "#f5a623",
            cloud
        ))

    render_html('<div class="section-title">Xác suất mưa 24 giờ tới</div>')

    fig_rain = px.bar(
        next_24h,
        x="time",
        y="precipitation_probability",
        labels={
            "time": "Thời gian",
            "precipitation_probability": "Xác suất mưa (%)"
        }
    )

    fig_rain.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f3eee8"
    )

    st.plotly_chart(fig_rain, use_container_width=True)


# =========================
# RAW DATA
# =========================
with st.expander("Xem dữ liệu hourly raw"):
    st.dataframe(hourly.head(48), use_container_width=True)

with st.expander("Xem dữ liệu current raw"):
    st.json(current)
