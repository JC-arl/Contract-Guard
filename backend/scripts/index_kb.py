"""
K&H2 지식 베이스(KB) 초기 인덱싱 스크립트.

주택임대차보호법 조문, 불리 조항 예시, 판례 요지 등을 ChromaDB에 적재한다.
AI Hub 데이터 없이도 기본 동작이 가능하도록 내장 데이터를 사용한다.
"""

import sys
import uuid
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.chroma_service import add_documents, collection_status


# ──────────────────────────────────────────────
# 1. 주택임대차보호법 주요 조문
# ──────────────────────────────────────────────
LAW_ARTICLES = [
    {
        "content": (
            "주택임대차보호법 제3조(대항력 등) "
            "① 임대차는 그 등기가 없는 경우에도 임차인이 주택의 인도와 "
            "주민등록을 마친 때에는 그 다음 날부터 제삼자에 대하여 효력이 생긴다. "
            "② 임차주택의 양수인(기타 임대할 권리를 승계한 자를 포함한다)은 "
            "임대인의 지위를 승계한 것으로 본다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제3조",
            "category": "대항력",
            "risk_type": "rights_restriction",
        },
    },
    {
        "content": (
            "주택임대차보호법 제3조의2(보증금의 회수) "
            "① 임대차가 끝난 후에도 임차인이 보증금을 반환받을 때까지는 "
            "임대차관계가 존속하는 것으로 본다. "
            "② 임차주택에 대하여 경매가 진행되는 경우 임차인은 "
            "보증금 중 일정액을 다른 담보물권자보다 우선하여 변제받을 권리가 있다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제3조의2",
            "category": "보증금_보호",
            "risk_type": "deposit_return",
        },
    },
    {
        "content": (
            "주택임대차보호법 제4조(임대차기간 등) "
            "① 기간을 정하지 아니하거나 2년 미만으로 정한 임대차는 "
            "그 기간을 2년으로 본다. 다만, 임차인은 2년 미만으로 정한 기간이 "
            "유효함을 주장할 수 있다. "
            "② 임대차가 종료한 경우에도 임차인이 보증금을 반환받을 때까지는 "
            "임대차관계가 존속하는 것으로 본다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제4조",
            "category": "임대차기간",
            "risk_type": "unilateral_termination",
        },
    },
    {
        "content": (
            "주택임대차보호법 제6조(계약의 갱신) "
            "① 임대인이 임대차기간이 끝나기 6개월 전부터 2개월 전까지의 기간에 "
            "임차인에게 갱신거절의 통지를 하지 아니하거나 계약조건을 변경하지 "
            "아니하면 갱신하지 아니한다는 뜻의 통지를 하지 아니한 경우에는 "
            "그 기간이 끝난 때에 전 임대차와 동일한 조건으로 다시 임대차한 것으로 본다. "
            "② 임차인이 임대차기간이 끝나기 2개월 전까지 통지하지 아니한 경우에도 "
            "또한 같다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제6조",
            "category": "묵시적_갱신",
            "risk_type": "renewal_exclusion",
        },
    },
    {
        "content": (
            "주택임대차보호법 제6조의3(계약갱신 요구 등) "
            "① 임대인은 임차인이 제6조제1항에 따라 계약갱신을 요구할 경우 "
            "정당한 사유 없이 거절하지 못한다. 다만, 다음 각 호의 어느 하나에 "
            "해당하는 경우에는 그러하지 아니하다. "
            "② 임차인은 당해 임대차에 관하여 1회의 계약갱신요구권을 행사할 수 있다. "
            "이 경우 갱신되는 임대차의 존속기간은 2년으로 본다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제6조의3",
            "category": "계약갱신요구권",
            "risk_type": "renewal_exclusion",
        },
    },
    {
        "content": (
            "주택임대차보호법 제7조(차임 등의 증감청구권) "
            "① 당사자는 약정한 차임이나 보증금이 임차주택에 관한 조세, 공과금, "
            "그 밖의 부담의 증감이나 경제사정의 변동으로 인하여 적절하지 아니하게 "
            "된 때에는 장래에 대하여 그 증감을 청구할 수 있다. "
            "② 증액의 경우에는 대통령령으로 정하는 기준에 따른 비율(연 5%)을 "
            "초과하지 못한다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제7조",
            "category": "차임_증감",
            "risk_type": "unlimited_rent_increase",
        },
    },
    {
        "content": (
            "주택임대차보호법 제10조(강행규정) "
            "이 법에 위반되는 약정으로서 임차인에게 불리한 것은 그 효력이 없다."
        ),
        "metadata": {
            "source": "주택임대차보호법",
            "article": "제10조",
            "category": "강행규정",
            "risk_type": "rights_restriction",
        },
    },
    {
        "content": (
            "민법 제623조(임대인의 의무) "
            "임대인은 목적물을 임차인에게 인도하고 계약존속 중 그 사용·수익에 "
            "필요한 상태를 유지하게 할 의무를 부담한다. "
            "민법 제624조(임대인의 수선의무) "
            "임대인은 목적물의 사용·수익에 필요한 수선을 하여야 한다. "
            "그러나 임차인의 과실로 인한 것은 그러하지 아니하다."
        ),
        "metadata": {
            "source": "민법",
            "article": "제623조, 제624조",
            "category": "수선의무",
            "risk_type": "repair_obligation",
        },
    },
]

