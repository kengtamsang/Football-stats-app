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

# ---------------- Sidebar สำหรับการตั้งค่า ----------------
st.sidebar.header("⚙️ ตัวกรองข้อมูล")

# เลือกช่วงเวลาที่ต้องการดูข้อมูล
days_back = st.sidebar.slider("ดึงผลย้อนหลัง (วัน)", min_value=1, max_value=14, value=3)
days_ahead = st.sidebar.slider("ดึงตารางแข่งล่วงหน้า (วัน)", min_value=1, max_value=14, value=5)

date_from = (now_th - timedelta(days=days_back)).strftime('%Y-%m-%d')
date_to = (now_th + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

st.caption(f"📅 แสดงข้อมูลตั้งแต่วันที่ **{date_from}** ถึง **{date_to}** (อัปเดตล่าสุด: {now_th.strftime('%H:%M น.')})")

# ---------------- ดึงข้อมูลจาก API ----------------
headers = {"X-Auth-Token": api_token}
url = f"https://api.football-data.org/v4/matches?dateFrom={date_from}&dateTo={date_to}"

@st.cache_data(ttl=300)  # บันทึก Cache 5 นาทีเพื่อป้องกัน API Rate Limit
def fetch_matches(api_url, headers_data):
    res = requests.get(api_url, headers=headers_data)
    if res.status_code == 200:
        return res.json().get("matches", [])
    return []

try:
    matches = fetch_matches(url, headers)
    
    if not matches:
        st.info("ไม่พบรายการแข่งขันในช่วงเวลาที่เลือก")
    else:
        # จัดกลุ่มแมตช์ตามลีก (Competition)
        leagues = {}
        for match in matches:
            comp_name = match.get("competition", {}).get("name", "รายการอื่นๆ")
            if comp_name not in leagues:
                leagues[comp_name] = []
            leagues[comp_name].append(match)

        # ตัวเลือกกรองลีกใน Sidebar
        all_leagues = list(leagues.keys())
        selected_leagues = st.sidebar.multiselect("เลือกลีกที่ต้องการดู", all_leagues, default=all_leagues)

        # แสดงข้อมูลแยกตามลีก
        for comp_name in selected_leagues:
            comp_matches = leagues[comp_name]
            
            with st.expander(f"🏆 **{comp_name}** ({len(comp_matches)} รายการ)", expanded=True):
                
                # แยกหมวดหมู่ย่อย: จบแล้ว / กำลังแข่ง / อนาคต
                finished = []
                live = []
                upcoming = []

                for m in comp_matches:
                    status = m.get("status", "")
                    if status in ["FINISHED", "AWARDED"]:
                        finished.append(m)
                    elif status in ["IN_PLAY", "PAUSED", "HALFTIME"]:
                        live.append(m)
                    else:
                        upcoming.append(m)

                # 🔴 1. แมตช์ที่กำลังแข่งขัน (Live)
                if live:
                    st.markdown("##### 🔴 กำลังแข่งขันสด")
                    for m in live:
                        home = m["homeTeam"]["name"]
                        away = m["awayTeam"]["name"]
                        score_h = m["score"]["fullTime"]["home"]
                        score_a = m["score"]["fullTime"]["away"]
                        st.warning(f"🔥 **{home}** `{score_h} - {score_a}` **{away}** | สถานะ: LIVE")

                # ✅ 2. ผลการแข่งขันที่ผ่านมา (Finished)
                if finished:
                    st.markdown("##### ✅ ผลการแข่งขันย้อนหลัง")
                    for m in finished:
                        home = m["homeTeam"]["name"]
                        away = m["awayTeam"]["name"]
                        score_h = m["score"]["fullTime"]["home"]
                        score_a = m["score"]["fullTime"]["away"]
                        
                        # แปลงเวลา
                        utc_dt = datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        m_time = utc_dt.astimezone(tz_th).strftime("%d/%m %H:%M น.")
                        
                        st.write(f"🟢 `{m_time}` | **{home}** `{score_h} - {score_a}` **{away}**")

                # 📅 3. โปรแกรมการแข่งขันในอนาคต (Upcoming)
                if upcoming:
                    st.markdown("##### 📅 โปรแกรมแข่งล่วงหน้า")
                    for m in upcoming:
                        home = m["homeTeam"]["name"]
                        away = m["awayTeam"]["name"]
                        
                        # แปลงเวลา
                        utc_dt = datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        m_time = utc_dt.astimezone(tz_th).strftime("%d/%m/%Y %H:%M น.")
                        
                        st.write(f"⏳ `{m_time}` | **{home}** vs **{away}**")

except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
