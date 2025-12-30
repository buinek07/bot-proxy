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
TOKEN = '8371917325:AAHN1yl83Nzzb7NjrhEiEq6VRVr6c3SXX7w' # HÃY KIỂM TRA LẠI TOKEN NÀY
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'
ADMIN_ID = 5519768222 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

app = Flask('')
@app.route('/')
def home(): return "Bot OTP System is Online"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- MỤC 1: LẤY THÔNG TIN TÀI KHOẢN API ---
def get_api_info():
    url = f"https://apisim.codesim.net/yourself/information-by-api-key?api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 200:
            return res['data'] # Trả về id, phone, balance, username
    except: return None

# --- MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Thuê OTP', '💳 Nạp tiền', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "⚡ Hệ thống cho thuê số OTP tự động 24/7", reply_markup=main_menu())

# --- MỤC 2: HIỂN THỊ DỊCH VỤ ---
@bot.message_handler(func=lambda m: m.text == '🛒 Thuê OTP')
def show_services(message):
    url = f"https://apisim.codesim.net/service/get_service_by_api_key?api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 200:
            markup = types.InlineKeyboardMarkup()
            # Hiển thị danh sách dịch vụ (Mục 2)
            for s in res['data'][:8]: # Hiển thị 8 cái đầu tiên
                markup.add(types.InlineKeyboardButton(f"{s['name']} - {s['price']}đ", callback_data=f"otp_{s['id']}_{s['price']}"))
            bot.send_message(message.chat.id, "✨ Chọn dịch vụ nhận mã:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ Lỗi kết nối API lấy dịch vụ.")

# --- MỤC 4, 5, 6: QUY TRÌNH THUÊ SỐ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('otp_'))
def handle_otp_request(call):
    _, s_id, price = call.data.split('_')
    price = int(price)
    user_id = call.from_user.id
    
    user = users_col.find_one({"user_id": user_id})
    if not user or user.get('balance', 0) < price:
        bot.answer_callback_query(call.id, "❌ Bạn không đủ tiền trên bot!", show_alert=True)
        return

    # Mục 4: Lấy số điện thoại
    api_url = f"https://apisim.codesim.net/sim/get_sim?service_id={s_id}&api_key={API_KEY_SIM}"
    try:
        res = requests.get(api_url).json()
        if res.get('status') == 200:
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -price}})
            data = res['data']
            otp_id, sim_id, phone = data['otpId'], data['simId'], data['phone']
            
            bot.edit_message_text(f"📞 Số: `{phone}`\n⏳ Đang đợi mã OTP...", call.message.chat.id, call.message.message_id)
            # Luồng kiểm tra mã (Mục 5)
            threading.Thread(target=otp_worker, args=(user_id, otp_id, sim_id, phone, call.message.message_id, price)).start()
        else:
            bot.answer_callback_query(call.id, f"❌ {res.get('message')}", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Lỗi hệ thống lấy số.", show_alert=True)

def otp_worker(user_id, otp_id, sim_id, phone, msg_id, price):
    for _ in range(30): # Thử lại trong ~2 phút
        time.sleep(5) # Mục 5: Độ trễ tối thiểu 4s/lần
        check_url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={otp_id}&api_key={API_KEY_SIM}"
        try:
            res = requests.get(check_url).json()
            if res.get('status') == 200 and res.get('data'):
                otp_code = res['data']['code']
                bot.edit_message_text(f"✅ **MÃ OTP: {otp_code}**\n📞 Số: `{phone}`", user_id, msg_id)
                return
        except: pass
    
    # Mục 6: Hủy nếu hết thời gian và hoàn tiền
    requests.get(f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}")
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": price}})
    bot.send_message(user_id, f"🔄 Đã hoàn {price}đ vì không nhận được mã cho số {phone}.")

# --- ADMIN & NẠP TIỀN ---
@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    bal = u.get('balance', 0) if u else 0
    bot.reply_to(message, f"👤 Tên: {message.from_user.first_name}\n💰 Số dư: `{bal:,} VND`", parse_mode="Markdown")

@bot.message_handler(commands=['plus'])
def plus(message):
    if message.from_user.id == ADMIN_ID:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt)}})
        bot.send_message(int(tid), f"🎉 Bạn được cộng `{int(amt):,}đ`. Cảm ơn bạn!")
        bot.send_message(ADMIN_ID, f"✅ Đã cộng cho {tid}")

# --- VÒNG LẶP DUY TRÌ ---
while True:
    try:
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1, timeout=20)
    except: time.sleep(5)
