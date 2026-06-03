"""변호사 피드백 가이드라인 파서.

가이드라인 형식:
    [조건] 어떤 상황에 적용되는지 (자연어)
    [판단] safe / low / medium / high
    [근거] 법령·판례·실무 이유 (자연어)
    [일반화] O(자동 적용) / X(케이스별)

4개 필드 모두 채워지고 [일반화]=O이면 활성 룰로 등록 가능.
일부만 있거나 자유 텍스트면 KB 참고 자료로만 보존.
"""

import re

from backend.app.models.feedback import ParsedFeedback


# [태그] 본문 (다음 [태그] 또는 문서 끝까지) — 한 라벨이 여러 줄에 걸쳐도 매칭
_BLOCK_RE = re.compile(
    r"\[\s*(조건|판단|근거|일반화)\s*\]\s*(.+?)"
    r"(?=\n\s*\[\s*(?:조건|판단|근거|일반화)\s*\]|\Z)",
    re.DOTALL,
)

# 판단 라벨 정규화 — 한글 동의어도 매핑 (변호사 자유 표현 흡수)
_JUDGMENT_MAP = {
    "safe": "safe", "안전": "safe", "정상": "safe",
    "low": "low", "검토": "low",
    "medium": "medium", "중간": "medium", "불리": "medium",
    "high": "high", "위반": "high", "위험": "high",
}

# 일반화 라벨 정규화
_GENERALIZE_TRUE = {"o", "yes", "y", "true", "1", "예", "응", "네", "ㅇ"}
_GENERALIZE_FALSE = {"x", "no", "n", "false", "0", "아니오", "아니요", "ㄴ"}

# 조건 텍스트에서 매칭용 키워드 추출 (한글·영문·숫자 토큰)
_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")

# 일반어·기능어 — 매칭 신호 약하므로 키워드에서 제외
_STOPWORDS = {
    "있다", "없다", "되다", "하다", "이다",
    "에서", "에게", "으로", "그리고", "또한", "그러나", "그런데", "그래서", "다만",
    "경우", "때", "것", "수", "등", "및", "또는",
    "조항", "내용", "사항", "조건",  # 가이드 텍스트 본문에 자주 등장
}


def parse_feedback(raw: str) -> tuple[ParsedFeedback, list[str]]:
    """가이드라인 따른 텍스트에서 4개 필드를 추출. 누락은 경고로 보고.

    Returns:
        (ParsedFeedback, warnings)
    """
    parsed = ParsedFeedback()
    warnings: list[str] = []

    if not raw or not raw.strip():
        return parsed, ["피드백 내용이 비어 있습니다."]

    blocks: dict[str, str] = {}
    for match in _BLOCK_RE.finditer(raw):
        label = match.group(1)
        body = match.group(2).strip()
        if body and label not in blocks:  # 첫 등장만 채택 — 변호사 재서술 흡수
            blocks[label] = body

    if "조건" in blocks:
        parsed.condition = blocks["조건"]
        parsed.condition_keywords = _extract_keywords(blocks["조건"])
    else:
        warnings.append("[조건] 블록이 없습니다.")

    if "판단" in blocks:
        normalized = _normalize_judgment(blocks["판단"])
        if normalized is not None:
            parsed.judgment = normalized
        else:
            warnings.append(
                f"[판단] 값 '{blocks['판단'][:30]}'을 safe/low/medium/high로 매핑할 수 없습니다."
            )
    else:
        warnings.append("[판단] 블록이 없습니다.")

    if "근거" in blocks:
        parsed.reason = blocks["근거"]
    else:
        warnings.append("[근거] 블록이 없습니다.")

    if "일반화" in blocks:
        gen = _normalize_generalize(blocks["일반화"])
        if gen is None:
            warnings.append(
                f"[일반화] 값 '{blocks['일반화'][:30]}'을 O/X로 해석할 수 없습니다."
            )
        else:
            parsed.generalize = gen
    else:
        warnings.append("[일반화] 블록이 없습니다 (룰 등록 불가).")

    return parsed, warnings


def is_complete_rule(parsed: ParsedFeedback) -> bool:
    """4개 필드 모두 채워졌고 [일반화]=True면 활성 룰 자격."""
    return (
        parsed.condition is not None
        and parsed.judgment is not None
        and parsed.reason is not None
        and parsed.generalize is True
    )


def _normalize_judgment(text: str) -> str | None:
    text_lower = text.strip().lower()
    for key, value in _JUDGMENT_MAP.items():
        if key in text_lower:
            return value
    return None


def _normalize_generalize(text: str) -> bool | None:
    text_lower = text.strip().lower().split()[0] if text.strip() else ""
    if text_lower in _GENERALIZE_TRUE:
        return True
    if text_lower in _GENERALIZE_FALSE:
        return False
    return None


def _extract_keywords(condition: str) -> list[str]:
    """조건 텍스트에서 매칭용 키워드 추출 (한글·영문 토큰, stopword 제거).

    룰 매칭 시 후보 키워드가 모두 본 조항에 등장해야 매칭 — recall 보장 위해
    너무 광범위하게 추출하지 않고 길이 2자+ 토큰만 채택.
    """
    tokens = _TOKEN_RE.findall(condition)
    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        if len(token) < 2 or token in _STOPWORDS or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords
