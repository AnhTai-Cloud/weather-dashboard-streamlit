import json
import ssl
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="IoT Weather Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# MQTT CONFIG - SỬA 3 DÒNG NÀY THEO HIVEMQ CỦA BẠN
# =========================================================
MQTT_BROKER = "70c5a54b752643dd817d84ea128f899d.s1.eu.hivemq.cloud"
MQTT_PORT = 8883

MQTT_USERNAME = "ESP32-client"
MQTT_PASSWORD = "Tan01052005!"

MQTT_CLIENT_ID = "streamlit_weather_dashboard"

MQTT_TOPIC_SENSOR_DATA = "smart_home/sensor/data"
MQTT_TOPIC_CONTROL_RACK = "smart_home/control/rack"
MQTT_TOPIC_CONTROL_DOOR = "smart_home/control/door"
MQTT_TOPIC_CONTROL_MODE = "smart_home/control/mode"


# =========================================================
# DEVICE CONFIG
# =========================================================
SERVO_NAME = "MG90S"
SERVO_OPEN_ANGLE = 90
SERVO_CLOSE_ANGLE = 0

DOOR_SERVO_NAME = "MG90S"
DOOR_OPEN_ANGLE = 90

GAS_SENSOR_NAME = "MQ-5"
GAS_SAFE_LIMIT = 300

DATA_SOURCE = "data.csv"


