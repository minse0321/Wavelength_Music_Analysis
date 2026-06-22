"""
음악 스트리밍 앱 (가상: Wavelength) 유저 행동 시뮬레이션
- 5개 페르소나 x N명의 가상 유저를 만들고
- 지정한 기간(일) 동안의 이벤트 로그를 생성한다
- 결과는 Amplitude HTTP API 포맷(JSON)으로 저장한다

실행: python3 generate_events.py
출력: events.json (Amplitude bulk upload용), events_raw.csv (Pandas EDA용)
"""

import json
import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------
# 0. 설정값
# ---------------------------------------------------------
N_USERS = 800
SIM_DAYS = 60
START_DATE = datetime(2026, 4, 1)

SONG_CATALOG = [f"song_{i:04d}" for i in range(1, 501)]
GENRES = ["pop", "hiphop", "indie", "ballad", "edm", "jazz", "rnb", "rock"]

PERSONAS = {
    "heavy":        {"weight": 0.15, "active_prob": 0.85, "songs_per_session": (8, 20), "skip_rate": 0.15, "churn_rate": 0.005},
    "light":        {"weight": 0.30, "active_prob": 0.35, "songs_per_session": (2, 7),  "skip_rate": 0.30, "churn_rate": 0.015},
    "churn":        {"weight": 0.25, "active_prob": 0.60, "songs_per_session": (3, 10), "skip_rate": 0.25, "churn_rate": 0.08},   # 시간 지날수록 활동 감소
    "convert":      {"weight": 0.15, "active_prob": 0.45, "songs_per_session": (3, 9),  "skip_rate": 0.25, "churn_rate": 0.01},
    "new_dropoff":  {"weight": 0.15, "active_prob": 0.50, "songs_per_session": (1, 4),  "skip_rate": 0.40, "churn_rate": 0.35},   # 가입 직후 급격히 이탈
}


def assign_persona():
    personas = list(PERSONAS.keys())
    weights = [PERSONAS[p]["weight"] for p in personas]
    return random.choices(personas, weights=weights, k=1)[0]


def make_users(n):
    users = []
    for i in range(n):
        persona = assign_persona()
        signup_offset = random.randint(0, SIM_DAYS - 5)  # 시뮬레이션 기간 내 아무 때나 가입
        users.append({
            "user_id": f"user_{uuid.uuid4().hex[:8]}",
            "persona": persona,
            "signup_day": signup_offset,
            "is_premium": False,
            "premium_since_day": None,
        })
    return users


def event(user_id, event_type, day_offset, event_props=None):
    ts = START_DATE + timedelta(days=day_offset, seconds=random.randint(0, 86399))
    return {
        "user_id": user_id,
        "event_type": event_type,
        "time": int(ts.timestamp() * 1000),  # Amplitude는 ms 단위 epoch
        "event_properties": event_props or {},
    }


def simulate_user(user):
    """한 유저의 SIM_DAYS 동안 이벤트 시퀀스 생성"""
    events = []
    persona_cfg = PERSONAS[user["persona"]]
    uid = user["user_id"]
    signup_day = user["signup_day"]

    events.append(event(uid, "sign_up", signup_day, {"persona": user["persona"]}))

    active_prob = persona_cfg["active_prob"]
    churn_rate = persona_cfg["churn_rate"]
    churned = False

    for day in range(signup_day, SIM_DAYS):
        if churned:
            break

        # churn 페르소나는 날짜가 갈수록 active_prob가 선형으로 감소
        days_since_signup = day - signup_day
        if user["persona"] == "churn":
            decay = max(0.05, active_prob - (days_since_signup * 0.03))
        elif user["persona"] == "new_dropoff":
            decay = active_prob if days_since_signup <= 2 else active_prob * 0.05
        else:
            decay = active_prob

        if random.random() > decay:
            continue  # 오늘은 접속 안 함

        events.append(event(uid, "open_app", day))

        n_songs = random.randint(*persona_cfg["songs_per_session"])
        for _ in range(n_songs):
            song = random.choice(SONG_CATALOG)
            genre = random.choice(GENRES)
            events.append(event(uid, "search_song", day, {"genre": genre}))
            events.append(event(uid, "play_song", day, {"song_id": song, "genre": genre}))

            if random.random() < persona_cfg["skip_rate"]:
                events.append(event(uid, "skip_song", day, {"song_id": song}))
            else:
                events.append(event(uid, "complete_song", day, {"song_id": song}))
                if random.random() < 0.2:
                    events.append(event(uid, "like_song", day, {"song_id": song}))
                if random.random() < 0.1:
                    events.append(event(uid, "add_to_playlist", day, {"song_id": song}))

        # 구독 전환 (convert 페르소나는 가입 후 5~20일 사이에 전환 확률 높임)
        if not user["is_premium"]:
            convert_chance = 0.02
            if user["persona"] == "convert" and 5 <= days_since_signup <= 20:
                convert_chance = 0.15
            elif user["persona"] == "heavy":
                convert_chance = 0.05
            if random.random() < convert_chance:
                events.append(event(uid, "subscribe_premium", day, {"plan": "premium_monthly"}))
                user["is_premium"] = True
        else:
            if random.random() < 0.01:  # 구독 해지 확률
                events.append(event(uid, "cancel_subscription", day))
                user["is_premium"] = False

        # 이탈 판정 (churn_rate 확률로 그날 이후 완전히 이탈)
        if random.random() < churn_rate:
            churned = True

    return events


def main():
    users = make_users(N_USERS)
    all_events = []
    for u in users:
        all_events.extend(simulate_user(u))

    all_events.sort(key=lambda e: e["time"])

    # Amplitude HTTP API 포맷으로 저장
    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(all_events, f, ensure_ascii=False)

    # Pandas EDA용 CSV도 같이 저장 (event_properties는 펼쳐서)
    rows = []
    for e in all_events:
        row = {
            "user_id": e["user_id"],
            "event_type": e["event_type"],
            "time": pd.to_datetime(e["time"], unit="ms"),
        }
        for k, v in e["event_properties"].items():
            row[f"prop_{k}"] = v  # users_meta.csv의 persona 컬럼과 충돌 방지
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv("events_raw.csv", index=False, encoding="utf-8-sig")

    # 유저 메타데이터도 따로 저장 (페르소나 라벨 — 나중에 실제로 군집화한 결과와 비교 검증용)
    pd.DataFrame(users).to_csv("users_meta.csv", index=False, encoding="utf-8-sig")

    print(f"유저 수: {len(users)}")
    print(f"총 이벤트 수: {len(all_events)}")
    print(f"이벤트 타입별 개수:\n{df['event_type'].value_counts()}")
    print("\n저장 완료: events.json (Amplitude 업로드용), events_raw.csv (EDA용), users_meta.csv (정답 라벨)")


if __name__ == "__main__":
    main()
