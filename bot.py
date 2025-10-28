import os
from fastapi import FastAPI, Request
from openai import OpenAI
from telegram import Update, Bot

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
client = OpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)

app = FastAPI()

async def ask_it_bot(message: str) -> str:
    is_complex = len(message) > 300 or any(
        kw in message.lower() for kw in ["class ", "def ", "docker", "api", "sql"]
    )
    model = "gpt-4o" if is_complex else "gpt-4o-mini"
    system_prompt = (
        "Ты — опытный IT-специалист. Кратко и по делу. Примеры кода в Markdown."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )
    return f"[Модель: {model}]\n\n{response.choices[0].message.content}"

@app.post(f"/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    if update.message:
        reply = await ask_it_bot(update.message.text)
        await bot.send_message(chat_id=update.message.chat.id, text=reply, parse_mode="Markdown")
    return {"ok": True}
