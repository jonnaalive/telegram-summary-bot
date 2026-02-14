"""매일 21:00에 자동 실행되는 스케줄러."""

import time
import asyncio
import schedule
from telegram_reader import create_client, read_today_messages, get_all_channels
from summarizer import summarize
from obsidian_writer import save


async def job():
    print("[*] 작업 시작...")
    client = create_client()
    async with client:
        peers = await get_all_channels(client)
        print(f"[+] 전체 채널 수: {len(peers)}")

        messages = await read_today_messages(client)
        if not messages:
            print("[!] 오늘 수집된 메시지가 없습니다.")
            return

        channel_names = {m["channel_name"] for m in messages}

        print("[*] Claude API 요약 중...")
        summary = summarize(messages)

        save(summary, len(channel_names), len(messages))
        print("[+] 작업 완료!")


def run_job():
    asyncio.run(job())


if __name__ == "__main__":
    schedule.every().day.at("21:00").do(run_job)
    print("[*] 스케줄러 시작 - 매일 21:00 실행 대기 중...")
    while True:
        schedule.run_pending()
        time.sleep(60)
