import streamlit as st
import requests
import pandas as pd
import plotly.express as px


# =========================
# CẤU HÌNH TRANG
# =========================
st.set_page_config(
    page_title="Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dòng test để biết app đã render
st.write("✅ App đã chạy")


# =========================
# CSS GIAO DIỆN
# =========================
st.markdown("""
<style>
.stApp {
    background-color: #f5f6fa;
}

.weather-card {
    background-color: #f4f1ec;
    padding: 22px;
    border-radius: 22px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.06);
    margin-bottom: 15px;
}

.small-card {
    background-color: #f4f1ec;
    padding: 20px;
    border-radius: 20px;
    box-shadow: 0px 4px 16px rgba(0,0,0,0.05);
    height: 150px;
    margin-bottom: 15px;
}

.big-temp {
    font-size: 70px;
    font-weight: 700;
    line-height: 1;
}

.weather-title {
    font-size: 24px;
    font-weight: 700;
}

.weather-sub {
    color: #666;
    font-size: 15px;
}

.metric-title {
    font-size: 17px;
    font-weight: 600;
    color: #333;
}

.metric-value {
    font-size: 32px;
    font-weight: 700;
    margin-top: 8px;
}

.metric-desc {
    color: #666;
    font-size: 14px;
}

.day-card {
    text-align: center;
    background-color: #f4f1ec;
    border-radius: 18px;
    padding: 14px;
    margin: 5px;
    min-height: 145px;
}

.status-badge {
    display: inline-block;
    background-color: #ffffff;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 14px;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HÀM ĐỔI WEATHER CODE
# =========================
def weather_code_to_text(code):
    codes = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Fog", "🌫️"),
        48: ("Rime fog", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Moderate drizzle", "🌦️"),
        55: ("Dense drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "⛈️"),
        71: ("Slight snow", "🌨️"),
        73: ("Moderate snow", "🌨️"),
        75: ("Heavy snow", "❄️"),
        80: ("Rain showers", "🌦️"),
        81: ("Rain showers", "🌧️"),
        82: ("Violent rain showers", "⛈️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with hail", "⛈️"),
        99: ("Thunderstorm with hail", "⛈️")
    }
    return codes.get(int(code), ("Unknown", "❓"))


def fahrenheit(c):
    return c * 9 / 5 + 32


def wind_direction_text(deg):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(deg / 45) % 8
    return directions[index]


# =========================
# LẤY DỮ LIỆU API
# =========================
@st.cache_data(ttl=1800)
def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,

        # SỬA Ở ĐÂY: dùng chuỗi, không dùng list
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
            "uv_index"
        ]),

        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "uv_index_max"
        ]),

        "timezone": "Asia/Bangkok",
        "forecast_days": 7
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


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
# GỌI API
# =========================
try:
    data = get_weather(lat, lon)
except Exception as e:
    st.error(f"Không lấy được dữ liệu thời tiết: {e}")
    st.stop()


# =========================
# XỬ LÝ DỮ LIỆU
# =========================
try:
    current = data["current"]
    hourly = pd.DataFrame(data["hourly"])
    daily = pd.DataFrame(data["daily"])
except Exception as e:
    st.error(f"Lỗi cấu trúc dữ liệu API: {e}")
    st.json(data)
    st.stop()

hourly["time"] = pd.to_datetime(hourly["time"])
daily["time"] = pd.to_datetime(daily["time"])

temp_now_c = current["temperature_2m"]
feels_c = current["apparent_temperature"]

if unit == "°F":
    temp_now = fahrenheit(temp_now_c)
    feels = fahrenheit(feels_c)

    daily["temperature_2m_max_show"] = daily["temperature_2m_max"].apply(fahrenheit)
    daily["temperature_2m_min_show"] = daily["temperature_2m_min"].apply(fahrenheit)
    hourly["temperature_2m_show"] = hourly["temperature_2m"].apply(fahrenheit)
else:
    temp_now = temp_now_c
    feels = feels_c

    daily["temperature_2m_max_show"] = daily["temperature_2m_max"]
    daily["temperature_2m_min_show"] = daily["temperature_2m_min"]
    hourly["temperature_2m_show"] = hourly["temperature_2m"]

weather_text, weather_icon = weather_code_to_text(current["weather_code"])

next_24h = hourly.head(24)


# =========================
# HEADER
# =========================
st.markdown(f"## 🌤️ Weather Dashboard - {display_city}")
st.caption(f"Cập nhật theo API: {current['time']} | Tọa độ: {lat}, {lon}")


# =========================
# LAYOUT CHÍNH
# =========================
left, right = st.columns([1.35, 1])

with left:
    st.markdown(f"""
    <div class="weather-card">
        <div class="weather-title">{display_city}, Vietnam</div>
        <div class="weather-sub">Current weather</div>
        <br>
        <div style="display:flex; align-items:center; gap:24px;">
            <div style="font-size:78px;">{weather_icon}</div>
            <div>
                <div class="big-temp">{temp_now:.0f}{unit}</div>
                <div class="weather-title">{weather_text}</div>
                <div class="weather-sub">Feels like {feels:.0f}{unit}</div>
                <span class="status-badge">Humidity {current["relative_humidity_2m"]}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Dự báo 7 ngày")

    day_cols = st.columns(7)

    for i, row in daily.iterrows():
        text, icon = weather_code_to_text(row["weather_code"])
        date_label = row["time"].strftime("%a %d")

        with day_cols[i]:
            st.markdown(f"""
            <div class="day-card">
                <div style="font-weight:700;">{date_label}</div>
                <div style="font-size:34px;">{icon}</div>
                <div>{row["temperature_2m_max_show"]:.0f}{unit} / {row["temperature_2m_min_show"]:.0f}{unit}</div>
                <div style="font-size:13px;color:#666;">Rain {row["precipitation_probability_max"]:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### Biểu đồ nhiệt độ 24 giờ tới")

    fig_temp = px.line(
        next_24h,
        x="time",
        y="temperature_2m_show",
        markers=True,
        labels={
            "time": "Thời gian",
            "temperature_2m_show": f"Nhiệt độ {unit}"
        }
    )

    fig_temp.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig_temp, use_container_width=True)


with right:
    c1, c2 = st.columns(2)

    with c1:
        visibility_km = hourly["visibility"].iloc[0] / 1000

        st.markdown(f"""
        <div class="small-card">
            <div class="metric-title">Visibility</div>
            <div class="metric-value">{visibility_km:.1f} km</div>
            <div class="metric-desc">Tầm nhìn hiện tại</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        wind_dir = wind_direction_text(current["wind_direction_10m"])

        st.markdown(f"""
        <div class="small-card">
            <div class="metric-title">Wind</div>
            <div class="metric-value">{current["wind_speed_10m"]:.0f} km/h</div>
            <div class="metric-desc">
                Hướng {wind_dir} - Gust {current["wind_gusts_10m"]:.0f} km/h
            </div>
        </div>
        """, unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown(f"""
        <div class="small-card">
            <div class="metric-title">Pressure</div>
            <div class="metric-value">{current["pressure_msl"]:.0f} hPa</div>
            <div class="metric-desc">Áp suất mực nước biển</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="small-card">
            <div class="metric-title">Humidity</div>
            <div class="metric-value">{current["relative_humidity_2m"]}%</div>
            <div class="metric-desc">Độ ẩm không khí</div>
        </div>
        """, unsafe_allow_html=True)

    c5, c6 = st.columns(2)

    with c5:
        st.markdown(f"""
        <div class="small-card">
            <div class="metric-title">UV Index</div>
            <div class="metric-value">{hourly["uv_index"].iloc[0]:.1f}</div>
            <div class="metric-desc">Chỉ số UV theo giờ</div>
        </div>
        """, unsafe_allow_html=True)

    with c6:
        st.markdown(f"""
        <div class="small-card">
            <div class="metric-title">Cloud Cover</div>
            <div class="metric-value">{current["cloud_cover"]}%</div>
            <div class="metric-desc">Mức độ mây che phủ</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Xác suất mưa 24 giờ tới")

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
        height=310,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig_rain, use_container_width=True)


# =========================
# BẢNG DỮ LIỆU
# =========================
with st.expander("Xem dữ liệu hourly raw"):
    st.dataframe(hourly.head(48), use_container_width=True)

with st.expander("Xem dữ liệu current raw"):
    st.json(current)
