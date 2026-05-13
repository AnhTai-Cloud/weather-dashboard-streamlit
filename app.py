import json
from string import Template

import streamlit as st
from streamlit.components.v1 import html


# =========================
# STREAMLIT PAGE CONFIG
# =========================
st.set_page_config(
    page_title="IoT Weather Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.6rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 0rem !important;
            max-width: 100% !important;
        }

        header {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        iframe {
            border: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# API CONFIG
# =========================
AI_API_BASE = "https://weather-model-api.onrender.com"


# =========================
# MQTT WEBSOCKET CONFIG
# =========================
MQTT_BROKER_HOST = "70c5a54b752643dd817d84ea128f899d.s1.eu.hivemq.cloud"
MQTT_WS_PORT = 8884
MQTT_WS_PATH = "/mqtt"

MQTT_USERNAME = "ESP32-client"

# Nên đặt MQTT_PASSWORD trong Streamlit Secrets.
# Nếu chưa dùng secrets, thay YOUR_MQTT_PASSWORD bằng mật khẩu MQTT thật.
MQTT_PASSWORD = st.secrets["MQTT_PASSWORD"] if "MQTT_PASSWORD" in st.secrets else "YOUR_MQTT_PASSWORD"

MQTT_TOPIC_SENSOR_DATA = "smart_home/sensor/data"
MQTT_TOPIC_CONTROL_RACK = "smart_home/control/rack"
MQTT_TOPIC_CONTROL_DOOR = "smart_home/control/door"
MQTT_TOPIC_CONTROL_MODE = "smart_home/control/mode"

MQTT_WS_URL = f"wss://{MQTT_BROKER_HOST}:{MQTT_WS_PORT}{MQTT_WS_PATH}"


html_template = Template(r"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css">
    <script src="https://unpkg.com/mqtt/dist/mqtt.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        * {
            box-sizing: border-box;
            font-family: "Segoe UI", "Inter", "Roboto", Arial, sans-serif;
        }

        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            background: #eef0f3;
            color: #2f3341;
            overflow-x: hidden;
        }

        .page {
            width: 100%;
            margin: 0;
            padding: 18px;
        }

        .hero {
            background: linear-gradient(135deg, #f7f1ea 0%, #edf2ff 100%);
            border-radius: 30px;
            padding: 24px 26px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.06);
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: 1.65fr 1fr;
            gap: 22px;
            align-items: center;
        }

        .title {
            font-size: 34px;
            font-weight: 950;
            line-height: 1.2;
            text-transform: uppercase;
            letter-spacing: -0.7px;
        }

        .hero-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 16px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 9px 15px;
            background: rgba(255,255,255,0.85);
            color: #535866;
            font-size: 13px;
            font-weight: 850;
        }

        .pill-ok {
            color: white;
            background: #43b36a;
        }

        .pill-wait {
            color: white;
            background: #f5a623;
        }

        .pill-error {
            color: white;
            background: #e74c3c;
        }

        .hero-ai {
            background: rgba(255,255,255,0.76);
            border-radius: 26px;
            padding: 22px;
            min-height: 150px;
        }

        .hero-ai-title {
            font-size: 14px;
            font-weight: 950;
            text-transform: uppercase;
            color: #74777f;
        }

        .hero-ai-main {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-top: 14px;
        }

        .hero-ai-value {
            font-size: 36px;
            font-weight: 950;
            letter-spacing: -0.8px;
        }

        .hero-ai-sub {
            margin-top: 10px;
            color: #2f4a8a;
            font-size: 14px;
            font-weight: 850;
            line-height: 1.45;
        }

        .hero-ai-icon {
            width: 70px;
            height: 70px;
            border-radius: 24px;
            background: #fff7e8;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .hero-ai-icon i {
            font-size: 36px;
            color: #f5a623;
        }

        .section-title {
            font-size: 23px;
            font-weight: 950;
            text-transform: uppercase;
            margin: 24px 0 14px 0;
            color: #2f3341;
            letter-spacing: -0.3px;
        }

        .forecast-card,
        .control-card,
        .chart-card {
            background: #f7f1ea;
            border-radius: 30px;
            padding: 20px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.045);
            margin-bottom: 18px;
        }

        .forecast-top {
            display: grid;
            grid-template-columns: 1.25fr 2.1fr;
            gap: 16px;
            align-items: stretch;
        }

        .current-weather {
            background: rgba(255,255,255,0.72);
            border-radius: 26px;
            padding: 20px;
            min-height: 190px;
        }

        .current-location {
            font-size: 15px;
            font-weight: 950;
            color: #3c4050;
        }

        .current-main {
            margin-top: 20px;
            display: flex;
            align-items: center;
            gap: 18px;
        }

        .current-main i {
            font-size: 60px;
            color: #f5a623;
        }

        .current-temp {
            font-size: 52px;
            font-weight: 950;
            letter-spacing: -1px;
        }

        .current-label {
            margin-top: 6px;
            font-size: 18px;
            font-weight: 900;
            color: #3c4050;
        }

        .daily-list {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 12px;
        }

        .day-item {
            background: rgba(255,255,255,0.72);
            border-radius: 24px;
            padding: 16px 12px;
            min-height: 190px;
            text-align: center;
        }

        .day-name {
            font-size: 14px;
            font-weight: 950;
            color: #3c4050;
        }

        .day-date {
            margin-top: 4px;
            font-size: 12px;
            font-weight: 800;
            color: #7a7f8c;
        }

        .day-icon {
            margin-top: 14px;
            font-size: 36px;
            color: #f5a623;
        }

        .day-temp {
            margin-top: 14px;
            font-size: 18px;
            font-weight: 950;
        }

        .day-rain {
            margin-top: 5px;
            font-size: 12px;
            font-weight: 850;
            color: #5b83ff;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 16px;
        }

        .card {
            background: #f7f1ea;
            border-radius: 26px;
            padding: 18px 20px;
            min-height: 158px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.045);
        }

        .card-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }

        .card-title {
            font-size: 14px;
            font-weight: 950;
            text-transform: uppercase;
            color: #3c4050;
        }

        .icon-box {
            width: 48px;
            height: 48px;
            border-radius: 17px;
            background: rgba(255,255,255,0.88);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .icon-box i {
            font-size: 25px;
        }

        .value {
            font-size: 31px;
            font-weight: 950;
            margin-top: 14px;
            word-break: break-word;
            letter-spacing: -0.6px;
        }

        .desc {
            color: #74777f;
            font-size: 13px;
            margin-top: 4px;
            font-weight: 700;
        }

        .progress-wrap {
            width: 100%;
            height: 9px;
            background: #ded8d1;
            border-radius: 999px;
            overflow: hidden;
            margin-top: 15px;
        }

        .progress-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.25s ease, background 0.25s ease;
        }

        .button-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }

        .button-row-2 {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-top: 12px;
        }

        button {
            border: none;
            border-radius: 18px;
            padding: 15px 12px;
            font-size: 15px;
            font-weight: 950;
            cursor: pointer;
            color: white;
            transition: transform 0.12s ease, opacity 0.12s ease;
        }

        button:hover {
            transform: translateY(-1px);
            opacity: 0.93;
        }

        button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
            transform: none;
        }

        .btn-open {
            background: #43b36a;
        }

        .btn-close {
            background: #e74c3c;
        }

        .btn-door {
            background: #5b83ff;
        }

        .btn-mode {
            background: #9a7dff;
        }

        .btn-ai {
            background: #f5a623;
        }

        .info-line {
            background: #e8eefc;
            color: #2f4a8a;
            border-radius: 17px;
            padding: 12px 14px;
            font-size: 14px;
            font-weight: 850;
            margin-top: 12px;
        }

        .raw-box {
            background: #20242c;
            color: #dbe6ff;
            border-radius: 22px;
            padding: 16px;
            overflow: auto;
            max-height: 260px;
            font-size: 13px;
            white-space: pre-wrap;
            margin-bottom: 10px;
        }

        @media (max-width: 1150px) {
            .hero {
                grid-template-columns: 1fr;
            }

            .forecast-top {
                grid-template-columns: 1fr;
            }

            .grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .daily-list {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }

        @media (max-width: 700px) {
            .page {
                padding: 12px 10px 26px 10px;
            }

            .title {
                font-size: 24px;
            }

            .grid,
            .button-row,
            .button-row-2,
            .daily-list {
                grid-template-columns: 1fr;
            }

            .hero-ai-value {
                font-size: 28px;
            }
        }
    </style>
</head>

<body>
<div class="page">

    <div class="hero">
        <div>
            <div class="title">IOT WEATHER DASHBOARD<br>HỆ THỐNG PHƠI ĐỒ THÔNG MINH</div>
            <div class="hero-meta">
                <div id="mqttBadge" class="pill pill-wait">Đang kết nối MQTT</div>
                <div class="pill">Cập nhật: <span id="lastUpdate">--</span></div>
                <div class="pill">Chế độ: <span id="heroMode">--</span></div>
            </div>
        </div>

        <div class="hero-ai">
            <div class="hero-ai-title">Dự báo hệ thống</div>
            <div class="hero-ai-main">
                <div>
                    <div class="hero-ai-value" id="aiPrediction">--</div>
                    <div class="hero-ai-sub" id="aiDecision">Khuyến nghị: --</div>
                </div>
                <div class="hero-ai-icon">
                    <i class="wi wi-day-cloudy" id="aiIcon"></i>
                </div>
            </div>
        </div>
    </div>

    <div class="section-title">Dự báo thời tiết</div>

    <div class="forecast-card">
        <div class="forecast-top">
            <div class="current-weather">
                <div class="current-location" id="forecastLocation">Hanoi, Vietnam</div>
                <div class="current-main">
                    <i id="currentIcon" class="wi wi-day-sunny"></i>
                    <div>
                        <div class="current-temp" id="currentTemp">--°C</div>
                        <div class="current-label" id="currentWeather">--</div>
                    </div>
                </div>
                <div class="desc" id="currentMore">Độ ẩm: -- | Áp suất: --</div>
            </div>

            <div class="daily-list" id="dailyForecast">
                <div class="day-item">
                    <div class="day-name">--</div>
                    <div class="day-date">--</div>
                    <div class="day-icon"><i class="wi wi-day-cloudy"></i></div>
                    <div class="day-temp">-- / --</div>
                    <div class="day-rain">Mưa: --</div>
                </div>
            </div>
        </div>
    </div>

    <div class="section-title">Dữ liệu cảm biến</div>

    <div class="grid">
        <div class="card">
            <div class="card-head">
                <div class="card-title">Nhiệt độ</div>
                <div class="icon-box"><i class="wi wi-thermometer" style="color:#f5a623;"></i></div>
            </div>
            <div class="value" id="temperature">-- °C</div>
            <div class="desc">Dữ liệu từ ESP32</div>
            <div class="progress-wrap"><div id="temperatureBar" class="progress-fill" style="width:0%; background:#f5a623;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Độ ẩm</div>
                <div class="icon-box"><i class="wi wi-humidity" style="color:#5b83ff;"></i></div>
            </div>
            <div class="value" id="humidity">-- %</div>
            <div class="desc">Độ ẩm không khí</div>
            <div class="progress-wrap"><div id="humidityBar" class="progress-fill" style="width:0%; background:#5b83ff;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Áp suất</div>
                <div class="icon-box"><i class="wi wi-barometer" style="color:#9a7dff;"></i></div>
            </div>
            <div class="value" id="pressure">-- hPa</div>
            <div class="desc">BMP280</div>
            <div class="progress-wrap"><div id="pressureBar" class="progress-fill" style="width:0%; background:#9a7dff;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Ánh sáng</div>
                <div class="icon-box"><i class="wi wi-day-sunny" style="color:#f5a623;"></i></div>
            </div>
            <div class="value" id="light">-- lux</div>
            <div class="desc">Light sensor</div>
            <div class="progress-wrap"><div id="lightBar" class="progress-fill" style="width:0%; background:#f5a623;"></div></div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-head">
                <div class="card-title">Cảm biến mưa</div>
                <div class="icon-box"><i class="wi wi-raindrop" id="rainIcon" style="color:#43b36a;"></i></div>
            </div>
            <div class="value" id="rainState">--</div>
            <div class="desc" id="rainRaw">Raw: --</div>
            <div class="progress-wrap"><div id="rainBar" class="progress-fill" style="width:10%; background:#43b36a;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Gas MQ-5</div>
                <div class="icon-box"><i class="wi wi-smoke" id="gasIcon" style="color:#43b36a;"></i></div>
            </div>
            <div class="value" id="gas">--</div>
            <div class="desc" id="gasStatus">Trạng thái: --</div>
            <div class="progress-wrap"><div id="gasBar" class="progress-fill" style="width:0%; background:#43b36a;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Dàn phơi</div>
                <div class="icon-box"><i class="wi wi-day-sunny" id="rackIcon" style="color:#e74c3c;"></i></div>
            </div>
            <div class="value" id="rackState">ĐANG ĐÓNG</div>
            <div class="desc">Trạng thái: <span id="rackRaw">--</span></div>
            <div class="progress-wrap"><div id="rackBar" class="progress-fill" style="width:100%; background:#e74c3c;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Cửa</div>
                <div class="icon-box"><i class="wi wi-direction-down" id="doorIcon" style="color:#e74c3c;"></i></div>
            </div>
            <div class="value" id="doorState">ĐANG ĐÓNG</div>
            <div class="desc">Trạng thái: <span id="doorRaw">--</span></div>
            <div class="progress-wrap"><div id="doorBar" class="progress-fill" style="width:100%; background:#e74c3c;"></div></div>
        </div>
    </div>

    <div class="section-title">Điều khiển</div>

    <div class="control-card">
        <div class="button-row">
            <button class="btn-open" id="btnOpenRack">MỞ DÀN PHƠI 90°</button>
            <button class="btn-close" id="btnCloseRack">ĐÓNG DÀN PHƠI 0°</button>
            <button class="btn-door" id="btnOpenDoor">MỞ CỬA MG90S</button>
        </div>

        <div class="button-row-2">
            <button class="btn-mode" id="btnManual">CHUYỂN MANUAL</button>
            <button class="btn-mode" id="btnAuto">CHUYỂN AUTO</button>
        </div>

        <div class="button-row-2">
            <button class="btn-ai" id="btnAiSend">GỬI LỆNH THEO DỰ BÁO</button>
            <button class="btn-close" id="btnCloseDoor">ĐÓNG CỬA MG90S</button>
        </div>

        <div class="info-line" id="lastCommand">Lệnh gần nhất: Chưa có lệnh</div>
    </div>

    <div class="section-title">Biểu đồ nhiệt độ</div>

    <div class="chart-card">
        <canvas id="tempChart" height="105"></canvas>
    </div>

    <div class="section-title">Payload mới nhất</div>
    <pre class="raw-box" id="rawPayload">Chưa có payload...</pre>

</div>

<script>
const MQTT_WS_URL = $MQTT_WS_URL;
const MQTT_USERNAME = $MQTT_USERNAME;
const MQTT_PASSWORD = $MQTT_PASSWORD;

const TOPIC_SENSOR = $TOPIC_SENSOR;
const TOPIC_RACK = $TOPIC_RACK;
const TOPIC_DOOR = $TOPIC_DOOR;
const TOPIC_MODE = $TOPIC_MODE;

const AI_API_BASE = $AI_API_BASE;

let mqttClient = null;
let latestData = null;
let lastAiCommand = "CLOSE";
let lastPredictTime = 0;
let lastForecastTime = 0;

const PREDICT_INTERVAL_MS = 30 * 60 * 1000;
const FORECAST_INTERVAL_MS = 30 * 60 * 1000;

const tempLabels = [];
const tempValues = [];
const MAX_POINTS = 24;

function el(id) {
    return document.getElementById(id);
}

function clampJs(x, minVal, maxVal) {
    const n = Number(x);
    if (Number.isNaN(n)) return minVal;
    return Math.max(minVal, Math.min(n, maxVal));
}

function nowText() {
    return new Date().toLocaleString("vi-VN");
}

function setBadge(text, cls) {
    const badge = el("mqttBadge");
    badge.className = "pill " + cls;
    badge.innerText = text;
}

function setProgress(id, percent, color) {
    const bar = el(id);
    bar.style.width = clampJs(percent, 0, 100) + "%";
    if (color) {
        bar.style.background = color;
    }
}

function iconClass(iconName) {
    if (iconName === "sunny") return "wi wi-day-sunny";
    if (iconName === "partly_cloudy") return "wi wi-day-cloudy";
    if (iconName === "cloudy") return "wi wi-cloudy";
    if (iconName === "fog") return "wi wi-fog";
    if (iconName === "drizzle") return "wi wi-sprinkle";
    if (iconName === "rain") return "wi wi-rain";
    if (iconName === "snow") return "wi wi-snow";
    if (iconName === "thunderstorm") return "wi wi-thunderstorm";
    return "wi wi-day-cloudy";
}

function updateAiIcon(label) {
    const icon = el("aiIcon");

    if (label === "Mưa" || label === "Mưa rào" || label === "Dông") {
        icon.className = "wi wi-rain";
        icon.style.color = "#5b83ff";
    } else if (label === "Âm u" || label === "Ít mây") {
        icon.className = "wi wi-cloudy";
        icon.style.color = "#f5a623";
    } else {
        icon.className = "wi wi-day-sunny";
        icon.style.color = "#f5a623";
    }
}

function updateRackState(state) {
    const s = String(state || "CLOSE").toUpperCase();
    el("rackRaw").innerText = s;

    if (s === "OPEN") {
        el("rackState").innerText = "ĐANG MỞ";
        el("rackIcon").className = "wi wi-day-sunny";
        el("rackIcon").style.color = "#43b36a";
        setProgress("rackBar", 100, "#43b36a");
    } else {
        el("rackState").innerText = "ĐANG ĐÓNG";
        el("rackIcon").className = "wi wi-rain";
        el("rackIcon").style.color = "#e74c3c";
        setProgress("rackBar", 100, "#e74c3c");
    }
}

function updateDoorState(state) {
    const s = String(state || "CLOSE").toUpperCase();
    el("doorRaw").innerText = s;

    if (s === "OPEN") {
        el("doorState").innerText = "ĐANG MỞ";
        el("doorIcon").className = "wi wi-direction-up";
        el("doorIcon").style.color = "#43b36a";
        setProgress("doorBar", 100, "#43b36a");
    } else {
        el("doorState").innerText = "ĐANG ĐÓNG";
        el("doorIcon").className = "wi wi-direction-down";
        el("doorIcon").style.color = "#e74c3c";
        setProgress("doorBar", 100, "#e74c3c");
    }
}

function updateRain(data) {
    const rainState = String(data.rain_state || "NO_RAIN").toUpperCase();
    const rainRaw = data.rain_raw ?? "--";

    el("rainRaw").innerText = "Raw: " + rainRaw + " | " + rainState;

    if (rainState === "RAIN" || rainState === "RAINING" || Number(data.rain || 0) === 1) {
        el("rainState").innerText = "Có mưa";
        el("rainIcon").style.color = "#e74c3c";
        setProgress("rainBar", 100, "#e74c3c");
    } else {
        el("rainState").innerText = "Không mưa";
        el("rainIcon").style.color = "#43b36a";
        setProgress("rainBar", 10, "#43b36a");
    }
}

function updateGas(data) {
    const gas = Number(data.gas_raw || data.gas || 0);
    const gasAlarm = Boolean(data.gas_alarm);
    const status = gasAlarm ? "CẢNH BÁO" : "AN TOÀN";
    const color = gasAlarm ? "#e74c3c" : "#43b36a";

    el("gas").innerText = gas.toFixed(0);
    el("gasStatus").innerText = "Trạng thái: " + status;
    el("gasIcon").style.color = color;
    setProgress("gasBar", gas / 1000 * 100, color);
}

function updateMode(data) {
    const mode = String(data.mode || "UNKNOWN").toUpperCase();
    const period = String(data.period || "UNKNOWN").toUpperCase();
    el("heroMode").innerText = mode + " / " + period;
}

function updateCards(data) {
    latestData = data;

    const temperature = Number(data.temperature || 0);
    const humidity = Number(data.humidity || 0);
    const pressure = Number(data.pressure_hpa || data.pressure || 0);
    const light = Number(data.light_lux || data.light || 0);

    el("temperature").innerText = temperature.toFixed(1) + "°C";
    el("humidity").innerText = humidity.toFixed(0) + "%";
    el("pressure").innerText = pressure.toFixed(1) + " hPa";
    el("light").innerText = light.toFixed(0) + " lux";

    setProgress("temperatureBar", temperature / 45 * 100, "#f5a623");
    setProgress("humidityBar", humidity, "#5b83ff");
    setProgress("pressureBar", (pressure - 950) * 2, "#9a7dff");
    setProgress("lightBar", light / 1000 * 100, "#f5a623");

    updateRain(data);
    updateGas(data);
    updateRackState(data.rack_state || "CLOSE");
    updateDoorState(data.door_state || "CLOSE");
    updateMode(data);

    el("lastUpdate").innerText = nowText();
    el("rawPayload").innerText = JSON.stringify(data, null, 2);

    updateChart(temperature);
}

const chartCtx = document.getElementById("tempChart").getContext("2d");

const tempChart = new Chart(chartCtx, {
    type: "line",
    data: {
        labels: tempLabels,
        datasets: [{
            label: "Nhiệt độ °C",
            data: tempValues,
            borderWidth: 4,
            tension: 0.35,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 7,
            borderColor: "rgba(255, 150, 150, 0.95)",
            backgroundColor: "rgba(255, 150, 150, 0.22)"
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                grid: {
                    color: "rgba(0,0,0,0.06)"
                }
            }
        }
    }
});

function updateChart(temp) {
    const label = new Date().toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });

    tempLabels.push(label);
    tempValues.push(temp);

    if (tempLabels.length > MAX_POINTS) {
        tempLabels.shift();
        tempValues.shift();
    }

    tempChart.update();
}

