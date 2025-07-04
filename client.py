import socket
import json
import threading
import sys

def receive_messages(client):
    while True:
        try:
            data = client.recv(1024).decode()
            if not data:
                print("اتصال قطع شد.")
                sys.exit()
            try:
                msg = json.loads(data)
                if msg["type"] == "chat":
                    print(f"[{msg['from']}] → شما: {msg['message']}")
                elif msg["type"] == "users":
                    print(f"🟢 کاربران آنلاین: {', '.join(msg['users'])}")
                elif msg["type"] == "error":
                    print(f"❌ خطا: {msg['msg']}")
                elif msg["type"] == "success":
                    print(f"✅ موفق: {msg['msg']}")
            except Exception as e:
                print("مشکل در دریافت پیام:", e)
        except:
            print("اتصال قطع شد.")
            sys.exit()

def send_message(client, to, message):
    client.send(json.dumps({"type": "chat", "to": to, "message": message}).encode())

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 12345))

    # دریافت پیام‌ها
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    # ثبت نام نام کاربری
    while True:
        username_input = input("نام کاربری خود را وارد کنید (مانند @ysnrfd): ")
        if username_input.startswith("@"):
            username = username_input[1:]
        else:
            username = username_input
        client.send(json.dumps({"type": "register", "username": username}).encode())
        response = client.recv(1024).decode()
        res = json.loads(response)
        if res["type"] == "success":
            print("ثبت‌نام موفق!")
            break
        else:
            print("نام کاربری تکراری است. نام دیگری انتخاب کنید.")

    # حالت چت
    current_recipient = None
    print("\n--- دستورات ---")
    print("/users → نمایش کاربران آنلاین")
    print("/to username → تعیین دریافت‌کننده")
    print("/exit → خروج")
    print("-----------\n")

    while True:
        try:
            text = input()
            if text.lower() == "/exit":
                print("خروج...")
                client.close()
                sys.exit()
            elif text.startswith("/users"):
                print("درخواست لیست کاربران...")
            elif text.startswith("/to "):
                current_recipient = text[4:]
                print(f"🎯 در حال ارسال به: {current_recipient}")
            elif current_recipient:
                send_message(client, current_recipient, text)
            else:
                print("⚠️ ابتدا دریافت‌کننده را با /to تعیین کنید")
        except KeyboardInterrupt:
            print("\nخروج...")
            client.close()
            sys.exit()

if __name__ == "__main__":
    start_client()