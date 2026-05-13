import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import time
import ssl
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from streamlit.components.v1 import html as components_html


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
# DATA SOURCE
# =========================
DATA_SOURCE = "data.csv"


# =========================
# MQTT CONFIG - FIX CỨNG HIVEMQ CLOUD
# =========================
MQTT_BROKER = "0d3bcdfd1bb6411ead82b3fc9491adf.s1.eu.hivemq.cloud"
MQTT_PORT = 8883

MQTT_USERNAME = "anhtai"
MQTT_PASSWORD = "NHAP_MAT_KHAU_HIVEMQ_CUA_BAN"

MQTT_CLIENT_ID = "streamlit_weather_dashboard"
MQTT_TOPIC_DATA = "iot/clothesline/data"
MQTT_TOPIC_CMD = "iot/clothesline/cmd"
MQTT_DEVICE_ID = "esp32_clothesline_01"


# =========================
# SERVO CONFIG - DÀN PHƠI
# =========================
SERVO_NAME = "MG90S"
SERVO_OPEN_ANGLE = 90
SERVO_CLOSE_ANGLE = 0


# =========================
# SERVO CONFIG - CỬA
# =========================
DOOR_SERVO_NAME = "MG90S"
DOOR_COMMAND = "MSG40"
DOOR_OPEN_ANGLE = 90
DOOR_ACTION = "Mở cửa bằng servo MG90S"


# =========================
# CSS
# =========================
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
html, body, .stApp, .main-title, .sub-title, .metric-card, .section-title, .control-note {
    font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif !important;
}

button, input, textarea, select, div, p, span {
    font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
}

/* Không ép font chữ thường vào icon */
i[class^="wi"], i[class*=" wi-"] {
    font-family: "weathericons" !important;
    font-style: normal !important;
}

.stApp {
    background: #eef0f3;
    color: #2f3341;
}

.block-container {
    max-width: 1320px;
    padding-top: 1.4rem;
}

section[data-testid="stSidebar"] {
    background: #e6e9ed;
}

.main-title {
    font-size: 30px;
    font-weight: 850;
    letter-spacing: 0.15px;
    color: #2f3341;
    margin-bottom: 6px;
    text-transform: uppercase;
    line-height: 1.28;
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
    font-size: 15px;
    font-weight: 850;
    letter-spacing: 0.15px;
    text-transform: uppercase;
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
    font-size: 30px;
    font-weight: 850;
    margin-top: 14px;
}

.metric-desc {
    color: #74777f;
    font-size: 13px;
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
    letter-spacing: 0.15px;
    text-transform: uppercase;
    margin: 24px 0 14px 0;
    color: #2f3341;
    line-height: 1.3;
}

.control-note {
    background: #f3eee8;
    border-radius: 18px;
    padding: 14px 16px;
    color: #2f3341;
    margin-bottom: 12px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.04);
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HELPER FUNCTIONS
# =========================
def clamp(x, min_val=0, max_val=100):
    return max(min_val, min(float(x), max_val))


def weather_icon(label):
    label = str(label).lower()

    if "mưa" in label or "rain" in label:
        return "wi wi-rain", "#5b83ff"

    if "âm" in label or "cloud" in label:
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


# =========================
# MQTT FUNCTIONS
# =========================
def get_mqtt_config():
    return {
        "broker": MQTT_BROKER,
        "port": MQTT_PORT,
        "username": MQTT_USERNAME,
        "password": MQTT_PASSWORD,
        "client_id": MQTT_CLIENT_ID,
        "topic_data": MQTT_TOPIC_DATA,
        "topic_cmd": MQTT_TOPIC_CMD,
        "device_id": MQTT_DEVICE_ID,
        "tls": True,
    }