function publish(topic, message, successText) {
    if (!mqttClient || !mqttClient.connected) {
        el("lastCommand").innerText = "Lỗi: MQTT chưa kết nối";
        return;
    }

    mqttClient.publish(topic, message, {
        qos: 0,
        retain: false
    });

    el("lastCommand").innerText = "Lệnh gần nhất: " + successText;
}

function setButtonsDisabled(disabled) {
    const ids = [
        "btnOpenRack",
        "btnCloseRack",
        "btnOpenDoor",
        "btnCloseDoor",
        "btnManual",
        "btnAuto",
        "btnAiSend"
    ];

    ids.forEach(function(id) {
        el(id).disabled = disabled;
    });
}

function normalizeForApi(data) {
    const rainState = String(data.rain_state || "NO_RAIN").toUpperCase();

    let rainValue = 0;

    if (rainState === "RAIN" || rainState === "RAINING") {
        rainValue = 1;
    } else if (data.rain !== undefined) {
        rainValue = Number(data.rain);
    }

    return {
        time: data.time || new Date().toISOString(),
        temperature: Number(data.temperature || 0),
        humidity: Number(data.humidity || 0),
        pressure: Number(data.pressure_hpa || data.pressure || 0),
        light: Number(data.light_lux || data.light || 0),
        rain: rainValue,
        gas: Number(data.gas_raw || data.gas || 0),
        rain_raw: data.rain_raw ?? null,
        rain_state: data.rain_state || null,
        gas_alarm: Boolean(data.gas_alarm),
        rack_state: data.rack_state || null,
        door_state: data.door_state || null,
        mode: data.mode || null,
        period: data.period || null
    };
}

