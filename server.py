import socket
import threading
import sqlite3
import json

# اتصال به دیتابیس
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# ساخت جدول کاربران
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    is_online INTEGER DEFAULT 0
)
""")
conn.commit()

# لیست کاربران آنلاین
clients = {}

def broadcast_users():
    """ارسال لیست کاربران آنلاین به همه"""
    online_users = [user for user, client in clients.items() if client]
    message = {"type": "users", "users": online_users}
    data = json.dumps(message)
    for user, client in clients.items():
        try:
            client.send(data.encode())
        except:
            pass

def send_private_message(sender, receiver, message):
    """ارسال پیام خصوصی به یک کاربر"""
    if receiver in clients:
        try:
            clients[receiver].send(json.dumps({
                "type": "chat",
                "from": sender,
                "message": message
            }).encode())
        except:
            pass
    else:
        # ارسال پیام خطا به فرستنده
        if sender in clients:
            clients[sender].send(json.dumps({
                "type": "error",
                "msg": f"کاربر {receiver} آفلاین است یا وجود ندارد"
            }).encode())

def remove_client(client_socket):
    """حذف کلاینت از لیست آنلاین‌ها"""
    for user, sock in list(clients.items()):
        if sock == client_socket:
            cursor.execute("UPDATE users SET is_online=0 WHERE username=?", (user,))
            conn.commit()
            del clients[user]
            broadcast_users()
            break

def handle_client(client_socket):
    username = None
    try:
        # ثبت نام کاربر
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            try:
                msg = json.loads(data)
                if msg["type"] == "register":
                    username = msg["username"]
                    try:
                        cursor.execute("INSERT INTO users (username, is_online) VALUES (?, 1)", (username,))
                        conn.commit()
                        clients[username] = client_socket
                        broadcast_users()
                        client_socket.send(json.dumps({"type": "success", "msg": "ثبت‌نام موفق!"}).encode())
                        break
                    except sqlite3.IntegrityError:
                        client_socket.send(json.dumps({"type": "error", "msg": "نام کاربری تکراری است"}).encode())
            except:
                continue

        # مدیریت پیام
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            try:
                msg = json.loads(data)
                if msg["type"] == "chat":
                    send_private_message(username, msg["to"], msg["message"])
            except Exception as e:
                print("Error:", e)
    except Exception as e:
        print("Connection error:", e)
    finally:
        remove_client(client_socket)
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 12345))
    server.listen(5)
    print("Server در حال گوش دادن...")

    while True:
        client, addr = server.accept()
        print(f"اتصال از {addr}")
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == "__main__":
    start_server()