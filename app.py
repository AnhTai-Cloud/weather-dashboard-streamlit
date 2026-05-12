import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import textwrap


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

.hero-card {
    background: var(--card);
    border-radius: 28px;
    padding: 26px 28px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.055);
    margin-bottom: 18px;
}

.hero-place {
    font-size: 19px;
    font-weight: 850;
    color: var(--text);
}

.hero-small {
    font-size: 14px;
    color: var(--muted);
    margin-top: 4px;
}

.hero-main {
    display: flex;
    align-items: center;
    gap: 26px;
    margin-top: 20px;
}

.hero-icon {
    font-size: 92px;
    color: var(--orange);
    min-width: 110px;
    text-align: center;
}

.hero-temp {
    font-size: 68px;
    font-weight: 850;
    line-height: 1;
    color: var(--text);
}

.hero-cond {
    font-size: 23px;
    font-weight: 850;
    color: var(--text);
    margin-top: 6px;
}

.hero-feel {
    color: var(--muted);
    font-size: 15px;
    margin-top: 6px;
}

.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}

.info-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #fff;
    border-radius: 999px;
    padding: 8px 12px;
    font-size: 13px;
    color: var(--text);
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
}

.info-badge i {
    color: var(--orange);
    font-size: 16px;
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

.hour-card {
    background: #fff;
    border-radius: 18px;
    padding: 12px 8px;
    min-height: 126px;
    text-align: center;
    box-shadow: 0 5px 14px rgba(0,0,0,0.045);
    margin-bottom: 10px;
}

.hour-time {
    font-size: 14px;
    font-weight: 850;
    color: var(--text);
}

.hour-icon {
    font-size: 30px;
    color: var(--orange);
    margin: 10px 0 8px 0;
}

.hour-temp {
    font-size: 18px;
    font-weight: 850;
    color: var(--text);
}

.hour-rain {
    font-size: 12px;
    color: var(--muted);
    margin-top: 4px;
}

.daily-card {
    background: var(--card);
    border-radius: 18px;
    padding: 14px 8px;
    min-height: 170px;
    text-align: center;
    box-shadow: 0 6px 16px rgba(0,0,0,0.045);
}

.daily-day {
    font-size: 14px;
    font-weight: 850;
    color: var(--text);
}

.daily-date {
    font-size: 13px;
    color: var(--muted);
    margin-top: 3px;
}

.daily-icon {
    font-size: 40px;
    color: var(--orange);
    margin: 12px 0 10px 0;
}

.daily-max {
    font-size: 23px;
    font-weight: 850;
    color: var(--text);
}

.daily-min {
    font-size: 14px;
    color: var(--muted);
}

.daily-rain {
    margin-top: 8px;
    font-size: 13px;
    color: var(--muted);
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

next_12h = hourly.head(12)
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
    # HERO CARD
    render_html(f"""
<div class="hero-card">
    <div class="hero-place">{display_city}, Vietnam</div>
    <div class="hero-small">Current weather</div>

    <div class="hero-main">
        <div class="hero-icon">
            <i class="{weather_icon}"></i>
        </div>

        <div>
            <div class="hero-temp">{temp_now:.0f}{unit}</div>
            <div class="hero-cond">{weather_text}</div>
            <div class="hero-feel">Feels like {feels:.0f}{unit}</div>

            <div class="badge-row">
                <div class="info-badge">
                    <i class="wi wi-humidity"></i>
                    Humidity {current["relative_humidity_2m"]}%
                </div>

                <div class="info-badge">
                    <i class="wi wi-strong-wind"></i>
                    Wind {current["wind_speed_10m"]:.0f} km/h
                </div>

                <div class="info-badge">
                    <i class="wi wi-raindrop"></i>
                    Rain {current["rain"]:.1f} mm
                </div>

                <div class="info-badge">
                    <i class="wi wi-cloudy"></i>
                    Cloud {current["cloud_cover"]}%
                </div>
            </div>
        </div>
    </div>
</div>
""")

    # HOURLY FORECAST
    render_html('<div class="section-title">Dự báo 12 giờ tới</div>')

    row1 = st.columns(6)
    for i, row in next_12h.iloc[:6].reset_index(drop=True).iterrows():
        _, icon = weather_code_to_text(row["weather_code"])
        hour_label = row["time"].strftime("%H:%M")

        with row1[i]:
            render_html(f"""
<div class="hour-card">
    <div class="hour-time">{hour_label}</div>
    <div class="hour-icon"><i class="{icon}"></i></div>
    <div class="hour-temp">{row["temperature_show"]:.0f}{unit}</div>
    <div class="hour-rain">Rain {row["precipitation_probability"]:.0f}%</div>
</div>
""")

    row2 = st.columns(6)
    for i, row in next_12h.iloc[6:12].reset_index(drop=True).iterrows():
        _, icon = weather_code_to_text(row["weather_code"])
        hour_label = row["time"].strftime("%H:%M")

        with row2[i]:
            render_html(f"""
<div class="hour-card">
    <div class="hour-time">{hour_label}</div>
    <div class="hour-icon"><i class="{icon}"></i></div>
    <div class="hour-temp">{row["temperature_show"]:.0f}{unit}</div>
    <div class="hour-rain">Rain {row["precipitation_probability"]:.0f}%</div>
</div>
""")

    # DAILY FORECAST
    render_html('<div class="section-title">Dự báo 7 ngày</div>')

    day_cols = st.columns(7)
    for i, row in daily.reset_index(drop=True).iterrows():
        _, icon = weather_code_to_text(row["weather_code"])
        day_name = row["time"].strftime("%a")
        day_num = row["time"].strftime("%d")

        with day_cols[i]:
            render_html(f"""
<div class="daily-card">
    <div class="daily-day">{day_name}</div>
    <div class="daily-date">{day_num}</div>
    <div class="daily-icon"><i class="{icon}"></i></div>
    <div class="daily-max">{row["temp_max_show"]:.0f}{unit}</div>
    <div class="daily-min">/ {row["temp_min_show"]:.0f}{unit}</div>
    <div class="daily-rain">
        <i class="wi wi-raindrop"></i> {row["precipitation_probability_max"]:.0f}%
    </div>
</div>
""")

    # TEMP CHART
    render_html('<div class="section-title">Biểu đồ nhiệt độ 24 giờ tới</div>')

    fig_temp = px.line(
        next_24h,
        x="time",
        y="temperature_show",
        markers=True,
        labels={
            "time": "Thời gian",
            "temperature_show": f"Nhiệt độ {unit}"
        }
    )

    fig_temp.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f3eee8"
    )

    st.plotly_chart(fig_temp, use_container_width=True)


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
