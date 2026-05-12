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


# =========================
# CSS GIAO DIỆN + WEATHER ICONS
# =========================
st.markdown("""
<style>
@import url("https://cdnjs.cloudflare.com/ajax/libs/weather-icons/2.0.12/css/weather-icons.min.css");

.stApp {
    background: linear-gradient(135deg, #f6f8fc 0%, #eef2f7 100%);
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

.weather-card {
    background: linear-gradient(135deg, #fffaf2 0%, #f4f1ec 100%);
    padding: 28px;
    border-radius: 28px;
    box-shadow: 0px 10px 28px rgba(0,0,0,0.07);
    margin-bottom: 22px;
}

.weather-main-row {
    display: flex;
    align-items: center;
    gap: 32px;
}

.weather-icon-main {
    font-size: 105px;
    color: #f6a623;
    min-width: 135px;
    text-align: center;
}

.big-temp {
    font-size: 72px;
    font-weight: 800;
    line-height: 1;
}

.weather-title {
    font-size: 25px;
    font-weight: 800;
}

.weather-sub {
    color: #666;
    font-size: 15px;
}

.status-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background-color: #ffffff;
    padding: 9px 13px;
    border-radius: 999px;
    font-size: 14px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.04);
}

.status-badge i {
    color: #f6a623;
    font-size: 18px;
}

.metric-card {
    background: linear-gradient(135deg, #fffaf2 0%, #f4f1ec 100%);
    padding: 20px;
    border-radius: 24px;
    box-shadow: 0px 8px 22px rgba(0,0,0,0.055);
    min-height: 165px;
    margin-bottom: 16px;
}

.metric-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.metric-title {
    font-size: 17px;
    font-weight: 700;
    color: #222;
}

.metric-icon {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0px 0px 0px 1px rgba(0,0,0,0.03);
}

.metric-icon i {
    font-size: 28px;
    color: #f6a623;
}

.metric-value {
    font-size: 34px;
    font-weight: 800;
    margin-top: 12px;
}

.metric-desc {
    color: #666;
    font-size: 14px;
    margin-top: 6px;
}

.progress-wrap {
    width: 100%;
    height: 8px;
    background: #e6e1da;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 14px;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #f6a623, #ffcf70);
    border-radius: 999px;
}

.day-card {
    text-align: center;
    background: linear-gradient(135deg, #fffaf2 0%, #f4f1ec 100%);
    border-radius: 20px;
    padding: 16px 10px;
    margin: 4px;
    min-height: 165px;
    box-shadow: 0px 6px 16px rgba(0,0,0,0.045);
}

.weather-icon-day {
    font-size: 42px;
    color: #f6a623;
    margin: 13px 0;
}

.hour-card {
    text-align: center;
    background: #ffffff;
    border-radius: 18px;
    padding: 13px 8px;
    box-shadow: 0px 5px 14px rgba(0,0,0,0.04);
    min-height: 128px;
}

.hour-icon {
    font-size: 31px;
    color: #f6a623;
    margin: 10px 0;
}

.section-title {
    font-size: 25px;
    font-weight: 800;
    margin: 26px 0 14px 0;
}
</style>
""", unsafe_allow_html=True)


