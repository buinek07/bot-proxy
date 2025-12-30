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
TOKEN = '8371917325:AAHN1yl83Nzzb7NjrhEiEq6VRVr6c3SXX7w'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'
ADMIN_ID = 5519768222 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- 1. LẤY THÔNG TIN TÀI KHOẢN API ---
def get_api_balance():
    url = f"https://apisim.codesim.net/yourself/information-by-api-key?api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 200:
            return res['data']['balance']
    except: return 0

# --- MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Thuê OTP', '💳 Nạp tiền', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Chào mừng bạn đến với dịch vụ OTP tự động!", reply_markup=main_menu())

# --- XỬ LÝ THUÊ OTP (MỤC 2 & 4) ---
@bot.message_handler(func=lambda m: m.text == '🛒 Thuê OTP')
def list_services(message):
    # Lấy danh sách dịch vụ (Mục 2)
    url = f"https://apisim.codesim.net/service/get_service_by_api_key?api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 200:
            markup = types.InlineKeyboardMarkup()
            # Hiển thị 5 dịch vụ tiêu biểu để tránh menu quá dài
            for s in res['data'][:10]:
                markup.add(types.InlineKeyboardButton(f"{s['name']} - {s['price']}đ", callback_data=f"buy_{s['id']}_{s['price']}"))
            bot.send_message(message.chat.id, "✅ Chọn dịch vụ bạn muốn thuê:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ Không thể lấy danh sách dịch vụ lúc này.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_buy(call):
    _, s_id, price = call.data.split('_')
    user_id = call.from_user.id
    user = users_col.find_one({"user_id": user_id})
    
    if not user or user.get('balance', 0) < int(price):
        bot.answer_callback_query(call.id, "❌ Số dư tài khoản Bot không đủ!", show_alert=True)
        return

    # Mục 4: Lấy số điện thoại
    get_sim_url = f"https://apisim.codesim.net/sim/get_sim?service_id={s_id}&api_key={API_KEY_SIM}"
    try:
        res = requests.get(get_sim_url).json()
        if res.get('status') == 200:
            data = res['data']
            otp_id = data['otpId']
            sim_id = data['simId']
            phone = data['phone']
            
            # Trừ tiền tài khoản người dùng trên Bot
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -int(price)}})
            
            msg = bot.edit_message_text(f"📲 Số của bạn: `{phone}`\n⏳ Đang đợi mã OTP (tối đa 2 phút)...", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            # Chạy luồng kiểm tra mã (Mục 5)
            threading.Thread(target=wait_for_otp, args=(user_id, otp_id, sim_id, phone, msg.message_id, int(price))).start()
        else:
            bot.answer_callback_query(call.id, f"❌ Lỗi: {res.get('message')}", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Lỗi kết nối máy chủ OTP.", show_alert=True)

# --- 5 & 6. KIỂM TRA MÃ VÀ HỦY SỐ ---
def wait_for_otp(user_id, otp_id, sim_id, phone, msg_id, price):
    # Kiểm tra mỗi 5 giây trong 2 phút (Mục 5 yêu cầu độ trễ tối thiểu 4s)
    for _ in range(24): 
        time.sleep(5)
        check_url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={otp_id}&api_key={API_KEY_SIM}"
        try:
            res = requests.get(check_url).json()
            if res.get('status') == 200 and res.get('data'):
                otp_code = res['data']['code']
                bot.edit_message_text(f"✅ **CÓ MÃ OTP!**\n📞 Số: `{phone}`\n📩 Mã: `{otp_code}`", user_id, msg_id, parse_mode="Markdown")
                return
        except: pass
    
    # Nếu hết thời gian mà không có mã -> Hủy số (Mục 6) và hoàn tiền
    cancel_url = f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}"
    requests.get(cancel_url)
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": price}})
    bot.send_message(user_id, f"🔄 Không nhận được mã cho số {phone}. Đã hoàn lại {price}đ vào tài khoản.")

# --- NẠP TIỀN & ADMIN ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def deposit(message):
    memo = f"nap{random.randint(10,99)}{message.from_user.id}"
    qr = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    bot.send_photo(message.chat.id, qr, caption=f"📌 Nội dung chuyển khoản: `{memo}`\n💰 Đợi admin cộng tiền.")
    bot.send_message(ADMIN_ID, f"🔔 Khách {message.from_user.first_name} ({message.from_user.id}) đang xem nạp tiền.")

@bot.message_handler(commands=['plus'])
def admin_plus(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt)}})
        bot.send_message(int(tid), f"🎉 **NẠP THÀNH CÔNG!**\n💰 +`{int(amt):,} VND`\n🙏 Cảm ơn bạn đã tin tưởng!")
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt} cho {tid}")
    except: pass

# --- KHỞI CHẠY ---
while True:
    try:
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1, timeout=20)
    except:
        time.sleep(5)
