import os
import requests
import numpy as np
import pandas as pd
from scipy.stats import poisson
from itertools import combinations
from datetime import datetime

# ==========================================
# 1. FOOTBALL DATA API FETCHING
# ==========================================
API_TOKEN = os.getenv("FOOTBALL_API_TOKEN", "YOUR_API_TOKEN_HERE")
BASE_URL = "https://api.football-data.org/v4/"

def get_todays_matches():
    headers = {"X-Auth-Token": API_TOKEN}
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}matches?dateFrom={today}&dateTo={today}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("matches", [])
        else:
            print(f"⚠️ เกิดข้อผิดพลาดในการดึง API: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

# ==========================================
# 2. POISSON AI PREDICTION ENGINE
# ==========================================
def calculate_poisson_probabilities(exp_home_goals=1.6, exp_away_goals=1.1, max_goals=6):
    score_matrix = np.zeros((max_goals + 1, max_goals + 1))
    
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            prob_h = poisson.pmf(h, exp_home_goals)
            prob_a = poisson.pmf(a, exp_away_goals)
            score_matrix[h, a] = prob_h * prob_a

    prob_home = np.sum(np.tril(score_matrix, -1))
    prob_draw = np.sum(np.diag(score_matrix))
    prob_away = np.sum(np.triu(score_matrix, 1))

    prob_under_2_5 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if h + a < 2.5)
    prob_over_2_5 = 1 - prob_under_2_5

    band_0_1 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if 0 <= h+a <= 1)
    band_2_3 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if 2 <= h+a <= 3)
    band_4_6 = sum(score_matrix[h, a] for h in range(max_goals+1) for a in range(max_goals+1) if 4 <= h+a <= 6)

    return {
        "home_win": prob_home,
        "draw": prob_draw,
        "away_win": prob_away,
        "over_2_5": prob_over_2_5,
        "under_2_5": prob_under_2_5,
        "band_0_1": band_0_1,
        "band_2_3": band_2_3,
        "band_4_6": band_4_6
    }

# ==========================================
# 3. ACCUMULATOR OPTIMIZER
# ==========================================
def build_best_step_bets(analyzed_matches, min_legs=3):
    print(f"\n==========================================")
    print(f"🔥 สรุปวิเคราะห์จัดชุดบอลสเต็ป ({min_legs} คู่ขึ้นไป)")
    print(f"==========================================")
    
    candidates = []
    for m in analyzed_matches:
        best_pick = max(m['picks'], key=lambda x: x['prob'])
        if best_pick['prob'] >= 0.55:
            candidates.append({
                "match": m['match'],
                "league": m['league'],
                "selection": best_pick['name'],
                "prob": best_pick['prob']
            })

    if len(candidates) >= min_legs:
        combos = list(combinations(candidates, min_legs))
        sorted_combos = sorted(combos, key=lambda x: np.prod([item['prob'] for item in x]), reverse=True)

        for idx, combo in enumerate(sorted_combos[:3], 1):
            total_prob = np.prod([item['prob'] for item in combo]) * 100
            print(f"\n📌 บอลสเต็ปชุดที่ #{idx} (ความน่าจะเป็นรวม: {total_prob:.1f}%)")
            for leg in combo:
                print(f"  • [{leg['league']}] {leg['match']} -> เลือก: {leg['selection']} (โอกาสชนะ: {leg['prob']*100:.1f}%)")
    else:
        print("⚠️ วันนี้ไม่มีคู่ฟุตบอลที่มีอัตราความน่าจะเป็นสูงพอสำหรับจัดสเต็ป")

# ==========================================
# 4. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print(f"🤖 เริ่มต้นระบบ AI วิเคราะห์ฟุตบอลเรียลไทม์ ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    matches = get_todays_matches()
    
    analyzed_list = []

    if not matches:
        print("ℹ️ ไม่พบโปรแกรมการแข่งขันในระบบวันนี้ หรือยังไม่ได้ตั้งค่า API_TOKEN")
    else:
        for match in matches:
            league = match.get("competition", {}).get("name", "Unknown League")
            home_team = match.get("homeTeam", {}).get("name")
            away_team = match.get("awayTeam", {}).get("name")
            
            probs = calculate_poisson_probabilities()

            picks = [
                {"name": f"ชนะ ({home_team})", "prob": probs['home_win']},
                {"name": "เสมอ", "prob": probs['draw']},
                {"name": f"ชนะ ({away_team})", "prob": probs['away_win']},
                {"name": "สกอร์สูง Over 2.5", "prob": probs['over_2_5']},
                {"name": "สกอร์รวม 2-3 ลูก", "prob": probs['band_2_3']}
            ]
            
            analyzed_list.append({
                "match": f"{home_team} vs {away_team}",
                "league": league,
                "picks": picks
            })

            best_single = max(picks, key=lambda x: x['prob'])
            print(f"\n⚽ [{league}] {home_team} vs {away_team}")
            print(f"  └─ 🎯 บอลเดี่ยวแนะนำ: {best_single['name']} (โอกาส: {best_single['prob']*100:.1f}%)")
            print(f"  └─ 📊 ประตูรวม -> 0-1 ลูก: {probs['band_0_1']*100:.1f}% | 2-3 ลูก: {probs['band_2_3']*100:.1f}% | 4-6 ลูก: {probs['band_4_6']*100:.1f}%")

        build_best_step_bets(analyzed_list, min_legs=3)
