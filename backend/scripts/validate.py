"""AI Hub Validation 데이터를 이용한 분석 정확도 검증 스크립트.

사용법:
    python -m backend.scripts.validate
    python -m backend.scripts.validate --limit 20    # 일부만 테스트
"""

import argparse
import asyncio
import json
import os
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import SUPPORTED_QUANTIZATIONS, settings
from backend.app.models.clause import Clause
from backend.app.rag.chain import analyze_all_clauses
from backend.app.services.llm_service import switch_quantization_if_needed


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def load_validation_set() -> list[dict]:
    """Validation 불리 + Training 유리 임대차 약관 데이터를 로드."""
    # CLAUDE.md: AI Hub 원천 데이터 위치는 backend/data/raw/aihub/ (프로젝트 루트의 data/raw/가 아님)
    aihub_base = PROJECT_ROOT / "backend" / "data" / "raw" / "aihub" / "01.데이터"
    items = []

    search_paths = [
        # Validation 불리
        (aihub_base / "2.Validation" / "라벨링데이터_230510_add", "validation"),
        # Training 유리 (검증용으로 일부 차용)
        (aihub_base / "1.Training" / "라벨링데이터_230510_add", "training"),
    ]

    for base_path, split in search_paths:
        if not base_path.exists():
            continue
        for root, dirs, files in os.walk(base_path):
            nfc_root = _nfc(root)
            if "약관" not in nfc_root:
                continue
            for f in files:
                nfc_f = _nfc(f)
                if "임대차" not in nfc_f or not nfc_f.endswith(".json"):
                    continue
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                articles = data.get("clauseArticle", [])
                clause_text = "\n".join(articles) if isinstance(articles, list) else str(articles)
                if not clause_text.strip():
                    continue

                dv = str(data.get("dvAntageous", ""))
                # 1=유리(safe), 2=불리(risky)
                ground_truth = "risky" if dv == "2" else "safe"

                items.append({
                    "clause_text": clause_text,
                    "ground_truth": ground_truth,
                    "dv": dv,
                    "filename": nfc_f,
                    "split": split,
                    "basis": data.get("illdcssBasiss", []),
                })

    return items


def prediction_matches(risk_level: str, ground_truth: str) -> bool:
    """LLM 판정과 정답이 일치하는지 확인."""
    if ground_truth == "safe":
        return risk_level in ("safe", "low")
    else:  # risky
        return risk_level in ("high", "medium")


async def run_validation(items: list[dict], save_detail: bool = True) -> dict:
    """검증 실행."""
    total = len(items)
    correct = 0
    results = []
    t_start = time.perf_counter()

    # 오판 분석용
    false_safe = []  # 불리인데 safe/low로 판정 (놓친 위험)
    false_risky = []  # 유리인데 high/medium으로 판정 (거짓 경보)

    print(f"\n검증 시작: 총 {total}건")
    print("=" * 60)

    for i, item in enumerate(items):
        clause = Clause(
            index=0,
            title=f"약관 조항 ({item['filename'][:30]})",
            content=item["clause_text"][:500],
        )

        try:
            result = await analyze_all_clauses([clause])
            parsed_list = result["parsed_list"]

            if parsed_list:
                risk_level = parsed_list[0].get("risk_level", "safe").lower().strip()
                explanation = parsed_list[0].get("explanation", "")
            else:
                risk_level = "safe"
                explanation = "파싱 실패"

        except Exception as e:
            risk_level = "error"
            explanation = str(e)

        gt = item["ground_truth"]
        match = prediction_matches(risk_level, gt)
        if match:
            correct += 1

        icon = "✅" if match else "❌"
        print(f"[{i+1}/{total}] {icon} 정답={gt:5s} 판정={risk_level:6s} | {item['filename'][:40]}")

        if not match:
            if gt == "risky" and risk_level in ("safe", "low"):
                false_safe.append({
                    "filename": item["filename"],
                    "risk_level": risk_level,
                    "text": item["clause_text"][:200],
                    "basis": item["basis"],
                })
            elif gt == "safe" and risk_level in ("high", "medium"):
                false_risky.append({
                    "filename": item["filename"],
                    "risk_level": risk_level,
                    "text": item["clause_text"][:200],
                })

        results.append({
            "filename": item["filename"],
            "ground_truth": gt,
            "prediction": risk_level,
            "match": match,
            "explanation": explanation[:100],
        })

    elapsed = time.perf_counter() - t_start
    sec_per_clause = elapsed / total if total > 0 else 0
    accuracy = correct / total if total > 0 else 0

    # 결과 요약
    print("\n" + "=" * 60)
    print(f"정확도: {correct}/{total} ({accuracy:.1%})")
    print(f"소요시간: {elapsed:.1f}초 (조항당 평균 {sec_per_clause:.2f}초)")

    safe_items = [r for r in results if r["ground_truth"] == "safe"]
    risky_items = [r for r in results if r["ground_truth"] == "risky"]

    safe_correct = sum(1 for r in safe_items if r["match"])
    risky_correct = sum(1 for r in risky_items if r["match"])

    if safe_items:
        print(f"  유리(safe) 정확도: {safe_correct}/{len(safe_items)} ({safe_correct/len(safe_items):.1%})")
    if risky_items:
        print(f"  불리(risky) 정확도: {risky_correct}/{len(risky_items)} ({risky_correct/len(risky_items):.1%})")

    print(f"\n오판 분석:")
    print(f"  놓친 위험 (불리→safe/low): {len(false_safe)}건")
    print(f"  거짓 경보 (유리→high/medium): {len(false_risky)}건")

    if false_safe:
        print(f"\n--- 놓친 위험 TOP 5 ---")
        for item in false_safe[:5]:
            basis = item["basis"][0][:80] if item["basis"] else "근거 없음"
            print(f"  [{item['risk_level']}] {item['filename'][:35]}")
            print(f"    조항: {item['text'][:80]}...")
            print(f"    근거: {basis}")

    if false_risky:
        print(f"\n--- 거짓 경보 TOP 5 ---")
        for item in false_risky[:5]:
            print(f"  [{item['risk_level']}] {item['filename'][:35]}")
            print(f"    조항: {item['text'][:80]}...")

    summary = {
        "accuracy": accuracy,
        "total": total,
        "correct": correct,
        "safe_accuracy": safe_correct / len(safe_items) if safe_items else 0,
        "risky_accuracy": risky_correct / len(risky_items) if risky_items else 0,
        "false_safe_count": len(false_safe),
        "false_risky_count": len(false_risky),
        "total_sec": elapsed,
        "sec_per_clause": sec_per_clause,
    }

    if save_detail:
        output_path = PROJECT_ROOT / "data" / "validation_result.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({**summary, "details": results}, f, ensure_ascii=False, indent=2)
        print(f"\n상세 결과 저장: {output_path}")

    return {
        **summary,
        "false_safe": false_safe,
        "false_risky": false_risky,
    }


