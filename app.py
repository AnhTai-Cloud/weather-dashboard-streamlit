import json
from string import Template

import streamlit as st
from streamlit.components.v1 import html


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="IoT Smart Clothesline Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================
# MQTT WEBSOCKET CONFIG
# =========================
# Chỉ nhập HOST, không nhập wss:// và không nhập :8884
MQTT_BROKER_HOST = "70c5a54b752643dd817d84ea128f899d.s1.eu.hivemq.cloud:8884/mqtt"

MQTT_WS_PORT = 8884
MQTT_WS_PATH = "/mqtt"

MQTT_USERNAME = "ESP32-client"
MQTT_PASSWORD = "Tan01052005!"

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

        body {
            margin: 0;
            background: #eef0f3;
            color: #2f3341;
        }

        .page {
            max-width: 1320px;
            margin: 0 auto;
            padding: 18px 18px 34px 18px;
        }

        .topbar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 16px;
        }

        .title {
            font-size: 30px;
            font-weight: 850;
            line-height: 1.25;
            text-transform: uppercase;
        }

        .subtitle {
            color: #74777f;
            font-size: 14px;
            margin-top: 5px;
        }

        .mqtt-status {
            min-width: 250px;
            text-align: right;
        }

        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 8px 13px;
            font-weight: 800;
            font-size: 13px;
            color: white;
        }

        .badge-wait {
            background: #f5a623;
        }

        .badge-ok {
            background: #43b36a;
        }

        .badge-error {
            background: #e74c3c;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 16px;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
            margin-bottom: 16px;
        }

        .card {
            background: #f3eee8;
            border-radius: 24px;
            padding: 18px 20px;
            min-height: 160px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.05);
        }

        .card-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title {
            font-size: 15px;
            font-weight: 850;
            text-transform: uppercase;
        }

        .icon-box {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: rgba(255,255,255,0.85);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .icon-box i {
            font-size: 25px;
        }

        .value {
            font-size: 30px;
            font-weight: 850;
            margin-top: 14px;
            word-break: break-word;
        }

        .desc {
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
            transition: width 0.25s ease, background 0.25s ease;
        }

        .section-title {
            font-size: 23px;
            font-weight: 850;
            text-transform: uppercase;
            margin: 24px 0 14px 0;
            color: #2f3341;
        }

        .control-card {
            background: #f3eee8;
            border-radius: 24px;
            padding: 18px 20px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.05);
            margin-bottom: 16px;
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
            font-weight: 850;
            cursor: pointer;
            color: white;
            transition: transform 0.12s ease, opacity 0.12s ease;
        }

        button:hover {
            transform: translateY(-1px);
            opacity: 0.92;
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
            border-radius: 16px;
            padding: 12px 14px;
            font-size: 14px;
            font-weight: 750;
            margin-top: 12px;
        }

        .chart-card {
            background: #f3eee8;
            border-radius: 28px;
            padding: 20px 20px 10px 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.055);
            margin-bottom: 16px;
        }

        .raw-box {
            background: #20242c;
            color: #dbe6ff;
            border-radius: 18px;
            padding: 14px;
            overflow: auto;
            max-height: 260px;
            font-size: 13px;
            white-space: pre-wrap;
        }

        .small-note {
            color: #74777f;
            font-size: 13px;
            line-height: 1.5;
        }

        @media (max-width: 1050px) {
            .grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .button-row {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 650px) {
            .grid, .grid-2, .button-row, .button-row-2 {
                grid-template-columns: 1fr;
            }

            .topbar {
                flex-direction: column;
            }

            .mqtt-status {
                text-align: left;
            }
        }
    </style>
</head>

<body>
<div class="page">

    <div class="topbar">
        <div>
            <div class="title">IOT WEATHER DASHBOARD - HỆ THỐNG PHƠI ĐỒ THÔNG MINH</div>
            <div class="subtitle">
                Dữ liệu cập nhật trực tiếp bằng MQTT WebSocket, không refresh Streamlit.
                <br>
                Cập nhật cuối: <span id="lastUpdate">--</span>
            </div>
        </div>

        <div class="mqtt-status">
            <div id="mqttBadge" class="badge badge-wait">ĐANG KẾT NỐI MQTT...</div>
            <div class="subtitle" id="mqttDetail">Broker: --</div>
        </div>
    </div>

    <div class="section-title">Dữ liệu cảm biến realtime</div>

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
                <div class="card-title">AI dự đoán</div>
                <div class="icon-box"><i class="wi wi-day-cloudy" id="aiIcon" style="color:#f5a623;"></i></div>
            </div>
            <div class="value" id="aiPrediction">--</div>
            <div class="desc">Nắng / Âm u / Mưa</div>
            <div class="progress-wrap"><div id="aiBar" class="progress-fill" style="width:80%; background:#f5a623;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Chế độ ESP</div>
                <div class="icon-box"><i class="wi wi-time-3" style="color:#9a7dff;"></i></div>
            </div>
            <div class="value" id="mode">--</div>
            <div class="desc">Period: <span id="period">--</span></div>
            <div class="progress-wrap"><div id="modeBar" class="progress-fill" style="width:80%; background:#9a7dff;"></div></div>
        </div>
    </div>

    <div class="section-title">Trạng thái thiết bị</div>

    <div class="grid-2">
        <div class="card">
            <div class="card-head">
                <div class="card-title">Trạng thái dàn phơi</div>
                <div class="icon-box"><i class="wi wi-day-sunny" id="rackIcon" style="color:#e74c3c;"></i></div>
            </div>
            <div class="value" id="rackState">ĐANG ĐÓNG</div>
            <div class="desc">ESP rack_state: <span id="rackRaw">--</span></div>
            <div class="progress-wrap"><div id="rackBar" class="progress-fill" style="width:100%; background:#e74c3c;"></div></div>
        </div>

        <div class="card">
            <div class="card-head">
                <div class="card-title">Trạng thái cửa</div>
                <div class="icon-box"><i class="wi wi-direction-down" id="doorIcon" style="color:#e74c3c;"></i></div>
            </div>
            <div class="value" id="doorState">ĐANG ĐÓNG</div>
            <div class="desc">ESP door_state: <span id="doorRaw">--</span></div>
            <div class="progress-wrap"><div id="doorBar" class="progress-fill" style="width:100%; background:#e74c3c;"></div></div>
        </div>
    </div>

    <div class="section-title">Điều khiển MQTT</div>

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
            <button class="btn-ai" id="btnAiSend">GỬI LỆNH THEO AI</button>
            <button class="btn-close" id="btnCloseDoor">ĐÓNG CỬA MG90S</button>
        </div>

        <div class="info-line" id="lastCommand">Lệnh gần nhất: Chưa có lệnh</div>
        <div class="info-line" id="aiDecision">AI đề xuất: --</div>
    </div>

    <div class="section-title">Biểu đồ nhiệt độ realtime</div>

    <div class="chart-card">
        <canvas id="tempChart" height="110"></canvas>
    </div>

    <div class="section-title">Payload MQTT mới nhất</div>
    <pre class="raw-box" id="rawPayload">Chưa có payload...</pre>

    <div class="small-note">
        Nếu dashboard không nhận dữ liệu, kiểm tra ESP đã publish retained lên
        <b>smart_home/sensor/data</b> chưa. Nếu nút điều khiển không chạy, kiểm tra ESP đã subscribe
        <b>smart_home/control/rack</b>, <b>smart_home/control/door</b>, <b>smart_home/control/mode</b> chưa.
    </div>

</div>

<script>
const MQTT_WS_URL = $MQTT_WS_URL;
const MQTT_USERNAME = $MQTT_USERNAME;
const MQTT_PASSWORD = $MQTT_PASSWORD;

const TOPIC_SENSOR = $TOPIC_SENSOR;
const TOPIC_RACK = $TOPIC_RACK;
const TOPIC_DOOR = $TOPIC_DOOR;
const TOPIC_MODE = $TOPIC_MODE;

let mqttClient = null;
let latestData = null;
let lastAiCommand = "CLOSE";

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
    badge.className = "badge " + cls;
    badge.innerText = text;
}

