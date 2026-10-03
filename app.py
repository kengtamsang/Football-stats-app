import streamlit as st
import os
import requests
import numpy as np
import pandas as pd
from scipy.stats import poisson
from itertools import combinations
from datetime import datetime

# ตั้งค่าหน้าตาแอป
st.set_page_config(page_title="Football AI Analyzer", page_icon="⚽", layout="wide")

st.title("⚽ AI Football Analyzer")
st.write(f"อัปเดตข้อมูลล่าสุด: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ดึง API Token จาก Environment Variable
API_TOKEN = st.secrets.get("FOOTBALL_API_TOKEN", os.getenv("FOOTBALL_API_TOKEN", ""))

if not API_TOKEN:
    st.error("⚠️ กรุณาตั้งค่า FOOTBALL_API_TOKEN ใน Streamlit Secrets ก่อนใช้งาน")
    st.stop()

BASE_URL = "https://api.football-data.org/v4/"

def calculate_poisson(exp_home=1.6, exp_away=1.1, max_goals=6):
    score_matrix = np.zeros((max_goals + 1, max_goals + 1))
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            score_matrix[h, a] = poisson.pmf(h, exp_home) * poisson.pmf(a, exp_away)

    prob_home = np.sum(np.tril(score_matrix, -1))
    prob_draw = np.sum(np.diag(score_matrix))
    prob_away = np.sum(np.triu(score_matrix, 1))

    band_0_1 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if 0 <= h+a <= 1)
    band_2_3 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if 2 <= h+a <= 3)
    band_4_6 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if 4 <= h+a <= 6)

    return {
        "home": prob_home, "draw": prob_draw, "away": prob_away,
        "b01": band_0_1, "b23": band_2_3, "b46": band_4_6
    }

headers = {"X-Auth-Token": API_TOKEN}
today = datetime.now().strftime("%Y-%m-%d")
url = f"{BASE_URL}matches?dateFrom={today}&dateTo={today}"

res = requests.get(url, headers=headers)

if res.status_code == 200:
    matches = res.json().get("matches", [])
    if not matches:
        st.info("ℹ️ วันนี้ไม่มีรายการแข่งขันในระบบ")
    else:
        st.subheader("📊 ผลการวิเคราะห์ประจำวัน")
        for match in matches:
            league = match.get("competition", {}).get("name", "League")
            home = match.get("homeTeam", {}).get("name")
            away = match.get("awayTeam", {}).get("name")
            
            p = calculate_poisson()
            
            with st.expander(f"⚽ [{league}] {home} vs {away}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("เจ้าบ้านชนะ", f"{p['home']*100:.1f}%")
                col2.metric("เสมอ", f"{p['draw']*100:.1f}%")
                col3.metric("ทีมเยือนชนะ", f"{p['away']*100:.1f}%")
                
                st.write("**ความน่าจะเป็นประตูรวม:**")
                st.write(f"- 0-1 ประตู: `{p['b01']*100:.1f}%` | 2-3 ประตู: `{p['b23']*100:.1f}%` | 4-6 ประตู: `{p['b46']*100:.1f}%`")
else:
    st.error("เกิดข้อผิดพลาดในการดึงข้อมูล API")
