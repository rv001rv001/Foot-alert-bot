import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
API_URL = "https://v3.football.api-sports.io/fixtures?live=all"

HEADERS = {"x-apisports-key": API_KEY}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

def is_high_pressure(team_stats):
    return (
        team_stats.get("attacks", 0) >= 100 and
        team_stats.get("dangerous_attacks", 0) >= 70 and
        team_stats.get("possession", 0) >= 60
    )

def check_live_matches():
    resp = requests.get(API_URL, headers=HEADERS)
    if resp.status_code != 200:
        return
    for match in resp.json().get("response", []):
        stats = match.get("statistics") or []
        if not stats:
            continue
        fixture = match["fixture"]
        # On ne traite que la 2ème mi‑temps
        if fixture["status"]["long"] != "Second Half":
            continue

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        elapsed = fixture["status"]["elapsed"]

        def parse(s_list, key):
            for stat in s_list:
                if stat["type"] == key:
                    return int((stat["value"] or "0").replace("%",""))
            return 0

        home_stats = stats[0]["statistics"]
        away_stats = stats[1]["statistics"]

        h = {
            "attacks": parse(home_stats, "Attacks"),
            "dangerous_attacks": parse(home_stats, "Dangerous Attacks"),
            "possession": parse(home_stats, "Ball Possession")
        }
        a = {
            "attacks": parse(away_stats, "Attacks"),
            "dangerous_attacks": parse(away_stats, "Dangerous Attacks"),
            "possession": parse(away_stats, "Ball Possession")
        }

        if is_high_pressure(h):
            send_telegram_message(f"PRESSION FORTÉE : {home} vs {away} – {home} pousse fort à la {elapsed}e")
        if is_high_pressure(a):
            send_telegram_message(f"PRESSION FORTÉE : {home} vs {away} – {away} pousse fort à la {elapsed}e")

if __name__ == "__main__":
    while True:
        try:
            check_live_matches()
        except Exception as e:
            print("Erreur :", e)
        time.sleep(60)