# ──────────────────────────────────────────────
# 2. 불리한 조항 예시 (위험 패턴)
# ──────────────────────────────────────────────
RISKY_CLAUSE_EXAMPLES = [
    {
        "content": (
            "[불리 조항 예시 - 보증금 미반환 위험] "
            "임대인은 임대차 종료 후 3개월 이내에 보증금을 반환한다. "
            "다만, 임차인의 원상복구가 완료되지 않은 경우 임대인은 "
            "보증금 반환을 무기한 유보할 수 있다. "
            "→ 위험: 원상복구 기준이 모호하여 보증금 반환이 무기한 지연될 수 있음. "
            "주택임대차보호법상 임대차 종료 시 보증금은 즉시 반환이 원칙."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "보증금_미반환",
            "risk_type": "deposit_return",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 보증금 공제] "
            "임대인은 임차인의 월세 연체, 시설물 훼손, 기타 채무 등을 이유로 "
            "보증금에서 일방적으로 공제할 수 있으며, 공제 금액에 대한 이의를 제기할 수 없다. "
            "→ 위험: 공제 사유와 금액이 불명확하고 이의제기권을 박탈함. "
            "보증금 공제는 객관적 근거와 합의가 필요함."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "보증금_미반환",
            "risk_type": "deposit_return",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 일방적 계약해지] "
            "임대인은 사전 통보 없이 언제든지 본 계약을 해지할 수 있으며, "
            "이 경우 임차인은 30일 이내에 퇴거하여야 한다. "
            "→ 위험: 임대인에게만 일방적 해지권 부여. 주택임대차보호법 제6조에 따라 "
            "임대인은 정당한 사유 없이 갱신 거절 불가. 강행규정 위반 소지."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "일방적_해지",
            "risk_type": "unilateral_termination",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 임차인 해지 제한] "
            "임차인은 계약기간 중 어떠한 사유로도 계약을 해지할 수 없으며, "
            "중도 해지 시 보증금 전액을 위약금으로 몰수한다. "
            "→ 위험: 임차인의 중도해지권을 완전히 박탈하고 보증금 전액 몰수는 "
            "부당이득에 해당할 수 있음."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "일방적_해지",
            "risk_type": "unilateral_termination",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 수선의무 전가] "
            "임차 기간 중 발생하는 모든 수선(누수, 보일러 고장, 배관 파손 등)은 "
            "원인에 관계없이 임차인의 비용으로 수리한다. "
            "→ 위험: 민법 제624조에 따라 목적물 사용·수익에 필요한 수선은 "
            "임대인 의무. 구조적 하자까지 임차인에게 전가하는 것은 위법."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "수선의무",
            "risk_type": "repair_obligation",
            "risk_level": "medium",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 소규모 수선 전가] "
            "소모품 교체, 도배, 장판 등 소규모 수선은 임차인이 부담한다. "
            "→ 참고: 소규모 수선비용은 임차인 부담이 관례이나, '소규모'의 범위가 "
            "명확해야 하며, 대규모 수선까지 포함하면 불리 조항."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "수선의무",
            "risk_type": "repair_obligation",
            "risk_level": "low",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 과도한 원상복구] "
            "임차인은 퇴거 시 임차 개시 당시와 완전히 동일한 상태로 원상복구하여야 하며, "
            "자연 마모 및 경년 변화도 복구 대상에 포함한다. "
            "→ 위험: 통상적인 사용에 의한 자연 마모(벽지 변색, 바닥 마모 등)는 "
            "원상복구 의무에 포함되지 않음. 임대인의 부당이득."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "원상복구",
            "risk_type": "excessive_restoration",
            "risk_level": "medium",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 원상복구 비용 일방 결정] "
            "원상복구에 소요되는 비용은 임대인이 지정하는 업체의 견적에 따르며, "
            "임차인은 이에 이의를 제기할 수 없다. "
            "→ 위험: 원상복구 비용 결정권을 임대인에게 독점시키고 "
            "이의제기권 박탈. 합리적 비용 산정이 보장되지 않음."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "원상복구",
            "risk_type": "excessive_restoration",
            "risk_level": "medium",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 무제한 차임 인상] "
            "임대인은 계약 갱신 시 차임을 자유롭게 인상할 수 있다. "
            "→ 위험: 주택임대차보호법 제7조에 따라 차임 증액은 연 5%를 "
            "초과할 수 없음. 이를 초과하는 인상 약정은 무효."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "차임_인상",
            "risk_type": "unlimited_rent_increase",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 차임 인상 사전 동의] "
            "임차인은 임대인이 통보하는 차임 인상에 무조건 동의하며, "
            "인상에 불응할 경우 이를 계약 위반으로 간주한다. "
            "→ 위험: 차임 증감은 쌍방의 청구권이며, 일방적 통보로 "
            "강제할 수 없음."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "차임_인상",
            "risk_type": "unlimited_rent_increase",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 과도한 위약금] "
            "임차인이 계약을 위반할 경우 보증금의 50%를 위약금으로 지급한다. "
            "→ 위험: 통상적인 위약금은 보증금의 10% 내외. "
            "50% 이상은 과도한 위약금으로 법원에서 감액될 수 있음."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "위약금",
            "risk_type": "excessive_penalty",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 포괄적 위약금] "
            "임차인이 본 계약의 조항을 하나라도 위반하는 경우, "
            "임대인은 계약을 즉시 해지하고 보증금 전액을 위약금으로 귀속시킬 수 있다. "
            "→ 위험: 경미한 위반에도 전액 몰수는 부당. 위반의 경중에 비례해야 함."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "위약금",
            "risk_type": "excessive_penalty",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 묵시적 갱신 배제] "
            "본 계약은 기간 만료 시 자동으로 종료되며, 묵시적 갱신은 적용되지 않는다. "
            "→ 위험: 주택임대차보호법 제6조의 묵시적 갱신 규정은 강행규정으로, "
            "이를 배제하는 약정은 무효. 임차인에게 불리한 약정."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "묵시적_갱신",
            "risk_type": "renewal_exclusion",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 갱신요구권 포기] "
            "임차인은 계약갱신요구권을 행사하지 않기로 하며, "
            "기간 만료 시 즉시 퇴거한다. "
            "→ 위험: 계약갱신요구권은 주택임대차보호법 제6조의3에 의해 "
            "보장되는 권리로, 사전 포기 약정은 강행규정 위반으로 무효."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "묵시적_갱신",
            "risk_type": "renewal_exclusion",
            "risk_level": "high",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 임차인 권리 제한] "
            "임차인은 임대인의 사전 서면 동의 없이 전대, 임차권 양도, "
            "주택 구조 변경, 인테리어 변경을 할 수 없으며, "
            "반려동물 사육, 악기 연주 등 일체의 소음 행위를 금지한다. "
            "→ 주의: 전대·양도 제한은 합법이나, 일상생활을 과도하게 "
            "제한하는 조항은 불합리."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "권리_제한",
            "risk_type": "rights_restriction",
            "risk_level": "medium",
        },
    },
    {
        "content": (
            "[불리 조항 예시 - 임대인 출입권] "
            "임대인은 사전 통보 없이 언제든지 임차 목적물에 출입할 수 있다. "
            "→ 위험: 임차인의 주거의 평온을 심각하게 침해. "
            "사전 동의나 최소한 사전 통보 후 출입이 원칙."
        ),
        "metadata": {
            "source": "불리조항_예시",
            "category": "권리_제한",
            "risk_type": "rights_restriction",
            "risk_level": "high",
        },
    },
]

