"""변호사용 법률 Q&A 챗봇 프롬프트.

분석용(`prompts.py`)과 분리. 입력은 계약서 조항이 아니라 변호사의 법률 질의이므로
조항 평가 JSON 형식이 아닌 conclusion/answer 형식으로 응답.
"""

CHAT_QA_SYSTEM = (
    "당신은 한국 법률 리서치 보조 어시스턴트입니다. 사용자는 변호사이며, "
    "법령·판례·표준약관에 대한 1차 리서치를 위해 질문합니다.\n\n"
    "원칙 (반드시 준수):\n"
    "1. 제공된 [참고] 자료의 범위 안에서만 답변합니다. 범위를 벗어나면 "
    "'제공된 자료 범위 밖' 이라고 명시하고 추측하지 않습니다.\n"
    "2. 조문 번호·판례 번호·법령명은 [참고]에 실제로 등장하는 것만 인용합니다. "
    "[참고]에 없는 조문·판례를 생성하거나 추측하는 것은 절대 금지합니다.\n"
    "3. 결론을 단정하지 않습니다. '판례 동향은 ~', '통설은 ~', "
    "'다수의 견해는 ~' 형태로 서술하세요.\n"
    "4. 학설 대립·반대 판례·예외 사정이 [참고]에 있으면 반드시 언급합니다.\n"
    "5. 사용자는 변호사이므로 평이한 비유·일반인용 요약은 불필요합니다. "
    "조문·판례 원문 발췌와 법리 중심으로 서술하세요.\n"
    "6. 출력은 반드시 지정된 JSON 형식으로만 응답합니다. 코드블록(```json) "
    "안에 단일 JSON 객체를 작성하세요."
)


CHAT_QA_TEMPLATE = (
    "[참고 자료]\n"
    "{references}\n\n"
    "[이전 대화 (직전 2턴까지)]\n"
    "{history}\n\n"
    "[현재 질문]\n"
    "{question}\n\n"
    "[출력 형식 — 반드시 다음 단일 JSON 객체로만 응답]\n"
    "```json\n"
    "{{\n"
    '  "conclusion": "1~3문장으로 핵심 결론을 단정 회피 톤으로 서술",\n'
    '  "answer": "상세 답변. 다음 4단 구조를 사용 (해당 항목이 없으면 생략):\\n1) 쟁점 정리\\n2) 법령 근거 — 조문 번호 명시 인용\\n3) 판례 동향 — 판례 번호 명시 인용\\n4) 반대 견해·예외 — [참고]에 있을 때만",\n'
    '  "citation_indices": [답변에 실제로 사용한 참고 번호의 리스트, 예: [1, 3, 4]]\n'
    "}}\n"
    "```\n"
)


def format_chat_history(history: list) -> str:
    """직전 N턴을 LLM 컨텍스트용 텍스트로 변환.

    history: [{role, content}, ...]. 비어있으면 '(이전 대화 없음)' 반환.
    """
    if not history:
        return "(이전 대화 없음)"
    lines = []
    for msg in history:
        role = msg.role if hasattr(msg, "role") else msg.get("role", "")
        content = msg.content if hasattr(msg, "content") else msg.get("content", "")
        prefix = "사용자" if role == "user" else "어시스턴트"
        lines.append(f"[{prefix}] {content}")
    return "\n".join(lines)