function setProgress(id, percent, color) {
    const bar = el(id);
    bar.style.width = clampJs(percent, 0, 100) + "%";
    if (color) {
        bar.style.background = color;
    }
}

function weatherLabel(data) {
    const rainState = String(data.rain_state || "NO_RAIN").toUpperCase();
    const light = Number(data.light_lux || data.light || 0);

    if (rainState === "RAIN" || rainState === "RAINING") {
        return "Mưa";
    }

    if (light < 300) {
        return "Âm u";
    }

    return "Nắng";
}

function updateAiIcon(label) {
    const icon = el("aiIcon");

    if (label === "Mưa") {
        icon.className = "wi wi-rain";
        icon.style.color = "#5b83ff";
        setProgress("aiBar", 85, "#5b83ff");
    } else if (label === "Âm u") {
        icon.className = "wi wi-cloudy";
        icon.style.color = "#f5a623";
        setProgress("aiBar", 70, "#f5a623");
    } else {
        icon.className = "wi wi-day-sunny";
        icon.style.color = "#f5a623";
        setProgress("aiBar", 90, "#f5a623");
    }
}

function decideAi(data) {
    const rainState = String(data.rain_state || "NO_RAIN").toUpperCase();
    const humidity = Number(data.humidity || 0);
    const light = Number(data.light_lux || data.light || 0);
    const label = weatherLabel(data);

    if (rainState === "RAIN" || rainState === "RAINING") {
        return {
            command: "CLOSE",
            reason: "Cảm biến mưa phát hiện có mưa"
        };
    }

    if (label === "Mưa") {
        return {
            command: "CLOSE",
            reason: "AI dự đoán trời mưa"
        };
    }

    if (label === "Âm u" && humidity >= 88 && light < 250) {
        return {
            command: "CLOSE",
            reason: "Trời âm u, độ ẩm cao, ánh sáng thấp"
        };
    }

    if (label === "Nắng" && rainState !== "RAIN") {
        return {
            command: "OPEN",
            reason: "Trời nắng, không phát hiện mưa"
        };
    }

    return {
        command: "CLOSE",
        reason: "Điều kiện chưa rõ, đưa dàn phơi về trạng thái an toàn"
    };
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

    if (rainState === "RAIN" || rainState === "RAINING") {
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

    el("mode").innerText = mode;
    el("period").innerText = period;

    if (mode === "AUTO") {
        setProgress("modeBar", 90, "#43b36a");
    } else if (mode === "MANUAL") {
        setProgress("modeBar", 70, "#f5a623");
    } else {
        setProgress("modeBar", 40, "#9a7dff");
    }
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

    const label = weatherLabel(data);
    el("aiPrediction").innerText = label;
    updateAiIcon(label);

    const ai = decideAi(data);
    lastAiCommand = ai.command;
    el("aiDecision").innerText = "AI đề xuất: " + ai.command + " | " + ai.reason;

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

    el("lastCommand").innerText = "Lệnh gần nhất: " + successText + " | Topic: " + topic + " | Message: " + message;
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
        el("mode").innerText = "MANUAL";
    });

    el("btnAuto").addEventListener("click", function() {
        publish(TOPIC_MODE, "AUTO", "CHUYỂN AUTO");
        el("mode").innerText = "AUTO";
    });

    el("btnAiSend").addEventListener("click", function() {
        publish(TOPIC_MODE, "AUTO", "CHUYỂN AUTO THEO AI");

        if (lastAiCommand === "OPEN") {
            publish(TOPIC_RACK, "OPEN", "AI GỬI OPEN");
            updateRackState("OPEN");
        } else {
            publish(TOPIC_RACK, "CLOSE", "AI GỬI CLOSE");
            updateRackState("CLOSE");
        }
    });
}