async function sendIngestToApi(data) {
    const payload = normalizeForApi(data);

    try {
        const res = await fetch(AI_API_BASE + "/ingest", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        return await res.json();
    } catch (err) {
        console.error("Ingest API error:", err);
        el("aiDecision").innerText = "Khuyến nghị: lỗi gửi dữ liệu";
        return null;
    }
}

async function callPredictApi(force = false) {
    const now = Date.now();

    if (!force && now - lastPredictTime < PREDICT_INTERVAL_MS) {
        return;
    }

    lastPredictTime = now;

    try {
        const res = await fetch(AI_API_BASE + "/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                history: []
            })
        });

        const json = await res.json();

        if (!json.ok) {
            el("aiPrediction").innerText = "Đang chờ";
            el("aiDecision").innerText = "Khuyến nghị: chưa đủ dữ liệu";
            return;
        }

        el("aiPrediction").innerText = json.prediction;
        updateAiIcon(json.prediction);

        lastAiCommand = json.command;

        const rainPercent = Number(json.rain_probability || 0) * 100;
        const commandText = json.command === "OPEN" ? "MỞ" : "ĐÓNG";

        el("aiDecision").innerText =
            "Khuyến nghị: " + commandText +
            " | Khả năng mưa: " + rainPercent.toFixed(1) + "%";

    } catch (err) {
        console.error("Predict API error:", err);
        el("aiDecision").innerText = "Khuyến nghị: lỗi dự báo";
    }
}

