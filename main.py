import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
from datetime import datetime
import requests
import random
import time

# --- CẤU HÌNH HỆ THỐNG ---
TOKEN = '8371917325:AAHN1yl83Nzzb7NjrhEiEq6VRVr6c3SXX7w' # Token mới bạn vừa gửi
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'

ADMIN_ID = 5519768222 # ID Admin của bạn
PROXY_PRICE = 1500
OTP_PRICE = 2500
SERVICE_ID_OTP = 49 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users
orders_col = db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is running with New Token!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- TIỆN ÍCH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

# --- LỆNH START ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    now = datetime.now().strftime("%d/%m/%Y")
    users_col.update_one({"user_id": user_id}, {"$set": {"first_name": message.from_user.first_name}, "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}}, upsert=True)
    bot.send_message(message.chat.id, f"👋 Chào mừng {message.from_user.first_name}!\n⚡ Hệ thống Proxy & OTP tự động 24/7.", reply_markup=main_menu())

# --- NẠP TIỀN & THÔNG BÁO ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    try:
        bot.send_message(ADMIN_ID, f"🔔 **KHÁCH XEM NẠP TIỀN**\n👤: {message.from_user.first_name}\n🆔: `{user_id}`")
    except: pass
    memo = f"nap{random.randint(10,99)}{user_id}"
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    bot.send_photo(message.chat.id, qr_url, caption=f"💳 **NẠP TIỀN TỰ ĐỘNG**\n\n📌 Nội dung: `{memo}`\n💰 Đợi Admin cộng tiền sau khi chuyển khoản.")

# --- CỘNG TIỀN + CẢM ƠN ---
@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt), "total_deposit": int(amt)}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt} cho {tid}")
        bot.send_message(int(tid), f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n💰 Số dư: +`{int(amt):,} VND`\n🙏 Cảm ơn bạn đã tin tưởng sử dụng dịch vụ!")
    except: pass

# --- XỬ LÝ OTP (THEO API BẠN GỬI) ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📲 THUÊ OTP (2.5k)", callback_data="buy_otp"))
    bot.send_message(message.chat.id, "🛒 Chọn dịch vụ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_otp")
def otp_buy(call):
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})
    if u['balance'] < OTP_PRICE:
        bot.answer_callback_query(call.id, "❌ Không đủ tiền!", show_alert=True)
        return

    # Mục 4: Lấy số
    url = f"https://apisim.codesim.net/sim/get_sim?service_id={SERVICE_ID_OTP}&api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('success'):
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -OTP_PRICE}})
            sim_id = res['data']['id']
            phone = res['data']['phone_number']
            bot.edit_message_text(f"📲 Số: `{phone}`\n⏳ Đang đợi OTP...", call.message.chat.id, call.message.message_id)
            threading.Thread(target=check_otp_loop, args=(user_id, sim_id, phone, call.message.message_id)).start()
        else:
            bot.edit_message_text(f"❌ Lỗi: {res.get('message')}", call.message.chat.id, call.message.message_id)
    except:
        bot.edit_message_text("❌ Lỗi kết nối API!", call.message.chat.id, call.message.message_id)

def check_otp_loop(user_id, sim_id, phone, msg_id):
    for _ in range(24): # Đợi 2 phút
        time.sleep(5)
        try:
            # Mục 5: Kiểm tra OTP
            url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={sim_id}&api_key={API_KEY_SIM}"
            res = requests.get(url).json()
            if res.get('success') and res.get('data'):
                code = res['data']['sms_content']
                bot.edit_message_text(f"✅ OTP: `{code}`\n📞 Số: `{phone}`", user_id, msg_id)
                return
        except: pass
    # Mục 6: Hủy và hoàn tiền nếu hết thời gian
    requests.get(f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}")
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": OTP_PRICE}})
    bot.send_message(user_id, f"🔄 Hoàn tiền {OTP_PRICE}đ cho số {phone}")

# --- VÒNG LẶP KHỞI CHẠY ---
def run_bot():
    while True:
        try:
            bot.remove_webhook() # Xóa sạch Webhook cũ để tránh lỗi Conflict 409
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