# ──────────────────────────────────────────────
# 3. 주요 판례 요지
# ──────────────────────────────────────────────
CASE_PRECEDENTS = [
    {
        "content": (
            "[판례] 대법원 2013다218156 - 보증금 반환 의무 "
            "임대차 계약이 종료된 이상 임대인은 특별한 사정이 없는 한 "
            "임차인에게 보증금을 반환할 의무가 있고, "
            "임차인의 원상복구의무 불이행을 이유로 보증금 반환을 거부할 수 없다. "
            "원상복구에 필요한 비용은 별도로 청구하여야 한다."
        ),
        "metadata": {
            "source": "판례",
            "case_number": "2013다218156",
            "court": "대법원",
            "category": "보증금_반환",
            "risk_type": "deposit_return",
        },
    },
    {
        "content": (
            "[판례] 대법원 98다34903 - 수선의무 "
            "임대인의 수선의무는 임대인이 부담하는 것이 원칙이며, "
            "이를 임차인에게 전가하는 특약은 소규모 수선에 한하여 유효하다. "
            "건물의 주요 구조부분이나 대규모 수선에 해당하는 사항을 "
            "임차인에게 전가하는 특약은 무효이다."
        ),
        "metadata": {
            "source": "판례",
            "case_number": "98다34903",
            "court": "대법원",
            "category": "수선의무",
            "risk_type": "repair_obligation",
        },
    },
    {
        "content": (
            "[판례] 대법원 2004다26133 - 위약금 감액 "
            "약정된 손해배상 예정액이 부당하게 과다한 경우 "
            "법원은 직권으로 이를 적당히 감액할 수 있다(민법 제398조 제2항). "
            "임대차 보증금의 50% 이상을 위약금으로 정한 것은 "
            "부당하게 과다한 것으로 판단한 사례."
        ),
        "metadata": {
            "source": "판례",
            "case_number": "2004다26133",
            "court": "대법원",
            "category": "위약금",
            "risk_type": "excessive_penalty",
        },
    },
    {
        "content": (
            "[판례] 대법원 2020다227455 - 묵시적 갱신과 계약갱신요구권 "
            "주택임대차보호법 제6조에 따른 묵시적 갱신 규정은 강행규정이므로, "
            "이에 반하여 임차인에게 불리한 약정은 그 효력이 없다. "
            "임대인이 갱신거절의 통지를 하지 않은 경우 동일 조건으로 갱신된 것으로 본다."
        ),
        "metadata": {
            "source": "판례",
            "case_number": "2020다227455",
            "court": "대법원",
            "category": "묵시적_갱신",
            "risk_type": "renewal_exclusion",
        },
    },
    {
        "content": (
            "[판례] 대법원 2010다57350 - 차임 증액 제한 "
            "주택임대차보호법 제7조에 따른 차임 증액 제한(5%)은 강행규정이며, "
            "이를 초과하는 증액 약정은 초과 부분에 한하여 무효이다. "
            "임대인이 일방적으로 통보한 차임 인상은 효력이 없다."
        ),
        "metadata": {
            "source": "판례",
            "case_number": "2010다57350",
            "court": "대법원",
            "category": "차임_증액",
            "risk_type": "unlimited_rent_increase",
        },
    },
    {
        "content": (
            "[판례] 대법원 2017다212194 - 원상복구 범위 "
            "임차인의 원상복구의무는 임차인이 설치한 물건의 철거 및 "
            "임차인의 과실로 인한 훼손의 수선에 한정된다. "
            "통상적인 사용에 의한 자연적 마모·손상(벽지 변색, 바닥 마모 등)은 "
            "원상복구 의무의 범위에 포함되지 않는다."
        ),
        "metadata": {
            "source": "판례",
            "case_number": "2017다212194",
            "court": "대법원",
            "category": "원상복구",
            "risk_type": "excessive_restoration",
        },
    },
]

