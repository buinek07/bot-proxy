import os
import telebot
import requests
import random
import time
import threading
from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from telebot import types

# --- 1. CẤU HÌNH HỆ THỐNG (Khôi phục từ code cũ) ---
TOKEN = os.getenv('TOKEN', '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee')
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'

ADMIN_ID = 5519768222 
BANK_ID = 'MB'
STK_MOI = '700122'
TEN_CTK = 'BUI DUC ANH'
PROXY_PRICE = 1500
OTP_PRICE = 2500
SERVICE_ID_OTP = 49 

# Khởi tạo Bot và Database
bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db # Giữ đúng tên db cũ của bạn
users_col = db.users
orders_col = db.orders

# 2. Flask Server để Koyeb không báo lỗi Unhealthy
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

# 3. Menu chính (Khôi phục giao diện hôm qua)
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

# --- 4. XỬ LÝ LỆNH ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    now = datetime.now().strftime("%d/%m/%Y")
    users_col.update_one({"user_id": user_id}, {"$set": {"first_name": message.from_user.first_name}, "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}}, upsert=True)
    bot.send_message(message.chat.id, f"👋 Chào mừng {message.from_user.first_name}!\n⚡ Hệ thống Proxy & OTP tự động 24/7.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    msg = (f"✨ **THÔNG TIN CÁ NHÂN** ✨\n\n"
           f"👤 Tên khách hàng: {u.get('first_name')}\n"
           f"🆔 ID của bạn: `{message.from_user.id}`\n"
           f"📅 Ngày gia nhập: {u.get('join_date')}\n"
           f"--------------------------\n"
           f"💰 Số dư: {u.get('balance', 0):,} VNĐ\n"
           f"📥 Tổng nạp: {u.get('total_deposit', 0):,} VNĐ\n"
           f"📤 Tổng chi: {u.get('total_spent', 0):,} VNĐ")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    try: bot.send_message(ADMIN_ID, f"🔔 **KHÁCH XEM NẠP TIỀN**\n👤: {message.from_user.first_name}\n🆔: `{user_id}`")
    except: pass
    memo = f"naptien {random.randint(10,99)}{user_id}"
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    bot.send_photo(message.chat.id, qr_url, caption=f"📌 Nội dung chuyển khoản: `{memo}`\n💰 Tối thiểu 20k.")

@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 PROXY (1.5k)", callback_data="buy_proxy"),
               types.InlineKeyboardButton("📲 NHẬN OTP (2.5k)", callback_data="buy_otp"))
    bot.send_message(message.chat.id, "🛒 Chọn loại dịch vụ:", reply_markup=markup)

# --- 5. LOGIC XỬ LÝ OTP (Đa luồng để không treo bot) ---

def check_otp(user_id, sim_id, phone, msg_id):
    for _ in range(24):
        time.sleep(5)
        try:
            url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={sim_id}&api_key={API_KEY_SIM}"
            res = requests.get(url).json()
            if res.get('success') and res.get('data'):
                code = res['data']['sms_content']
                bot.edit_message_text(f"✅ OTP: `{code}`\n📞 Số: `{phone}`", user_id, msg_id)
                orders_col.insert_one({"user_id": user_id, "type": "OTP", "data": f"{phone}|{code}", "date": datetime.now()})
                return
        except: pass
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": OTP_PRICE}})
    bot.send_message(user_id, f"🔄 Đã hoàn {OTP_PRICE}đ cho số {phone}")

@bot.callback_query_handler(func=lambda call: call.data == "buy_otp")
def otp_process(call):
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})
    if u['balance'] < OTP_PRICE:
        bot.answer_callback_query(call.id, "❌ Không đủ tiền!", show_alert=True)
        return
    url = f"https://apisim.codesim.net/sim/get_sim?service_id={SERVICE_ID_OTP}&api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('success'):
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -OTP_PRICE}})
            data = res['data']
            sim_id, phone = data['id'], data['phone_number']
            bot.edit_message_text(f"📲 Số: `{phone}`\n⏳ Đang đợi OTP...", call.message.chat.id, call.message.message_id)
            threading.Thread(target=check_otp, args=(user_id, sim_id, phone, call.message.message_id)).start()
        else: bot.edit_message_text(f"❌ Lỗi: {res.get('message', 'Hết số')}", call.message.chat.id, call.message.message_id)
    except: bot.edit_message_text("❌ Lỗi kết nối API!", call.message.chat.id, call.message.message_id)

# --- 6. KHỞI CHẠY ĐA LUỒNG ---

def run_web():
    app.run(host='0.0.0.0', port=8000)

if __name__ == "__main__":
    # Chạy Web server ở luồng riêng
    threading.Thread(target=run_web).start()
    
    # Chạy Bot chính
    print("Bot đang khởi động với đầy đủ tính năng...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=40)
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(5)
