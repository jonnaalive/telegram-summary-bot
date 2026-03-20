"""매일 07:00에 자동 실행되는 스케줄러."""

import time
import asyncio
import schedule
from run_once import run


def run_job():
    asyncio.run(run())


if __name__ == "__main__":
    schedule.every().day.at("07:00").do(run_job)
    print("[*] 스케줄러 시작 - 매일 07:00 실행 대기 중...")
    while True:
        schedule.run_pending()
        time.sleep(60)
