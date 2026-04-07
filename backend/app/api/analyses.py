import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.app.models.analysis import AnalysisResponse, AnalysisResult
from backend.app.config import settings

router = APIRouter()


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str):
    result_file = Path(settings.results_dir) / f"{analysis_id}.json"
    if result_file.exists():
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AnalysisResponse(
            status="completed",
            result=AnalysisResult(**data),
        )

    raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
