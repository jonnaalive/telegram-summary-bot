import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import InputPeerChannel
import config


def create_client():
    return TelegramClient(
        "telegram_summary_session",
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH,
    )


async def get_folder_channels(client: TelegramClient, folder_name: str) -> list:
    """특정 폴더에 속한 채널 목록을 반환한다."""
    result = await client(GetDialogFiltersRequest())
    for f in result.filters:
        title = getattr(f, "title", None)
        if title and (
            (isinstance(title, str) and title == folder_name)
            or (hasattr(title, "text") and title.text == folder_name)
        ):
            peers = getattr(f, "include_peers", [])
            return peers
    return []


async def get_all_channels(client: TelegramClient) -> list:
    """설정된 모든 폴더에서 채널 목록을 합쳐서 반환한다."""
    all_peers = []
    seen = set()
    for folder_name in config.FOLDER_NAMES:
        peers = await get_folder_channels(client, folder_name)
        print(f"[+] '{folder_name}' 폴더: 채널 {len(peers)}개")
        for p in peers:
            peer_id = getattr(p, "channel_id", None) or getattr(p, "user_id", None) or id(p)
            if peer_id not in seen:
                seen.add(peer_id)
                all_peers.append(p)
    return all_peers


async def read_today_messages(client: TelegramClient) -> list[dict]:
    """설정된 폴더들의 채널에서 오늘 메시지를 수집한다."""
    peers = await get_all_channels(client)
    if not peers:
        print(f"[!] 폴더 {config.FOLDER_NAMES}에서 채널을 찾을 수 없습니다.")
        return []

    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    messages = []
    for peer in peers:
        try:
            entity = await client.get_entity(peer)
            channel_name = getattr(entity, "title", str(peer))

            async for msg in client.iter_messages(
                entity,
                offset_date=now,
                reverse=False,
            ):
                if msg.date < today_start:
                    break
                if not msg.text:
                    continue
                messages.append(
                    {
                        "channel_name": channel_name,
                        "message_text": msg.text,
                        "date": msg.date.isoformat(),
                        "url": f"https://t.me/{getattr(entity, 'username', '')}/{msg.id}"
                        if getattr(entity, "username", None)
                        else "",
                    }
                )
        except Exception as e:
            print(f"[!] 채널 읽기 실패 ({peer}): {e}")

    print(f"[+] 채널 {len(peers)}개에서 메시지 {len(messages)}개 수집 완료")
    return messages