# =========================
# MAP WEATHER CODE
# =========================
def weather_code_to_text(code):
    codes = {
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

    return codes.get(int(code), ("Unknown", "wi wi-na"))


def fahrenheit(c):
    return c * 9 / 5 + 32


def wind_direction_text(deg):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(deg / 45) % 8
    return directions[index]


def clamp(value, min_value=0, max_value=100):
    return max(min_value, min(value, max_value))


def metric_card(title, value, desc, icon_class, percent=50):
    percent = clamp(percent)

    return f"""
    <div class="metric-card">
        <div class="metric-top">
            <div class="metric-title">{title}</div>
            <div class="metric-icon">
                <i class="{icon_class}"></i>
            </div>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-desc">{desc}</div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{percent}%;"></div>
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
# LOAD DATA
# =========================
try:
    data = get_weather(lat, lon)
except Exception as e:
    st.error(f"Không lấy được dữ liệu thời tiết: {e}")
    st.stop()

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
next_12h = hourly.head(12)


# =========================
# HEADER
# =========================
st.markdown(f"## Weather Dashboard - {display_city}")
st.caption(f"Cập nhật theo API: {current['time']} | Tọa độ: {lat}, {lon}")


# =========================
# MAIN LAYOUT
# =========================
left, right = st.columns([1.35, 1])

with left:
    st.markdown(f"""
    <div class="weather-card">
        <div class="weather-title">{display_city}, Vietnam</div>
        <div class="weather-sub">Current weather</div>

        <div class="weather-main-row">
            <div class="weather-icon-main">
                <i class="{weather_icon}"></i>
            </div>

            <div>
                <div class="big-temp">{temp_now:.0f}{unit}</div>
                <div class="weather-title">{weather_text}</div>
                <div class="weather-sub">Feels like {feels:.0f}{unit}</div>

                <div class="status-row">
                    <div class="status-badge">
                        <i class="wi wi-humidity"></i>
                        Humidity {current["relative_humidity_2m"]}%
                    </div>

                    <div class="status-badge">
                        <i class="wi wi-strong-wind"></i>
                        Wind {current["wind_speed_10m"]:.0f} km/h
                    </div>

                    <div class="status-badge">
                        <i class="wi wi-raindrop"></i>
                        Rain {current["rain"]:.1f} mm
                    </div>

                    <div class="status-badge">
                        <i class="wi wi-cloudy"></i>
                        Cloud {current["cloud_cover"]}%
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Dự báo 12 giờ tới</div>', unsafe_allow_html=True)

    hour_cols = st.columns(6)
    for i, row in next_12h.iloc[:6].iterrows():
        text, icon = weather_code_to_text(row["weather_code"])
        hour_label = row["time"].strftime("%H:%M")

        with hour_cols[i]:
            st.markdown(f"""
            <div class="hour-card">
                <div style="font-weight:700;">{hour_label}</div>
                <div class="hour-icon"><i class="{icon}"></i></div>
                <div style="font-weight:700;">{row["temperature_2m_show"]:.0f}{unit}</div>
                <div style="font-size:13px;color:#666;">Rain {row["precipitation_probability"]:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

    hour_cols_2 = st.columns(6)
    for j, row in enumerate(next_12h.iloc[6:12].itertuples()):
        text, icon = weather_code_to_text(row.weather_code)
        hour_label = row.time.strftime("%H:%M")

        with hour_cols_2[j]:
            st.markdown(f"""
            <div class="hour-card">
                <div style="font-weight:700;">{hour_label}</div>
                <div class="hour-icon"><i class="{icon}"></i></div>
                <div style="font-weight:700;">{row.temperature_2m_show:.0f}{unit}</div>
                <div style="font-size:13px;color:#666;">Rain {row.precipitation_probability:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Dự báo 7 ngày</div>', unsafe_allow_html=True)

    day_cols = st.columns(7)

    for i, row in daily.iterrows():
        text, icon = weather_code_to_text(row["weather_code"])
        date_label = row["time"].strftime("%a")
        day_label = row["time"].strftime("%d")

        with day_cols[i]:
            st.markdown(f"""
            <div class="day-card">
                <div style="font-weight:800;">{date_label}</div>
                <div style="font-size:14px;color:#666;">{day_label}</div>
                <div class="weather-icon-day">
                    <i class="{icon}"></i>
                </div>
                <div style="font-weight:700;">{row["temperature_2m_max_show"]:.0f}{unit}</div>
                <div style="color:#555;">/ {row["temperature_2m_min_show"]:.0f}{unit}</div>
                <div style="font-size:13px;color:#666;margin-top:6px;">
                    <i class="wi wi-raindrop"></i> {row["precipitation_probability_max"]:.0f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Biểu đồ nhiệt độ 24 giờ tới</div>', unsafe_allow_html=True)

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
    visibility_km = hourly["visibility"].iloc[0] / 1000
    wind_dir = wind_direction_text(current["wind_direction_10m"])
    humidity = current["relative_humidity_2m"]
    cloud = current["cloud_cover"]
    uv = hourly["uv_index"].iloc[0]
    wind_speed = current["wind_speed_10m"]
    pressure = current["pressure_msl"]

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            metric_card(
                "Visibility",
                f"{visibility_km:.1f} km",
                "Tầm nhìn hiện tại",
                "wi wi-fog",
                percent=clamp(visibility_km * 8)
            ),
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            metric_card(
                "Wind",
                f"{wind_speed:.0f} km/h",
                f"Hướng {wind_dir} - Gust {current['wind_gusts_10m']:.0f} km/h",
                "wi wi-strong-wind",
                percent=clamp(wind_speed * 3)
            ),
            unsafe_allow_html=True
        )

    c3, c4 = st.columns(2)

    with c3:
        st.markdown(
            metric_card(
                "Pressure",
                f"{pressure:.0f} hPa",
                "Áp suất mực nước biển",
                "wi wi-barometer",
                percent=clamp((pressure - 950) / 100 * 100)
            ),
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            metric_card(
                "Humidity",
                f"{humidity}%",
                "Độ ẩm không khí",
                "wi wi-humidity",
                percent=humidity
            ),
            unsafe_allow_html=True
        )

    c5, c6 = st.columns(2)

    with c5:
        st.markdown(
            metric_card(
                "UV Index",
                f"{uv:.1f}",
                "Chỉ số UV theo giờ",
                "wi wi-hot",
                percent=clamp(uv / 12 * 100)
            ),
            unsafe_allow_html=True
        )

    with c6:
        st.markdown(
            metric_card(
                "Cloud Cover",
                f"{cloud}%",
                "Mức độ mây che phủ",
                "wi wi-cloudy",
                percent=cloud
            ),
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title">Xác suất mưa 24 giờ tới</div>', unsafe_allow_html=True)

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
# RAW DATA
# =========================
with st.expander("Xem dữ liệu hourly raw"):
    st.dataframe(hourly.head(48), use_container_width=True)

with st.expander("Xem dữ liệu current raw"):
    st.json(current)
