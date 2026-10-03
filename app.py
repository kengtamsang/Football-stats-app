import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="AI Football Statistics & Fixtures", page_icon="⚽", layout="wide")

st.title("⚽ AI Football Statistics & Season Tracker")

api_token = st.secrets.get("FOOTBALL_API_TOKEN", "")
if not api_token:
    st.error("กรุณาตั้งค่า FOOTBALL_API_TOKEN ใน Streamlit Secrets")
    st.stop()

tz_th = timezone(timedelta(hours=7))
headers = {"X-Auth-Token": api_token}

# รหัสลีกยอดนิยมใน API ฟรี
LEAGUES = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🇪🇸 La Liga": "PD",
    "🇩🇪 Bundesliga": "BL1",
    "🇮🇹 Serie A": "SA",
    "🇫🇷 Ligue 1": "FL1",
    "🏆 UEFA Champions League": "CL"
}

st.sidebar.header("⚙️ ตัวเลือกข้อมูล")
selected_league_name = st.sidebar.selectbox("เลือกลีกที่ต้องการดู", list(LEAGUES.keys()))
league_code = LEAGUES[selected_league_name]

# ฟังก์ชันดึงข้อมูลแมตช์ทั้งหมดในฤดูกาลของลีกนั้น
@st.cache_data(ttl=1800) # บันทึกข้อมูลไว้ 30 นาที
def get_season_matches(code):
    url = f"https://api.football-data.org/v4/competitions/{code}/matches"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json().get("matches", [])
    return []

matches = get_season_matches(league_code)

if not matches:
    st.warning("ไม่สามารถดึงข้อมูลลีกนี้ได้ หรือเกินโควต้า API ชั่วคราว (ลองรีเฟรชในอีก 1 นาที)")
else:
    # แปลงข้อมูลเป็น List เพื่อทำ DataFrame
    data_list = []
    matchdays = set()

    for m in matches:
        matchday = m.get("matchday", 0)
        if matchday:
            matchdays.add(matchday)
            
        utc_date = m.get("utcDate", "")
        if utc_date:
            utc_dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            local_time = utc_dt.astimezone(tz_th).strftime("%d/%m/%Y %H:%M")
        else:
            local_time = "-"

        status = m.get("status", "")
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        
        score_home = m["score"]["fullTime"]["home"]
        score_away = m["score"]["fullTime"]["away"]
        
        if status == "FINISHED":
            score_str = f"{score_home} - {score_away}"
            status_th = "จบแล้ว"
        elif status in ["IN_PLAY", "PAUSED", "HALFTIME"]:
            score_str = f"{score_home} - {score_away}"
            status_th = "🔴 กำลังแข่ง"
        else:
            score_str = "vs"
            status_th = "⏳ รอนัดเตะ"

        data_list.append({
            "นัดที่ (Matchday)": matchday,
            "วัน-เวลา (ไทย)": local_time,
            "ทีมเหย้า": home,
            "ผล / เวลา": score_str,
            "ทีมเยือน": away,
            "สถานะ": status_th
        })

    df = pd.DataFrame(data_list)

    # ตัวกรองใน Sidebar: เลือกดูเฉพาะนัดที่ (Matchday) หรือดูทั้งหมด
    st.sidebar.markdown("---")
    view_option = st.sidebar.radio("รูปแบบการแสดงผล", ["แสดงทั้งหมดทั้งฤดูกาล", "กรองตามนัดที่ (Matchday)", "กรองตามสถานะ"])

    st.subheader(f"📊 ตารางการแข่งขัน {selected_league_name}")

    if view_option == "กรองตามนัดที่ (Matchday)":
        sorted_matchdays = sorted(list(matchdays))
        selected_md = st.sidebar.selectbox("เลือกนัดที่ (Matchday)", sorted_matchdays)
        filtered_df = df[df["นัดที่ (Matchday)"] == selected_md]
        st.write(f"### นัดที่ {selected_md}")
        st.dataframe(filtered_df.drop(columns=["นัดที่ (Matchday)"]), use_container_width=True, hide_index=True)

    elif view_option == "กรองตามสถานะ":
        status_choice = st.sidebar.selectbox("เลือกสถานะ", ["จบแล้ว", "⏳ รอนัดเตะ", "🔴 กำลังแข่ง"])
        filtered_df = df[df["สถานะ"] == status_choice]
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    else:
        # แสดงตารางทั้งหมด
        st.dataframe(df, use_container_width=True, hide_index=True)
