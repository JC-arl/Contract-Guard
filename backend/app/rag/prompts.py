from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

SYSTEM_PROMPT = """당신은 한국 주택임대차 계약서를 임차인(세입자) 관점에서 분석하는 법률 AI입니다.
반드시 JSON만 출력하세요. 설명이나 인사말 없이 JSON만 답변하세요. /no_think"""

BATCH_ANALYSIS_TEMPLATE = """/no_think
아래 임대차 계약 조항들을 임차인 관점에서 분석하세요.

## 핵심 원칙
조항의 실제 내용만 판단하세요. 조항에 적혀있지 않은 내용을 추측하지 마세요.
보증금 금액, 차임 금액, 계약기간 등 단순 숫자/사실 기재는 무조건 safe입니다.

## safe 판정 기준 (아래 중 하나라도 해당하면 반드시 safe)
- 목적물 주소, 면적, 용도 기재
- 보증금 금액, 차임 금액, 납부일정 기재 (금액 크기와 무관하게 safe)
- 임대차 기간 기재 (갱신 관련 조항이 별도로 없어도 기간만 기재하면 safe)
- 보증금을 계약 종료일 또는 종료 후 합리적 기간(1개월) 이내 반환
- 위약금이 보증금의 10% 이하이며 쌍방 동일 적용
- 차임 증액 제한이 연 5% 이내
- 임대인이 주요 수선, 임차인이 소규모 수선 분담
- 자연마모/경년변화를 원상복구 대상에서 제외
- 전대/양도 금지 및 위반 시 해지 (법률상 당연한 제한이므로 "즉시 해지"라고 써있어도 safe)
- 갱신요구권을 인정하고 증액 제한을 두는 조항
- 임차인에게 유리한 특약 (도배 임대인 부담, 주차 보장, 에어컨 설치 등)
- 반려동물을 조건부 허용 (소형견 1마리 등)
- 흡연 장소 제한 (베란다만 등 합리적 제한)

## medium 판정 기준
- 위약금이 보증금의 10~30% (쌍방 동일 적용)
- 해지 통보기간이 쌍방 약간 비대칭 (1개월 차이 이내)
- 반려동물 완전 금지 (즉시 퇴거 조항은 없음)
- 동거인 제한 등 생활 자유 일부 제한
- 분리수거 등 사소한 위반에 과태료 부과

## high 판정 기준 (아래 해당 시 반드시 high — 하나라도 포함되면 무조건 high)
- 보증금 반환을 3개월 이상 지연하거나 무기한 유보
- 임대인만 일방적 해지 가능하고 임차인은 해지 불가
- 위약금이 보증금의 30% 이상
- 차임 인상 제한 없음 (연 5% 초과 허용)
- 모든 수선비용 임차인 전가 (구조적 하자 포함)
- 자연마모까지 원상복구 요구
- "묵시적 갱신 적용 안 됨" 또는 "갱신요구권을 행사하지 않는다" 등 갱신권 포기/배제 문구
- 사전 통보 없이 임대인 출입 허용
- "본 계약에 정하지 않은 사항은 임대인의 결정에 따른다" 등 임대인 일방 결정권
- 임차인의 이의제기권/항변권 박탈
- 사소한 위반에 즉시 퇴거 조항

주의: 조항에 여러 항목이 있을 때 하나라도 high 기준에 해당하면 전체를 high로 판정하세요.

## 분석 대상 조항
{clauses_text}

## 참고 법률/판례
{reference_context}

각 조항의 clause_index는 반드시 대괄호 안의 숫자를 그대로 사용하세요 (예: [9]이면 clause_index:9).
각 조항의 분석은 반드시 해당 조항의 내용만 기반으로 작성하세요. 다른 조항의 내용을 섞지 마세요.
explanation은 해당 조항의 구체적 내용을 인용하여 작성하세요.

JSON 배열로만 답변하세요. 다른 텍스트 없이 [로 시작하세요:
[{{"clause_index":9,"risk_level":"high|medium|low|safe","confidence":0.0~1.0,"risks":[{{"risk_type":"유형","description":"설명","suggestion":"개선안"}}],"explanation":"요약"}}]

위험유형: 보증금_미반환_위험, 일방적_계약해지, 수선의무_전가, 원상복구_과다, 차임증액_무제한, 권리제한, 위약금_과다, 묵시적_갱신_배제
safe 조항은 반드시 risk_level="safe", risks=[]로 판정하세요."""

NO_REFERENCE_CONTEXT = "일반 임대차보호법 원칙에 기반하여 분석."

# 배치 분석 프롬프트
batch_analysis_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(BATCH_ANALYSIS_TEMPLATE),
])


def format_references(references: list[dict]) -> str:
    """참고 법률/판례를 프롬프트용 텍스트로 변환."""
    if not references:
        return NO_REFERENCE_CONTEXT
    ref_lines = []
    for i, ref in enumerate(references, 1):
        text = ref.get("text", "")[:300]
        ref_lines.append(f"[참고{i}] {text}")
    return "\n".join(ref_lines[:5])
