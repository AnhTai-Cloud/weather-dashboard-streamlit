import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit.components.v1 import html as components_html
from datetime import datetime, timedelta


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="IoT Weather Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# CONFIG
# =========================
DATA_SOURCE = "data.csv"

# Nếu sau này dùng Google Sheet, đổi thành link CSV:
# DATA_SOURCE = "https://docs.google.com/spreadsheets/d/xxxxx/export?format=csv"


# =========================
# CSS STREAMLIT
# =========================
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
.stApp {
    background: #eef0f3;
    color: #2f3341;
}

.block-container {
    max-width: 1280px;
    padding-top: 1.6rem;
}

section[data-testid="stSidebar"] {
    background: #e6e9ed;
}

.main-title {
    font-size: 32px;
    font-weight: 850;
    color: #2f3341;
    margin-bottom: 6px;
}

.sub-title {
    color: #74777f;
    font-size: 14px;
    margin-bottom: 18px;
}

.metric-card {
    background: #f3eee8;
    border-radius: 24px;
    padding: 18px 20px;
    min-height: 164px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.05);
    margin-bottom: 16px;
}

.metric-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.metric-title {
    font-size: 16px;
    font-weight: 850;
}

.metric-icon-box {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    background: rgba(255,255,255,0.85);
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
    margin-top: 14px;
}

.metric-desc {
    color: #74777f;
    font-size: 14px;
    margin-top: 4px;
}

.progress-wrap {
    width: 100%;
    height: 9px;
    background: #ded8d1;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 14px;
}

.progress-fill {
    height: 100%;
    border-radius: 999px;
}

