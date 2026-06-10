"""변호사 피드백 jsonl 저장소 — 경로/조회/상태 갱신 공용 유틸.

피드백은 DB가 아니라 `data/verified_rules/{contract_type}.jsonl`에 누적된다.
승인 워크플로우(pending→approved/rejected)를 위해 jsonl을 횡단 조회하고 특정 id의
status를 원자적으로 갱신하는 함수를 모은다. feedback.py(작성)와 admin.py(승인) 양쪽이 사용.
"""

import json
import logging
import os
import re
import uuid
from pathlib import Path

from backend.app.config import DATA_DIR
from backend.app.models.feedback import FeedbackEntry

logger = logging.getLogger(__name__)

FEEDBACK_DIR = Path(DATA_DIR) / "verified_rules"
# contract_type을 파일명에 쓰기 전에 영문·하이픈만 허용 (path traversal 방지)
_CT_SAFE_RE = re.compile(r"[^A-Za-z0-9_-]")


def feedback_path(contract_type: str) -> Path:
    safe = _CT_SAFE_RE.sub("", contract_type or "")[:32]
    if not safe:
        safe = "unknown"
    return FEEDBACK_DIR / f"{safe}.jsonl"


def append_entry(entry: FeedbackEntry) -> None:
    path = feedback_path(entry.contract_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


def _iter_raw_entries():
    """모든 jsonl 파일의 각 라인을 (path, dict)로 순회. 손상 라인은 건너뜀."""
    if not FEEDBACK_DIR.exists():
        return
    for path in FEEDBACK_DIR.glob("*.jsonl"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield path, json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError as e:
            logger.warning(f"피드백 파일 읽기 실패 {path}: {e}")


def _status_of(entry: dict) -> str:
    # 레거시(필드 없음)=approved 로 grandfather 처리
    return entry.get("status") or "approved"


def iter_pending(team_id: int | None) -> list[dict]:
    """status=="pending" 항목. team_id가 주어지면 해당 팀만. 최신순(등록일 내림차순)."""
    out: list[dict] = []
    for _path, entry in _iter_raw_entries():
        if _status_of(entry) != "pending":
            continue
        if team_id is not None and entry.get("team_id") != team_id:
            continue
        out.append(entry)
    out.sort(key=lambda e: e.get("registered_at") or "", reverse=True)
    return out


def count_pending(team_id: int | None) -> int:
    n = 0
    for _path, entry in _iter_raw_entries():
        if _status_of(entry) != "pending":
            continue
        if team_id is not None and entry.get("team_id") != team_id:
            continue
        n += 1
    return n


def count_active_rules(team_id: int | None) -> int:
    """승인된 활성 룰 수 (status==approved and is_rule)."""
    return len(iter_active_rules(team_id))


def iter_active_rules(team_id: int | None) -> list[dict]:
    """승인된 활성 룰 목록 (status==approved and is_rule). team_id 주어지면 해당 팀만. 최신순."""
    out: list[dict] = []
    for _path, entry in _iter_raw_entries():
        if not entry.get("is_rule"):
            continue
        if _status_of(entry) != "approved":
            continue
        if team_id is not None and entry.get("team_id") != team_id:
            continue
        out.append(entry)
    out.sort(key=lambda e: e.get("reviewed_at") or e.get("registered_at") or "", reverse=True)
    return out


def get_entry(entry_id: str) -> dict | None:
    for _path, entry in _iter_raw_entries():
        if entry.get("id") == entry_id:
            return entry
    return None


def update_fields(entry_id: str, changes: dict) -> dict | None:
    """entry_id를 찾아 changes를 병합하고 그 파일을 원자적으로 재작성.

    갱신된 entry dict를 반환(없으면 None). os.replace로 mtime이 갱신되어
    chain.py의 mtime 기반 룰 캐시가 자동 무효화된다.
    """
    if not FEEDBACK_DIR.exists():
        return None

    for path in FEEDBACK_DIR.glob("*.jsonl"):
        lines: list[str] = []
        updated: dict | None = None
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_lines = f.readlines()
        except OSError as e:
            logger.warning(f"피드백 파일 읽기 실패 {path}: {e}")
            continue

        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError:
                lines.append(stripped)  # 손상 라인 보존
                continue
            if updated is None and entry.get("id") == entry_id:
                entry.update(changes)
                updated = entry
            lines.append(json.dumps(entry, ensure_ascii=False))

        if updated is None:
            continue

        # 원자적 재작성: 임시 파일 → os.replace (Windows에서도 atomic, mtime 갱신)
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                for ln in lines:
                    f.write(ln + "\n")
            os.replace(tmp, path)
        except OSError as e:
            logger.exception(f"피드백 갱신 실패 {path}: {e}")
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            return None
        return updated

    return None


def update_status(
    entry_id: str,
    new_status: str,
    reviewer_id: str,
    reviewer_name: str,
    reviewed_at: str,
) -> dict | None:
    """승인/반려 — status와 reviewer 정보를 갱신."""
    return update_fields(entry_id, {
        "status": new_status,
        "reviewed_by": reviewer_id,
        "reviewer_name": reviewer_name,
        "reviewed_at": reviewed_at,
    })


def new_id() -> str:
    return str(uuid.uuid4())
