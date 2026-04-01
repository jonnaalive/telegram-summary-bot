import time
import config

MAX_CHARS_PER_CHUNK = 30000

SYSTEM_PROMPT = """\
당신은 금융·경제 뉴스 전문 편집자이자 주식 애널리스트입니다.
여러 텔레그램 채널에서 수집한 오늘의 메시지를 분석하여,
오늘 시장에서 가장 중요한 10가지 토픽을 뽑아주세요.

출력 형식 (마크다운):
## 1. [토픽 제목]
요약 내용 (2-3문장)

**1차 관련주 (직접 수혜):**
- AAPL: 직접적인 관련 이유
- 삼성전자(005930): 직접적인 관련 이유

**2차 관련주 (간접 수혜):**
- 공급망/부품: TSM(반도체 파운드리), LG이노텍(011070, 카메라모듈) 등
- 소재/장비: 한솔케미칼(014680, 반도체소재) 등
- 관련 산업: 해당 뉴스로 수혜받는 연관 산업 종목

> 출처: 채널A, 채널B

...

## 10. [토픽 제목]
(동일 형식)

규칙:
- 한국어로 작성
- 요약은 간결하고 핵심만
- 출처는 실제 채널명 기재
- 제목은 구체적으로 (예: "미 연준 금리 동결 시사" O, "금리 관련 뉴스" X)
- 티커 형식: 미국주식은 심볼, 한국주식은 종목명(종목코드)
- 1차 관련주: 뉴스에 직접 언급되거나 직접적 영향 받는 종목
- 2차 관련주: 공급망, 부품사, 소재/장비, 경쟁사, 대체재, 연관 산업 등 간접 수혜주
- 각 종목별로 왜 수혜를 받는지 구체적으로 한 줄 설명
"""

CHUNK_SYSTEM_PROMPT = """\
당신은 금융·경제 뉴스 전문 편집자이자 주식 애널리스트입니다.
아래 텔레그램 채널 메시지들에서 핵심 뉴스/토픽을 추출하여 간결하게 요약해주세요.
- 한국어로 작성
- 각 토픽은 제목 + 2-3문장 요약 + 1차 관련주 + 2차 관련주(공급망/부품/소재/연관산업) + 출처
- 중요도 순으로 최대 10개
"""

MERGE_SYSTEM_PROMPT = """\
당신은 금융·경제 뉴스 전문 편집자이자 주식 애널리스트입니다.
아래는 여러 배치에서 추출한 부분 요약들입니다.
이를 통합하여 오늘 시장에서 가장 중요한 10가지 토픽으로 최종 정리해주세요.

출력 형식 (마크다운):
## 1. [토픽 제목]
요약 내용 (2-3문장)

**1차 관련주 (직접 수혜):**
- AAPL: 직접적인 관련 이유
- 삼성전자(005930): 직접적인 관련 이유

**2차 관련주 (간접 수혜):**
- 공급망/부품: TSM, LG이노텍(011070) 등
- 소재/장비: 관련 종목
- 관련 산업: 연관 산업 종목

> 출처: 채널A, 채널B

... (10개까지)

규칙:
- 한국어로 작성
- 요약은 간결하고 핵심만
- 출처는 실제 채널명 기재
- 제목은 구체적으로 (예: "미 연준 금리 동결 시사" O, "금리 관련 뉴스" X)
- 티커 형식: 미국주식은 심볼, 한국주식은 종목명(종목코드)
- 1차 관련주: 뉴스에 직접 언급되거나 직접적 영향 받는 종목
- 2차 관련주: 공급망, 부품사, 소재/장비, 경쟁사, 대체재, 연관 산업 등 간접 수혜주
- 각 종목별로 왜 수혜를 받는지 구체적으로 한 줄 설명
- 중복 토픽은 병합
"""


def _call_llm(prompt: str, max_tokens: int = 4096) -> str:
    """Groq → Gemini → OpenAI → Claude 폴백 체인으로 LLM을 호출한다."""
    # 1) Groq (무료, 빠름)
    try:
        from groq import Groq
        client = Groq(api_key=config.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        print("[*] LLM: Groq 사용")
        return response.choices[0].message.content
    except Exception as e:
        print(f"[!] Groq 실패: {e}")

    # 2) Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
        )
        print("[*] LLM: Gemini 사용")
        return response.text
    except Exception as e:
        print(f"[!] Gemini 실패: {e}")

    # 2) OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        print("[*] LLM: OpenAI 사용")
        return response.choices[0].message.content
    except Exception as e:
        print(f"[!] OpenAI 실패: {e}")

    # 3) Claude
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        print("[*] LLM: Claude 사용")
        return response.content[0].text
    except Exception as e:
        print(f"[!] Claude 실패: {e}")

    raise RuntimeError("모든 LLM API 호출 실패")


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
    """긴 텍스트를 줄 단위로 청크 분할한다."""
    lines = user_content.split("\n")
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > MAX_CHARS_PER_CHUNK and current:
            chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks


def summarize(messages: list[dict]) -> str:
    """메시지 목록을 Gemini API로 요약한다."""
    if not messages:
        return "수집된 메시지가 없습니다."

    user_content = _build_user_content(messages)

    # 단일 호출로 처리 가능한 경우
    if len(user_content) <= MAX_CHARS_PER_CHUNK:
        return _call_llm(f"{SYSTEM_PROMPT}\n\n{user_content}", max_tokens=4096)

    # 청크 분할 → 부분 요약 → 최종 병합
    chunks = _split_chunks(user_content)
    print(f"[*] 메시지가 커서 {len(chunks)}개 청크로 분할 처리합니다.")

    partial_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"[*] 청크 {i+1}/{len(chunks)} 요약 중...")
        if i > 0:
            time.sleep(2)  # Rate limit 여유
        result = _call_llm(f"{CHUNK_SYSTEM_PROMPT}\n\n{chunk}", max_tokens=2048)
        partial_summaries.append(result)

    # 최종 병합
    print("[*] 부분 요약 병합 중...")
    time.sleep(2)
    merged_input = "\n\n---\n\n".join(
        f"### 배치 {i+1} 요약\n{s}" for i, s in enumerate(partial_summaries)
    )
    return _call_llm(f"{MERGE_SYSTEM_PROMPT}\n\n{merged_input}", max_tokens=4096)
