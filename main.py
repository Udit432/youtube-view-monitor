import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

# ===== CONFIG =====
API_KEY = "AIzaSyDT0FGdoRzoH29r_2r4B8HqgAySh71WDqc"
BOT_TOKEN = "8601479357:AAHEDqZUTzwRvFt1Uyl9nvs81xUT_VhsJFA"

CHAT_ID = None
VIDEO_ID = None
tracking = False
last_views = None
alert_active = False

# ===== TELEGRAM SEND =====
def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })

# ===== ALARM SYSTEM =====
def trigger_alarm(message):
    global alert_active

    if alert_active:
        return

    alert_active = True

    def alarm_loop():
        global alert_active

        while alert_active:
            for i in range(10):  # 🔥 burst alerts
                send_alert(f"🚨 {message} 🚨")
                time.sleep(1)

            time.sleep(10)  # gap then repeat

    threading.Thread(target=alarm_loop, daemon=True).start()

# ===== YOUTUBE FETCH =====
def get_views():
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={VIDEO_ID}&key={API_KEY}"
    res = requests.get(url).json()
    return int(res['items'][0]['statistics']['viewCount'])

# ===== BACKGROUND WORKER =====
def background_worker():
    global last_views, tracking

    while True:
        if tracking and VIDEO_ID:
            try:
                current_views = get_views()
                print("Views:", current_views)

                if last_views is not None:
                    if current_views < last_views:
                        drop = last_views - current_views
                        trigger_alarm(f"VIEWS DROP\nPrev: {last_views}\nNow: {current_views}\nDrop: {drop}")

                last_views = current_views

            except Exception as e:
                print("Error:", e)

        time.sleep(60)

# ===== TELEGRAM WEBHOOK =====
@app.route('/', methods=['POST', 'GET'])
def webhook():
    global tracking, VIDEO_ID, CHAT_ID, alert_active

    if request.method == "POST":
        data = request.json

        if 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '')

            CHAT_ID = chat_id

            if text.startswith("/start"):
                tracking = True
                send_alert("✅ Tracking Started")

            elif text.startswith("/stop"):
                tracking = False
                send_alert("⛔ Tracking Stopped")

            elif text.startswith("/setvideo"):
                try:
                    VIDEO_ID = text.split(" ")[1]
                    send_alert(f"🎯 Video Set: {VIDEO_ID}")
                except:
                    send_alert("❌ Use: /setvideo VIDEO_ID")

            elif text.startswith("/stopalert"):
                alert_active = False
                send_alert("🛑 Alert Stopped")

    return "OK"

# ===== START THREAD =====
threading.Thread(target=background_worker, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
