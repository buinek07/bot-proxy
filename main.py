import os, telebot, requests, random, time, threading
from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from telebot import types

# --- 1. CẤU HÌNH HỆ THỐNG ---
TOKEN = os.getenv('TOKEN', '8371917325:AAE4ftu8HJkA5CyNd5On69r39WS10Osl1JQ')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee')
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
API_KEY_SIM = 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJidWluZWsiLCJqdGkiOiI4MTI1NyIsImlhdCI6MTc2MjU0Mzc1MCwiZXhwIjoxODI0NzUxNzUwfQ.samlD0eFL1r0fx2JYsMX0qS6LK1zVCXXPPWHJHeHh9cWlbOWV3_WMfm64RTU2HIzQ0O6fyeog7TfDNlnmvcg2g'

ADMIN_ID = 5519768222 
PROXY_PRICE = 1500
OTP_PRICE = 2500
SERVICE_ID_OTP = 49 

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col, orders_col = db.users, db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is Healthy!"

# --- 2. MENU CHÍNH ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

# --- 3. LỆNH START & TÀI KHOẢN ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    now = datetime.now().strftime("%d/%m/%Y")
    users_col.update_one({"user_id": user_id}, {"$set": {"username": username, "first_name": message.from_user.first_name}, "$setOnInsert": {"join_date": now, "balance": 0, "total_deposit": 0, "total_spent": 0}}, upsert=True)
    bot.send_message(message.chat.id, f"👋 Chào mừng **{message.from_user.first_name}** đã quay trở lại!\n⚡ Hệ thống Proxy & OTP tự động 24/7 uy tín số 1.", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '👤 Tài khoản')
def account_info(message):
    u = users_col.find_one({"user_id": message.from_user.id})
    msg = (f"🌟 **THÔNG TIN CÁ NHÂN** 🌟\n\n"
           f"👤 Tên khách hàng: {u.get('username', 'None')}\n"
           f"🆔 ID của bạn: `{message.from_user.id}`\n"
           f"📅 Ngày gia nhập: {u.get('join_date', 'None')}\n"
           f"━━━━━━━━━━━━━━━━━━━━━\n"
           f"💰 Số dư khả dụng: `{u.get('balance', 0):,} VNĐ`\n"
           f"📥 Tổng nạp: `{u.get('total_deposit', 0):,} VNĐ`\n"
           f"📤 Tổng đã chi tiêu: `{u.get('total_spent', 0):,} VNĐ`\n\n"
           f"💎 *Cảm ơn bạn đã tin tưởng dịch vụ!*")
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# --- 4. CỬA HÀNG DỊCH VỤ ---
@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌐 PROXY SIÊU TỐC (1.500đ)", callback_data="proxy_menu"),
        types.InlineKeyboardButton("📲 THUÊ OTP GIÁ RẺ (2.500đ)", callback_data="buy_otp_confirm")
    ) #
    
    shop_text = (
        "🛒 **CỬA HÀNG DỊCH VỤ**\n\n"
        "Vui lòng chọn loại dịch vụ bạn muốn trải nghiệm bên dưới:\n\n"
        "🔹 **Proxy**: Proxy tĩnh tốc độ cao, ổn định, hỗ trợ đa nhà mạng.\n"
        "🔹 **Thuê OTP**: Nhận mã nhanh chóng, hoàn tiền 100% nếu lỗi."
    )
    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode="Markdown")

# --- 5. LUỒNG MUA PROXY (CHỌN -> NHẬP SỐ LƯỢNG -> XÁC NHẬN) ---
@bot.callback_query_handler(func=lambda call: call.data == "proxy_menu")
def proxy_carriers(call):
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(types.InlineKeyboardButton("🌐 Viettel", callback_data="setqty_Viettel"),
               types.InlineKeyboardButton("🌐 VNPT", callback_data="setqty_VNPT"),
               types.InlineKeyboardButton("🌐 FPT", callback_data="setqty_FPT"))
    bot.edit_message_text("✨ **CHỌN NHÀ MẠNG PROXY**\n\nHệ thống cung cấp Proxy sạch, tốc độ cao. Vui lòng chọn nhà mạng:", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("setqty_"))
def ask_quantity(call):
    carrier = call.data.replace("setqty_", "")
    msg = bot.edit_message_text(
        f"🔢 **NHẬP SỐ LƯỢNG CẦN MUA**\n\n"
        f"🌐 Nhà mạng: **{carrier}**\n"
        f"💵 Đơn giá: `1,500 VNĐ/Proxy`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 Vui lòng **nhập số lượng** bạn muốn mua (từ **1** đến **50**):",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, confirm_proxy_purchase, carrier)

