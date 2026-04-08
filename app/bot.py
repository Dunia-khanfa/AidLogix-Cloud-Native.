import os, json, boto3, telebot, uuid
from telebot import types

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
SQS_URL = os.environ.get('QUEUE_URL')
REGION = "eu-west-1"

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

def send_to_queue(message, action_type):
    payload = {
        "id": str(uuid.uuid4())[:8],
        "user": message.from_user.username or "Guest",
        "chat_id": message.chat.id,
        "type": action_type,
        "content": message.text
    }
    sqs.send_message(QueueUrl=SQS_URL, MessageBody=json.dumps(payload))
    bot.reply_to(message, f"✅ Registered in Logistics Queue. ID: {payload['id']}")

if __name__ == "__main__":
    bot.polling()