async def run_sweep(items: list[dict], tags: list[str]) -> dict:
    """여러 양자화 수준을 순회하며 동일 검증셋으로 측정."""
    sweep_results: dict[str, dict] = {}
    for tag in tags:
        print("\n" + "#" * 60)
        print(f"# 양자화 수준: {tag}")
        print("#" * 60)
        await switch_quantization_if_needed(tag)
        result = await run_validation(items, save_detail=False)
        sweep_results[tag] = {
            "active_model": settings.ollama_model_name,
            "accuracy": result["accuracy"],
            "safe_accuracy": result["safe_accuracy"],
            "risky_accuracy": result["risky_accuracy"],
            "false_safe_count": result["false_safe_count"],
            "false_risky_count": result["false_risky_count"],
            "total_sec": result["total_sec"],
            "sec_per_clause": result["sec_per_clause"],
        }

    print("\n" + "=" * 72)
    print("스윕 비교 결과")
    print("=" * 72)
    header = f"{'tag':<10}{'accuracy':>10}{'safe_acc':>10}{'risky_acc':>12}{'sec/clause':>14}{'total_sec':>12}"
    print(header)
    print("-" * 72)
    for tag, r in sweep_results.items():
        print(
            f"{tag:<10}{r['accuracy']:>10.1%}{r['safe_accuracy']:>10.1%}"
            f"{r['risky_accuracy']:>12.1%}{r['sec_per_clause']:>14.2f}{r['total_sec']:>12.1f}"
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = PROJECT_ROOT / "data" / f"validation_sweep_{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"sweep": sweep_results, "sample_size": len(items)}, f, ensure_ascii=False, indent=2)
    print(f"\n스윕 결과 저장: {output_path}")
    return sweep_results


async def _main(args) -> None:
    items = load_validation_set()
    print(f"검증 데이터 로드: {len(items)}건")
    print(f"  유리(safe): {sum(1 for i in items if i['ground_truth']=='safe')}건")
    print(f"  불리(risky): {sum(1 for i in items if i['ground_truth']=='risky')}건")

    if args.limit > 0:
        # 유리/불리 균형 맞춰서 샘플링
        safe_items_all = [i for i in items if i["ground_truth"] == "safe"]
        risky_items_all = [i for i in items if i["ground_truth"] == "risky"]
        half = args.limit // 2
        items = safe_items_all[:half] + risky_items_all[:args.limit - half]
        print(f"  -> {len(items)}건으로 제한")

    if args.sweep:
        tags = [t.strip() for t in args.sweep.split(",") if t.strip()]
        invalid = [t for t in tags if t not in SUPPORTED_QUANTIZATIONS]
        if invalid:
            raise SystemExit(
                f"지원하지 않는 양자화 수준: {invalid}. 허용 값: {list(SUPPORTED_QUANTIZATIONS)}"
            )
        await run_sweep(items, tags)
        return

    if args.quantization:
        await switch_quantization_if_needed(args.quantization)

    await run_validation(items)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Hub 데이터 기반 분석 정확도 검증")
    parser.add_argument("--limit", type=int, default=0, help="검증 건수 제한 (0=전체)")
    parser.add_argument(
        "--quantization",
        default=None,
        help=f"단일 검증용 양자화 태그. 허용: {list(SUPPORTED_QUANTIZATIONS)}",
    )
    parser.add_argument(
        "--sweep",
        default=None,
        help="쉼표로 구분한 양자화 태그 목록 (예: q2_K,q4_K_M,q8_0). 지정 시 --quantization 무시",
    )
    args = parser.parse_args()

    asyncio.run(_main(args))