def confirm_proxy_purchase(message, carrier):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "❌ **Lỗi:** Vui lòng chỉ nhập số lượng là chữ số (Ví dụ: 5).")
        return
    
    qty = int(message.text)
    if qty < 1 or qty > 50:
        bot.send_message(message.chat.id, "❌ **Lỗi:** Số lượng mua tối thiểu là 1 và tối đa là 50 Proxy.")
        return

    total = qty * PROXY_PRICE
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Thanh toán ngay", callback_data=f"pay_proxy_{carrier}_{qty}"),
               types.InlineKeyboardButton("❌ Hủy bỏ", callback_data="proxy_menu"))

    confirm_text = (
        f"📝 **CHI TIẾT ĐƠN HÀNG**\n\n"
        f"🔹 Dịch vụ: **Proxy {carrier}**\n"
        f"🔢 Số lượng: `{qty}` Proxy\n"
        f"💰 Tổng thanh toán: `{total:,} VNĐ`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Lưu ý: Sau khi xác nhận, tiền sẽ được trừ trực tiếp vào số dư.*"
    )
    bot.send_message(message.chat.id, confirm_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_proxy_"))
def final_payment(call):
    _, _, carrier, qty = call.data.split('_')
    qty = int(qty)
    total = qty * PROXY_PRICE
    u = users_col.find_one({"user_id": call.from_user.id})

    if u.get('balance', 0) < total:
        bot.answer_callback_query(call.id, "❌ Tài khoản của bạn không đủ số dư!", show_alert=True)
        return

    bot.edit_message_text(f"⏳ Đang thực hiện giao dịch và lấy Proxy {carrier}...", call.message.chat.id, call.message.message_id)
    api_url = f"https://proxy.vn/apiv2/muaproxy.php?loaiproxy={carrier}&key={API_KEY_PROXY}&soluong={qty}&ngay=1&type=HTTP&user=random&password=random"
    
    try:
        res = requests.get(api_url, timeout=30).json()
        if res.get('status') == 'success':
            p_data = res.get('data')
            users_col.update_one({"user_id": call.from_user.id}, {"$inc": {"balance": -total, "total_spent": total}})
            orders_col.insert_one({"user_id": call.from_user.id, "type": f"Proxy {carrier} x{qty}", "data": p_data, "date": datetime.now()})
            bot.edit_message_text(f"✅ **MUA HÀNG THÀNH CÔNG!**\n\n🎁 **Thông tin Proxy của bạn:**\n`{p_data}`\n\n🙏 Cảm ơn bạn đã ủng hộ!", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        else: bot.edit_message_text(f"❌ **Lỗi API:** {res.get('message')}", call.message.chat.id, call.message.message_id)
    except: bot.edit_message_text("❌ **Lỗi:** Không thể kết nối với máy chủ Proxy.vn", call.message.chat.id, call.message.message_id)

# --- 6. PHẦN ĐƠN HÀNG & NẠP TIỀN (CHỈNH ĐẸP) ---
@bot.message_handler(func=lambda m: m.text == '📋 Đơn hàng')
def order_history(message):
    orders = list(orders_col.find({"user_id": message.from_user.id}).sort("date", -1).limit(10))
    if not orders:
        bot.send_message(message.chat.id, "📦 **ĐƠN HÀNG CỦA BẠN**\n\nHiện tại bạn chưa có giao dịch nào trên hệ thống.", parse_mode="Markdown")
        return
    msg = "📋 **LỊCH SỬ GIAO DỊCH GẦN NHẤT**\n\n"
    for o in orders:
        msg += f"📅 {o['date'].strftime('%d/%m %H:%M')} | 🛒 {o['type']}\n🔑 `{o['data']}`\n\n"
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == '💳 Nạp tiền')
def recharge(message):
    user_id = message.from_user.id
    memo = f"tiencafe{user_id}"
    qr_url = f"https://img.vietqr.io/image/MB-700122-compact2.jpg?amount=20000&addInfo={memo}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Xác nhận đã chuyển khoản", callback_data=f"confirm_{memo}"))
    bot.send_photo(message.chat.id, qr_url, caption=f"💳 **NẠP TIỀN TỰ ĐỘNG**\n\n🏦 Ngân hàng: **MBBank**\n📝 STK: `700122`\n👤 CTK: **BUI DUC ANH**\n\n📌 Nội dung: `{memo}`\n💰 Nạp tối thiểu: **20,000đ**\n\n⚠️ *Vui lòng đợi 1-3 phút sau khi nạp để Admin duyệt!*", reply_markup=markup, parse_mode="Markdown")

# --- 7. VẬN HÀNH BOT ---
def run_web(): app.run(host='0.0.0.0', port=8000)
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    while True:
        try: bot.polling(none_stop=True, interval=0, timeout=40)
        except: time.sleep(5)
