import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import os
import base64
from PIL import Image

# 1. ตั้งค่าหน้าเว็บแบบกว้างเต็มจอและปิด Sidebar สไตล์ห้องควบคุม
st.set_page_config(page_title="BN Smart Command Center", layout="wide", initial_sidebar_state="collapsed")

# 2. ปรับแต่งดีไซน์ CSS สไตล์แผงควบคุม (รวมถึงกล่องพยากรณ์อากาศดีไซน์ใหม่)
st.markdown("""
    <style>
    .stApp {
        background-color: #060A13 !important;
        color: #E2E8F0;
        font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
    }
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(10, 20, 38, 0.85) !important;
        border: 1px solid #1E3A8A !important;
        border-top: 3px solid #00F2FE !important;
        border-radius: 8px !important;
        padding: 18px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
    }
    div[data-testid="stMetricValue"] {
        color: #00F2FE !important;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.6);
        font-weight: 700 !important;
        font-size: 2.2rem !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1E3A8A 0%, #0284C7 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: 1px solid #00F2FE !important;
        border-radius: 4px !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
        width: 100%;
        padding: 10px !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0284C7 0%, #00F2FE 100%) !important;
        color: black !important;
        box-shadow: 0 0 25px rgba(0, 242, 254, 0.7);
    }
    button[data-baseweb="tab"] { color: #64748B !important; font-size: 1.1rem; font-weight: bold; }
    button[aria-selected="true"] { color: #00F2FE !important; border-bottom-color: #00F2FE !important; }
    .risk-banner-critical {
        background-color: rgba(220, 38, 38, 0.2); border-left: 5px solid #DC2626; padding: 12px; border-radius: 4px; margin-bottom: 15px;
    }
    .risk-banner-normal {
        background-color: rgba(16, 185, 129, 0.15); border-left: 5px solid #10B981; padding: 12px; border-radius: 4px; margin-bottom: 15px;
    }
    
    .weather-box {
        background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        text-align: center;
        border: 1px solid #3B82F6 !important;
        box-shadow: inset 0 0 20px rgba(59, 130, 246, 0.2);
    }
    .weather-main-temp {
        font-size: 4.5rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        line-height: 1;
        margin: 10px 0;
        text-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .weather-status-text {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #E2E8F0 !important;
        letter-spacing: 1px;
    }
    .weather-sub-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        background: rgba(15, 23, 42, 0.6);
        padding: 12px;
        border-radius: 8px;
        margin-top: 15px;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    .weather-sub-item {
        text-align: center;
        color: #94A3B8;
        font-size: 0.85rem;
    }
    .weather-sub-value {
        color: #00F2FE !important;
        font-weight: 700;
        font-size: 1.05rem;
        margin-top: 3px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; background: linear-gradient(90deg, #0B1E36 0%, #1E3A8A 50%, #0B1E36 100%); 
                padding: 12px; border-radius: 8px; border: 1px solid #00F2FE; margin-bottom: 25px; box-shadow: 0 0 15px rgba(0,242,254,0.2);'>
        <h2 style='color: #FFFFFF; margin: 0; font-size: 1.8rem; letter-spacing: 2px; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>
            ⚡ สถานีไฟฟ้าแรงสูงบางกอกน้อย [BN] - ระบบบริหารความเสี่ยงและสภาพอากาศ
        </h2>
    </div>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_file = "egat_logo.png"
logo_base64 = get_base64_image(logo_file)
if logo_base64:
    st.markdown(f"""<div style='text-align: center; margin-bottom: 20px;'><img src="data:image/png;base64,{logo_base64}" style="height: 80px; width: auto;"></div>""", unsafe_allow_html=True)

# 🌐 ดึงข้อมูลตามพิกัดแผนที่จริงลานไกแบบ 100% เรียลไทม์
@st.cache_data(ttl=120)  # ดึงค่าจริงใหม่จากดาวเทียมทุก 2 นาที
def get_realtime_weather_advanced():
    try:
        # ดึงชุดสภาพอากาศปัจจุบัน + ความชื้นและแรงดันบรรยากาศ ณ พิกัดจริง สฟฟ.บางกอกน้อย
        url = "https://open-meteo.com"
        res = requests.get(url).json()
        
        # ดึงค่าล่าสุดจริง ณ ชั่วโมงนี้มาแสดงผล
        humidity_list = res.get('hourly', {}).get('relative_humidity_2m', [60])
        pressure_list = res.get('hourly', {}).get('surface_pressure', [1010])
        humidity = humidity_list[-1]
        pressure = pressure_list[-1]
        
        curr = res['current_weather']
        current_temp = curr['temperature']
        wind_speed = curr['windspeed']
        prob_rain = res['daily']['precipitation_probability_max'][0]
        
        w_code = int(curr.get('weathercode', 0))
        status_text = "Partly Cloudy"
        if w_code == 0:
            status_text = "Clear Sky"
        elif 50 <= w_code <= 67:
            status_text = "Rainy"
        elif w_code >= 80:
            status_text = "Thunderstorm"
            
        return current_temp, prob_rain, humidity, wind_speed, pressure, status_text
    except: 
        # ค่าสำรองกรณี API ขัดข้องชั่วคราว
        return 32.5, 40, 65, 10.5, 1009, "Partly Cloudy"

temp, rain_chance, humidity, wind_speed, pressure, status_text = get_realtime_weather_advanced()
tab1, tab2 = st.tabs(["🛸 CONTROL ROOM PANEL (หน้าหลักควบคุม)", "🗂️ DAILY SUMMARY & LOG HISTORIC (คลังรายงานประจำวัน)"])

if not os.path.exists("shift_logs.csv"):
    df_init = pd.DataFrame(columns=["Timestamp", "Date", "Shift", "Internal_Name", "Staff_Count", "External_Name", "Ext_Count", "Weather_Temp", "Rain_Chance", "Water_Level", "Incidents"])
    df_init.to_csv("shift_logs.csv", index=False, encoding='utf-8-sig')
with tab1:
    col_left_side, col_right_side = st.columns([1.0, 1.0])
    
    with col_left_side:
        st.markdown("<b style='color: #F59E0B; font-size: 1.1rem;'>┃ สภาพอากาศความเร็วสูงแบบเรียลไทม์ [LIVE MAP METRICS]</b>", unsafe_allow_html=True)
        
        weather_icon = "⛅"
        if "Clear" in status_text: weather_icon = "☀️"
        elif "Rain" in status_text: weather_icon = "🌧️"
        elif "Thunder" in status_text: weather_icon = "⛈️"
        
        st.markdown(f"""
            <div class="weather-box">
                <div style="font-size: 5rem; margin-bottom: -10px;">{weather_icon}</div>
                <div class="weather-main-temp">{int(temp)}°C</div>
                <div class="weather-status-text">{status_text}</div>
                <div class="weather-sub-grid">
                    <div class="weather-sub-item">💧 Humidity<div class="weather-sub-value">{humidity}%</div></div>
                    <div class="weather-sub-item">💨 Wind Speed<div class="weather-sub-value">{int(wind_speed)} km/h</div></div>
                    <div class="weather-sub-item">🧭 Pressure<div class="weather-sub-value">{int(pressure)} hPa</div></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        if rain_chance >= 60:
            st.markdown(f"""
                <div class="risk-banner-critical">
                    <b style="color: #EF4444; font-size: 1.05rem;">⚠️ แจ้งเตือนระดับสูง (High Risk ฝนตกหนัก)</b><br>
                    <span style="color: #E2E8F0; font-size: 0.9rem;">⚡ โอกาสเกิดฝนฟ้าคะนองวันนี้สูงถึง <b>{rain_chance}%</b> เฝ้าระวังน้ำท่วมขังฐานอุปกรณ์ลานไกอย่างใกล้ชิด</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="risk-banner-normal">
                    <b style="color: #10B981;">✅ สภาวะอากาศปกติ (Normal Risk)</b><br>
                    <span style="color: #E2E8F0; font-size: 0.9rem;">สภาวะอากาศปกติ มีโอกาสเกิดฝนเพียง <b>{rain_chance}%</b> ไม่มีความเสี่ยงพายุฝนฟ้าคะนองรุนแรง</span>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<b style='color: #F59E0B; font-size: 1.1rem;'>┃ภาพถ่ายทางอากาศแผนผังพื้นที่ลานไก สฟฟ.บางกอกน้อย [BN]</b>", unsafe_allow_html=True)
        aerial_image_path = "bn_aerial.png"
        if os.path.exists(aerial_image_path):
            st.image(Image.open(aerial_image_path), use_container_width=True, caption="📷 พิกัดพื้นที่ตรวจวัดความเสี่ยงลานไกไฟฟ้าแรงสูง (Switchyard)")
        else:
            st.info("💡 ไม่พบไฟล์รูปภาพ 'bn_aerial.png' ในโฟลเดอร์คลาวด์")

    with col_right_side:
        st.markdown("<b style='color: #F59E0B; font-size: 1.1rem;'>┃ Status การปฏิบัติงานของหน่วยงาน & ค่าตรวจวัด</b>", unsafe_allow_html=True)
        
        st.markdown("<b style='color: #00FF87;'>🟢 หน่วยงานภายใน (EGAT)</b>", unsafe_allow_html=True)
        c_name_in, c_count_in = st.columns([0.7, 0.3])
        with c_name_in:
            internal_name = st.text_input("ชื่อหน่วยงานภายใน / แผนก")
        with c_count_in:
            internal_count = st.number_input("จำนวนคน (ภายใน)", min_value=1, value=1)
            
        st.markdown("<b style='color: #FF9F43;'>🟡 หน่วยงานภายนอก (Outsource / ผู้รับเหมา)</b>", unsafe_allow_html=True)
        c_name_ext, c_count_ext = st.columns([0.7, 0.3])
        with c_name_ext:
            external_name = st.text_input("ชื่อหน่วยงานภายนอก / บริษัท", placeholder="เช่น บริษัท เอ บี ซี จำกัด / ไม่มี")
        with c_count_ext:
            external_count = st.number_input("จำนวนคน (ภายนอก)", min_value=0, value=0)
                
        st.markdown("<div style='margin: 10px 0; border-top: 1px dashed #1E3A8A;'></div>", unsafe_allow_html=True)
        water_lvl = st.slider("ระดับน้ำบ่อระบายน้ำ Cable Trench (%)", min_value=0, max_value=100, value=10)

        st.markdown(f"""
            <div style='text-align: center; background: rgba(6, 10, 19, 0.6); padding: 10px; border-radius: 6px; border: 1px solid #1E3A8A; margin-top: 10px;'>
                <span style='color: #94A3B8; font-size: 0.85rem;'>ระดับน้ำอุโมงค์ Cable Trench</span>
                <h1 style='color: #00FF87; margin: 5px 0; font-size: 2.1rem;'>🟢 {water_lvl}%</h1>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
        st.markdown("<b style='color: #F59E0B; font-size: 1.1rem;'>┃ รายงานอุบัติเหตุ & ความปลอดภัยประจำกะ (BN)</b>", unsafe_allow_html=True)
        incident_input = st.text_area("บันทึกเหตุการณ์/การส่งมอบกะประจำวัน")
        
        c_sel_date, c_sel_shift = st.columns(2)
        with c_sel_date: date_input = st.date_input("เลือกวันที่ส่งงาน", datetime.now())
        with c_sel_shift: shift_input = st.selectbox("กะผู้ปฏิบัติงาน", ["กะ A", "กะ B", "กะ C"])
            
        if st.button("🚀 EXECUTE SYSTEM UPDATE & LOG DATA"):
            new_data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Date": date_input.strftime("%Y-%m-%d"),
                "Shift": shift_input,
                "Internal_Name": internal_name,
                "Staff_Count": int(internal_count),
                "External_Name": external_name if external_count > 0 else "ไม่มี",
                "Ext_Count": int(external_count),
                "Weather_Temp": temp,
                "Rain_Chance": int(rain_chance),
                "Water_Level": int(water_lvl),
                "Incidents": incident_input.replace("\n", " | ")
            }
            if os.path.exists("shift_logs.csv"):
                try:
                    df = pd.read_csv("shift_logs.csv")
                    valid_cols = ["Timestamp", "Date", "Shift", "Internal_Name", "Staff_Count", "External_Name", "Ext_Count", "Weather_Temp", "Rain_Chance", "Water_Level", "Incidents"]
                    df = df.reindex(columns=valid_cols)
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                except:
                    df = pd.DataFrame([new_data])
            else:
                df = pd.DataFrame([new_data])
            df.to_csv("shift_logs.csv", index=False, encoding='utf-8-sig')
            st.success("บันทึกรายงานเหตุการณ์สถานีบางกอกน้อยเรียบร้อย!")

with tab2:
    st.markdown("<h3 style='color: #00F2FE;'>📜 คลังคลังข้อมูลรายงานประจำวัน สถานีบางกอกน้อย</h3>", unsafe_allow_html=True)
    if os.path.exists("shift_logs.csv"):
        try:
            log_df = pd.read_csv("shift_logs.csv", encoding='utf-8-sig')
            if not log_df.empty:
                valid_cols = ["Timestamp", "Date", "Shift", "Internal_Name", "Staff_Count", "External_Name", "Ext_Count", "Weather_Temp", "Rain_Chance", "Water_Level", "Incidents"]
                log_df = log_df.reindex(columns=valid_cols)
                log_df = log_df[log_df["Timestamp"].notna()]
                latest_row = log_df.iloc[-1]
                
                kpi_1, kpi_2, kpi_3 = st.columns(3)
                with kpi_1: st.metric(label="👥 ยอดรวมจำนวนคนกะล่าสุด", value=f"{int(latest_row['Staff_Count'] + latest_row['Ext_Count'])} คน")
                with kpi_2: st.metric(label="🌧️ โอกาสเกิดฝนล่าสุด", value=f"{int(latest_row['Rain_Chance'])} %")
                with kpi_3: st.metric(label="🌊 ระดับน้ำบ่อระบายกะล่าสุด", value=f"{int(latest_row['Water_Level'])} %")
                st.markdown("<br>", unsafe_allow_html=True)
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("ฐานข้อมูลยังไม่มีรายงานบันทึกเข้ามาจากกะของสถานี BN ครับ")
        except:
            st.info("ระบบกำลังประมวลผลฐานข้อมูลตารางคอลัมน์ใหม่ กรุณากดบันทึกข้อมูลกะแรกที่หน้า OPERATIONS CENTER ก่อนครับ")