def mqtt_publish(command, reason="Manual control from dashboard"):
    cfg = get_mqtt_config()

    command = command.upper().strip()

    if command == "OPEN":
        target_angle = SERVO_OPEN_ANGLE
        action_text = "Mở dàn phơi"
        target_device = "clothesline_servo"
        servo_name = SERVO_NAME

    elif command == "CLOSE":
        target_angle = SERVO_CLOSE_ANGLE
        action_text = "Đóng / thu dàn phơi"
        target_device = "clothesline_servo"
        servo_name = SERVO_NAME

    elif command == "MSG40":
        target_angle = 90
        action_text = "Mở cửa bằng servo MG90S"
        target_device = "door_servo"
        servo_name = "MG90S"

    else:
        return False, "Lệnh không hợp lệ"

        payload = {
        "device": cfg["device_id"],
        "target": target_device,
        "command": command,
        "angle": target_angle,
        "servo": servo_name,
        "action": action_text,
        "source": "streamlit",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        connected = {"ok": False, "rc": None}

        def on_connect(client, userdata, flags, rc):
            connected["rc"] = rc
            connected["ok"] = (rc == 0)

        client_id = cfg["client_id"] + "_" + str(int(time.time()))

        client = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311
        )

        client.on_connect = on_connect
        client.username_pw_set(cfg["username"], cfg["password"])

        client.tls_set(
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT
        )

        client.connect(cfg["broker"], cfg["port"], keepalive=60)
        client.loop_start()

        start_time = time.time()
        while connected["rc"] is None and time.time() - start_time < 5:
            time.sleep(0.1)

        if not connected["ok"]:
            client.loop_stop()
            client.disconnect()
            return False, f"MQTT connect failed, rc={connected['rc']}"

        msg_info = client.publish(
            cfg["topic_cmd"],
            json.dumps(payload, ensure_ascii=False),
            qos=1,
            retain=True
        )

        msg_info.wait_for_publish(timeout=5)

        client.loop_stop()
        client.disconnect()

        if msg_info.rc == mqtt.MQTT_ERR_SUCCESS:
            return True, payload

        return False, f"Publish failed, rc={msg_info.rc}"

    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def auto_decide_command(latest):
    rain_sensor = int(latest["rain_sensor"])
    prediction = str(latest["ai_prediction"])
    humidity = float(latest["humidity"])
    light = float(latest["light"])

    if rain_sensor == 1:
        return "CLOSE", "Cảm biến mưa phát hiện có mưa"

    if prediction == "Mưa":
        return "CLOSE", "AI dự đoán trời mưa"

    if prediction == "Âm u" and humidity >= 88 and light < 250:
        return "CLOSE", "Trời âm u, độ ẩm cao, ánh sáng thấp"

    if prediction == "Nắng" and rain_sensor == 0:
        return "OPEN", "Trời nắng, không phát hiện mưa"

    return "CLOSE", "Điều kiện chưa rõ, đưa dàn phơi về trạng thái an toàn"