.section-title {
    font-size: 24px;
    font-weight: 850;
    margin: 22px 0 12px 0;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HELPER
# =========================
def clamp(x, min_val=0, max_val=100):
    return max(min_val, min(float(x), max_val))


def weather_icon(label):
    label = str(label).lower()

    if "mưa" in label or "rain" in label:
        return "wi wi-rain", "#5b83ff"

    if "âm" in label or "cloud" in label or "u" in label:
        return "wi wi-cloudy", "#f5a623"

    if "nắng" in label or "clear" in label or "sun" in label:
        return "wi wi-day-sunny", "#f5a623"

    return "wi wi-day-cloudy", "#f5a623"


def metric_card(title, value, desc, icon_class, color, percent):
    percent = clamp(percent)

    html = f"""
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

    st.markdown(" ".join(html.split()), unsafe_allow_html=True)


def make_demo_data():
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    rows = []
    for i in range(36):
        t = now - timedelta(hours=35 - i)

        temp = 26 + np.sin(i / 4) * 2 + np.random.normal(0, 0.2)
        hum = 78 + np.sin(i / 5) * 10 + np.random.normal(0, 1)
        pressure = 1006 + np.sin(i / 7) * 2
        light = max(0, 850 * np.sin((t.hour / 24) * np.pi))
        rain = 1 if hum > 88 and light < 250 else 0

        if rain == 1:
            label = "Mưa"
        elif light < 300:
            label = "Âm u"
        else:
            label = "Nắng"

        rows.append({
            "time": t,
            "temperature": round(temp, 1),
            "humidity": round(hum, 1),
            "pressure": round(pressure, 1),
            "light": round(light, 0),
            "rain_sensor": rain,
            "weather_label": label,
            "ai_prediction": label,
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_data():
    try:
        df = pd.read_csv(DATA_SOURCE)
    except Exception:
        df = make_demo_data()

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    required_cols = [
        "temperature",
        "humidity",
        "pressure",
        "light",
        "rain_sensor",
        "weather_label",
        "ai_prediction",
    ]

    for col in required_cols:
        if col not in df.columns:
            if col == "ai_prediction":
                df[col] = "Chưa dự đoán"
            elif col == "weather_label":
                df[col] = "Không rõ"
            else:
                df[col] = 0

    return df


# =========================
# BING STYLE MAIN CARD
# =========================
def main_iot_weather_card(df, latest):
    last_7 = df.tail(7).copy().reset_index(drop=True)

    temps = last_7["temperature"].astype(float).tolist()
    hums = last_7["humidity"].astype(float).tolist()
    rains = last_7["rain_sensor"].astype(float).tolist()
    times = [t.strftime("%I %p").lstrip("0") for t in last_7["time"]]

    min_t = min(temps)
    max_t = max(temps)
    temp_range = max(max_t - min_t, 1)

    width = 720
    height = 170
    left_pad = 38
    right_pad = 30
    top_pad = 24
    bottom_pad = 54

    usable_w = width - left_pad - right_pad
    usable_h = height - top_pad - bottom_pad

    points = []
    temp_labels = ""
    rain_labels = ""

    for i, temp in enumerate(temps):
        x = left_pad + i * usable_w / (len(temps) - 1)
        y = top_pad + (max_t - temp) / temp_range * usable_h
        points.append((x, y))

        temp_labels += f"""
        <div class="temp-label" style="left:{x - 10}px; top:{y - 24}px;">
            {temp:.0f}°
        </div>
        """

        rain_text = "Có mưa" if rains[i] == 1 else "0%"
        rain_labels += f"""
        <div class="rain-label" style="left:{x - 22}px;">
            <span class="drop">💧</span>{rain_text}
            <div class="time-label">{times[i]}</div>
        </div>
        """

    polyline_points = " ".join([f"{x},{y}" for x, y in points])

    area_points = (
        f"{left_pad},{height-bottom_pad} "
        + polyline_points
        + f" {width-right_pad},{height-bottom_pad}"
    )

    prediction = latest["ai_prediction"]
    icon_class, icon_color = weather_icon(prediction)

    rain_status = "Có mưa" if int(latest["rain_sensor"]) == 1 else "Không mưa"

    if prediction == "Mưa" or int(latest["rain_sensor"]) == 1:
        action = "CẤT ĐỒ"
        action_color = "#e74c3c"
    elif prediction == "Âm u":
        action = "THEO DÕI THÊM"
        action_color = "#f5a623"
    else:
        action = "TIẾP TỤC PHƠI"
        action_color = "#43b36a"

    daily_boxes = ""
    for i, row in last_7.iterrows():
        box_icon, box_color = weather_icon(row["weather_label"])

        if i == len(last_7) - 1:
            label = "Now"
        else:
            label = row["time"].strftime("%H:%M")

        daily_boxes += f"""
        <div class="day-box">
            <div class="day-name">{label}</div>
            <div class="day-icon" style="color:{box_color};">
                <i class="{box_icon}"></i>
            </div>
            <div class="day-temp">{row["temperature"]:.0f}°C</div>
        </div>
        """

    html = f"""
    <html>
    <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">

        <style>
            body {{
                margin: 0;
                font-family: Arial, Helvetica, sans-serif;
                color: #2f2f35;
                background: transparent;
            }}

            .card {{
                background: #f3eee8;
                border-radius: 26px;
                overflow: hidden;
                box-shadow: 0 8px 24px rgba(0,0,0,0.06);
            }}

            .top {{
                padding: 22px 24px 8px 24px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}

            .place {{
                font-size: 19px;
                font-weight: 800;
            }}

            .updated {{
                margin-top: 6px;
                font-size: 13px;
                color: #777;
            }}

            .action {{
                background: {action_color};
                color: white;
                font-weight: 800;
                border-radius: 999px;
                padding: 9px 14px;
                font-size: 13px;
            }}

            .main {{
                padding: 8px 24px 14px 24px;
                display: flex;
                align-items: center;
                gap: 22px;
            }}

            .main-icon {{
                width: 92px;
                text-align: center;
                font-size: 82px;
                color: {icon_color};
            }}

            .main-content {{
                flex: 1;
            }}

            .temp-row {{
                display: flex;
                align-items: center;
                gap: 24px;
            }}

            .temp {{
                font-size: 60px;
                font-weight: 850;
                line-height: 1;
            }}

            .condition {{
                font-size: 23px;
                font-weight: 850;
            }}

            .desc {{
                margin-top: 8px;
                font-size: 15px;
                color: #555;
            }}

            .pill-row {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 13px;
            }}

            .pill {{
                background: white;
                border-radius: 999px;
                padding: 7px 11px;
                font-size: 13px;
                color: #444;
            }}

            .pill i {{
                color: #f5a623;
                margin-right: 6px;
            }}

            .days {{
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                background: rgba(255,255,255,0.45);
            }}

            .day-box {{
                text-align: center;
                padding: 13px 6px 12px 6px;
                border-right: 1px solid rgba(0,0,0,0.04);
            }}

            .day-box:last-child {{
                background: rgba(255,255,255,0.75);
            }}

            .day-name {{
                font-weight: 800;
                font-size: 14px;
                margin-bottom: 7px;
            }}

            .day-icon {{
                font-size: 30px;
                margin-bottom: 7px;
            }}

            .day-temp {{
                font-size: 14px;
                color: #555;
            }}

            .chart-wrap {{
                position: relative;
                height: 185px;
                background: #f8f6f3;
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
                color: #555;
            }}

            .rain-label {{
                position: absolute;
                bottom: 18px;
                min-width: 48px;
                font-size: 13px;
                color: #0076b6;
                text-align: center;
            }}

            .time-label {{
                margin-top: 9px;
                color: #555;
                font-size: 13px;
            }}

            .drop {{
                font-size: 10px;
                margin-right: 2px;
            }}
        </style>
    </head>

    <body>
        <div class="card">
            <div class="top">
                <div>
                    <div class="place">Trạm IoT phơi đồ thông minh</div>
                    <div class="updated">Cập nhật: {latest["time"].strftime("%d/%m/%Y %H:%M:%S")}</div>
                </div>

                <div class="action">{action}</div>
            </div>

            <div class="main">
                <div class="main-icon">
                    <i class="{icon_class}"></i>
                </div>

                <div class="main-content">
                    <div class="temp-row">
                        <div class="temp">{latest["temperature"]:.0f}°C</div>
                        <div class="condition">{prediction}</div>
                    </div>

                    <div class="desc">
                        Độ ẩm {latest["humidity"]:.0f}% · Áp suất {latest["pressure"]:.1f} hPa · Ánh sáng {latest["light"]:.0f} lux · {rain_status}
                    </div>

                    <div class="pill-row">
                        <div class="pill"><i class="wi wi-humidity"></i>{latest["humidity"]:.0f}% độ ẩm</div>
                        <div class="pill"><i class="wi wi-barometer"></i>{latest["pressure"]:.1f} hPa</div>
                        <div class="pill"><i class="wi wi-day-sunny"></i>{latest["light"]:.0f} lux</div>
                        <div class="pill"><i class="wi wi-raindrop"></i>{rain_status}</div>
                    </div>
                </div>
            </div>

            <div class="days">
                {daily_boxes}
            </div>

            <div class="chart-wrap">
                <svg class="chart-svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
                    <polygon points="{area_points}" fill="rgba(255, 138, 138, 0.25)"></polygon>
                    <polyline points="{polyline_points}" fill="none" stroke="rgba(245, 155, 155, 0.75)" stroke-width="3"></polyline>
                    <line x1="{left_pad}" y1="{height-bottom_pad}" x2="{width-right_pad}" y2="{height-bottom_pad}" stroke="#ddd" stroke-width="1"></line>
                </svg>

                {temp_labels}
                {rain_labels}
            </div>
        </div>
    </body>
    </html>
    """

    components_html(html, height=600)


# =========================
# LOAD DATA
# =========================
df = load_data()
latest = df.iloc[-1]


# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Cài đặt hệ thống")

st.sidebar.write("Nguồn dữ liệu:")
st.sidebar.code(DATA_SOURCE)

refresh = st.sidebar.slider(
    "Chu kỳ cập nhật giao diện",
    min_value=5,
    max_value=120,
    value=30,
    step=5
)

st.sidebar.markdown("---")
st.sidebar.write("Các cột dữ liệu yêu cầu:")
st.sidebar.code("""
time
temperature
humidity
pressure
light
rain_sensor
weather_label
ai_prediction
""")


# =========================
# HEADER
# =========================
st.markdown(
    '<div class="main-title">IoT Weather Dashboard - Hệ thống phơi đồ thông minh</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="sub-title">Dữ liệu cảm biến mới nhất: {latest["time"]}</div>',
    unsafe_allow_html=True
)


# =========================
# LAYOUT
# =========================
left, right = st.columns([1.35, 1])

with left:
    main_iot_weather_card(df, latest)

with right:
    c1, c2 = st.columns(2)

    with c1:
        metric_card(
            "Nhiệt độ",
            f'{latest["temperature"]:.1f}°C',
            "Cảm biến DHT/BME",
            "wi wi-thermometer",
            "#f5a623",
            clamp(latest["temperature"] / 45 * 100)
        )

    with c2:
        metric_card(
            "Độ ẩm",
            f'{latest["humidity"]:.0f}%',
            "Độ ẩm không khí",
            "wi wi-humidity",
            "#5b83ff",
            latest["humidity"]
        )

    c3, c4 = st.columns(2)

    with c3:
        metric_card(
            "Áp suất",
            f'{latest["pressure"]:.1f} hPa',
            "BMP280",
            "wi wi-barometer",
            "#9a7dff",
            clamp((latest["pressure"] - 950) * 2)
        )

    with c4:
        metric_card(
            "Ánh sáng",
            f'{latest["light"]:.0f} lux',
            "Cường độ ánh sáng",
            "wi wi-day-sunny",
            "#f5a623",
            clamp(latest["light"] / 1000 * 100)
        )

    c5, c6 = st.columns(2)

    with c5:
        rain_text = "Có mưa" if int(latest["rain_sensor"]) == 1 else "Không mưa"

        metric_card(
            "Cảm biến mưa",
            rain_text,
            "Rain sensor",
            "wi wi-raindrop",
            "#43b36a" if int(latest["rain_sensor"]) == 0 else "#e74c3c",
            100 if int(latest["rain_sensor"]) == 1 else 10
        )

    with c6:
        pred = latest["ai_prediction"]
        icon, color = weather_icon(pred)

        metric_card(
            "AI dự đoán",
            pred,
            "Nắng / Âm u / Mưa",
            icon,
            color,
            80
        )

    st.markdown('<div class="section-title">Biểu đồ cảm biến</div>', unsafe_allow_html=True)

    chart_df = df.tail(24).copy()

    fig = px.line(
        chart_df,
        x="time",
        y=["temperature", "humidity"],
        markers=True,
        labels={
            "time": "Thời gian",
            "value": "Giá trị",
            "variable": "Cảm biến"
        }
    )

    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f3eee8"
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================
# DATA TABLE
# =========================
with st.expander("Xem dữ liệu cảm biến"):
    st.dataframe(df.tail(100), use_container_width=True)
