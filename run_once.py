"""수동 1회 실행 스크립트. 테스트/디버그 및 Task Scheduler 등록용."""

import asyncio
from telegram_reader import create_client, read_messages_since_last_run, get_all_channels
from summarizer import summarize
from obsidian_writer import save, build_content
from gdrive_writer import upload_to_gdrive


async def run():
    client = create_client()
    async with client:
        # 폴더 채널 목록 확인
        peers = await get_all_channels(client)
        print(f"[+] 전체 채널 수: {len(peers)}")

        # 마지막 실행 이후 메시지 수집
        messages = await read_messages_since_last_run(client)
        if not messages:
            print("[!] 새로운 메시지가 없습니다. 종료합니다.")
            return

        # 채널 수 계산
        channel_names = {m["channel_name"] for m in messages}

        # Claude API 요약
        print("[*] Claude API 요약 중...")
        summary = summarize(messages)

        # 옵시디언 저장 (로컬)
        filepath = save(summary, len(channel_names), len(messages))

        # Google Drive 업로드
        try:
            import datetime
            content = build_content(summary, len(channel_names), len(messages))
            filename = f"텔레그램_시장_데일리요약_{datetime.date.today().isoformat()}.md"
            upload_to_gdrive(content, filename)
        except Exception as e:
            print(f"[!] Google Drive 업로드 실패 (계속 진행): {e}")

        # 텔레그램 Saved Messages로 전송
        print("[*] 텔레그램으로 전송 중...")
        tg_message = f"📊 **시장 데일리 요약**\n\n{summary}\n\n---\n_채널 {len(channel_names)}개 | 메시지 {len(messages)}개_"
        await client.send_message("me", tg_message)
        print("[+] 텔레그램 전송 완료!")

        print("[+] 완료!")

    # bot-monitor heartbeat
    from heartbeat import send_heartbeat_sync
    send_heartbeat_sync("telegram-summary-bot")


if __name__ == "__main__":
    asyncio.run(run())
