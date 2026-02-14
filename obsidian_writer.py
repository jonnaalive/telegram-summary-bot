import os
import datetime
import config


def save(summary: str, channel_count: int, message_count: int) -> str:
    """요약 결과를 옵시디언 볼트에 마크다운으로 저장한다. 저장된 파일 경로를 반환."""
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().strftime("%H:%M")

    content = f"# 시장 데일리 요약 - {today}\n\n"
    content += summary
    content += f"\n\n---\n*수집 채널: {channel_count}개 | 메시지: {message_count}개 | 생성: {now}*\n"

    folder = os.path.join(config.OBSIDIAN_VAULT_PATH, "Daily Summary")
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, f"{today}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[+] 저장 완료: {filepath}")
    return filepath
