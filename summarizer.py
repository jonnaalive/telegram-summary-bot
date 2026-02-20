from openai import OpenAI
import config

MODEL = "gpt-4o-mini"

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


def summarize(messages: list[dict]) -> str:
    """메시지 목록을 OpenAI API로 요약한다."""
    if not messages:
        return "수집된 메시지가 없습니다."

    # 메시지를 채널별로 정리
    grouped: dict[str, list[str]] = {}
    for m in messages:
        name = m["channel_name"]
        grouped.setdefault(name, []).append(m["message_text"])

    user_content = ""
    for channel, texts in grouped.items():
        user_content += f"\n### {channel}\n"
        for t in texts:
            user_content += f"- {t[:500]}\n"

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content
