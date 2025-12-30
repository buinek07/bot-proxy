import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
from datetime import datetime, timedelta
import requests
import random
import time

# --- CẤU HÌNH HỆ THỐNG ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'

# Cấu hình Admin và Ngân hàng
ADMIN_ID = 5519768222 
BANK_ID = 'MB'
STK_MOI = '700122'
TEN_CTK = 'BUI DUC ANH'

# Giá dịch vụ
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
def home(): return "Bot is running!"
def run_web(): app.run(host='0.0.0.0', port=8000)
threading.Thread(target=run_web).start()

# --- MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

def generate_random_memo(user_id):
    prefixes = ['tiencafe', 'tienche', 'uongnuoc', 'naptien', 'muaproxy', 'banh mi', 'cafe']
    return f"{random.choice(prefixes)} {random.randint(10,99)}{user_id}"

# --- LỆNH KHỞI ĐẦU ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    now = datetime.now().strftime("%d/%m/%Y")
    users_col.update_one({"user_id": user_id}, {"$set": {"first_name": message.from_user.first_name}, "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}}, upsert=True)
    bot.send_message(message.chat.id, f"👋 **Chào mừng {message.from_user.first_name}!**\n⚡ Hệ thống cung cấp Proxy & OTP tự động 24/7.", reply_markup=main_menu(), parse_mode="Markdown")

# --- QUẢN LÝ TÀI KHOẢN ---
@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    msg = (f"🌟 **THÔNG TIN CÁ NHÂN** 🌟\n\n"
           f"👤 Tên khách hàng: **{u.get('first_name')}**\n"
           f"🆔 ID của bạn: `{u['user_id']}`\n"
           f"📅 Ngày gia nhập: {u.get('join_date')}\n"
           f"──────────────────\n"
           f"💰 Số dư khả dụng: `{u.get('balance', 0):,} VND`\n"
           f"📈 Tổng nạp: `{u.get('total_deposit', 0):,} VND`\n"
           f"💸 Tổng đã chi tiêu: `{u.get('total_spent', 0):,} VND`\n\n"
           f"💡 *Nạp thêm tiền để trải nghiệm dịch vụ tốt hơn!*")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- MUA HÀNG ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop_category(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🌐 PROXY SIÊU TỐC", callback_data="cat_proxy"),
               types.InlineKeyboardButton("📲 THUÊ OTP GIÁ RẺ", callback_data="cat_otp"))
    
    msg = ("🛒 **CỬA HÀNG DỊCH VỤ**\n\nVui lòng chọn loại dịch vụ bạn muốn trải nghiệm bên dưới:\n\n"
           "🔹 **Proxy:** Proxy tĩnh tốc độ cao, ổn định, hỗ trợ đa nhà mạng.\n"
           "🔹 **Thuê OTP:** Nhận mã nhanh chóng, hoàn tiền nếu chưa nhận được mã.")
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

# Menu Proxy
@bot.callback_query_handler(func=lambda call: call.data == "cat_proxy")
def proxy_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📡 Viettel", callback_data="pre_Viettel"),
               types.InlineKeyboardButton("📡 VNPT", callback_data="pre_VNPT"),
               types.InlineKeyboardButton("📡 FPT", callback_data="pre_FPT"))
    markup.add(types.InlineKeyboardButton("⬅️ Quay lại Menu", callback_data="back_to_shop"))
    bot.edit_message_text("🌐 **DANH SÁCH PROXY TĨNH**\n\n💎 Giá bán: **1.500đ / 1**\n⚡ Thời gian sử dụng: 24h.\n\nVui lòng chọn nhà mạng:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Menu OTP
@bot.callback_query_handler(func=lambda call: call.data == "cat_otp")
def otp_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 Nhận OTP - 2.500đ", callback_data="pre_OTP"))
    markup.add(types.InlineKeyboardButton("⬅️ Quay lại Menu", callback_data="back_to_shop"))
    bot.edit_message_text("📲 **DỊCH VỤ NHẬN OTP TỰ ĐỘNG**\n\n✨ Giá mỗi mã: **2.500đ**\n⚠️ *Lưu ý: Hệ thống chỉ tính phí khi nhận mã thành công!*", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# --- XÁC NHẬN THANH TOÁN ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pre_"))
def pre_pay(call):
    user_id = call.from_user.id
    u = users_col.find_one({"user_id": user_id})
    service = call.data.split("_")[1]
    price = PROXY_PRICE if service != "OTP" else OTP_PRICE
    item_name = f"Proxy {service}" if service != "OTP" else "Dịch vụ Nhận OTP"
    
    text = (f"💳 **XÁC NHẬN THANH TOÁN**\n──────────────────\n"
            f"📦 Sản phẩm: **{item_name}**\n"
            f"💰 Giá dịch vụ: `{price:,} VND`\n"
            f"💵 Số dư của bạn: `{u.get('balance', 0):,} VND`\n──────────────────\n"
            f"❓ Bạn có muốn tiến hành thanh toán không?")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Xác nhận", callback_data=f"pay_{service}"),
               types.InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# --- XỬ LÝ THANH TOÁN ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_payment(call):
    user_id = call.from_user.id
    service = call.data.split("_")[1]
    price = PROXY_PRICE if service != "OTP" else OTP_PRICE
    u = users_col.find_one({"user_id": user_id})

    if u.get('balance', 0) < price:
        bot.answer_callback_query(call.id, "❌ Tài khoản không đủ số dư!", show_alert=True)
        return

    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -price, "total_spent": price}})

    if service != "OTP":
        api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={service}&key={API_KEY_PROXY}&soluong=1&ngay=1&type=HTTP&user=random&password=random"
        try:
            res = requests.get(api_url).text
            if "error" in res.lower(): raise Exception()
            orders_col.insert_one({"user_id": user_id, "isp": service, "data": res, "date": datetime.now()})
            bot.edit_message_text(f"✅ **GIAO DỊCH THÀNH CÔNG**\n\n🛰 Sản phẩm: Proxy {service}\n🔑 Thông tin: `{res}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except:
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": price, "total_spent": -price}})
            bot.edit_message_text("❌ Lỗi API. Đã hoàn lại tiền!", call.message.chat.id, call.message.message_id)
    else:
        api_get_sim = f"https://apisim.codesim.net/sim/get_sim?service_id={SERVICE_ID_OTP}&api_key={API_KEY_SIM}"
        try:
            res = requests.get(api_get_sim).json()
            if res.get('success'):
                sim_data = res.get('data')
                sim_id, phone = sim_data.get('id'), sim_data.get('phone_number')
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🚫 Hủy số & Hoàn tiền", callback_data=f"cancel_sim_{sim_id}_{price}"))
                bot.edit_message_text(f"📲 **LẤY SỐ THÀNH CÔNG**\n\n📞 Số điện thoại: `{phone}`\n⏳ Trạng thái: **Đang chờ mã OTP...**\n\n⚠️ *Tự động hoàn tiền sau 2 phút nếu không có mã.*", 
                                      call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
                threading.Thread(target=check_otp_logic, args=(user_id, sim_id, phone, price, call.message.message_id)).start()
            else: raise Exception()
        except:
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": price, "total_spent": -price}})
            bot.edit_message_text("❌ Lỗi kho số. Đã hoàn lại tiền!", call.message.chat.id, call.message.message_id)

# --- LOGIC OTP & HOÀN TIỀN ---
def check_otp_logic(user_id, sim_id, phone, price, msg_id):
    timeout = time.time() + 120
    success = False
    while time.time() < timeout:
        try:
            check_url = f"https://apisim.codesim.net/otp/get_otp_by_phone_api_key?otp_id={sim_id}&api_key={API_KEY_SIM}"
            res = requests.get(check_url).json()
            if res.get('success') and res.get('data'):
                otp_code = res.get('data').get('sms_content')
                bot.edit_message_text(f"✅ **NHẬN MÃ THÀNH CÔNG**\n\n📞 Số: `{phone}`\n📩 Mã OTP: `{otp_code}`", user_id, msg_id, parse_mode="Markdown")
                orders_col.insert_one({"user_id": user_id, "isp": "OTP", "data": f"Số: {phone} | Mã: {otp_code}", "date": datetime.now()})
                success = True; break
        except: pass
        time.sleep(5)

    if not success:
        requests.get(f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}")
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": price, "total_spent": -price}})
        bot.send_message(user_id, f"🔄 **HOÀN TIỀN:** Không nhận được mã cho số `{phone}`. `{price:,}đ` đã được hoàn trả.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_sim_"))
def cancel_sim_manual(call):
    _, _, sim_id, price = call.data.split("_")
    requests.get(f"https://apisim.codesim.net/sim/cancel_api_key/{sim_id}?api_key={API_KEY_SIM}")
    users_col.update_one({"user_id": call.from_user.id}, {"$inc": {"balance": int(price), "total_spent": -int(price)}})
    bot.edit_message_text(f"🚫 **ĐÃ HỦY:** Giao dịch đã dừng và hoàn lại `{int(price):,}đ`.", call.message.chat.id, call.message.message_id)

# --- NẠP TIỀN & ĐƠN HÀNG ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    memo = generate_random_memo(message.from_user.id)
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{STK_MOI}-compact2.jpg?amount=20000&addInfo={memo}"
    caption = (f"💳 **THÔNG TIN NẠP TIỀN TỰ ĐỘNG**\n\n🏦 Ngân hàng: **MBBank**\n📝 STK: `{STK_MOI}`\n👤 CTK: **{TEN_CTK}**\n\n"
               f"💰 Tối thiểu: `20,000 VND`\n📌 Nội dung: `{memo}`\n\n📩 Hỗ trợ: @buinek")
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '📋 Đơn hàng')
def order_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔍 Xem đơn hàng Proxy/OTP", callback_data="view_orders"))
    bot.send_message(message.chat.id, "📋 **QUẢN LÝ ĐƠN HÀNG**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "view_orders")
def view_orders(call):
    orders = list(orders_col.find({"user_id": call.from_user.id}).sort("date", -1).limit(5))
    if not orders:
        bot.answer_callback_query(call.id, "❌ Bạn chưa có đơn hàng!", show_alert=True); return
    msg = "🛒 **ĐƠN HÀNG GẦN ĐÂY**\n\n"
    for o in orders:
        msg += f"📅 `{o['date'].strftime('%H:%M %d/%m')}` | **{o['isp']}**\n🔑 `{o['data']}`\n\n"
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# --- LỆNH ADMIN + CẢM ƠN ---
@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        amt_int = int(amt)
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": amt_int, "total_deposit": amt_int}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {amt_int:,}đ cho ID {tid}")
        
        # Tin nhắn cảm ơn khách hàng
        thanks_msg = (f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n"
                      f"──────────────────\n"
                      f"💰 Bạn vừa được cộng: `{amt_int:,} VND`\n"
                      f"🙏 **Cảm ơn bạn đã tin tưởng sử dụng dịch vụ!**\n\n"
                      f"🚀 Bạn có thể bắt đầu mua Proxy hoặc nhận OTP ngay.")
        bot.send_message(int(tid), thanks_msg, parse_mode="Markdown")
    except:
        bot.send_message(ADMIN_ID, "❌ Lỗi. Cú pháp: /plus [ID] [Số tiền]")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_action(call): bot.edit_message_text("❌ Giao dịch đã bị hủy.", call.message.chat.id, call.message.message_id)
@bot.callback_query_handler(func=lambda call: call.data == "back_to_shop")
def back_to_shop(call): shop_category(call.message); bot.delete_message(call.message.chat.id, call.message.message_id)

bot.polling(none_stop=True)
