"""legalize-kr GitHub 저장소에서 Contract-Guard가 다루는 계약 유형 관련 법률 본문을
backend/data/raw/laws/ 디렉토리로 내려받는다.

사용법:
    python -m backend.scripts.download_laws            # 신규 파일만 받음
    python -m backend.scripts.download_laws --force    # 기존 파일도 덮어씀

다운로드 후 build_kb.py가 이 디렉토리를 읽어 ChromaDB에 인덱싱한다.
"""

import argparse
import urllib.parse
import urllib.request
from pathlib import Path

from backend.app.config import DATA_DIR


# 계약 유형 매핑 (build_kb.py와 공유)
LAW_TO_CONTRACT_TYPES: dict[str, list[str]] = {
    "주택임대차보호법": ["lease"],
    "상가건물임대차보호법": ["lease"],
    "민법": ["lease", "sales"],  # 임대차편/매매편 양쪽으로 라우팅 (article_no 범위 필터)
    "공인중개사법": ["sales"],
    "부동산거래신고등에관한법률": ["sales"],
    "근로기준법": ["employment"],
    "최저임금법": ["employment"],
    "기간제및단시간근로자보호등에관한법률": ["employment"],
    "남녀고용평등과일ㆍ가정양립지원에관한법률": ["employment"],
}

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/legalize-kr/legalize-kr/main/kr"
TARGET_FILE = "법률.md"  # 시행령/시행규칙은 일단 제외 (본법 조문이 grounding 핵심)


def _build_url(law_name: str) -> str:
    return f"{GITHUB_RAW_BASE}/{urllib.parse.quote(law_name)}/{urllib.parse.quote(TARGET_FILE)}"


def _download_file(url: str, dest: Path, timeout: int = 30) -> int:
    """파일을 다운로드하여 dest에 저장. 다운로드한 바이트 수 반환."""
    req = urllib.request.Request(url, headers={"User-Agent": "Contract-Guard-KB-Builder"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return len(data)


def download_all(force: bool = False) -> None:
    laws_dir = Path(DATA_DIR) / "raw" / "laws"
    print(f"[다운로드 위치] {laws_dir}")

    success, skipped, failed = 0, 0, 0
    for law_name, contract_types in LAW_TO_CONTRACT_TYPES.items():
        dest = laws_dir / law_name / TARGET_FILE
        if dest.exists() and not force:
            print(f"  [SKIP] {law_name} (이미 존재, --force로 덮어쓰기)")
            skipped += 1
            continue

        url = _build_url(law_name)
        try:
            size = _download_file(url, dest)
            ct_label = ",".join(contract_types)
            print(f"  [OK]   {law_name} ({size:,} bytes, contract_type={ct_label})")
            success += 1
        except Exception as e:
            print(f"  [FAIL] {law_name}: {e}")
            failed += 1

    print(f"\n완료: 성공 {success}, 스킵 {skipped}, 실패 {failed}")
    if success or skipped:
        print(f"빌드: python -m backend.scripts.build_kb --include-laws --clear")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="legalize-kr에서 계약 관련 법률 본문 다운로드")
    parser.add_argument("--force", action="store_true", help="기존 파일도 덮어쓰기")
    args = parser.parse_args()
    download_all(force=args.force)
