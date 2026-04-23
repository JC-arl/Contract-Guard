from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.config import SUPPORTED_QUANTIZATIONS, settings
from backend.app.services.llm_service import switch_quantization_if_needed

router = APIRouter()


class ModelInfo(BaseModel):
    base_model: str
    quantization: str
    active_model: str
    override_active: bool
    supported: list[str]


class QuantizationChangeRequest(BaseModel):
    quantization: str


@router.get("/model", response_model=ModelInfo)
async def get_model_info() -> ModelInfo:
    return ModelInfo(
        base_model=settings.llm_base_model,
        quantization=settings.llm_quantization,
        active_model=settings.ollama_model_name,
        override_active=bool(settings.ollama_model_name_override),
        supported=list(SUPPORTED_QUANTIZATIONS),
    )


@router.post("/model/quantization", response_model=ModelInfo)
async def change_quantization(body: QuantizationChangeRequest) -> ModelInfo:
    try:
        await switch_quantization_if_needed(body.quantization)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return await get_model_info()
