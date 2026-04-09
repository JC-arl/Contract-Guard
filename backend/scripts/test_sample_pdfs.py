"""data/test_*.pdf 4종의 조항별 분석 결과를 기대값과 비교.

사용법:
  python -m backend.scripts.test_sample_pdfs
  python -m backend.scripts.test_sample_pdfs --only standard
"""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services import document_service, clause_service
from backend.app.rag.chain import analyze_all_clauses


# 기대값 — 조항 번호 → 기대 레벨
# safe/low/medium/high. 판정 일치 판단은 "카테고리"로: safe+low vs medium+high
EXPECTED: dict[str, dict[int, str]] = {
  "test_standard_contract.pdf": {
    # 표준 계약서 — 전부 safe여야 함
    1: "safe", 2: "safe", 3: "safe", 4: "safe", 5: "safe",
    6: "safe", 7: "safe", 8: "safe", 9: "safe", 10: "safe",
  },
  "test_jeonse_contract.pdf": {
    1: "safe", 2: "safe", 3: "safe",
    4: "high",    # 후순위 입주 없으면 반환 연기 + 이자 없음
    5: "medium",  # 위약금 20% 쌍방
    6: "safe", 7: "safe", 8: "safe", 9: "safe",
  },
  "test_officetel_contract.pdf": {
    1: "safe", 2: "safe", 3: "safe", 4: "safe",
    5: "medium",  # 해지 통보 비대칭 1개월
    6: "high",    # 증액 20% (법정 5% 초과)
    7: "safe", 8: "safe", 9: "safe", 10: "safe",
  },
  "test_oneroom_contract.pdf": {
    1: "safe", 2: "safe", 3: "safe",
    4: "high",    # 하자 시 무기한 유보 + 청소비 자동 공제
    5: "high",    # 2회 연체 즉시 해지 퇴거
    6: "high",    # 모든 수선 임차인 부담
    7: "high",    # 도배/장판 전액 임차인
    8: "high",    # 반려동물 즉시 퇴거
    9: "high",    # 긴급시 통보없이 임대인 출입
    10: "high",   # "임대인의 결정에 따른다" 일방 결정권
  },
}


def category(level: str) -> str:
  """risk_level을 risky/safe 두 가지로 분류."""
  level = (level or "").lower().strip()
  if level in ("safe", "low"):
    return "safe"
  if level in ("medium", "high"):
    return "risky"
  return "unknown"


def strict_match(actual: str, expected: str) -> bool:
  """엄격 비교 — 정확한 레벨 일치."""
  return (actual or "").lower().strip() == expected.lower().strip()


async def run_one(pdf_name: str) -> dict:
  pdf_path = PROJECT_ROOT / "data" / pdf_name
  text, _ = document_service.extract_text(str(pdf_path))
  contract_type = clause_service.detect_contract_type(text)
  clauses = clause_service.split_clauses(text)

  print(f"\n{'='*72}")
  print(f"📄 {pdf_name}  (유형: {contract_type}, 조항 {len(clauses)}개)")
  print("=" * 72)

  result = await analyze_all_clauses(clauses, contract_type=contract_type)
  parsed = {p["clause_index"]: p for p in result["parsed_list"]}

  expected = EXPECTED[pdf_name]
  rows = []
  strict_correct = 0
  category_correct = 0

  for clause in clauses:
    idx = clause.index
    exp = expected.get(idx, "?")
    obj = parsed.get(idx, {})
    got = (obj.get("risk_level") or "missing").lower()
    expl = (obj.get("explanation") or "")[:80]

    s_match = strict_match(got, exp)
    c_match = category(got) == category(exp)
    if s_match:
      strict_correct += 1
    if c_match:
      category_correct += 1

    icon = "✅" if c_match else ("🔶" if s_match else "❌")
    rows.append({
      "idx": idx,
      "title": clause.title[:30],
      "expected": exp,
      "got": got,
      "category_match": c_match,
      "strict_match": s_match,
      "explanation": expl,
    })
    print(f"  {icon} 제{idx:2d}조 기대={exp:6s} 실제={got:7s} | {clause.title[:28]}")
    if not c_match and expl:
      print(f"       └─ {expl}")

  total = len(clauses)
  print(f"\n  카테고리 일치: {category_correct}/{total} ({category_correct/total:.0%})")
  print(f"  엄격 일치:    {strict_correct}/{total} ({strict_correct/total:.0%})")

  return {
    "pdf": pdf_name,
    "total": total,
    "category_correct": category_correct,
    "strict_correct": strict_correct,
    "rows": rows,
  }


async def main(only: str | None) -> None:
  targets = list(EXPECTED.keys())
  if only:
    targets = [t for t in targets if only in t]

  all_results = []
  for name in targets:
    try:
      all_results.append(await run_one(name))
    except Exception as e:
      print(f"\n❌ {name} 실행 실패: {e}")
      import traceback
      traceback.print_exc()

  # 종합
  print(f"\n{'='*72}")
  print("📊 종합 결과")
  print("=" * 72)
  total = sum(r["total"] for r in all_results)
  cat = sum(r["category_correct"] for r in all_results)
  strict = sum(r["strict_correct"] for r in all_results)
  for r in all_results:
    print(f"  {r['pdf']:35s} 카테고리 {r['category_correct']:2d}/{r['total']:2d}  엄격 {r['strict_correct']:2d}/{r['total']:2d}")
  if total:
    print(f"\n  전체: 카테고리 {cat}/{total} ({cat/total:.0%})  엄격 {strict}/{total} ({strict/total:.0%})")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--only", type=str, default=None, help="특정 파일만 (예: standard)")
  args = parser.parse_args()
  asyncio.run(main(args.only))
