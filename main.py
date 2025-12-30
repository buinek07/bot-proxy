import telebot
from telebot import types
from pymongo import MongoClient
from flask import Flask
import threading
from datetime import datetime, timedelta
import requests
import random

# --- CẤU HÌNH ---
TOKEN = '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'

ADMIN_ID = 5698547214 
BANK_ID = 'MB'
STK_MOI = '700122'
TEN_CTK = 'BUI DUC ANH'
PROXY_PRICE = 1500

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

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

def generate_random_memo(user_id):
    prefixes = ['tiencafe', 'tienche', 'uongnuoc', 'naptien', 'muaproxy', 'banh mi', 'cafe']
    return f"{random.choice(prefixes)} {random.randint(10,99)}{user_id}"

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name if message.from_user.first_name else "Khách hàng"
    now = datetime.now().strftime("%d/%m/%Y")
    users_col.update_one({"user_id": user_id}, {"$set": {"first_name": first_name}, "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}}, upsert=True)
    bot.send_message(message.chat.id, "🤖 **Bot Proxy đã sẵn sàng!**", reply_markup=main_menu(), parse_mode="Markdown")

# --- PHẦN ĐƠN HÀNG ---
@bot.message_handler(func=lambda m: m.text == '📋 Đơn hàng')
def order_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛒 Đơn hàng Proxy", callback_data="view_orders"))
    bot.send_message(message.chat.id, "📋 **Quản lý đơn hàng của bạn:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "view_orders")
def view_orders(call):
    user_id = call.from_user.id
    # Lấy 10 đơn hàng gần nhất
    orders = list(orders_col.find({"user_id": user_id}).sort("date", -1).limit(10))
    
    if not orders:
        bot.answer_callback_query(call.id, "❌ bạn chưa mua đơn hàng nào!", show_alert=True)
        return

    msg = "🛒 **DANH SÁCH PROXY ĐÃ MUA**\n\n"
    for idx, order in enumerate(orders, 1):
        buy_date = order['date']
        # Tính thời gian hết hạn (24h kể từ khi mua)
        expire_date = buy_date + timedelta(hours=24)
        time_left = expire_date - datetime.now()
        
        if time_left.total_seconds() > 0:
            hours, remainder = divmod(time_left.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            status = f"✅ Còn: {int(hours)}h {int(minutes)}m"
        else:
            status = "❌ Đã hết hạn"

        msg += (f"{idx}. **{order['isp']}** | {status}\n"
                f"🌐 IP: `{order['data']}`\n"
                f"📅 _Mua lúc: {buy_date.strftime('%H:%M %d/%m')}_\n\n")

    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# --- PHẦN NẠP TIỀN GIAO DIỆN MỚI ---
@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    memo = generate_random_memo(user_id)
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{STK_MOI}-compact2.jpg?amount=20000&addInfo={memo}"
    
    caption = (f"💳 **THÔNG TIN NẠP TIỀN**\n\n"
               f"🏦 **Ngân hàng:** MBBank\n"
               f"📝 **Số tài khoản:** `{STK_MOI}`\n"
               f"👤 **Chủ tài khoản:** {TEN_CTK}\n\n"
               f"💰 **Số tiền tối thiểu:** `20,000 VND`\n\n"
               f"📌 **Nội dung chuyển khoản:**\n`{memo}`\n\n"
               f"⚠️ **Lưu ý quan trọng:**\n"
               f"• 📸 Quét mã QR để chuyển khoản nhanh chóng.\n"
               f"• ✍️ Ghi chính xác nội dung chuyển khoản.\n"
               f"• ⛔ Chuyển dưới 20,000đ sẽ không được cộng tiền.\n"
               f"• 📩 Hỗ trợ nạp tiền: @buinek\n\n"
               f"*(Hỗ trợ nếu sau 30p chưa cộng tiền)*")
    bot.send_photo(message.chat.id, qr_url, caption=caption, parse_mode="Markdown")

# --- CÁC PHẦN KHÁC (Tài khoản, Mua hàng, Plus) ---
@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    if u:
        msg = (f"👤 **Thông tin tài khoản**\n\n👤 Tên: **{u.get('first_name')}**\n🆔 ID: `{u['user_id']}`\n"
               f"📅 Ngày tham gia: {u.get('join_date')}\n\n💰 Số dư: {u.get('balance', 0):,} VND\n"
               f"📊 Tổng nạp: {u.get('total_deposit', 0):,} VND\n💸 Tổng chi: {u.get('total_spent', 0):,} VND")
        bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🌐 Viettel", callback_data="buy_Viettel"),
               types.InlineKeyboardButton("🌐 VNPT", callback_data="buy_VNPT"),
               types.InlineKeyboardButton("🌐 FPT", callback_data="buy_FPT"))
    bot.send_message(message.chat.id, f"✨ **Chọn nhà mạng ({PROXY_PRICE:,}đ/24h):**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def confirm_purchase(call):
    isp = call.data.split("_")[1]
    text = f"⚠️ **XÁC NHẬN THANH TOÁN**\n\n📦 Sản phẩm: Proxy {isp}\n💰 Giá: {PROXY_PRICE:,} VND\n⏳ Thời hạn: 24 Giờ"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Thanh toán", callback_data=f"pay_{isp}"),
               types.InlineKeyboardButton("❌ Hủy bỏ", callback_data="cancel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_payment(call):
    user_id = call.from_user.id
    isp = call.data.split("_")[1]
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data or user_data.get('balance', 0) < PROXY_PRICE:
        bot.answer_callback_query(call.id, "❌ Số dư không đủ!", show_alert=True)
        return
    api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={isp}&key={API_KEY_PROXY}&soluong=1&ngay=1&type=HTTP&user=random&password=random"
    try:
        response = requests.get(api_url).text
        if "error" in response.lower() or "không đủ" in response.lower():
            bot.send_message(user_id, "❌ Kho hàng hết hoặc lỗi hệ thống.")
            return
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -PROXY_PRICE, "total_spent": PROXY_PRICE}})
        orders_col.insert_one({"user_id": user_id, "isp": isp, "data": response, "date": datetime.now()})
        bot.edit_message_text(f"✅ **THÀNH CÔNG!**\n\n📦 Loại: Proxy {isp}\n🌐 IP: `{response}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"💰 Khách {user_id} mua {isp}")
    except: bot.send_message(user_id, "❌ Lỗi kết nối API.")

@bot.message_handler(commands=['plus'])
def plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        users_col.update_one({"user_id": int(tid)}, {"$inc": {"balance": int(amt), "total_deposit": int(amt)}})
        bot.send_message(ADMIN_ID, f"✅ Đã cộng {int(amt):,} VND cho `{tid}`")
        bot.send_message(int(tid), f"✅ Bạn được cộng {int(amt):,} VND!")
    except: bot.send_message(ADMIN_ID, "❌ Lỗi cú pháp.")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_action(call):
    bot.edit_message_text("❌ Giao dịch đã bị hủy.", call.message.chat.id, call.message.message_id)

bot.polling(none_stop=True)
