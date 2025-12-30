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
ADMIN_ID = 5519768222 # Admin ID của bạn

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

# Giữ bot sống trên Koyeb
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- LỆNH CỘNG TIỀN + CẢM ƠN (Đã cập nhật theo ý bạn) ---
@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt)}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt} cho {tid}")
        
        # Gửi lời cảm ơn khách hàng
        thanks_msg = (f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n"
                      f"💰 Bạn được cộng: `{int(amt):,} VND`\n"
                      f"🙏 **Cảm ơn bạn đã tin tưởng sử dụng dịch vụ!**")
        bot.send_message(int(tid), thanks_msg, parse_mode="Markdown")
    except:
        bot.send_message(ADMIN_ID, "❌ Lỗi. Cú pháp: /plus [ID] [Số tiền]")

# --- THÔNG BÁO CHO ADMIN KHI KHÁCH NHẤN NẠP TIỀN ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    try:
        bot.send_message(ADMIN_ID, f"🔔 **THÔNG BÁO:** Khách **{message.from_user.first_name}** (ID: `{user_id}`) đang xem thông tin nạp tiền!")
    except: pass
    
    memo = f"nap{random.randint(10,99)}{user_id}"
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    bot.send_photo(message.chat.id, qr_url, caption=f"📌 Nội dung: `{memo}`\n💰 Đợi Admin duyệt sau khi CK.")

# --- VÒNG LẶP KHỞI CHẠY (CHỐNG TREO & XUNG ĐỘT) ---
def start_bot():
    while True:
        try:
            print("Đang khởi động bot...")
            # Quan trọng: Xóa webhook cũ để tránh lỗi Conflict 409
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"Lỗi: {e}. Thử lại sau 5 giây...")
            time.sleep(5)

if __name__ == "__main__":
    start_bot()
