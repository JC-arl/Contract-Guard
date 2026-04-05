"""AI HUB 법률 데이터를 파싱하여 ChromaDB에 인덱싱하는 스크립트.

사용법:
    python -m backend.scripts.build_kb --data-dir data/raw/aihub

데이터가 없는 경우 내장 임대차 관련 법률 조항으로 기본 KB를 구축합니다.
"""

import argparse
import json
import uuid
from pathlib import Path


def get_builtin_lease_data() -> list[dict]:
    """내장 임대차보호법 핵심 조항 데이터."""
    return [
        {
            "id": "htlpa-s3",
            "text": "주택임대차보호법 제3조(대항력): 임대차는 그 등기가 없는 경우에도 임차인이 주택의 인도와 주민등록을 마친 때에는 그 다음 날부터 제삼자에 대하여 효력이 생긴다.",
            "metadata": {"source": "주택임대차보호법", "article": "제3조", "topic": "대항력"},
        },
        {
            "id": "htlpa-s3-2",
            "text": "주택임대차보호법 제3조의2(보증금의 회수): 임차인은 임차주택에 대하여 보증금 반환청구소송의 확정판결 기타 이에 준하는 집행권원에 의하여 경매를 신청할 수 있다.",
            "metadata": {"source": "주택임대차보호법", "article": "제3조의2", "topic": "보증금회수"},
        },
        {
            "id": "htlpa-s4",
            "text": "주택임대차보호법 제4조(임대차기간): 기간을 정하지 아니하거나 2년 미만으로 정한 임대차는 그 기간을 2년으로 본다. 다만, 임차인은 2년 미만으로 정한 기간이 유효함을 주장할 수 있다.",
            "metadata": {"source": "주택임대차보호법", "article": "제4조", "topic": "임대차기간"},
        },
        {
            "id": "htlpa-s6",
            "text": "주택임대차보호법 제6조(계약의 갱신): 임대인이 임대차기간이 끝나기 6개월 전부터 2개월 전까지의 기간에 임차인에게 갱신거절의 통지를 하지 아니하거나 계약조건을 변경하지 아니하면 갱신하지 아니한다는 뜻의 통지를 하지 아니한 경우에는 그 기간이 끝난 때에 전 임대차와 동일한 조건으로 다시 임대차한 것으로 본다.",
            "metadata": {"source": "주택임대차보호법", "article": "제6조", "topic": "묵시적갱신"},
        },
        {
            "id": "htlpa-s6-3",
            "text": "주택임대차보호법 제6조의3(계약갱신 요구 등): 임차인은 임대차기간이 끝나기 6개월 전부터 2개월 전까지 계약갱신을 요구할 수 있다. 임대인은 정당한 사유 없이 거절하지 못한다. 갱신되는 임대차의 존속기간은 2년으로 본다.",
            "metadata": {"source": "주택임대차보호법", "article": "제6조의3", "topic": "계약갱신요구권"},
        },
        {
            "id": "htlpa-s7",
            "text": "주택임대차보호법 제7조(차임 등의 증감청구권): 당사자는 약정한 차임이나 보증금이 임차주택에 관한 조세, 공과금, 그 밖의 부담의 증감이나 경제사정의 변동으로 인하여 적절하지 아니하게 된 때에는 장래에 대하여 그 증감을 청구할 수 있다. 증액의 경우에는 약정한 차임 등의 20분의 1의 금액을 초과하지 못한다.",
            "metadata": {"source": "주택임대차보호법", "article": "제7조", "topic": "차임증감"},
        },
        {
            "id": "htlpa-s7-2",
            "text": "주택임대차보호법 제7조의2(월차임 전환 시 산정률의 제한): 보증금의 전부 또는 일부를 월 단위의 차임으로 전환하는 경우에는 그 전환되는 금액에 은행법에 따른 은행의 대출금리와 해당 지역의 경제여건 등을 고려하여 대통령령으로 정하는 비율을 곱한 월차임의 범위를 초과할 수 없다.",
            "metadata": {"source": "주택임대차보호법", "article": "제7조의2", "topic": "월차임전환"},
        },
        {
            "id": "htlpa-s9",
            "text": "주택임대차보호법 제9조(주택의 수선의무): 임대인은 임대주택의 사용·수익에 필요한 상태를 유지하게 할 의무를 부담한다. 다만, 임차인의 책임 있는 사유로 인한 파손은 그러하지 아니하다.",
            "metadata": {"source": "주택임대차보호법", "article": "제9조", "topic": "수선의무"},
        },
        {
            "id": "htlpa-s10",
            "text": "주택임대차보호법 제10조(강행규정): 이 법에 위반된 약정으로서 임차인에게 불리한 것은 그 효력이 없다.",
            "metadata": {"source": "주택임대차보호법", "article": "제10조", "topic": "강행규정"},
        },
        {
            "id": "civil-s623",
            "text": "민법 제623조(임대인의 의무): 임대인은 목적물을 임차인에게 인도하고 계약존속 중 그 사용, 수익에 필요한 상태를 유지하게 할 의무를 부담한다.",
            "metadata": {"source": "민법", "article": "제623조", "topic": "임대인의무"},
        },
        {
            "id": "civil-s624",
            "text": "민법 제624조(임차인의 의무): 임차인은 선량한 관리자의 주의로 임차물을 보존하여야 한다.",
            "metadata": {"source": "민법", "article": "제624조", "topic": "임차인의무"},
        },
        {
            "id": "civil-s625",
            "text": "민법 제625조(임차인의 통지의무): 임차물의 수리를 요하거나 임차물에 대하여 권리를 주장하는 자가 있는 때에는 임차인은 지체없이 임대인에게 이를 통지하여야 한다.",
            "metadata": {"source": "민법", "article": "제625조", "topic": "통지의무"},
        },
        {
            "id": "civil-s626",
            "text": "민법 제626조(임차인의 상환청구권): 임차인이 임차물의 보존에 관한 필요비를 지출한 때에는 임대인에 대하여 그 상환을 청구할 수 있다.",
            "metadata": {"source": "민법", "article": "제626조", "topic": "상환청구권"},
        },
        {
            "id": "civil-s652",
            "text": "민법 제652조(강행규정): 제627조, 제628조, 제631조, 제635조, 제638조, 제640조, 제641조, 제643조 내지 제647조의 규정에 위반하는 약정으로 임차인이나 전차인에게 불리한 것은 그 효력이 없다.",
            "metadata": {"source": "민법", "article": "제652조", "topic": "강행규정"},
        },
        {
            "id": "practice-deposit",
            "text": "임대차 계약 시 보증금 반환 관련 주의사항: 계약 종료 시 보증금은 원칙적으로 임차인이 목적물을 반환한 때에 동시이행으로 반환받을 수 있다. 보증금에서 일방적으로 수리비를 공제하는 조항이나, 보증금 반환 시기를 부당하게 지연시키는 조항은 임차인에게 불리할 수 있다.",
            "metadata": {"source": "판례/실무", "article": "", "topic": "보증금반환"},
        },
        {
            "id": "practice-termination",
            "text": "임대차 계약 해지 관련 주의사항: 임대인이 일방적으로 계약을 해지할 수 있는 조항, 또는 임차인의 사소한 의무 위반을 이유로 즉시 해지가 가능한 조항은 불공정할 수 있다. 주택임대차보호법에 따르면 임차인의 계약갱신요구권이 보장되며, 임대인의 갱신거절은 법정 사유에 해당하는 경우에만 가능하다.",
            "metadata": {"source": "판례/실무", "article": "", "topic": "계약해지"},
        },
        {
            "id": "practice-restoration",
            "text": "원상복구 관련 주의사항: 임차인의 원상복구 의무는 통상적인 사용에 의한 손모(자연 마모)는 포함하지 않는 것이 원칙이다. 도배, 장판 등 통상적인 사용에 의한 변색이나 마모까지 임차인에게 복구 의무를 부과하는 것은 부당할 수 있다.",
            "metadata": {"source": "판례/실무", "article": "", "topic": "원상복구"},
        },
        {
            "id": "practice-penalty",
            "text": "위약금 관련 주의사항: 임대차 계약에서 위약금이 보증금의 일정 비율을 초과하거나, 임차인에게만 과도한 위약금을 부과하는 조항은 공정성에 문제가 있을 수 있다. 판례에 따르면 부당하게 과다한 위약금 약정은 법원에 의해 감액될 수 있다.",
            "metadata": {"source": "판례/실무", "article": "", "topic": "위약금"},
        },
    ]


