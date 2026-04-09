import os, json, boto3, telebot, uuid
from telebot import types

# תיקון שמות המשתנים כדי שיתאימו בדיוק למה שהגדרת ב-GitHub Secrets
TOKEN = os.environ.get('TELEGRAM_TOKEN') 
SQS_URL = os.environ.get('SQS_URL')
REGION = "eu-west-1"

# בדיקת תקינות - אם אחד מהם חסר, הקוד יעצור ויסביר למה
if not TOKEN:
    raise ValueError("Missing TELEGRAM_TOKEN environment variable")
if not SQS_URL:
    raise ValueError("Missing SQS_URL environment variable")

sqs = boto3.client('sqs', region_name=REGION)
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🆘 Request Aid", "📦 Donate Items")
    bot.send_message(message.chat.id, "AidLogix System Online. Select an option:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🆘 Request Aid")
def ask_help(message):
    msg = bot.send_message(message.chat.id, "Describe items and quantity (e.g., 50 Sleeping Bags):")
    bot.register_next_step_handler(msg, send_to_queue, "NEED")

@bot.message_handler(func=lambda m: m.text == "📦 Donate Items")
def ask_donate(message):
    msg = bot.send_message(message.chat.id, "What would you like to donate? (e.g., 20 Canned Foods):")
    bot.register_next_step_handler(msg, send_to_queue, "DONATION")

def send_to_queue(message, action_type):
    try:
        payload = {
            "id": str(uuid.uuid4())[:8],
            "user": message.from_user.username or "Guest",
            "chat_id": message.chat.id,
            "type": action_type,
            "content": message.text
        }
        # שליחה ל-SQS
        sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
        bot.reply_to(message, f"✅ Registered in Logistics Queue. ID: {payload['id']}")
    except Exception as e:
        bot.reply_to(message, "❌ Error connecting to cloud logistics.")
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Bot is starting...")
    bot.polling(none_stop=True)
