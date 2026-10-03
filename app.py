import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="AI Football Analyzer", page_icon="⚽", layout="wide")

st.title("⚽ AI Football Analyzer")

# ดึง API Token จาก Streamlit Secrets
api_token = st.secrets.get("FOOTBALL_API_TOKEN", "")

if not api_token:
    st.error("กรุณาตั้งค่า FOOTBALL_API_TOKEN ใน Streamlit Secrets ก่อนใช้งาน")
    st.stop()

# ตั้งค่าเวลาไทย (UTC+7)
tz_th = timezone(timedelta(hours=7))
now_th = datetime.now(tz_th)
st.caption(f"อัปเดตข้อมูลล่าสุด: {now_th.strftime('%Y-%m-%d %H:%M')}")

# ดึงข้อมูลย้อนหลัง 1 วัน และล่วงหน้า 2 วัน
date_from = (now_th - timedelta(days=1)).strftime('%Y-%m-%d')
date_to = (now_th + timedelta(days=2)).strftime('%Y-%m-%d')

headers = {"X-Auth-Token": api_token}
url = f"https://api.football-data.org/v4/matches?dateFrom={date_from}&dateTo={date_to}"

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    
    matches = data.get("matches", [])
    
    if not matches:
        st.info("ไม่พบรายการแข่งขันในช่วงเวลานี้ในระบบ API")
    else:
        st.success(f"พบรายการแข่งขันทั้งหมด {len(matches)} รายการ")
        
        for match in matches:
            competition = match.get("competition", {}).get("name", "Unknown League")
            home_team = match.get("homeTeam", {}).get("name", "Home")
            away_team = match.get("awayTeam", {}).get("name", "Away")
            status = match.get("status", "SCHEDULED")
            utc_date = match.get("utcDate", "")
            
            # แปลงเวลาเป็นเวลาไทย (UTC+7)
            if utc_date:
                utc_dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                match_time = utc_dt.astimezone(tz_th)
                time_str = match_time.strftime("%d/%m/%Y %H:%M น.")
            else:
                time_str = "ไม่ระบุเวลา"

            with st.container():
                st.subheader(f"🏆 {competition}")
                st.write(f"**{home_team}** vs **{away_team}**")
                st.write(f"📅 เวลาแข่ง: {time_str} | สถานะ: `{status}`")
                st.divider()

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