async function loadForecast(force = false) {
    const now = Date.now();

    if (!force && now - lastForecastTime < FORECAST_INTERVAL_MS) {
        return;
    }

    lastForecastTime = now;

    try {
        const res = await fetch(AI_API_BASE + "/forecast?days=5");

        if (!res.ok) {
            el("currentWeather").innerText = "Chưa có dữ liệu";
            el("currentMore").innerText = "Kiểm tra API dự báo";
            return;
        }

        const json = await res.json();

        if (!json.ok) {
            el("currentWeather").innerText = "Không lấy được dự báo";
            el("currentMore").innerText = "API trả về lỗi";
            return;
        }

        el("forecastLocation").innerText = json.location || "Hanoi, Vietnam";

        const current = json.current || {};

        el("currentTemp").innerText =
            Number(current.temperature || 0).toFixed(0) + "°C";

        el("currentWeather").innerText =
            current.weather || "--";

        el("currentMore").innerText =
            "Độ ẩm: " + Number(current.humidity || 0).toFixed(0) + "% | " +
            "Áp suất: " + Number(current.pressure || 0).toFixed(1) + " hPa";

        el("currentIcon").className = iconClass(current.icon);

        const daily = json.daily || [];
        let forecastHtml = "";

        daily.slice(0, 5).forEach(function(day) {
            forecastHtml += ""
                + "<div class='day-item'>"
                + "<div class='day-name'>" + (day.day_name || "--") + "</div>"
                + "<div class='day-date'>" + (day.date || "--") + "</div>"
                + "<div class='day-icon'><i class='" + iconClass(day.icon) + "'></i></div>"
                + "<div class='day-temp'>"
                + Number(day.temp_max || 0).toFixed(0) + "° / "
                + Number(day.temp_min || 0).toFixed(0) + "°"
                + "</div>"
                + "<div class='day-rain'>Mưa: "
                + Number(day.rain_probability || 0).toFixed(0)
                + "%</div>"
                + "</div>";
        });

        if (forecastHtml === "") {
            forecastHtml = ""
                + "<div class='day-item'>"
                + "<div class='day-name'>--</div>"
                + "<div class='day-date'>--</div>"
                + "<div class='day-icon'><i class='wi wi-day-cloudy'></i></div>"
                + "<div class='day-temp'>-- / --</div>"
                + "<div class='day-rain'>Mưa: --</div>"
                + "</div>";
        }

        el("dailyForecast").innerHTML = forecastHtml;

    } catch (err) {
        console.error("Forecast API error:", err);
        el("currentWeather").innerText = "Lỗi dự báo";
        el("currentMore").innerText = "Không gọi được API dự báo";
    }
}

