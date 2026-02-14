"""수동 1회 실행 스크립트. 테스트/디버그 및 Task Scheduler 등록용."""

import asyncio
from telegram_reader import create_client, read_today_messages, get_all_channels
from summarizer import summarize
from obsidian_writer import save


async def run():
    client = create_client()
    async with client:
        # 폴더 채널 목록 확인
        peers = await get_all_channels(client)
        print(f"[+] 전체 채널 수: {len(peers)}")

        # 오늘 메시지 수집
        messages = await read_today_messages(client)
        if not messages:
            print("[!] 오늘 수집된 메시지가 없습니다. 종료합니다.")
            return

        # 채널 수 계산
        channel_names = {m["channel_name"] for m in messages}

        # Claude API 요약
        print("[*] Claude API 요약 중...")
        summary = summarize(messages)

        # 옵시디언 저장
        save(summary, len(channel_names), len(messages))
        print("[+] 완료!")


if __name__ == "__main__":
    asyncio.run(run())