function connectMqtt() {
    setButtonsDisabled(true);

    el("mqttDetail").innerText = "Broker: " + MQTT_WS_URL;

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
        setBadge("ĐÃ KẾT NỐI MQTT WEBSOCKET", "badge-ok");
        el("mqttDetail").innerText = "Đã subscribe: " + TOPIC_SENSOR;
        mqttClient.subscribe(TOPIC_SENSOR, {
            qos: 0
        });
        setButtonsDisabled(false);
    });

    mqttClient.on("reconnect", function() {
        setBadge("ĐANG KẾT NỐI LẠI...", "badge-wait");
        setButtonsDisabled(true);
    });

    mqttClient.on("close", function() {
        setBadge("MẤT KẾT NỐI MQTT", "badge-error");
        setButtonsDisabled(true);
    });

    mqttClient.on("error", function(err) {
        setBadge("LỖI MQTT", "badge-error");
        el("mqttDetail").innerText = "Lỗi: " + err.message;
        console.error(err);
    });

    mqttClient.on("message", function(topic, message) {
        try {
            const text = message.toString();
            const data = JSON.parse(text);
            updateCards(data);
        } catch (e) {
            console.error("Payload parse error:", e);
            el("rawPayload").innerText = "Payload parse error: " + e.message + "\\n" + message.toString();
        }
    });
}

setupButtons();
connectMqtt();
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
)

html(html_code, height=1200, scrolling=True)