function setupButtons() {
    el("btnOpenRack").addEventListener("click", function() {
        publish(TOPIC_RACK, "OPEN", "MỞ DÀN PHƠI 90°");
        updateRackState("OPEN");
    });

    el("btnCloseRack").addEventListener("click", function() {
        publish(TOPIC_RACK, "CLOSE", "ĐÓNG DÀN PHƠI 0°");
        updateRackState("CLOSE");
    });

    el("btnOpenDoor").addEventListener("click", function() {
        publish(TOPIC_DOOR, "OPEN", "MỞ CỬA MG90S");
        updateDoorState("OPEN");
    });

    el("btnCloseDoor").addEventListener("click", function() {
        publish(TOPIC_DOOR, "CLOSE", "ĐÓNG CỬA MG90S");
        updateDoorState("CLOSE");
    });

    el("btnManual").addEventListener("click", function() {
        publish(TOPIC_MODE, "MANUAL", "CHUYỂN MANUAL");
        el("heroMode").innerText = "MANUAL";
    });

    el("btnAuto").addEventListener("click", function() {
        publish(TOPIC_MODE, "AUTO", "CHUYỂN AUTO");
        el("heroMode").innerText = "AUTO";
    });

    el("btnAiSend").addEventListener("click", async function() {
        publish(TOPIC_MODE, "AUTO", "CHUYỂN AUTO THEO DỰ BÁO");

        await callPredictApi(true);

        if (lastAiCommand === "OPEN") {
            publish(TOPIC_RACK, "OPEN", "DỰ BÁO GỬI OPEN");
            updateRackState("OPEN");
        } else {
            publish(TOPIC_RACK, "CLOSE", "DỰ BÁO GỬI CLOSE");
            updateRackState("CLOSE");
        }
    });
}

