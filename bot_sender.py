"""텔레그램 봇 API로 메시지 발송."""

import os
from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MAX_LENGTH = 4096


def _split(text: str) -> list[str]:
    """4096자 제한으로 메시지 분할."""
    if len(text) <= MAX_LENGTH:
        return [text]
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX_LENGTH:
            chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks


async def send_via_bot(message: str):
    """봇 토큰으로 메시지 발송. HTML 파싱 실패 시 plain text 폴백."""
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 미설정, 봇 발송 건너뜀")
        return

    bot = Bot(token=BOT_TOKEN)
    chunks = _split(message)

    for chunk in chunks:
        try:
            await bot.send_message(
                chat_id=CHAT_ID, text=chunk, parse_mode=ParseMode.HTML,
            )
        except Exception:
            # HTML 파싱 실패 시 plain text로 재시도
            await bot.send_message(chat_id=CHAT_ID, text=chunk)
