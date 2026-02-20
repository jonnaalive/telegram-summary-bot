import time
from openai import OpenAI
import config

MODEL = "gpt-4o-mini"
MAX_CHARS_PER_CHUNK = 120000  # ~30K tokens, 128K 컨텍스트 한도 내 안전 마진

SYSTEM_PROMPT = """\
당신은 금융·경제 뉴스 전문 편집자입니다.
여러 텔레그램 채널에서 수집한 오늘의 메시지를 분석하여,
오늘 시장에서 가장 중요한 10가지 토픽을 뽑아주세요.

출력 형식 (마크다운):
## 1. [토픽 제목]
요약 내용 (2-3문장)
**관련 티커:** AAPL, 삼성전자(005930) 등
- AAPL: 관련 이유 한 줄
- 삼성전자: 관련 이유 한 줄
> 출처: 채널A, 채널B

## 2. [토픽 제목]
요약 내용 (2-3문장)
**관련 티커:** NVDA, SK하이닉스(000660) 등
- NVDA: 관련 이유 한 줄
- SK하이닉스: 관련 이유 한 줄
> 출처: 채널C

...

## 10. [토픽 제목]
요약 내용 (2-3문장)
**관련 티커:** ...
- 티커: 관련 이유 한 줄
> 출처: 채널D

규칙:
- 한국어로 작성
- 요약은 간결하고 핵심만
- 출처는 실제 채널명 기재
- 제목은 구체적으로 (예: "미 연준 금리 동결 시사" O, "금리 관련 뉴스" X)
- 관련 티커는 미국주식은 티커 심볼, 한국주식은 종목명(종목코드) 형식
- 각 티커별로 왜 관련주인지 한 줄로 간략히 설명
"""

CHUNK_SYSTEM_PROMPT = """\
당신은 금융·경제 뉴스 전문 편집자입니다.
아래 텔레그램 채널 메시지들에서 핵심 뉴스/토픽을 추출하여 간결하게 요약해주세요.
- 한국어로 작성
- 각 토픽은 제목 + 2-3문장 요약 + 관련 티커 + 출처 채널명
- 중요도 순으로 최대 10개
"""

MERGE_SYSTEM_PROMPT = """\
당신은 금융·경제 뉴스 전문 편집자입니다.
아래는 여러 배치에서 추출한 부분 요약들입니다.
이를 통합하여 오늘 시장에서 가장 중요한 10가지 토픽으로 최종 정리해주세요.

출력 형식 (마크다운):
## 1. [토픽 제목]
요약 내용 (2-3문장)
**관련 티커:** AAPL, 삼성전자(005930) 등
- AAPL: 관련 이유 한 줄
- 삼성전자: 관련 이유 한 줄
> 출처: 채널A, 채널B

... (10개까지)

규칙:
- 한국어로 작성
- 요약은 간결하고 핵심만
- 출처는 실제 채널명 기재
- 제목은 구체적으로 (예: "미 연준 금리 동결 시사" O, "금리 관련 뉴스" X)
- 관련 티커는 미국주식은 티커 심볼, 한국주식은 종목명(종목코드) 형식
- 각 티커별로 왜 관련주인지 한 줄로 간략히 설명
- 중복 토픽은 병합
"""


def _build_user_content(messages: list[dict]) -> str:
    """메시지를 채널별로 정리한 텍스트를 생성한다."""
    grouped: dict[str, list[str]] = {}
    for m in messages:
        name = m["channel_name"]
        grouped.setdefault(name, []).append(m["message_text"])

    user_content = ""
    for channel, texts in grouped.items():
        user_content += f"\n### {channel}\n"
        for t in texts:
            user_content += f"- {t[:500]}\n"
    return user_content


def _split_chunks(user_content: str) -> list[str]:
    """긴 텍스트를 채널 단위로 청크 분할한다."""
    sections = user_content.split("\n### ")
    chunks = []
    current = ""
    for section in sections:
        section_text = "\n### " + section if section else ""
        if len(current) + len(section_text) > MAX_CHARS_PER_CHUNK and current:
            chunks.append(current)
            current = section_text
        else:
            current += section_text
    if current:
        chunks.append(current)
    return chunks


def summarize(messages: list[dict]) -> str:
    """메시지 목록을 OpenAI API로 요약한다."""
    if not messages:
        return "수집된 메시지가 없습니다."

    user_content = _build_user_content(messages)
    client = OpenAI(api_key=config.OPENAI_API_KEY)

    # 단일 호출로 처리 가능한 경우
    if len(user_content) <= MAX_CHARS_PER_CHUNK:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        return response.choices[0].message.content

    # 청크 분할 → 부분 요약 → 최종 병합
    chunks = _split_chunks(user_content)
    print(f"[*] 메시지가 커서 {len(chunks)}개 청크로 분할 처리합니다.")

    partial_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"[*] 청크 {i+1}/{len(chunks)} 요약 중...")
        if i > 0:
            time.sleep(5)  # TPM 한도 여유 확보
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2048,
            messages=[
                {"role": "system", "content": CHUNK_SYSTEM_PROMPT},
                {"role": "user", "content": chunk},
            ],
        )
        partial_summaries.append(response.choices[0].message.content)

    # 최종 병합
    print("[*] 부분 요약 병합 중...")
    time.sleep(5)
    merged_input = "\n\n---\n\n".join(
        f"### 배치 {i+1} 요약\n{s}" for i, s in enumerate(partial_summaries)
    )
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": MERGE_SYSTEM_PROMPT},
            {"role": "user", "content": merged_input},
        ],
    )
    return response.choices[0].message.content
