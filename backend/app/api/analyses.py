import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.app.models.analysis import AnalysisResponse, AnalysisResult
from backend.app.config import settings

router = APIRouter()

# 인메모리 결과 저장소 (MVP)
_results: dict[str, dict] = {}


def store_result(result: AnalysisResult):
    _results[result.id] = result.model_dump()
    results_dir = Path(settings.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / f"{result.id}.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    if analysis_id in _results:
        return AnalysisResponse(
            status="completed",
            result=AnalysisResult(**_results[analysis_id]),
        )

    result_file = Path(settings.results_dir) / f"{analysis_id}.json"
    if result_file.exists():
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AnalysisResponse(
            status="completed",
            result=AnalysisResult(**data),
        )

    raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
