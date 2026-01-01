import os, telebot, requests, random, time, threading
from flask import Flask
from pymongo import MongoClient
from datetime import datetime
from telebot import types

# --- 1. CẤU HÌNH HỆ THỐNG ---
TOKEN = '8371917325:AAGLIPfishX6fCE6B3OdsEmUMtRAEG9eo6s'
MONGO_URI = 'mongodb+srv://buinek:XH1S550j3EzKpVFg@bottlee.qnaas3k.mongodb.net/?appName=bottlee'
API_KEY_PROXY = 'AvqAKLwQAuDDSNyWtVQUsv'
ADMIN_ID = 5519768222 
PROXY_PRICE = 1500

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client.bot_proxy_db
users_col, orders_col = db.users, db.orders

app = Flask('')
@app.route('/')
def home(): return "Bot is Healthy!"

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('👤 Tài khoản', '🛒 Mua hàng', '💳 Nạp tiền', '📋 Đơn hàng', '📞 Admin')
    return markup

@bot.message_handler(func=lambda m: m.text == '🛒 Mua hàng')
def shop(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🌐 PROXY SIÊU TỐC (1.5k)", callback_data="proxy_menu"),
        types.InlineKeyboardButton("📲 THUÊ OTP GIÁ RẺ (2.5k)", callback_data="buy_otp_confirm"),
        types.InlineKeyboardButton("🔗 LINK VƯỢT GIÁ RẺ (10k)", callback_data="link_vuot_intro")
    )
    shop_text = "🛒 **CỬA HÀNG DỊCH VỤ**\n\nVui lòng chọn loại dịch vụ bên dưới:"
    bot.send_message(message.chat.id, shop_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "link_vuot_intro")
def link_vuot_intro(call):
    text = "🔗 **THÔNG TIN LINK VƯỢT**\n\nLink vượt app giá **10k/1**\n\n📝 **Vui lòng ghi tên game cần vượt**"
    msg = bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_link_vuot_request)

def process_link_vuot_request(message):
    bot.send_message(message.chat.id, "⏳ Vui lòng đợi 1-2p để lấy link vượt...")
    admin_msg = f"🚀 **YÊU CẦU LINK VƯỢT**\n👤 Khách: {message.from_user.id}\n🎮 Game: **{message.text}**"
    bot.send_message(ADMIN_ID, admin_msg)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8000)).start()
    bot.polling(none_stop=True)
