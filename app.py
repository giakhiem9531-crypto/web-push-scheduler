from flask import Flask, render_template, request, jsonify
import schedule
import threading
import time
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI
import os
import json

app = Flask(__name__, template_folder="templates")

# Lưu subscriptions của user
subscriptions = {}
last_sent = {}
COOLDOWN = 60  # giây

# Load env
load_dotenv()
VAPID_PUBLIC_KEY = os.getenv("PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("PRIVATE_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# =================== Web Push ===================
def send_web_push(subscription_info, message):
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"message": message}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:your_email@example.com"}
        )
        print(f"[SUCCESS] Đã gửi thông báo tới {subscription_info['endpoint']}")
    except WebPushException as ex:
        print(f"[ERROR] Gửi thất bại: {ex}")
        if ex.response and ex.response.status_code == 410:
            # Subscription hết hạn
            device_ids_to_remove = [k for k, v in subscriptions.items() if v == subscription_info]
            for k in device_ids_to_remove:
                subscriptions.pop(k, None)

def job_send(message, time_key, device_id):
    now = datetime.now()
    if time_key not in last_sent or (now - last_sent[time_key]).total_seconds() >= COOLDOWN:
        sub = subscriptions.get(device_id)
        if sub:
            send_web_push(sub, message)
            last_sent[time_key] = now
            print("Đã gửi đến device:", device_id)

# Scheduler chạy nền
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler, daemon=True).start()

# =================== Routes ===================
@app.route('/')
def index():
    return render_template('index1.html', vapid_key=VAPID_PUBLIC_KEY)

@app.route('/service-worker.js')
def sw():
    return app.send_static_file('service-worker.js')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    subscription = data.get("subscription")
    device_id = data.get("device_id")
    if not device_id or not subscription:
        return jsonify({"error": "missing device_id or subscription"}), 400
    subscriptions[device_id] = subscription
    print("Đăng ký thành công cho device:", device_id)
    return jsonify({"status": "success"})

@app.route('/send', methods=['POST'])
def send_all_push():
    message = request.json.get("message", "Bạn có thông báo mới!")
    for device_id, sub in subscriptions.items():
        send_web_push(sub, message)
        print(f"Đã gửi tới device: {device_id}")
    return jsonify({"status": "sent", "devices": list(subscriptions.keys())})

@app.route('/add', methods=['POST'])
def add_schedule():
    data = request.json
    hour = int(data['hour'])
    minute = int(data['minute'])
    message = data['message'][:1000]  # Giới hạn nội dung
    device_id = data.get("device_id")
    if not device_id:
        return jsonify({"error": "device_id missing"}), 400

    time_str = f"{hour:02d}:{minute:02d}"
    time_key = f"{time_str}-{device_id}"

    # Gọi OpenAI tạo nội dung
    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Bạn là người bạn tốt, động viên người dùng, gửi hotline nếu cần."},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=50
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        print("Lỗi OpenAI:", e)
        answer = "Hiện hệ thống đang bận. Bạn thử lại sau nhé."

    # Lên lịch gửi
    schedule.every().day.at(time_str).do(job_send, answer, time_key, device_id)

    return jsonify({"status": "scheduled", "time": time_str, "message": answer})
@app.route('/send-test')
def send_test():
    for sub in subscriptions.values():
        send_web_push(sub, "Test message")
    return "Sent"
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
