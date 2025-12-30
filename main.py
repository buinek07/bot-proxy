import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
from datetime import datetime
import requests
import random
import time

# --- CẤU HÌNH ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'
ADMIN_ID = 5519768222 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

# Server giữ cho Bot sống trên Koyeb
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- TÍNH NĂNG THÔNG BÁO NẠP TIỀN CHO ADMIN ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    # Thông báo ngay cho bạn khi có khách nhấn nút
    try:
        bot.send_message(ADMIN_ID, f"🔔 **KHÁCH ĐANG XEM NẠP TIỀN**\n👤 Tên: {message.from_user.first_name}\n🆔 ID: `{user_id}`")
    except: pass

    memo = f"naptien {random.randint(10,99)}{user_id}"
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    bot.send_photo(message.chat.id, qr_url, caption=f"📌 Nội dung chuyển khoản: `{memo}`\n💰 Tối thiểu 20k.")

# --- LỆNH CỘNG TIỀN + CẢM ƠN ---
@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt)}})
        bot.send_message(ADMIN_ID, f"✅ Đã nạp {amt} cho {tid}")
        # Gửi lời cảm ơn khách hàng
        bot.send_message(int(tid), f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n💰 Bạn đã được cộng `{int(amt):,} VND`.\n🙏 Cảm ơn bạn đã tin tưởng dịch vụ!")
    except:
        bot.send_message(ADMIN_ID, "❌ Sai cú pháp: /plus [ID] [Số tiền]")

# --- VÒNG LẶP TỰ KHỞI ĐỘNG LẠI KHI LỖI ---
def start_bot():
    while True:
        try:
            print("Bot đang chạy...")
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception as e:
            print(f"Lỗi: {e}. Thử lại sau 5s...")
            time.sleep(5)

if __name__ == "__main__":
    start_bot()
