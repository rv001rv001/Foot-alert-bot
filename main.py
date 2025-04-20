import os
import requests
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

API_KEY        = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID")
API_URL        = "https://v3.football.api-sports.io/fixtures?live=all"
HEADERS        = {"x-apisports-key": API_KEY}

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
    if resp.status_code != 200: return
    for match in resp.json().get("response", []):
        stats = match.get("statistics") or []
        if not stats: continue
        fix = match["fixture"]
        if fix["status"]["long"] != "Second Half": continue

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        elapsed = fix["status"]["elapsed"]

        def parse(s_list, key):
            for st in s_list:
                if st["type"] == key:
                    return int((st["value"] or "0").replace("%",""))
            return 0

        h_stats = stats[0]["statistics"]
        a_stats = stats[1]["statistics"]

        h = {
            "attacks": parse(h_stats, "Attacks"),
            "dangerous_attacks": parse(h_stats, "Dangerous Attacks"),
            "possession": parse(h_stats, "Ball Possession")
        }
        a = {
            "attacks": parse(a_stats, "Attacks"),
            "dangerous_attacks": parse(a_stats, "Dangerous Attacks"),
            "possession": parse(a_stats, "Ball Possession")
        }

        if is_high_pressure(h):
            send_telegram_message(f"PRESSION FORTÉE : {home} vs {away} – {home} pousse fort à la {elapsed}e")
        if is_high_pressure(a):
            send_telegram_message(f"PRESSION FORTÉE : {home} vs {away} – {away} pousse fort à la {elapsed}e")

def bot_loop():
    while True:
        try:
            check_live_matches()
        except Exception as e:
            print("Erreur dans la boucle :", e)
        time.sleep(60)

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

if __name__ == "__main__":
    # Démarre la boucle du bot en arrière‑plan
    threading.Thread(target=bot_loop, daemon=True).start()

    # Démarre un serveur HTTP “pingable” sur le port fourni par Render
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    print(f"Listening on port {port} for health checks…")
    server.serve_forever()
