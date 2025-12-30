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
TOKEN = '8371917325:AAHN1yl83Nzzb7NjrhEiEq6VRVr6c3SXX7w'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'
ADMIN_ID = 5519768222 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col = db.users

# Server giữ bot sống trên Koyeb
app = Flask('')
@app.route('/')
def home(): return "Bot OTP System is Healthy!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- MỤC 1: LẤY THÔNG TIN TÀI KHOẢN (API BALANCE) ---
def get_api_balance():
    url = f"https://apisim.codesim.net/yourself/information-by-api-key?api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 200:
            return res['data']['balance']
    except: return "N/A"

# --- MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Thuê OTP', '💳 Nạp tiền', '📞 Admin')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Chào mừng bạn đến với hệ thống thuê OTP tự động!", reply_markup=main_menu())

# --- MỤC 2 & 4: DANH SÁCH DỊCH VỤ VÀ THUÊ SỐ ---
@bot.message_handler(func=lambda m: m.text == '🛒 Thuê OTP')
def list_services(message):
    # Lấy danh sách dịch vụ (Mục 2)
    url = f"https://apisim.codesim.net/service/get_service_by_api_key?api_key={API_KEY_SIM}"
    try:
        res = requests.get(url).json()
        if res.get('status') == 200:
            markup = types.InlineKeyboardMarkup()
            # Hiển thị 10 dịch vụ đầu tiên để tránh menu quá dài
            for s in res['data'][:10]:
                markup.add(types.InlineKeyboardButton(f"{s['name']} - {s['price']}đ", callback_data=f"buy_{s['id']}_{s['price']}"))
            bot.send_message(message.chat.id, "✨ Chọn dịch vụ muốn thuê số:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ Lỗi lấy danh sách dịch vụ.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_buy(call):
    _, s_id, price = call.data.split('_')
    user_id = call.from_user.id
    user = users_col.find_one({"user_id": user_id})
    
    if not user or user.get('balance', 0) < int(price):
        bot.answer_callback_query(call.id, "❌ Tài khoản Bot không đủ tiền!", show_alert=True)
        return

    # Mục 4: Lấy số điện thoại
    get_url = f"https://apisim.codesim.net/sim/get_sim?service_id={s_id}&api_key={API_KEY_SIM}"
    try:
        res = requests.get(get_url).json()
        if res.get('status') == 200:
            data = res['data']
            # Trừ tiền trên Bot trước
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -int(price)}})
            
            msg = bot.edit_message_text(f"📞 Số: `{data['phone']}`\n⏳ Trạng thái: **Đang đợi mã OTP...**", 
                                        call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            # Chạy luồng kiểm tra (Mục 5)
            threading.Thread(target=check_otp_worker, args=(user_id, data['otpId'], data['simId'], data['phone'], msg.message_id, int(price))).start()
        else:
            bot.answer_callback_query(call.id, f"❌ {res.get('message')}", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ Lỗi kết nối API lấy số.", show_alert=True)

# --- MỤC 5 & 6: KIỂM TRA MÃ VÀ HỦY SỐ ---
def check_otp_worker(user_id, otp_id, sim_id, phone, msg_id, price):
    for _ in range(24): # Thử lại mỗi 5s trong vòng 2 phút
        time.sleep(5) # Mục 5: Độ trễ tối thiểu 4s/lần
        check_url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={otp_id}&api_key={API_KEY_SIM}"
        try:
            res = requests.get(check_url).json()
            if res.get('status') == 200 and res.get('data'):
                otp_code = res['data']['code']
                bot.edit_message_text(f"✅ **NHẬN MÃ THÀNH CÔNG**\n📞 Số: `{phone}`\n📩 Mã OTP: `{otp_code}`", user_id, msg_id, parse_mode="Markdown")
                return
        except: pass
    
    # Mục 6: Hủy số và hoàn tiền nếu hết 2 phút không có mã
    cancel_url = f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}"
    requests.get(cancel_url)
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": price}})
    bot.send_message(user_id, f"🔄 Đã hoàn {price}đ cho số {phone} do không nhận được mã.")

# --- TÀI KHOẢN & NẠP TIỀN ---
@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    bal = u.get('balance', 0) if u else 0
    bot.reply_to(message, f"👤 Khách hàng: {message.from_user.first_name}\n💰 Số dư: `{bal:,} VND`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    memo = f"nap{random.randint(10,99)}{message.from_user.id}"
    qr = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    bot.send_photo(message.chat.id, qr, caption=f"💳 **NẠP TIỀN TỰ ĐỘNG**\n\n🏦 MBBank: `700122`\n📌 Nội dung: `{memo}`\n⚠️ Đợi Admin duyệt sau khi CK.")
    bot.send_message(ADMIN_ID, f"🔔 Khách `{message.from_user.id}` đang xem nạp tiền.")

@bot.message_handler(commands=['plus'])
def admin_plus(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt)}})
        bot.send_message(int(tid), f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n💰 +`{int(amt):,}`đ. 🙏 Cảm ơn bạn!")
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt} cho {tid}")
    except: pass

# --- VÒNG LẶP DUY TRÌ ---
while True:
    try:
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1, timeout=30)
    except:
        time.sleep(5)
