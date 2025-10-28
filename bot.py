import os
import json
from fastapi import FastAPI, Request
from telegram import Update, Bot
from openai import OpenAI

# --- Настройки ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

HISTORY_FILE = "history.json"
MAX_HISTORY = 15

# --- Загрузка и сохранение истории ---
def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

chat_history = load_history()

# --- Функция запроса к OpenAI ---
async def ask_it_bot(messages):
    # Выбор модели по длине/сложности последнего сообщения
    last_msg = messages[-1]["content"] if messages else ""
    model = "gpt-4o" if len(last_msg) > 300 or any(kw in last_msg.lower() for kw in ["class ", "def ", "docker", "api", "sql"]) else "gpt-4o-mini"

    system_prompt = "Ты — опытный IT-специалист. Кратко и по делу. Примеры кода в Markdown."

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}] + messages
    )
    return f"[Модель: {model}]\n\n{response.choices[0].message.content}"

# --- Тестовый GET для проверки сервера ---
@app.get("/")
async def root():
    return {"status": "IT-бот работает!"}

# --- Webhook POST ---
@app.post(f"/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    if update.message:
        user_id = str(update.message.chat.id)
        text = update.message.text

        if user_id not in chat_history:
            chat_history[user_id] = []

        chat_history[user_id].append({"role": "user", "content": text})
        # Ограничиваем историю
        chat_history[user_id] = chat_history[user_id][-MAX_HISTORY:]

        # Запрос к OpenAI
        reply = await ask_it_bot(chat_history[user_id])

        chat_history[user_id].append({"role": "assistant", "content": reply})
        save_history(chat_history)

        await bot.send_message(chat_id=user_id, text=reply, parse_mode="Markdown")
    return {"ok": True}