# ──────────────────────────────────────────────
# 4. 표준 임대차 계약서 주요 조항 (안전한 조항 예시)
# ──────────────────────────────────────────────
STANDARD_CONTRACT_CLAUSES = [
    {
        "content": (
            "[표준계약서] 보증금 반환 조항 "
            "임대인은 임대차 계약이 종료된 날에 임차인에게 보증금 전액을 반환한다. "
            "다만, 연체 차임이나 관리비 등 임차인의 채무가 있는 경우 "
            "이를 공제하고 반환할 수 있다."
        ),
        "metadata": {
            "source": "표준계약서",
            "category": "보증금",
            "risk_type": "deposit_return",
            "risk_level": "safe",
        },
    },
    {
        "content": (
            "[표준계약서] 수선의무 조항 "
            "임대인은 임대목적물의 사용·수익에 필요한 수선을 하여야 한다. "
            "다만, 임차인의 과실로 인한 파손이나 소모품의 교체·수리 등 "
            "소규모 수선은 임차인이 부담한다."
        ),
        "metadata": {
            "source": "표준계약서",
            "category": "수선의무",
            "risk_type": "repair_obligation",
            "risk_level": "safe",
        },
    },
    {
        "content": (
            "[표준계약서] 계약 해지 조항 "
            "임대인 또는 임차인이 본 계약을 해지하고자 할 때에는 "
            "상대방에게 최소 3개월 전에 서면으로 통지하여야 한다. "
            "정당한 사유 없이 일방적으로 해지할 수 없다."
        ),
        "metadata": {
            "source": "표준계약서",
            "category": "계약_해지",
            "risk_type": "unilateral_termination",
            "risk_level": "safe",
        },
    },
    {
        "content": (
            "[표준계약서] 차임 인상 조항 "
            "계약 갱신 시 차임 또는 보증금의 증액은 약정한 차임 등의 "
            "20분의 1(5%)을 초과하지 못한다."
        ),
        "metadata": {
            "source": "표준계약서",
            "category": "차임_인상",
            "risk_type": "unlimited_rent_increase",
            "risk_level": "safe",
        },
    },
]


def build_kb():
    """모든 데이터를 ChromaDB에 인덱싱."""
    all_entries = (
        LAW_ARTICLES
        + RISKY_CLAUSE_EXAMPLES
        + CASE_PRECEDENTS
        + STANDARD_CONTRACT_CLAUSES
    )

    ids = [str(uuid.uuid4()) for _ in all_entries]
    documents = [e["content"] for e in all_entries]
    metadatas = [e["metadata"] for e in all_entries]

    print(f"총 {len(all_entries)}건 인덱싱 시작...")
    print(f"  - 법률 조문: {len(LAW_ARTICLES)}건")
    print(f"  - 불리 조항 예시: {len(RISKY_CLAUSE_EXAMPLES)}건")
    print(f"  - 판례 요지: {len(CASE_PRECEDENTS)}건")
    print(f"  - 표준계약서 조항: {len(STANDARD_CONTRACT_CLAUSES)}건")

    add_documents(ids=ids, documents=documents, metadatas=metadatas)

    status = collection_status()
    print(f"\n인덱싱 완료! ChromaDB 컬렉션: {status['name']}, 문서 수: {status['count']}")


if __name__ == "__main__":
    build_kb()
