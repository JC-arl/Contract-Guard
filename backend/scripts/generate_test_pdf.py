"""불리한 조항이 포함된 테스트용 임대차 계약서 PDF 생성."""

import os
import sys
from pathlib import Path
from fpdf import FPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "test_lease_contract.pdf"

# 한국어 지원 폰트 경로 (macOS)
FONT_PATHS = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/Library/Fonts/NanumGothic.ttf",
]


def find_korean_font():
    for path in FONT_PATHS:
        if os.path.exists(path):
            return path
    return None


def create_test_contract():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    font_path = find_korean_font()
    if font_path:
        pdf.add_font("Korean", "", font_path, uni=True)
        font_name = "Korean"
    else:
        print("한국어 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
        font_name = "Helvetica"

    pdf.add_page()

    # 제목
    pdf.set_font(font_name, size=18)
    pdf.cell(0, 15, "주택 임대차 계약서", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # 계약 당사자
    pdf.set_font(font_name, size=10)
    pdf.multi_cell(0, 7, (
        "임대인(갑): 홍길동 (서울특별시 강남구 테헤란로 123)\n"
        "임차인(을): 김철수 (서울특별시 서초구 반포대로 456)\n"
        "\n"
        "임대인과 임차인은 아래와 같이 주택 임대차 계약을 체결한다.\n"
    ))
    pdf.ln(5)

    clauses = [
        (
            "제1조 (목적물)",
            "임대인은 아래 표시 부동산을 임대차 목적물로 임차인에게 임대한다.\n"
            "소재지: 서울특별시 강남구 역삼동 123-45 행복아파트 101동 1001호\n"
            "면적: 전용 84.5㎡"
        ),
        (
            "제2조 (보증금 및 차임)",
            "보증금: 금 삼억원정 (300,000,000원)\n"
            "월 차임: 금 백만원정 (1,000,000원)\n"
            "임차인은 계약 체결 시 계약금 삼천만원을 지불하고, "
            "잔금은 입주일에 지불한다."
        ),
        (
            "제3조 (임대차 기간)",
            "임대차 기간은 2025년 4월 1일부터 2027년 3월 31일까지 2년으로 한다."
        ),
        (
            "제4조 (보증금 반환)",
            "임대인은 임대차 종료 후 6개월 이내에 보증금을 반환한다. "
            "다만, 임차인의 원상복구가 임대인이 만족하는 수준으로 완료되지 않은 경우 "
            "임대인은 보증금 반환을 무기한 유보할 수 있으며, "
            "원상복구 비용은 임대인이 지정하는 업체의 견적에 따라 "
            "보증금에서 공제한다. 임차인은 공제 금액에 대해 이의를 제기할 수 없다."
        ),
        (
            "제5조 (계약 해지)",
            "임대인은 1개월 전 통보로 본 계약을 해지할 수 있다. "
            "임차인은 계약 기간 중 어떠한 사유로도 계약을 해지할 수 없으며, "
            "부득이하게 중도 해지하는 경우 보증금의 50%를 위약금으로 지급한다."
        ),
        (
            "제6조 (차임 인상)",
            "임대인은 계약 갱신 시 차임을 자유롭게 인상할 수 있으며, "
            "임차인은 임대인이 통보하는 인상된 차임에 동의하여야 한다. "
            "차임 인상에 동의하지 않는 경우 계약 위반으로 간주한다."
        ),
        (
            "제7조 (수선의무)",
            "임차 기간 중 발생하는 모든 수선(누수, 보일러 고장, 배관 파손, "
            "벽체 균열, 창호 파손 등)은 그 원인에 관계없이 "
            "임차인의 비용으로 수리하여야 한다."
        ),
        (
            "제8조 (원상복구)",
            "임차인은 퇴거 시 임차 개시 당시와 완전히 동일한 상태로 "
            "원상복구하여야 하며, 자연 마모 및 경년 변화도 복구 대상에 포함한다. "
            "원상복구에 소요되는 비용은 임대인이 지정하는 업체의 견적에 따른다."
        ),
        (
            "제9조 (계약 갱신)",
            "본 계약은 기간 만료 시 자동으로 종료되며, "
            "묵시적 갱신은 적용되지 않는다. "
            "임차인은 계약갱신요구권을 행사하지 않기로 한다."
        ),
        (
            "제10조 (임대인의 출입)",
            "임대인은 시설물 점검 등을 위하여 "
            "사전 통보 없이 언제든지 임차 목적물에 출입할 수 있다."
        ),
        (
            "제11조 (특약사항)",
            "1. 임차인은 반려동물을 사육할 수 없다.\n"
            "2. 임차인은 임대인의 사전 서면 동의 없이 벽에 못을 박거나 "
            "인테리어를 변경할 수 없다.\n"
            "3. 본 계약에 명시되지 않은 사항은 임대인의 결정에 따른다."
        ),
    ]

    for title, content in clauses:
        pdf.set_font(font_name, size=12)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_name, size=10)
        pdf.multi_cell(0, 7, content)
        pdf.ln(3)

    # 서명란
    pdf.ln(10)
    pdf.set_font(font_name, size=10)
    pdf.cell(0, 7, "2025년 3월 30일", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.cell(90, 7, "임대인: 홍길동  (인)", align="C")
    pdf.cell(90, 7, "임차인: 김철수  (인)", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(OUTPUT_PATH))
    print(f"테스트 계약서 생성 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_test_contract()