# =========================================================
# CSS + ICON PACK
# =========================================================
st.markdown(
    """
    <link rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
html, body, .stApp {
    font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif !important;
}

button, input, textarea, select, div, p, span {
    font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
}

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

.section-title {
    font-size: 23px;
    font-weight: 850;
    text-transform: uppercase;
    margin: 24px 0 14px 0;
    color: #2f3341;
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

.status-box {
    background: #f3eee8;
    border-radius: 22px;
    padding: 16px 18px;
    box-shadow: 0 8px 22px rgba(0,0,0,0.05);
    margin-bottom: 14px;
}

.status-title {
    font-size: 14px;
    color: #74777f;
    text-transform: uppercase;
    font-weight: 750;
}

.status-value {
    font-size: 25px;
    font-weight: 850;
    margin-top: 8px;
}

.mqtt-live {
    background: #e8f6ef;
    color: #20724b;
    border-radius: 14px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-weight: 700;
}

.mqtt-warn {
    background: #fff5d9;
    color: #8a6200;
    border-radius: 14px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# BASIC HELPERS
# =========================================================
def clamp(x, min_val=0, max_val=100):
    try:
        return max(min_val, min(float(x), max_val))
    except Exception:
        return min_val


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


def status_box(title, value, desc, color):
    html = f"""
    <div class="status-box">
        <div class="status-title">{title}</div>
        <div class="status-value" style="color:{color};">{value}</div>
        <div class="metric-desc">{desc}</div>
    </div>
    """
    st.markdown(" ".join(html.split()), unsafe_allow_html=True)


# =========================================================
# MQTT
# =========================================================
def create_mqtt_client(suffix):
    client_id = f"{MQTT_CLIENT_ID}_{suffix}_{int(time.time() * 1000)}"

    client = mqtt.Client(
        client_id=client_id,
        protocol=mqtt.MQTTv311,
    )

    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )

    return client


def mqtt_get_latest_sensor_data(timeout_sec=1.2):
    """
    Đọc payload mới nhất từ topic sensor.
    ESP nên publish retained để fragment đọc được ngay.
    """

    result = {
        "payload": None,
        "error": None,
        "raw": None,
    }

    try:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                client.subscribe(MQTT_TOPIC_SENSOR_DATA, qos=1)
            else:
                result["error"] = f"MQTT connect failed, rc={rc}"

        def on_message(client, userdata, msg):
            try:
                text = msg.payload.decode("utf-8")
                result["raw"] = text
                result["payload"] = json.loads(text)
            except Exception as e:
                result["error"] = f"Parse payload error: {type(e).__name__}: {e}"

        client = create_mqtt_client("sub")
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
        client.loop_start()

        start = time.time()
        while time.time() - start < timeout_sec:
            if result["payload"] is not None or result["error"] is not None:
                break
            time.sleep(0.05)

        client.loop_stop()
        client.disconnect()

        return result["payload"], result["error"], result["raw"]

    except Exception as e:
        return None, f"{type(e).__name__}: {e}", None


def mqtt_publish_control(topic, message):
    """
    Gửi lệnh nhanh xuống ESP.
    QoS 0 để giảm delay.
    """

    try:
        client = create_mqtt_client("pub_fast")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)
        client.loop_start()

        time.sleep(0.15)

        info = client.publish(
            topic,
            message,
            qos=0,
            retain=False,
        )

        start = time.time()
        while not info.is_published() and time.time() - start < 0.6:
            time.sleep(0.03)

        client.loop_stop()
        client.disconnect()

        return True, {
            "topic": topic,
            "message": message,
        }

    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def mqtt_open_rack():
    return mqtt_publish_control(MQTT_TOPIC_CONTROL_RACK, "OPEN")


def mqtt_close_rack():
    return mqtt_publish_control(MQTT_TOPIC_CONTROL_RACK, "CLOSE")


def mqtt_open_door():
    return mqtt_publish_control(MQTT_TOPIC_CONTROL_DOOR, "OPEN")


def mqtt_close_door():
    return mqtt_publish_control(MQTT_TOPIC_CONTROL_DOOR, "CLOSE")


def mqtt_set_auto_mode():
    return mqtt_publish_control(MQTT_TOPIC_CONTROL_MODE, "AUTO")


def mqtt_set_manual_mode():
    return mqtt_publish_control(MQTT_TOPIC_CONTROL_MODE, "MANUAL")


# =========================================================
# DATA MAPPING
# =========================================================
def mqtt_payload_to_row(payload):
    rain_state = str(payload.get("rain_state", "NO_RAIN")).upper()
    rack_state = str(payload.get("rack_state", "CLOSE")).upper()
    door_state = str(payload.get("door_state", "CLOSE")).upper()

    temperature = float(payload.get("temperature", 0))
    humidity = float(payload.get("humidity", 0))
    pressure = float(payload.get("pressure_hpa", payload.get("pressure", 0)))
    light = float(payload.get("light_lux", payload.get("light", 0)))
    gas = float(payload.get("gas_raw", payload.get("gas", 0)))

    rain_sensor = 1 if rain_state in ["RAIN", "RAINING", "YES", "1", "TRUE"] else 0

    if rain_sensor == 1:
        weather_label = "Mưa"
    elif light < 300:
        weather_label = "Âm u"
    else:
        weather_label = "Nắng"

    return {
        "time": datetime.now(),
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "light": light,
        "rain_sensor": rain_sensor,
        "gas": gas,
        "weather_label": weather_label,
        "ai_prediction": weather_label,

        "rain_raw": int(payload.get("rain_raw", 0)),
        "rain_state": rain_state,
        "gas_alarm": bool(payload.get("gas_alarm", False)),
        "rack_state": rack_state,
        "door_state": door_state,
        "mode": str(payload.get("mode", "UNKNOWN")).upper(),
        "period": str(payload.get("period", "UNKNOWN")).upper(),
        "mqtt_raw": payload,
    }


# =========================================================
# FALLBACK DATA
# =========================================================
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
        gas = max(0, 120 + np.random.normal(0, 18))

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
            "gas": round(gas, 0),
            "weather_label": label,
            "ai_prediction": label,
            "rain_raw": 0,
            "rain_state": "RAIN" if rain == 1 else "NO_RAIN",
            "gas_alarm": gas >= GAS_SAFE_LIMIT,
            "rack_state": "CLOSE",
            "door_state": "CLOSE",
            "mode": "DEMO",
            "period": "UNKNOWN",
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=30)
def load_fallback_data():
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
        "gas",
        "weather_label",
        "ai_prediction",
        "rain_raw",
        "rain_state",
        "gas_alarm",
        "rack_state",
        "door_state",
        "mode",
        "period",
    ]

    for col in required_cols:
        if col not in df.columns:
            if col in ["weather_label", "ai_prediction"]:
                df[col] = "Không rõ"
            elif col in ["rain_state", "rack_state", "door_state", "mode", "period"]:
                df[col] = "UNKNOWN"
            elif col == "gas_alarm":
                df[col] = False
            else:
                df[col] = 0

    return df


# =========================================================
# UI STATE
# =========================================================
def init_state():
    if "live_df" not in st.session_state:
        st.session_state.live_df = pd.DataFrame()

    if "latest_data" not in st.session_state:
        fallback_df = load_fallback_data()
        st.session_state.latest_data = fallback_df.iloc[-1].to_dict()

    if "mqtt_payload" not in st.session_state:
        st.session_state.mqtt_payload = None

    if "mqtt_error" not in st.session_state:
        st.session_state.mqtt_error = None

    if "data_source_name" not in st.session_state:
        st.session_state.data_source_name = "DATA.CSV FALLBACK"

    if "clothesline_state" not in st.session_state:
        st.session_state.clothesline_state = "ĐANG ĐÓNG"

    if "door_state" not in st.session_state:
        st.session_state.door_state = "ĐANG ĐÓNG"

    if "last_manual_action" not in st.session_state:
        st.session_state.last_manual_action = "CHƯA CÓ LỆNH"


def update_state_from_latest(row):
    rack_state = str(row.get("rack_state", "CLOSE")).upper()
    door_state = str(row.get("door_state", "CLOSE")).upper()

    if rack_state == "OPEN":
        st.session_state.clothesline_state = "ĐANG MỞ"
    elif rack_state == "CLOSE":
        st.session_state.clothesline_state = "ĐANG ĐÓNG"

    if door_state == "OPEN":
        st.session_state.door_state = "ĐANG MỞ"
    elif door_state == "CLOSE":
        st.session_state.door_state = "ĐANG ĐÓNG"


# =========================================================
# AI DECISION
# =========================================================
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


# =========================================================
# LIVE DATA FRAGMENT
# =========================================================
@st.fragment(run_every="2s")
def live_sensor_fragment():
    mqtt_payload, mqtt_error, mqtt_raw = mqtt_get_latest_sensor_data(timeout_sec=1.2)

    if mqtt_payload is not None:
        mqtt_row = mqtt_payload_to_row(mqtt_payload)

        st.session_state.latest_data = mqtt_row
        st.session_state.mqtt_payload = mqtt_payload
        st.session_state.mqtt_error = None
        st.session_state.data_source_name = "MQTT REALTIME"

        st.session_state.live_df = pd.concat(
            [st.session_state.live_df, pd.DataFrame([mqtt_row])],
            ignore_index=True,
        ).tail(100)

        update_state_from_latest(mqtt_row)

    else:
        st.session_state.mqtt_error = mqtt_error

    latest = pd.Series(st.session_state.latest_data)

    if st.session_state.data_source_name == "MQTT REALTIME":
        st.markdown(
            '<div class="mqtt-live">ĐANG NHẬN DỮ LIỆU MQTT REALTIME TỪ ESP32</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="mqtt-warn">CHƯA NHẬN ĐƯỢC MQTT, ĐANG DÙNG DỮ LIỆU DỰ PHÒNG</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="sub-title">Cập nhật: {latest["time"]}</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Nhiệt độ",
            f'{float(latest["temperature"]):.1f}°C',
            st.session_state.data_source_name,
            "wi wi-thermometer",
            "#f5a623",
            clamp(float(latest["temperature"]) / 45 * 100),
        )

    with c2:
        metric_card(
            "Độ ẩm",
            f'{float(latest["humidity"]):.0f}%',
            st.session_state.data_source_name,
            "wi wi-humidity",
            "#5b83ff",
            latest["humidity"],
        )

    with c3:
        metric_card(
            "Áp suất",
            f'{float(latest["pressure"]):.1f} hPa',
            "BMP280",
            "wi wi-barometer",
            "#9a7dff",
            clamp((float(latest["pressure"]) - 950) * 2),
        )

    with c4:
        metric_card(
            "Ánh sáng",
            f'{float(latest["light"]):.0f} lux',
            "Light sensor",
            "wi wi-day-sunny",
            "#f5a623",
            clamp(float(latest["light"]) / 1000 * 100),
        )

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        rain_text = "Có mưa" if int(latest["rain_sensor"]) == 1 else "Không mưa"

        metric_card(
            "Cảm biến mưa",
            rain_text,
            f'Raw: {latest.get("rain_raw", 0)} | {latest.get("rain_state", "UNKNOWN")}',
            "wi wi-raindrop",
            "#e74c3c" if int(latest["rain_sensor"]) == 1 else "#43b36a",
            100 if int(latest["rain_sensor"]) == 1 else 10,
        )

    with c6:
        gas_value = float(latest["gas"])
        gas_alarm = bool(latest.get("gas_alarm", gas_value >= GAS_SAFE_LIMIT))
        gas_status = "CẢNH BÁO" if gas_alarm else "AN TOÀN"

        metric_card(
            "Gas MQ-5",
            f"{gas_value:.0f}",
            f"{gas_status} | Ngưỡng {GAS_SAFE_LIMIT}",
            "wi wi-smoke",
            "#e74c3c" if gas_alarm else "#43b36a",
            clamp(gas_value / 1000 * 100),
        )

    with c7:
        pred = latest["ai_prediction"]
        icon, color = weather_icon(pred)

        metric_card(
            "AI dự đoán",
            pred,
            "Nắng / Âm u / Mưa",
            icon,
            color,
            80,
        )

    with c8:
        metric_card(
            "Chế độ ESP",
            str(latest.get("mode", "UNKNOWN")),
            f'Period: {latest.get("period", "UNKNOWN")}',
            "wi wi-time-3",
            "#43b36a" if str(latest.get("mode", "")).upper() == "AUTO" else "#f5a623",
            80,
        )

    st.markdown('<div class="section-title">TRẠNG THÁI THIẾT BỊ</div>', unsafe_allow_html=True)

    s1, s2 = st.columns(2)

    with s1:
        color = "#43b36a" if st.session_state.clothesline_state == "ĐANG MỞ" else "#e74c3c"
        status_box(
            "Trạng thái dàn phơi",
            st.session_state.clothesline_state,
            f'ESP: {latest.get("rack_state", "UNKNOWN")}',
            color,
        )

    with s2:
        color = "#43b36a" if st.session_state.door_state == "ĐANG MỞ" else "#e74c3c"
        status_box(
            "Trạng thái cửa",
            st.session_state.door_state,
            f'ESP: {latest.get("door_state", "UNKNOWN")}',
            color,
        )

    auto_cmd, auto_reason = auto_decide_command(latest)

    if auto_cmd == "CLOSE":
        control_color = "#e74c3c"
        control_icon = "wi wi-rain"
        control_text = f"ĐÓNG {SERVO_CLOSE_ANGLE}°"
    else:
        control_color = "#43b36a"
        control_icon = "wi wi-day-sunny"
        control_text = f"MỞ {SERVO_OPEN_ANGLE}°"

    metric_card(
        "AI điều khiển dàn phơi",
        control_text,
        auto_reason,
        control_icon,
        control_color,
        100,
    )

    if st.session_state.mqtt_error:
        st.warning(f"Lỗi MQTT gần nhất: {st.session_state.mqtt_error}")


# =========================================================
# CHART FRAGMENT
# =========================================================
@st.fragment(run_every="6s")
def chart_fragment():
    fallback_df = load_fallback_data()

    if not st.session_state.live_df.empty:
        df = pd.concat([fallback_df, st.session_state.live_df], ignore_index=True)
    else:
        df = fallback_df

    chart_df = df.tail(24).copy()
    chart_df["time"] = pd.to_datetime(chart_df["time"])

    min_temp = chart_df["temperature"].astype(float).min()
    max_temp = chart_df["temperature"].astype(float).max()

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
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["time"],
            y=chart_df["temperature"],
            mode="lines+markers+text",
            text=[f"{float(v):.0f}°" for v in chart_df["temperature"]],
            textposition="top center",
            line=dict(
                width=4,
                color="rgba(255, 150, 150, 0.95)",
                shape="spline",
                smoothing=1.15,
            ),
            marker=dict(
                size=8,
                color="rgba(255, 130, 130, 1)",
                line=dict(width=2, color="white"),
            ),
            fill="tonexty",
            fillcolor="rgba(255, 150, 150, 0.22)",
            showlegend=False,
            hovertemplate="<b>%{x|%H:%M}</b><br>Nhiệt độ: %{y:.1f}°C<extra></extra>",
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
            color="#2f3341",
        ),
        xaxis=dict(
            title="",
            showgrid=False,
            tickmode="array",
            tickvals=tick_df["time"],
            ticktext=[t.strftime("%H:%M") for t in tick_df["time"]],
            linecolor="rgba(0,0,0,0.08)",
            tickfont=dict(size=13),
            fixedrange=True,
        ),
        yaxis=dict(
            title="NHIỆT ĐỘ °C",
            range=[y_bottom, y_top],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.06)",
            zeroline=False,
            tickfont=dict(size=12),
            fixedrange=True,
        ),
    )

    st.markdown(
        '<div class="section-title">BIỂU ĐỒ NHIỆT ĐỘ & MƯA GẦN NHẤT</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
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
                        <div style="color:#555; margin-top:6px; font-size:13px;">
                            {time_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =========================================================
# INIT
# =========================================================
init_state()


# =========================================================
# SIDEBAR - KHÔNG AUTO REFRESH TOÀN TRANG
# =========================================================
st.sidebar.title("⚙️ CÀI ĐẶT HỆ THỐNG")

st.sidebar.write("Broker:")
st.sidebar.code(MQTT_BROKER)

st.sidebar.write("Sensor topic:")
st.sidebar.code(MQTT_TOPIC_SENSOR_DATA)

st.sidebar.write("Rack topic:")
st.sidebar.code(MQTT_TOPIC_CONTROL_RACK)

st.sidebar.write("Door topic:")
st.sidebar.code(MQTT_TOPIC_CONTROL_DOOR)

st.sidebar.write("Mode topic:")
st.sidebar.code(MQTT_TOPIC_CONTROL_MODE)

st.sidebar.markdown("---")
st.sidebar.subheader("📡 ĐIỀU KHIỂN MQTT")

if st.sidebar.button("CHUYỂN MANUAL", use_container_width=True):
    ok, result = mqtt_set_manual_mode()
    if ok:
        st.sidebar.success("Đã gửi MANUAL")
    else:
        st.sidebar.error(f"Lỗi: {result}")

if st.sidebar.button("CHUYỂN AUTO", use_container_width=True):
    ok, result = mqtt_set_auto_mode()
    if ok:
        st.sidebar.success("Đã gửi AUTO")
    else:
        st.sidebar.error(f"Lỗi: {result}")

st.sidebar.markdown("### ĐIỀU KHIỂN THỦ CÔNG")

side_col1, side_col2 = st.sidebar.columns(2)

with side_col1:
    if st.button("MỞ 90°", use_container_width=True, key="side_open"):
        ok, result = mqtt_open_rack()
        if ok:
            st.session_state.clothesline_state = "ĐANG MỞ"
            st.session_state.last_manual_action = "MỞ DÀN PHƠI 90°"
            st.sidebar.success("Đã gửi OPEN")
        else:
            st.sidebar.error(f"Lỗi: {result}")

with side_col2:
    if st.button("ĐÓNG 0°", use_container_width=True, key="side_close"):
        ok, result = mqtt_close_rack()
        if ok:
            st.session_state.clothesline_state = "ĐANG ĐÓNG"
            st.session_state.last_manual_action = "ĐÓNG DÀN PHƠI 0°"
            st.sidebar.success("Đã gửi CLOSE")
        else:
            st.sidebar.error(f"Lỗi: {result}")

if st.sidebar.button("MỞ CỬA MG90S", use_container_width=True, key="side_door"):
    ok, result = mqtt_open_door()
    if ok:
        st.session_state.door_state = "ĐANG MỞ"
        st.session_state.last_manual_action = "MỞ CỬA MG90S"
        st.sidebar.success("Đã gửi DOOR OPEN")
    else:
        st.sidebar.error(f"Lỗi: {result}")

st.sidebar.markdown("---")
if st.session_state.mqtt_payload:
    with st.sidebar.expander("Payload MQTT mới nhất"):
        st.json(st.session_state.mqtt_payload)
else:
    st.sidebar.warning("Chưa có payload MQTT trong phiên này")


# =========================================================
# HEADER
# =========================================================
st.markdown(
    '<div class="main-title">IOT WEATHER DASHBOARD - HỆ THỐNG PHƠI ĐỒ THÔNG MINH</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">Dữ liệu cảm biến tự cập nhật theo từng phần, không refresh toàn trang.</div>',
    unsafe_allow_html=True,
)


# =========================================================
# LIVE SENSOR SECTION - FRAGMENT
# =========================================================
st.markdown('<div class="section-title">DỮ LIỆU CẢM BIẾN REALTIME</div>', unsafe_allow_html=True)
live_sensor_fragment()


# =========================================================
# CONTROL SECTION - KHÔNG NẰM TRONG FRAGMENT
# =========================================================
st.markdown('<div class="section-title">ĐIỀU KHIỂN THỦ CÔNG</div>', unsafe_allow_html=True)

btn1, btn2, btn3 = st.columns(3)

with btn1:
    if st.button("MỞ DÀN PHƠI 90°", use_container_width=True, key="main_open"):
        ok, result = mqtt_open_rack()

        if ok:
            st.session_state.clothesline_state = "ĐANG MỞ"
            st.session_state.last_manual_action = "MỞ DÀN PHƠI 90°"
            st.success("Đã gửi lệnh mở dàn phơi")
        else:
            st.error(f"Không gửi được MQTT: {result}")

with btn2:
    if st.button("ĐÓNG DÀN PHƠI 0°", use_container_width=True, key="main_close"):
        ok, result = mqtt_close_rack()

        if ok:
            st.session_state.clothesline_state = "ĐANG ĐÓNG"
            st.session_state.last_manual_action = "ĐÓNG DÀN PHƠI 0°"
            st.success("Đã gửi lệnh đóng dàn phơi")
        else:
            st.error(f"Không gửi được MQTT: {result}")

with btn3:
    if st.button("MỞ CỬA MG90S", use_container_width=True, key="main_door_open"):
        ok, result = mqtt_open_door()

        if ok:
            st.session_state.door_state = "ĐANG MỞ"
            st.session_state.last_manual_action = "MỞ CỬA MG90S"
            st.success("Đã gửi lệnh mở cửa MG90S")
        else:
            st.error(f"Không gửi được MQTT: {result}")

st.info(f"Lệnh gần nhất: {st.session_state.last_manual_action}")


# =========================================================
# AI CONTROL SECTION
# =========================================================
st.markdown('<div class="section-title">AI ĐIỀU KHIỂN DÀN PHƠI</div>', unsafe_allow_html=True)

latest = pd.Series(st.session_state.latest_data)
auto_cmd, auto_reason = auto_decide_command(latest)

ai_col1, ai_col2 = st.columns([2, 1])

with ai_col1:
    st.info(f"AI đề xuất: {auto_cmd}\n\nLý do: {auto_reason}")

with ai_col2:
    if st.button("GỬI LỆNH THEO AI", use_container_width=True):
        mqtt_set_auto_mode()

        if auto_cmd == "OPEN":
            ok, result = mqtt_open_rack()
        else:
            ok, result = mqtt_close_rack()

        if ok:
            if auto_cmd == "OPEN":
                st.session_state.clothesline_state = "ĐANG MỞ"
            else:
                st.session_state.clothesline_state = "ĐANG ĐÓNG"

            st.session_state.last_manual_action = f"AI GỬI {auto_cmd}"
            st.success(f"Đã gửi lệnh {auto_cmd}")
        else:
            st.error(f"Không gửi được MQTT: {result}")


# =========================================================
# CHART SECTION - FRAGMENT RIÊNG
# =========================================================
chart_fragment()


# =========================================================
# DATA TABLE
# =========================================================
with st.expander("Xem dữ liệu cảm biến đã lưu trong phiên"):
    if not st.session_state.live_df.empty:
        st.dataframe(st.session_state.live_df.tail(100), use_container_width=True)
    else:
        st.write("Chưa có dữ liệu realtime trong phiên này.")

with st.expander("Format payload MQTT cần nhận"):
    st.code(
        """
{
  "temperature": 28.45,
  "humidity": 70.12,
  "pressure_hpa": 1007.25,
  "light_lux": 325.50,
  "rain_raw": 4095,
  "rain_state": "NO_RAIN",
  "gas_raw": 1200,
  "gas_alarm": false,
  "rack_state": "OPEN",
  "door_state": "CLOSE",
  "mode": "AUTO",
  "period": "SANG"
}
        """,
        language="json",
    )