function connectMqtt() {
    setButtonsDisabled(true);

    const options = {
        username: MQTT_USERNAME,
        password: MQTT_PASSWORD,
        clean: true,
        protocolVersion: 4,
        connectTimeout: 5000,
        reconnectPeriod: 2000
    };

    mqttClient = mqtt.connect(MQTT_WS_URL, options);

    mqttClient.on("connect", function() {
        setBadge("MQTT online", "pill-ok");

        mqttClient.subscribe(TOPIC_SENSOR, {
            qos: 0
        });

        setButtonsDisabled(false);
    });

    mqttClient.on("reconnect", function() {
        setBadge("Đang kết nối lại", "pill-wait");
        setButtonsDisabled(true);
    });

    mqttClient.on("close", function() {
        setBadge("MQTT offline", "pill-error");
        setButtonsDisabled(true);
    });

    mqttClient.on("error", function(err) {
        setBadge("Lỗi MQTT", "pill-error");
        console.error(err);
    });

    mqttClient.on("message", async function(topic, message) {
        try {
            const text = message.toString();
            const data = JSON.parse(text);

            updateCards(data);
            await sendIngestToApi(data);
            await callPredictApi(false);
            await loadForecast(false);

        } catch (e) {
            console.error("Payload parse error:", e);
            el("rawPayload").innerText =
                "Payload parse error: " + e.message + "\\n" + message.toString();
        }
    });
}

setupButtons();
connectMqtt();
loadForecast(true);
callPredictApi(true);
</script>

</body>
</html>
""")


html_code = html_template.substitute(
    MQTT_WS_URL=json.dumps(MQTT_WS_URL),
    MQTT_USERNAME=json.dumps(MQTT_USERNAME),
    MQTT_PASSWORD=json.dumps(MQTT_PASSWORD),
    TOPIC_SENSOR=json.dumps(MQTT_TOPIC_SENSOR_DATA),
    TOPIC_RACK=json.dumps(MQTT_TOPIC_CONTROL_RACK),
    TOPIC_DOOR=json.dumps(MQTT_TOPIC_CONTROL_DOOR),
    TOPIC_MODE=json.dumps(MQTT_TOPIC_CONTROL_MODE),
    AI_API_BASE=json.dumps(AI_API_BASE),
)

html(html_code, height=3000, scrolling=True)