LEASE_KEYWORDS = ["임대", "임차", "보증금", "차임", "월세", "전세", "임대차", "주택임대"]


def _is_lease_related(text: str) -> bool:
    return any(kw in text for kw in LEASE_KEYWORDS)


def _normalize_filename(name: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFC", name)


def _load_clause_data(data_path: Path) -> list[dict]:
    """약관 라벨링데이터(JSON)에서 임대차계약 관련 항목을 파싱."""
    items = []
    for json_file in data_path.rglob("*.json"):
        nfc_name = _normalize_filename(json_file.name)
        if "임대차" not in nfc_name:
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        # 약관 조항 텍스트
        articles = data.get("clauseArticle", [])
        clause_text = "\n".join(articles) if isinstance(articles, list) else str(articles)
        if not clause_text.strip():
            continue

        # 위법성 판단 근거
        bases = data.get("illdcssBasiss", [])
        basis_text = "\n".join(bases) if isinstance(bases, list) else str(bases)

        # 관련 법령
        laws = data.get("relateLaword", [])
        law_text = "\n".join(laws) if isinstance(laws, list) else str(laws)

        # 유불리 판단: "1"=유리, "2"=불리
        dv = data.get("dvAntageous", "")
        advantage = "불리" if str(dv) == "2" else "유리"

        # 불리한 조항 유형
        unfav = data.get("unfavorableProvision", "")

        # 조합된 텍스트
        combined = f"[약관-{advantage}] {clause_text}"
        if basis_text.strip():
            combined += f"\n판단근거: {basis_text}"
        if law_text.strip():
            combined += f"\n관련법령: {law_text}"

        items.append({
            "id": str(uuid.uuid4()),
            "text": combined[:2000],
            "metadata": {
                "source": "aihub_약관",
                "filename": nfc_name,
                "topic": "임대차_약관",
                "advantage": advantage,
            },
        })

    return items


def _load_judgment_data(data_path: Path) -> list[dict]:
    """판결문 라벨링데이터(JSON)에서 임대차 관련 민사 판결문을 파싱."""
    items = []
    # 민사 판결문만 탐색
    for json_file in data_path.rglob("*.json"):
        nfc_path = _normalize_filename(str(json_file))
        if "민사" not in nfc_path:
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        # 사건명으로 1차 필터
        info = data.get("info", {})
        case_nm = info.get("caseNm", "")
        relate_laws = info.get("relateLaword", [])
        law_str = " ".join(relate_laws) if isinstance(relate_laws, list) else str(relate_laws)

        # 기초사실 + 판단 텍스트 (dict 안에 list가 중첩된 구조)
        facts_raw = data.get("facts", {})
        if isinstance(facts_raw, dict):
            facts_list = []
            for v in facts_raw.values():
                if isinstance(v, list):
                    facts_list.extend(v)
            facts_text = "\n".join(facts_list)
        else:
            facts_text = str(facts_raw)

        dcss_raw = data.get("dcss", {})
        if isinstance(dcss_raw, dict):
            dcss_list = []
            for v in dcss_raw.values():
                if isinstance(v, list):
                    dcss_list.extend(v)
            dcss_text = "\n".join(dcss_list)
        else:
            dcss_text = str(dcss_raw)

        full_text = f"{case_nm} {law_str} {facts_text} {dcss_text}"

        # 임대차 관련 여부 확인
        if not _is_lease_related(full_text):
            continue

        case_no = info.get("caseNo", "")
        court = info.get("courtNm", "")

        combined = f"[판결문] {court} {case_no} - {case_nm}"
        if facts_text.strip():
            combined += f"\n기초사실: {facts_text[:800]}"
        if dcss_text.strip():
            combined += f"\n판단: {dcss_text[:800]}"
        if law_str.strip():
            combined += f"\n관련법령: {law_str}"

        items.append({
            "id": str(uuid.uuid4()),
            "text": combined[:2000],
            "metadata": {
                "source": "aihub_판결문",
                "case_no": case_no,
                "court": court,
                "topic": "임대차_판결",
            },
        })

    return items


def load_aihub_data(data_dir: str) -> list[dict]:
    """AI HUB 법률 데이터에서 임대차 관련 항목을 추출."""
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"[INFO] 데이터 디렉토리가 없습니다: {data_dir}")
        return []

    print("  약관 데이터 로딩 중...")
    clause_items = _load_clause_data(data_path)
    print(f"    약관 임대차: {len(clause_items)}건")

    print("  판결문 데이터 로딩 중...")
    judgment_items = _load_judgment_data(data_path)
    print(f"    판결문 임대차: {len(judgment_items)}건")

    return clause_items + judgment_items


def build_knowledge_base(data_dir: str | None = None):
    from backend.app.services import chroma_service

    print("[1/2] 데이터 수집 중...")
    items = get_builtin_lease_data()
    print(f"  내장 데이터: {len(items)}건")

    if data_dir:
        aihub_items = load_aihub_data(data_dir)
        print(f"  AI HUB 데이터: {len(aihub_items)}건")
        items.extend(aihub_items)

    print(f"[2/2] 임베딩 생성 + ChromaDB 저장 중... (총 {len(items)}건)")
    ids = [item["id"] for item in items]
    texts = [item["text"] for item in items]
    metadatas = [item.get("metadata", {}) for item in items]

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        chroma_service.add_documents(
            ids=ids[i:end],
            documents=texts[i:end],
            metadatas=metadatas[i:end],
        )

    status = chroma_service.collection_status()
    print(f"완료! 컬렉션 '{status['name']}' 에 {status['count']}건 저장됨.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="임대차 법률 지식베이스 구축")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="AI HUB 데이터 디렉토리 경로 (없으면 내장 데이터만 사용)",
    )
    args = parser.parse_args()
    build_knowledge_base(data_dir=args.data_dir)