# =========================
# DEMO DATA
# =========================
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
# MAIN CARD
# =========================
def main_iot_weather_card(df, latest):
    last_7 = df.tail(7).copy().reset_index(drop=True)

    temps = last_7["temperature"].astype(float).tolist()
    rains = last_7["rain_sensor"].astype(float).tolist()
    times = [t.strftime("%H:%M") for t in last_7["time"]]

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

    auto_cmd, auto_reason = auto_decide_command(latest)

    if command == "OPEN":
        target_angle = SERVO_OPEN_ANGLE
        action_text = "Mở dàn phơi"
        target_device = "clothesline_servo"
        servo_name = SERVO_NAME

    elif command == "CLOSE":
        target_angle = SERVO_CLOSE_ANGLE
        action_text = "Đóng / thu dàn phơi"
        target_device = "clothesline_servo"
        servo_name = SERVO_NAME

    elif command == "MSG40":
        target_angle = DOOR_OPEN_ANGLE
        action_text = DOOR_ACTION
        target_device = "door_servo"
        servo_name = DOOR_SERVO_NAME

    else:
        return False, "Lệnh không hợp lệ"

    daily_boxes = ""

    for i, row in last_7.iterrows():
        box_icon, box_color = weather_icon(row["weather_label"])

        if i == len(last_7) - 1:
            label = "NOW"
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
            body, .card, .place, .updated, .action, .temp, .condition, .desc, .reason, .pill, .day-name, .day-temp, .time-label {{
                font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif !important;
            }}

            i[class^="wi"], i[class*=" wi-"] {{
                font-family: "weathericons" !important;
                font-style: normal !important;
            }}

            body {{
                margin: 0;
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
                font-size: 18px;
                font-weight: 850;
                text-transform: uppercase;
                letter-spacing: 0.1px;
            }}

            .updated {{
                margin-top: 6px;
                font-size: 13px;
                color: #777;
            }}

            .action {{
                background: {action_color};
                color: white;
                font-weight: 850;
                border-radius: 999px;
                padding: 9px 14px;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.1px;
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
                font-size: 58px;
                font-weight: 850;
                line-height: 1;
            }}

            .condition {{
                font-size: 22px;
                font-weight: 850;
                text-transform: uppercase;
            }}

            .desc {{
                margin-top: 8px;
                font-size: 14px;
                color: #555;
            }}

            .reason {{
                margin-top: 7px;
                font-size: 13px;
                color: #777;
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
                font-weight: 850;
                font-size: 13px;
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
                    <div class="place">TRẠM IOT PHƠI ĐỒ THÔNG MINH</div>
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

                    <div class="reason">
                        Quyết định: {auto_reason}
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

    components_html(html, height=610)


# =========================
# BIG TEMPERATURE CHART
# =========================
def render_big_temperature_chart(df):
    chart_df = df.tail(24).copy()
    chart_df["time"] = pd.to_datetime(chart_df["time"])

    min_temp = chart_df["temperature"].min()
    max_temp = chart_df["temperature"].max()

    y_bottom = min_temp - 1.5
    y_top = max_temp + 1.8

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=[y_bottom] * len(chart_df),
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["temperature"],
            mode="lines+markers+text",
            text=[f"{v:.0f}°" for v in chart_df["temperature"]],
            textposition="top center",
            line=dict(
                width=4,
                color="rgba(255, 150, 150, 0.95)",
                shape="spline",
                smoothing=1.15
            ),
            marker=dict(
                size=8,
                color="rgba(255, 130, 130, 1)",
                line=dict(width=2, color="white")
            ),
            fill="tonexty",
            fillcolor="rgba(255, 150, 150, 0.22)",
            showlegend=False,
            hovertemplate=(
                "<b>%{x|%H:%M}</b><br>"
                "Nhiệt độ: %{y:.1f}°C"
                "<extra></extra>"
            )
        )
    )

    tick_df = chart_df.iloc[::3]

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=35, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f8f6f3",
        showlegend=False,
        autosize=True,
        font=dict(
            family="Segoe UI, Inter, Roboto, Arial, sans-serif",
            size=13,
            color="#2f3341"
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            tickmode="array",
            tickvals=tick_df["time"],
            ticktext=[t.strftime("%H:%M") for t in tick_df["time"]],
            linecolor="rgba(0,0,0,0.08)",
            tickfont=dict(size=13),
            fixedrange=True
        ),
        yaxis=dict(
            title="NHIỆT ĐỘ °C",
            range=[y_bottom, y_top],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            zeroline=False,
            tickfont=dict(size=12),
            fixedrange=True
        )
    )

    st.markdown(
        '<div class="section-title">BIỂU ĐỒ NHIỆT ĐỘ & MƯA 24 GIỜ GẦN NHẤT</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True
            }
        )

        rain_data = chart_df.tail(8).reset_index(drop=True)
        rain_cols = st.columns(8)

        for i, row in rain_data.iterrows():
            rain_text = "Có mưa" if int(row["rain_sensor"]) == 1 else "0%"
            time_text = row["time"].strftime("%H:%M")

            with rain_cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        font-size:14px;
                        color:#0076b6;
                        margin-top:-6px;
                        margin-bottom:10px;
                        font-family:'Segoe UI', Arial, sans-serif;
                    ">
                        💧 {rain_text}
                        <div style="
                            color:#555;
                            margin-top:6px;
                            font-size:13px;
                        ">
                            {time_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# =========================
# LOAD DATA
# =========================
df = load_data()
latest = df.iloc[-1]


# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ CÀI ĐẶT HỆ THỐNG")

st.sidebar.write("Nguồn dữ liệu:")
st.sidebar.code(DATA_SOURCE)

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
# MQTT CONTROL SIDEBAR
# =========================
st.sidebar.markdown("---")
st.sidebar.subheader("📡 ĐIỀU KHIỂN MQTT")

mqtt_cfg = get_mqtt_config()

st.sidebar.write("Broker:")
st.sidebar.code(mqtt_cfg["broker"])

st.sidebar.write("Port:")
st.sidebar.code(str(mqtt_cfg["port"]))

st.sidebar.write("Topic CMD:")
st.sidebar.code(mqtt_cfg["topic_cmd"])

st.sidebar.write("Servo:")
st.sidebar.code(f"{SERVO_NAME} | OPEN={SERVO_OPEN_ANGLE}° | CLOSE={SERVO_CLOSE_ANGLE}°")

control_mode = st.sidebar.radio(
    "Chế độ điều khiển",
    ["Thủ công", "Tự động theo AI"]
)

st.sidebar.markdown("### ĐIỀU KHIỂN THỦ CÔNG")

col_open, col_close = st.sidebar.columns(2)

with col_open:
    if st.button("MỞ 90°", use_container_width=True):
        ok, result = mqtt_publish(
            "OPEN",
            "Người dùng bấm mở dàn phơi 90 độ"
        )

        if ok:
            st.sidebar.success("Đã gửi OPEN 90°")
        else:
            st.sidebar.error(f"Không gửi được MQTT: {result}")

with col_close:
    if st.button("ĐÓNG 0°", use_container_width=True):
        ok, result = mqtt_publish(
            "CLOSE",
            "Người dùng bấm đóng dàn phơi về 0 độ"
        )

        if ok:
            st.sidebar.success("Đã gửi CLOSE 0°")
        else:
            st.sidebar.error(f"Không gửi được MQTT: {result}")


# =========================
# AUTO CONTROL THEO AI
# =========================
if "last_auto_command" not in st.session_state:
    st.session_state.last_auto_command = None

if control_mode == "Tự động theo AI":
    auto_cmd, auto_reason = auto_decide_command(latest)

    st.sidebar.markdown("### AI ĐỀ XUẤT")
    st.sidebar.info(f"Lệnh: {auto_cmd}\n\nLý do: {auto_reason}")

    auto_send = st.sidebar.checkbox(
        "Cho phép tự động gửi lệnh về ESP",
        value=False
    )

    if auto_send:
        current_key = f"{auto_cmd}_{latest['time']}"

        if st.session_state.last_auto_command != current_key:
            ok, result = mqtt_publish(auto_cmd, auto_reason)

            if ok:
                st.session_state.last_auto_command = current_key
                st.sidebar.success(f"Đã tự động gửi lệnh {auto_cmd}")
            else:
                st.sidebar.error(f"Không gửi được MQTT: {result}")
        else:
            st.sidebar.caption("Lệnh này đã được gửi, không gửi lặp lại.")


# =========================
# HEADER
# =========================
st.markdown(
    '<div class="main-title">IOT WEATHER DASHBOARD - HỆ THỐNG PHƠI ĐỒ THÔNG MINH</div>',
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

    auto_cmd, auto_reason = auto_decide_command(latest)

    if auto_cmd == "CLOSE":
        control_color = "#e74c3c"
        control_icon = "wi wi-rain"
        control_text = f"ĐÓNG {SERVO_CLOSE_ANGLE}°"

    elif auto_cmd == "OPEN":
        control_color = "#43b36a"
        control_icon = "wi wi-day-sunny"
        control_text = f"MỞ {SERVO_OPEN_ANGLE}°"

    else:
        control_color = "#f5a623"
        control_icon = "wi wi-na"
        control_text = "GIỮ NGUYÊN"

    metric_card(
        "Điều khiển MG90S",
        control_text,
        auto_reason,
        control_icon,
        control_color,
        100
    )

    st.markdown('<div class="section-title">ĐIỀU KHIỂN THỦ CÔNG</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="control-note">
            SERVO: <b>{SERVO_NAME}</b><br>
            OPEN → {SERVO_OPEN_ANGLE}° &nbsp;&nbsp; | &nbsp;&nbsp;
            CLOSE → {SERVO_CLOSE_ANGLE}°
        </div>
        """,
        unsafe_allow_html=True
    )

    btn1, btn2, btn3 = st.columns(3)

    with btn1:
        if st.button("MỞ DÀN PHƠI 90°", use_container_width=True, key="main_open"):
            ok, result = mqtt_publish(
                "OPEN",
                "Người dùng bấm mở dàn phơi 90 độ trên dashboard"
            )
    
            if ok:
                st.success("Đã gửi lệnh mở dàn phơi 90°")
            else:
                st.error(f"Không gửi được MQTT: {result}")
    
    with btn2:
        if st.button("ĐÓNG DÀN PHƠI 0°", use_container_width=True, key="main_close"):
            ok, result = mqtt_publish(
                "CLOSE",
                "Người dùng bấm đóng dàn phơi về 0 độ trên dashboard"
            )
    
            if ok:
                st.success("Đã gửi lệnh đóng dàn phơi 0°")
            else:
                st.error(f"Không gửi được MQTT: {result}")
    
    with btn3:
        if st.button("MỞ CỬA MG90S", use_container_width=True, key="main_msg40"):
            ok, result = mqtt_publish(
                "MSG40",
                "Người dùng bấm mở cửa bằng servo MG90S trên dashboard"
            )
    
            if ok:
                st.success("Đã gửi lệnh MSG40 - mở cửa MG90S 90°")
            else:
                st.error(f"Không gửi được MQTT: {result}")

# =========================
# BIG CHART
# =========================
render_big_temperature_chart(df)


# =========================
# DATA TABLE
# =========================
with st.expander("Xem dữ liệu cảm biến"):
    st.dataframe(df.tail(100), use_container_width=True)
